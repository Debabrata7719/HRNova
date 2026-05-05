"""
Memory Cleanup Script
Run this periodically (e.g., daily cron job) to delete old memories

Usage:
    python cleanup_memory.py              # Delete memories older than 30 days
    python cleanup_memory.py --days 60    # Delete memories older than 60 days
"""

import sys
import os
import argparse

# Go up one level from scripts/ to project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.memory_store import get_memory_store


def main():
    parser = argparse.ArgumentParser(description="Clean up old memories from ChromaDB")
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Delete memories older than this many days (default: 30)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without actually deleting"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("NovaHR Memory Cleanup")
    print("=" * 60)
    print(f"Deleting memories older than {args.days} days...")
    print()
    
    # Get memory store
    store = get_memory_store()
    
    # Get stats before cleanup
    stats_before = store.get_stats()
    print(f"Total memories before cleanup: {stats_before['total_memories']}")
    
    if args.dry_run:
        print("\n[DRY RUN MODE] - No memories will be deleted")
        # TODO: Implement dry-run logic to show what would be deleted
        print("Dry-run mode not yet implemented. Run without --dry-run to delete.")
    else:
        # Run cleanup
        store.cleanup_old_memories(days=args.days)
        
        # Get stats after cleanup
        stats_after = store.get_stats()
        deleted = stats_before['total_memories'] - stats_after['total_memories']
        
        print()
        print(f"Total memories after cleanup: {stats_after['total_memories']}")
        print(f"Memories deleted: {deleted}")
    
    print()
    print("Cleanup complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
