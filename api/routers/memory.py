"""
Memory Management Router - Admin endpoints for memory operations
"""

import sys
import os
import asyncio
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import APIRouter, Depends, HTTPException
from api.dependencies.auth import get_current_user
from src.utils.memory_store import get_memory_store
from pydantic import BaseModel

router = APIRouter()

# Thread pool for running blocking ChromaDB calls off the main thread
_executor = ThreadPoolExecutor(max_workers=2)

# Lazy initialization — initialized once on first use
_memory_store = None

def get_store():
    global _memory_store
    if _memory_store is None:
        _memory_store = get_memory_store()
    return _memory_store


async def run_in_thread(fn, *args):
    """Run a blocking function in a thread pool so it doesn't block the event loop."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_executor, fn, *args)


class CleanupRequest(BaseModel):
    """Request model for memory cleanup"""
    days: int = 30

    class Config:
        # Allow days=0 (delete all)
        json_schema_extra = {"example": {"days": 30}}


@router.get("/memory/stats")
async def get_memory_stats(user=Depends(get_current_user)):
    """Get memory statistics. Available to all authenticated users."""
    stats = await run_in_thread(lambda: get_store().get_stats())
    return stats


@router.get("/memory/user")
async def get_user_memories(user=Depends(get_current_user)):
    """Get all memories for the current user."""
    user_id = str(user.get("user_id"))
    memories = await run_in_thread(lambda: get_store().get_all_memories(user_id, limit=50))
    return {
        "user_id": user_id,
        "total_memories": len(memories),
        "memories": memories
    }


@router.get("/memory/all")
async def get_all_users_memories(user=Depends(get_current_user)):
    """Get memories for ALL users (HR only)."""
    if user.get("role") != "HR":
        raise HTTPException(status_code=403, detail="Only HR can view all users' memories")

    memories_by_user = await run_in_thread(lambda: get_store().get_all_users_memories(limit=200))
    total = sum(len(mems) for mems in memories_by_user.values())
    return {
        "total_memories": total,
        "total_users": len(memories_by_user),
        "memories_by_user": memories_by_user
    }


@router.delete("/memory/user")
async def clear_user_memories(user=Depends(get_current_user)):
    """Clear all memories for the current user."""
    user_id = str(user.get("user_id"))
    await run_in_thread(lambda: get_store().clear_user_memories(user_id))
    return {"message": f"All memories cleared for user {user_id}", "user_id": user_id}


@router.post("/memory/cleanup")
async def cleanup_old_memories(request: CleanupRequest, user=Depends(get_current_user)):
    """Delete old memories manually (HR only)."""
    if user.get("role") != "HR":
        raise HTTPException(status_code=403, detail="Only HR can perform memory cleanup")

    stats_before = await run_in_thread(lambda: get_store().get_stats())
    await run_in_thread(lambda: get_store().cleanup_old_memories(days=request.days))
    stats_after = await run_in_thread(lambda: get_store().get_stats())
    deleted = stats_before['total_memories'] - stats_after['total_memories']

    return {
        "message": f"Deleted memories older than {request.days} days",
        "days": request.days,
        "memories_before": stats_before['total_memories'],
        "memories_after": stats_after['total_memories'],
        "deleted": deleted
    }


@router.post("/memory/cleanup/trigger")
async def trigger_cleanup_now(user=Depends(get_current_user)):
    """Trigger immediate cleanup (HR only). Uses default 30-day threshold."""
    if user.get("role") != "HR":
        raise HTTPException(status_code=403, detail="Only HR can trigger memory cleanup")

    stats_before = await run_in_thread(lambda: get_store().get_stats())
    await run_in_thread(lambda: get_store().cleanup_old_memories(days=30))
    stats_after = await run_in_thread(lambda: get_store().get_stats())
    deleted = stats_before['total_memories'] - stats_after['total_memories']

    return {
        "message": "Cleanup triggered successfully",
        "days": 30,
        "memories_before": stats_before['total_memories'],
        "memories_after": stats_after['total_memories'],
        "deleted": deleted
    }


@router.delete("/memory/user/{user_id}")
async def clear_specific_user_memories(user_id: int, user=Depends(get_current_user)):
    """Clear all memories for a specific user (HR only)."""
    if user.get("role") != "HR":
        raise HTTPException(status_code=403, detail="Only HR can clear other users' memories")

    await run_in_thread(lambda: get_store().clear_user_memories(str(user_id)))
    return {"message": f"All memories cleared for user {user_id}", "user_id": user_id}

