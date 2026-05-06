"""
Query Agent for Policy and Leave Balance
Answers employee queries using ChromaDB (policy) + MySQL (leave balance)
"""

import os
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from src.tools.db_connection import get_db
from src.config import get_settings
from src.logger import get_logger
from src.main_agent.memory import (
    create_memory_list_from_dict,
    serialize_memory_for_state,
    add_user_message_to_memory,
    add_assistant_message_to_memory,
)
from langsmith import traceable

logger = get_logger(__name__)
_settings = get_settings()

# Initialize Groq LLM
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.3,
    api_key=_settings.GROQ_API_KEY,
)

# ChromaDB settings
COLLECTION_NAME = "novahr_policy"
# Get base directory (project root)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
DB_DIRECTORY = os.path.join(BASE_DIR, "data", "chroma_db")

# Leave types and their limits
LEAVE_POLICY = {
    "EL": 18,  # Earned Leave
    "CL": 12,  # Casual Leave
    "SL": 12,  # Sick Leave
}


def get_policy_db():
    """Load policy vector database"""
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    db = Chroma(
        persist_directory=DB_DIRECTORY,
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
    )
    return db


def query_policy_chunks(query: str, k: int = 3) -> list[str]:
    """Query policy database for relevant chunks"""
    try:
        db = get_policy_db()
        results = db.similarity_search(query, k=k)
        return [doc.page_content for doc in results]
    except Exception as e:
        logger.error("Policy DB error: %s", e)
        return []


def get_employee_balance(employee_id: int) -> dict:
    """Get leave balance for an employee from MySQL"""
    db = get_db()
    balance = {}

    for leave_type in LEAVE_POLICY:
        query = """
        SELECT COALESCE(SUM(days), 0) as total_used
        FROM leaves
        WHERE employee_id = %s 
        AND leave_type = %s 
        AND status IN ('approved', 'pending')
        """
        result = db.execute_query(query, (employee_id, leave_type))
        used_days = result[0]["total_used"] if result else 0
        allowed_days = LEAVE_POLICY[leave_type]
        balance[leave_type] = {
            "used": used_days,
            "allowed": allowed_days,
            "remaining": allowed_days - used_days,
        }

    return balance


def format_balance_response(balance: dict) -> str:
    """Format balance as readable response"""
    response = "Your Leave Balance:\n"
    for lt, data in balance.items():
        name = {"EL": "Earned", "CL": "Casual", "SL": "Sick"}[lt]
        response += f"  {lt} ({name}): {data['used']} used, {data['remaining']} remaining out of {data['allowed']}\n"
    return response


def get_leave_status(employee_id: int) -> list:
    """Get all leave requests for employee (approved + pending + rejected)"""
    db = get_db()
    query = """
    SELECT start_date, end_date, leave_type, days, status, reason, submitted_at
    FROM leaves 
    WHERE employee_id = %s
    ORDER BY submitted_at DESC
    """
    result = db.execute_query(query, (employee_id,))
    return result if result else []


def format_status_response(leaves: list) -> str:
    """Format leave status as readable response"""
    if not leaves:
        return "You have no leave requests on record."

    response = "Your Leave Requests:\n"
    for i, leave in enumerate(leaves, 1):
        status = leave["status"].upper().replace("_", " ")
        response += f"{i}. {leave['start_date']} to {leave['end_date']} ({leave['leave_type']}) - {leave['days']} day(s) - {status}\n"
        response += f"   Reason: {leave['reason']}\n"
    return response


SYSTEM_PROMPT = """You are NovaHR, an AI-powered HR Assistant. Your name is NovaHR.

You specialize in answering employee questions about company policies and leave balances.

Rules:
1. For leave balance questions — use the provided balance data directly
2. For policy questions — use the retrieved policy chunks to answer
3. If you don't know the answer, say so honestly
4. Keep responses clear and concise
5. If referring to policy, mention the source
6. If asked your name, say: "I'm NovaHR, your AI HR assistant!"
"""


@traceable(name="Query Agent")
def query_agent(state: dict) -> dict:
    """
    Handle policy and leave balance queries.

    State should have:
    - input: user query
    - employee_id: employee ID (for balance queries)
    - employee_name: employee name (for identification)
    - query_agent_memory: memory dict

    Returns state with output and updated memory.
    """
    user_input = state.get("input", "").strip()
    employee_id = state.get("employee_id", 0)
    employee_name = state.get("employee_name", "")
    step = state.get("step", "initial")

    # Get memory
    memory_dict = state.get("query_agent_memory", {})
    memory = create_memory_list_from_dict(memory_dict)
    memory.window_size = 10

    # Add user message to memory
    add_user_message_to_memory(memory, user_input)

    try:
        # Step 1: Identify employee if not logged in
        if step == "initial" or step == "identify_employee":
            if not employee_name and employee_id == 0:
                # First time - user needs to provide name
                if not user_input:
                    response = "I can help with leave balance and policy questions. What's your name?"
                    state["step"] = "identify_employee"
                    state["output"] = response
                    state["query_agent_memory"] = serialize_memory_for_state(memory)
                    return state

                # Search for employee
                from src.main_agent.agents.leave.executor import find_employee

                emp = find_employee(user_input)
                if emp:
                    employee_id = emp["id"]
                    employee_name = emp["name"]
                    state["employee_id"] = employee_id
                    state["employee_name"] = employee_name
                    state["step"] = "query"
                else:
                    response = f"I couldn't find employee '{user_input}'. Please provide your exact name."
                    state["step"] = "identify_employee"
                    state["output"] = response
                    state["query_agent_memory"] = serialize_memory_for_state(memory)
                    return state
            else:
                step = "query"

        # Now answer the query
        user_lower = user_input.lower()

        # Build base messages with long-term memory context
        long_term_memory = state.get("long_term_memory", [])
        base_messages = [SystemMessage(content=SYSTEM_PROMPT)]
        if long_term_memory:
            memory_context = "\n".join([f"- {mem}" for mem in long_term_memory])
            base_messages.append(SystemMessage(
                content=f"[PAST MEMORY ABOUT THIS USER]\n{memory_context}\n[END MEMORY]"
            ))

        # Check if asking about POLICY (not balance) - higher priority
        if "policy" in user_lower or "what is" in user_lower or "explain" in user_lower:
            if not any(
                word in user_lower
                for word in ["balance", "remaining", "left", "how many"]
            ):
                # Query policy from ChromaDB
                chunks = query_policy_chunks(user_input, k=3)
                if chunks:
                    context = "\n\n".join([f"Policy: {chunk}" for chunk in chunks])
                    messages = base_messages + [
                        HumanMessage(
                            content=f"Context from company policy:\n{context}\n\nQuestion: {user_input}"
                        ),
                    ]
                    llm_response = llm.invoke(messages)
                    response = llm_response.content.strip()
                else:
                    response = "I couldn't find relevant policy information."
                # Add response to memory and return
                add_assistant_message_to_memory(memory, response)
                state["output"] = response
                state["query_agent_memory"] = serialize_memory_for_state(memory)
                state["step"] = "completed"
                return state

        # Check if asking about leave balance
        if any(
            word in user_lower for word in ["balance", "how many", "remaining", "left"]
        ):
            if "leave" in user_lower or any(
                lt.lower() in user_lower
                for lt in ["el", "cl", "sl", "earned", "casual", "sick"]
            ):
                if employee_id:
                    balance = get_employee_balance(employee_id)
                    response = format_balance_response(balance)
                else:
                    response = "Please provide your name first to check leave balance."
            else:
                response = "I can check your leave balance. Please provide your name."

        # Check if asking about leave status (approved/pending/rejected)
        elif any(
            word in user_lower
            for word in [
                "status",
                "approved",
                "pending",
                "rejected",
                "my leave",
                "leave request",
                "is it approved",
                "is my leave",
            ]
        ):
            if employee_id:
                leaves = get_leave_status(employee_id)
                response = format_status_response(leaves)
            else:
                response = "Please provide your name first to check leave status."

        # Check if asking about specific leave type balance
        elif any(
            lt.lower() in user_lower
            for lt in ["el", "cl", "sl", "earned", "casual", "sick"]
        ):
            if employee_id:
                balance = get_employee_balance(employee_id)
                for lt in ["EL", "CL", "SL"]:
                    if lt.lower() in user_lower:
                        data = balance[lt]
                        name = {"EL": "Earned", "CL": "Casual", "SL": "Sick"}[lt]
                        response = f"{lt} ({name}): {data['used']} used, {data['remaining']} remaining out of {data['allowed']}"
                        break
                else:
                    response = format_balance_response(balance)
            else:
                response = "Please provide your name first."

        # Otherwise, query policy from ChromaDB
        else:
            # Get relevant policy chunks
            chunks = query_policy_chunks(user_input, k=3)

            if chunks:
                # Build context from chunks
                context = "\n\n".join([f"Policy: {chunk}" for chunk in chunks])

                # Create messages for LLM
                messages = base_messages + [
                    HumanMessage(
                        content=f"Context from company policy:\n{context}\n\nQuestion: {user_input}"
                    ),
                ]

                # Get LLM response
                llm_response = llm.invoke(messages)
                response = llm_response.content.strip()
            else:
                response = "I couldn't find relevant policy information. Could you please rephrase your question?"

        # Add response to memory
        add_assistant_message_to_memory(memory, response)

    except Exception as e:
        logger.error("Query agent error: %s", e)
        response = "I'm having trouble processing your request. Please try again."
        add_assistant_message_to_memory(memory, response)

    # Update state
    state["output"] = response
    state["query_agent_memory"] = serialize_memory_for_state(memory)
    state["step"] = "completed"

    return state
