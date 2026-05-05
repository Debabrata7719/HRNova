"""Chat Router - Handles chat endpoints for NovaHR"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import APIRouter, HTTPException, Depends
from api.models import ChatRequest, ChatResponse, SessionInfo
from api.dependencies.auth import get_current_user
from src.main_agent import run_main_agent
from src.utils.memory_store import get_memory_store
from src.utils.memory_filter import is_important, should_store_agent_response
from typing import Dict

router = APIRouter()

# In-memory session store
sessions: Dict[str, dict] = {}

# Memory store — initialized lazily on first use to avoid slow startup
_memory_store = None

def get_memory():
    """Lazy-load memory store so it doesn't block server startup."""
    global _memory_store
    if _memory_store is None:
        _memory_store = get_memory_store()
    return _memory_store


def get_initial_state(employee_id: int = 0, employee_name: str = "", role: str = "EMPLOYEE") -> dict:
    """
    Returns a fresh initial state for a new session.

    Args:
        employee_id: Employee ID from JWT token
        employee_name: Employee name from JWT token
        role: User role from JWT token (HR or EMPLOYEE)

    Returns:
        Initial state dictionary
    """
    return {
        "input": "",
        "intent": "",
        "step": "initial",
        "leave_data": {},
        "email_data": {},
        "schedule_data": {},
        "output": "",
        "employee_id": employee_id,
        "employee_name": employee_name,
        "role": role,
        "schedule_title": "",
        "schedule_date": "",
        "schedule_time": "",
        "schedule_description": "",
        "leave_agent_memory": {},
        "email_agent_memory": {},
        "general_agent_memory": {},
        "query_agent_memory": {},
        "schedule_agent_memory": {},
        "long_term_memory": [],  # Long-term memory from ChromaDB
        "session_summaries": {},
    }


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, user=Depends(get_current_user)):
    """
    Process a chat message and return the agent's response.
    Requires a valid JWT token in the Authorization header.
    
    Now includes long-term memory:
    - Retrieves relevant past memories before processing
    - Stores important information after processing

    Args:
        request: ChatRequest with message and session_id
        user: Decoded JWT payload (injected by get_current_user)

    Returns:
        ChatResponse with agent's response and session state

    Raises:
        HTTPException 401: If token is invalid
        HTTPException 500: If agent processing fails
    """
    try:
        # Extract user info from JWT token
        employee_id = user.get("user_id", 0)
        employee_name = user.get("name", "")
        role = user.get("role", "EMPLOYEE")
        user_id = str(employee_id)
        user_input = request.message

        # 🔍 STEP 1: Retrieve relevant long-term memories
        memories = get_memory().search_memory(user_id, user_input, n_results=3)
        
        # Get or create session
        if request.session_id not in sessions:
            sessions[request.session_id] = get_initial_state(
                employee_id=employee_id,
                employee_name=employee_name,
                role=role
            )

        # Get current state
        state = sessions[request.session_id]

        # 🧠 STEP 2: Inject memories into state
        state["long_term_memory"] = memories
        
        # Inject user message
        state["input"] = user_input

        # 🤖 STEP 3: Run through agent pipeline
        state = run_main_agent(state)

        # Save updated state back to session
        sessions[request.session_id] = state
        
        response_text = state.get("output", "")
        current_intent = state.get("intent", None)
        current_step = state.get("step", None)

        # 💾 STEP 4: Store important information in long-term memory
        # Store user input if important
        if is_important(user_input, intent=current_intent, step=current_step):
            get_memory().add_memory(
                user_id=user_id,
                text=user_input,
                metadata={
                    "intent": current_intent,
                    "step": current_step,
                    "type": "user_input"
                }
            )
        
        # Store agent response if it's a confirmation or completion
        if should_store_agent_response(response_text, intent=current_intent, step=current_step):
            get_memory().add_memory(
                user_id=user_id,
                text=response_text,
                metadata={
                    "intent": current_intent,
                    "step": current_step,
                    "type": "agent_response"
                }
            )

        return ChatResponse(
            response=response_text,
            session_id=request.session_id,
            intent=current_intent,
            step=current_step
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Agent processing failed: {str(e)}"
        )


@router.get("/chat/session/{session_id}", response_model=SessionInfo)
async def get_session(session_id: str, user=Depends(get_current_user)):
    """
    Get information about a specific session.
    Requires a valid JWT token.

    Args:
        session_id: The session ID to query
        user: Decoded JWT payload (injected by get_current_user)

    Returns:
        SessionInfo with session state information
    """
    if session_id in sessions:
        state = sessions[session_id]
        return SessionInfo(
            session_id=session_id,
            intent=state.get("intent", None),
            step=state.get("step", None),
            exists=True
        )
    else:
        return SessionInfo(
            session_id=session_id,
            intent=None,
            step=None,
            exists=False
        )


@router.delete("/chat/session/{session_id}")
async def delete_session(session_id: str, user=Depends(get_current_user)):
    """
    Delete a session and clear its state.
    Requires a valid JWT token.

    Args:
        session_id: The session ID to delete
        user: Decoded JWT payload (injected by get_current_user)

    Returns:
        Success or not found message
    """
    if session_id in sessions:
        del sessions[session_id]
        return {"message": "Session cleared successfully"}
    else:
        return {"message": "Session not found"}


@router.get("/chat/sessions")
async def list_sessions(user=Depends(get_current_user)):
    """
    List all active sessions (for debugging/monitoring).
    Requires a valid JWT token.

    Returns:
        Dictionary with session count and session IDs
    """
    return {
        "total_sessions": len(sessions),
        "session_ids": list(sessions.keys())
    }
