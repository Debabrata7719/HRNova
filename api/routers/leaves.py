"""Leaves Router - HR leave management endpoints"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import APIRouter, Depends, HTTPException
from src.tools.db_connection import get_db
from api.dependencies.auth import get_current_user

router = APIRouter()


def check_hr(user: dict):
    """Raise 403 if the current user is not HR."""
    if user.get("role") != "HR":
        raise HTTPException(status_code=403, detail="Only HR is allowed to perform this action")


@router.get("/leaves/stats")
def get_leave_stats(user=Depends(get_current_user)):
    """
    Get leave statistics summary.
    HR only. Returns counts by status.
    """
    check_hr(user)

    db = get_db()

    query = """
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
            SUM(CASE WHEN status = 'approved' THEN 1 ELSE 0 END) as approved,
            SUM(CASE WHEN status = 'rejected' THEN 1 ELSE 0 END) as rejected
        FROM leaves
    """

    result = db.execute_query(query)

    if not result:
        raise HTTPException(status_code=500, detail="Failed to fetch stats")

    row = result[0]
    return {
        "total": int(row["total"] or 0),
        "pending": int(row["pending"] or 0),
        "approved": int(row["approved"] or 0),
        "rejected": int(row["rejected"] or 0),
    }


@router.get("/leaves")
def get_all_leaves(user=Depends(get_current_user)):
    """
    Get all leave requests with employee details.
    HR only.
    """
    check_hr(user)

    db = get_db()

    query = """
        SELECT
            l.leave_id,
            e.name,
            e.email,
            l.leave_type,
            l.start_date,
            l.end_date,
            l.days,
            l.status,
            l.reason,
            l.submitted_at
        FROM leaves l
        JOIN employees e ON l.employee_id = e.id
        ORDER BY l.leave_id DESC
    """

    result = db.execute_query(query)

    if result is None:
        raise HTTPException(status_code=500, detail="Failed to fetch leave requests")

    # Convert date/datetime objects to strings for JSON serialization
    leaves = []
    for row in result:
        leaves.append({
            "leave_id": row["leave_id"],
            "name": row["name"],
            "email": row["email"],
            "leave_type": row["leave_type"],
            "start_date": str(row["start_date"]) if row["start_date"] else None,
            "end_date": str(row["end_date"]) if row["end_date"] else None,
            "days": row["days"],
            "status": row["status"],
            "reason": row["reason"],
            "submitted_at": str(row["submitted_at"]) if row["submitted_at"] else None,
        })

    return leaves


@router.put("/leaves/{leave_id}/approve")
def approve_leave(leave_id: int, user=Depends(get_current_user)):
    """
    Approve a leave request by ID.
    HR only.
    """
    check_hr(user)

    db = get_db()

    # Check leave exists
    existing = db.execute_query(
        "SELECT leave_id, status FROM leaves WHERE leave_id = %s",
        (leave_id,)
    )

    if not existing:
        raise HTTPException(status_code=404, detail="Leave request not found")

    if existing[0]["status"] == "approved":
        return {"message": "Leave is already approved"}

    db.execute_query(
        "UPDATE leaves SET status = 'approved' WHERE leave_id = %s",
        (leave_id,)
    )

    return {"message": "Leave approved successfully"}


@router.put("/leaves/{leave_id}/reject")
def reject_leave(leave_id: int, user=Depends(get_current_user)):
    """
    Reject a leave request by ID.
    HR only.
    """
    check_hr(user)

    db = get_db()

    # Check leave exists
    existing = db.execute_query(
        "SELECT leave_id, status FROM leaves WHERE leave_id = %s",
        (leave_id,)
    )

    if not existing:
        raise HTTPException(status_code=404, detail="Leave request not found")

    if existing[0]["status"] == "rejected":
        return {"message": "Leave is already rejected"}

    db.execute_query(
        "UPDATE leaves SET status = 'rejected' WHERE leave_id = %s",
        (leave_id,)
    )

    return {"message": "Leave rejected successfully"}
