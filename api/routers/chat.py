"""Chat Router - Handles chat endpoints for NovaHR"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import APIRouter, HTTPException
from api.models import ChatRequest, ChatResponse, SessionInfo
from src.main_agent import run_main_agent
from typing import Dict

router = APIRouter()

# In-memory session store
sessions: Dict[str, dict] = {}


def get_initial_state(employee_id: int = 0, employee_name: str = "") -> dict:
    """
    Returns a fresh initial state for a new session.
    
    Args:
        employee_id: Employee ID (0 for HR/anonymous)
        employee_name: Employee name (empty for HR/anonymous)
    
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
        "schedule_title": "",
        "schedule_date": "",
        "schedule_time": "",
        "schedule_description": "",
        "leave_agent_memory": {},
        "email_agent_memory": {},
        "general_agent_memory": {},
        "query_agent_memory": {},
        "schedule_agent_memory": {},
        "session_summaries": {},
    }


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Process a chat message and return the agent's response.
    
    This endpoint:
    - Creates or retrieves a session based on session_id
    - Processes the message through the NovaHR agent pipeline
    - Returns the agent's response along with session state
    
    Args:
        request: ChatRequest containing message, session_id, role, employee info
    
    Returns:
        ChatResponse with agent's response and session state
    
    Raises:
        HTTPException: 500 if agent processing fails
    """
    try:
        # Get or create session
        if request.session_id not in sessions:
            # Create new session with initial state
            sessions[request.session_id] = get_initial_state(
                employee_id=request.employee_id,
                employee_name=request.employee_name
            )
        
        # Get current state
        state = sessions[request.session_id]
        
        # Inject user message
        state["input"] = request.message
        
        # Run through agent pipeline
        state = run_main_agent(state)
        
        # Save updated state back to session
        sessions[request.session_id] = state
        
        # Extract response
        response = state.get("output", "")
        intent = state.get("intent", None)
        step = state.get("step", None)
        
        return ChatResponse(
            response=response,
            session_id=request.session_id,
            intent=intent,
            step=step
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Agent processing failed: {str(e)}"
        )


@router.get("/chat/session/{session_id}", response_model=SessionInfo)
async def get_session(session_id: str):
    """
    Get information about a specific session.
    
    Args:
        session_id: The session ID to query
    
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
async def delete_session(session_id: str):
    """
    Delete a session and clear its state.
    
    Args:
        session_id: The session ID to delete
    
    Returns:
        Success or not found message
    """
    if session_id in sessions:
        del sessions[session_id]
        return {"message": "Session cleared successfully"}
    else:
        return {"message": "Session not found"}


@router.get("/chat/sessions")
async def list_sessions():
    """
    List all active sessions (for debugging/monitoring).
    
    Returns:
        Dictionary with session count and session IDs
    """
    return {
        "total_sessions": len(sessions),
        "session_ids": list(sessions.keys())
    }
