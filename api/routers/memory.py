"""
Memory Management Router - Admin endpoints for memory operations
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import APIRouter, Depends, HTTPException
from api.dependencies.auth import get_current_user
from src.utils.memory_store import get_memory_store
from pydantic import BaseModel

router = APIRouter()
memory_store = get_memory_store()


class CleanupRequest(BaseModel):
    """Request model for memory cleanup"""
    days: int = 30

    class Config:
        # Allow days=0 (delete all)
        json_schema_extra = {"example": {"days": 30}}


@router.get("/memory/stats")
def get_memory_stats(user=Depends(get_current_user)):
    """
    Get memory statistics.
    Available to all authenticated users.
    
    Returns:
        Total memory count and collection info
    """
    stats = memory_store.get_stats()
    return stats


@router.get("/memory/user")
def get_user_memories(user=Depends(get_current_user)):
    """
    Get all memories for the current user.
    Users can only see their own memories.
    
    Returns:
        List of user's memories with metadata
    """
    user_id = str(user.get("user_id"))
    memories = memory_store.get_all_memories(user_id, limit=50)
    
    return {
        "user_id": user_id,
        "total_memories": len(memories),
        "memories": memories
    }


@router.get("/memory/all")
def get_all_users_memories(user=Depends(get_current_user)):
    """
    Get memories for ALL users (HR only).
    Returns memories grouped by user_id.
    
    Returns:
        Dict keyed by user_id with memory lists
    """
    # Check if user is HR
    if user.get("role") != "HR":
        raise HTTPException(
            status_code=403,
            detail="Only HR can view all users' memories"
        )
    
    memories_by_user = memory_store.get_all_users_memories(limit=200)
    
    # Calculate total
    total = sum(len(mems) for mems in memories_by_user.values())
    
    return {
        "total_memories": total,
        "total_users": len(memories_by_user),
        "memories_by_user": memories_by_user
    }


@router.delete("/memory/user")
def clear_user_memories(user=Depends(get_current_user)):
    """
    Clear all memories for the current user.
    Users can only delete their own memories.
    
    Returns:
        Success message
    """
    user_id = str(user.get("user_id"))
    memory_store.clear_user_memories(user_id)
    
    return {
        "message": f"All memories cleared for user {user_id}",
        "user_id": user_id
    }


@router.post("/memory/cleanup")
def cleanup_old_memories(
    request: CleanupRequest,
    user=Depends(get_current_user)
):
    """
    Delete old memories manually (HR only).
    Deletes memories older than specified days.
    
    Note: Automatic cleanup runs daily at 2 AM (deletes 30+ day old memories).
    Use this endpoint to run cleanup manually or with custom days.
    
    Args:
        request: CleanupRequest with days parameter
        
    Returns:
        Cleanup result
    """
    # Check if user is HR
    if user.get("role") != "HR":
        raise HTTPException(
            status_code=403,
            detail="Only HR can perform memory cleanup"
        )
    
    # Get stats before cleanup
    stats_before = memory_store.get_stats()
    
    # Run cleanup
    memory_store.cleanup_old_memories(days=request.days)
    
    # Get stats after cleanup
    stats_after = memory_store.get_stats()
    deleted = stats_before['total_memories'] - stats_after['total_memories']
    
    return {
        "message": f"Deleted memories older than {request.days} days",
        "days": request.days,
        "memories_before": stats_before['total_memories'],
        "memories_after": stats_after['total_memories'],
        "deleted": deleted
    }


@router.post("/memory/cleanup/trigger")
def trigger_cleanup_now(user=Depends(get_current_user)):
    """
    Trigger automatic cleanup immediately (HR only).
    Uses default 30-day threshold.
    
    Returns:
        Cleanup result
    """
    # Check if user is HR
    if user.get("role") != "HR":
        raise HTTPException(
            status_code=403,
            detail="Only HR can trigger memory cleanup"
        )
    
    # Get stats before cleanup
    stats_before = memory_store.get_stats()
    
    # Run cleanup with default 30 days
    memory_store.cleanup_old_memories(days=30)
    
    # Get stats after cleanup
    stats_after = memory_store.get_stats()
    deleted = stats_before['total_memories'] - stats_after['total_memories']
    
    return {
        "message": "Cleanup triggered successfully",
        "days": 30,
        "memories_before": stats_before['total_memories'],
        "memories_after": stats_after['total_memories'],
        "deleted": deleted
    }


@router.delete("/memory/user/{user_id}")
def clear_specific_user_memories(
    user_id: int,
    user=Depends(get_current_user)
):
    """
    Clear all memories for a specific user (HR only).
    
    Args:
        user_id: The user ID to clear memories for
        
    Returns:
        Success message
    """
    # Check if user is HR
    if user.get("role") != "HR":
        raise HTTPException(
            status_code=403,
            detail="Only HR can clear other users' memories"
        )
    
    memory_store.clear_user_memories(str(user_id))
    
    return {
        "message": f"All memories cleared for user {user_id}",
        "user_id": user_id
    }
