"""
General conversation agent for handling non-task messages
Provides friendly responses using LLM when user is just chatting
"""

from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from dotenv import load_dotenv
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
If the user seems to want help with a task (leave requests, emails, etc.), suggest they can ask you directly for those tasks."""


def general_agent(state):
    """
    Handle general conversation with users using LLM.

    Args:
        state: Dictionary containing 'input' key

    Returns:
        state: Updated dictionary with 'output' key
    """
    user_input = state.get("input", "").strip()

    # Handle empty input
    if not user_input:
        state["output"] = (
            "I'm here to help! Feel free to ask me anything about HR matters."
        )
        state["step"] = "completed"
        return state

    try:
        # Generate response using LLM with proper message format
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=user_input),
        ]
        response = llm.invoke(messages)

        state["output"] = response.content.strip()
        state["step"] = "completed"

    except Exception as e:
        # Fallback response if LLM fails - with error details for debugging
        print(f"[LLM Error] {type(e).__name__}: {str(e)[:100]}")
        state["output"] = (
            "I'm here to help with: leave requests, sending emails, or general HR questions."
        )
        state["step"] = "completed"

    return state
