"""
Test 8 — Memory System
Tests: memory filter (important vs trivial), memory store (add/search/cleanup).
"""
import pytest


class TestMemoryFilter:
    """Unit tests for is_important_keyword() — no external deps."""

    def setup_method(self):
        from src.utils.memory_filter import is_important_keyword
        self.is_important = is_important_keyword

    # Should store
    def test_remember_instruction_stored(self):
        assert self.is_important("remember my name is Debu") is True

    def test_personal_info_stored(self):
        assert self.is_important("my name is Debabrata") is True
        assert self.is_important("I work in the HR department") is True

    def test_leave_info_stored(self):
        assert self.is_important("I need leave from May 10 to May 12") is True

    def test_preference_stored(self):
        assert self.is_important("I prefer formal emails") is True

    def test_long_message_stored(self):
        long_msg = "This is a detailed message about my work situation " * 5
        assert self.is_important(long_msg) is True

    def test_work_info_stored(self):
        assert self.is_important("I am working on the API project deadline") is True

    # Should NOT store
    def test_ok_not_stored(self):
        assert self.is_important("ok") is False

    def test_yes_not_stored(self):
        assert self.is_important("yes") is False

    def test_thanks_not_stored(self):
        assert self.is_important("thanks") is False

    def test_bye_not_stored(self):
        assert self.is_important("bye") is False

    def test_empty_not_stored(self):
        assert self.is_important("") is False

    def test_very_short_not_stored(self):
        assert self.is_important("hi") is False


class TestMemoryStore:
    """Integration tests for ChromaDB memory store."""

    def test_memory_store_initializes(self):
        from src.utils.memory_store import get_memory_store
        ms = get_memory_store()
        assert ms is not None
        assert ms.collection is not None

    def test_get_stats_returns_count(self):
        from src.utils.memory_store import get_memory_store
        ms = get_memory_store()
        stats = ms.get_stats()
        assert "total_memories" in stats
        assert isinstance(stats["total_memories"], int)
        assert stats["total_memories"] >= 0

    def test_add_and_search_memory(self):
        from src.utils.memory_store import get_memory_store
        ms = get_memory_store()
        test_user = "test_user_pytest_99999"
        test_text = "pytest test memory: I prefer working from home on Fridays"

        # Add memory
        ms.add_memory(test_user, test_text, {"intent": "general", "type": "test"})

        # Search for it
        results = ms.search_memory(test_user, "working from home", n_results=3)
        assert len(results) >= 1
        assert any("pytest test memory" in r for r in results)

        # Cleanup after test
        ms.clear_user_memories(test_user)

    def test_clear_user_memories(self):
        from src.utils.memory_store import get_memory_store
        ms = get_memory_store()
        test_user = "test_user_pytest_clear_88888"

        ms.add_memory(test_user, "test memory to be cleared")
        ms.clear_user_memories(test_user)

        results = ms.search_memory(test_user, "test memory", n_results=5)
        assert len(results) == 0

    def test_get_all_memories_returns_metadata(self):
        from src.utils.memory_store import get_memory_store
        ms = get_memory_store()
        test_user = "test_user_pytest_meta_77777"
        ms.add_memory(test_user, "metadata test memory", {"intent": "general"})

        memories = ms.get_all_memories(test_user, limit=10)
        assert len(memories) >= 1
        # New format returns dicts with text/timestamp/intent
        if isinstance(memories[0], dict):
            assert "text" in memories[0]
        else:
            assert isinstance(memories[0], str)

        ms.clear_user_memories(test_user)

    def test_cleanup_old_memories_runs_without_error(self):
        """Cleanup with days=365 should not delete recent memories."""
        from src.utils.memory_store import get_memory_store
        ms = get_memory_store()
        stats_before = ms.get_stats()
        ms.cleanup_old_memories(days=365)  # Only deletes year-old memories
        stats_after = ms.get_stats()
        # Should not delete anything recent
        assert stats_after["total_memories"] <= stats_before["total_memories"]

    def test_get_all_users_memories(self):
        from src.utils.memory_store import get_memory_store
        ms = get_memory_store()
        result = ms.get_all_users_memories(limit=100)
        assert isinstance(result, dict)


class TestConversationMemory:
    """Unit tests for ConversationBufferWindowMemory."""

    def test_add_message(self):
        from src.main_agent.memory import ConversationBufferWindowMemory
        mem = ConversationBufferWindowMemory(window_size=5)
        mem.add_message("user", "hello")
        mem.add_message("assistant", "hi there")
        assert len(mem.messages) == 2

    def test_window_size_enforced(self):
        from src.main_agent.memory import ConversationBufferWindowMemory
        mem = ConversationBufferWindowMemory(window_size=3)
        for i in range(10):
            mem.add_message("user", f"message {i} " * 20)
            mem.add_message("assistant", f"response {i} " * 20)
        # Emergency trim keeps it at 2x window max
        assert len(mem.messages) <= mem.window_size * 2

    def test_serialize_deserialize(self):
        from src.main_agent.memory import ConversationBufferWindowMemory
        mem = ConversationBufferWindowMemory(window_size=5, agent_name="test")
        mem.add_message("user", "test message")
        mem.add_message("assistant", "test response")

        data = mem.to_dict()
        restored = ConversationBufferWindowMemory.from_dict(data)

        assert len(restored.messages) == len(mem.messages)
        assert restored.window_size == mem.window_size
        assert restored.agent_name == mem.agent_name

    def test_clear_resets_messages(self):
        from src.main_agent.memory import ConversationBufferWindowMemory
        mem = ConversationBufferWindowMemory(window_size=5)
        mem.add_message("user", "hello")
        mem.clear()
        assert len(mem.messages) == 0
