"""
General conversation agent for handling non-task messages
Provides friendly responses using LLM when user is just chatting
Now includes conversation history with ConversationBufferWindowMemory (window: 7)
"""

from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from dotenv import load_dotenv
from src.main_agent.memory import (
    create_memory_list_from_dict,
    serialize_memory_for_state,
    add_user_message_to_memory,
    add_assistant_message_to_memory,
)
from langsmith import traceable
import os

# Load environment variables
load_dotenv()

# Initialize Groq LLM
llm = ChatGroq(
    model="llama-3.3-70b-versatile", temperature=0.7, api_key=os.getenv("GROQ_API_KEY")
)

SYSTEM_PROMPT = """You are a friendly HR Assistant chatbot. You are helpful, professional, and conversational. 
When users send general messages (not task-related), respond naturally and helpfully.
Keep responses concise and friendly (1-2 sentences).
If the user seems to want help with a task (leave requests, emails, etc.), suggest they can ask you directly for those tasks.

IMPORTANT: You have access to long-term memory about this user. Use it to personalize your responses and remember past conversations."""


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
                messages.append(HumanMessage(content=f"Assistant: {msg['content']}"))

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
        # Fallback response if LLM fails
        print(f"[LLM Error] {type(e).__name__}: {str(e)[:100]}")
        state["output"] = (
            "I'm here to help with: leave requests, sending emails, or general HR questions."
        )
        state["step"] = "completed"
        # Still save memory even on error
        state["general_agent_memory"] = serialize_memory_for_state(memory)

    return state
