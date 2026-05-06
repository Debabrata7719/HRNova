"""
General conversation agent for handling non-task messages
Provides friendly responses using LLM when user is just chatting
Now includes conversation history with ConversationBufferWindowMemory (window: 7)
"""

from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
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

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.7,
    api_key=_settings.GROQ_API_KEY,
)

SYSTEM_PROMPT = """You are NovaHR, an AI-powered HR Assistant chatbot built to help employees with HR tasks.

Your name is NovaHR. Always introduce yourself as NovaHR when asked.

You are helpful, professional, and conversational. Keep responses concise and friendly (1-2 sentences).

You can ANSWER QUESTIONS about:
- Leave requests, leave balance, leave status
- Company policy questions
- General HR questions
- Past conversations (using your memory)

You can GUIDE users to perform actions by telling them what to say, but you CANNOT perform these actions yourself:
- Scheduling meetings → tell the user to say "schedule a meeting at [time]"
- Sending emails → tell the user to say "send an email to [person]"
- Applying for leave → tell the user to say "I want to apply for leave"

CRITICAL RULES — NEVER BREAK THESE:
1. NEVER say "I've scheduled", "I've sent", "I've booked", "I've created" — you cannot perform these actions
2. NEVER pretend to schedule a meeting, send an email, or submit a leave request
3. If a user asks you to do something like "do same for tomorrow 4pm", tell them to use the proper command
4. If asked about past actions from memory, you can CONFIRM what was done, but do NOT re-do it yourself
5. If the user asks your name, say: "I'm NovaHR, your AI HR assistant!"
6. If the user asks you to remember something, confirm you've noted it

IMPORTANT: You have access to long-term memory about this user from past sessions. Use it to personalize your responses."""


@traceable(name="General Agent")
def general_agent(state):
    """
    Handle general conversation with users using LLM with conversation memory.

    Uses ConversationBufferWindowMemory with a window size of 7 messages.
    When the window fills, old messages are automatically summarized before being dropped.

    Args:
        state: Dictionary containing 'input' key and 'general_agent_memory' key

    Returns:
        state: Updated dictionary with 'output' key and updated 'general_agent_memory'
    """
    user_input = state.get("input", "").strip()

    # If router already set a response (e.g. blocked feature for this role), pass through
    if state.get("step") == "completed" and state.get("output"):
        return state

    # Extract memory from state (window size: 7)
    memory_dict = state.get("general_agent_memory", {})
    memory = create_memory_list_from_dict(memory_dict)
    # Ensure correct window size for general_agent
    memory.window_size = 7

    # Handle empty input
    if not user_input:
        state["output"] = (
            "I'm here to help! Feel free to ask me anything about HR matters."
        )
        state["step"] = "completed"
        state["general_agent_memory"] = serialize_memory_for_state(memory)
        return state

    try:
        # Add user message to memory
        add_user_message_to_memory(memory, user_input)

        # Build message list for LLM from conversation history
        messages = [SystemMessage(content=SYSTEM_PROMPT)]
        
        # 🧠 Add long-term memory context if available
        long_term_memory = state.get("long_term_memory", [])
        if long_term_memory:
            memory_context = "\n".join([f"- {mem}" for mem in long_term_memory])
            messages.append(SystemMessage(
                content=f"[PAST MEMORY ABOUT THIS USER]\n{memory_context}\n[END MEMORY]\n\nUse this information to personalize your response if relevant."
            ))

        # Add all messages from memory to context
        for msg in memory.messages:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))

        # Generate response using LLM
        response = llm.invoke(messages)
        assistant_response = response.content.strip()

        # Add assistant response to memory
        add_assistant_message_to_memory(memory, assistant_response)

        state["output"] = assistant_response
        state["step"] = "completed"

        # Serialize memory back to state
        state["general_agent_memory"] = serialize_memory_for_state(memory)

    except Exception as e:
        logger.error("General agent LLM error: %s: %s", type(e).__name__, str(e)[:100])
        state["output"] = (
            "I'm here to help with: leave requests, sending emails, or general HR questions."
        )
        state["step"] = "completed"
        # Still save memory even on error
        state["general_agent_memory"] = serialize_memory_for_state(memory)

    return state
