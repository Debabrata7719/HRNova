"""
Memory Manager for Sub-Agents
Implements ConversationBufferWindowMemory with summarization capability
Summarizes old messages before they're dropped from the window
"""

from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from dotenv import load_dotenv
from typing import Optional
import os
import json

# Load environment variables
load_dotenv()

# Initialize Groq LLM for summarization
summarizer_llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.3,
    max_tokens=100,  # Limit output for faster summarization
    api_key=os.getenv("GROQ_API_KEY"),
)


class ConversationBufferWindowMemory:
    """
    Manages conversation history with a fixed window size.
    When the window is full and a new message is added, old messages are summarized
    before being dropped.

    This is specifically designed for sub-agents (leave, email, general).
    """

    def __init__(self, window_size: int = 10, agent_name: str = "agent"):
        """
        Initialize the memory buffer.

        Args:
            window_size: Maximum number of messages to keep (default: 10)
            agent_name: Name of the agent for summarization context
        """
        self.window_size = window_size
        self.agent_name = agent_name
        self.messages = []  # List of {"role": "user"/"assistant", "content": "..."}
        self.summaries = []  # List of summarized message chunks
        self._summarize_done = False  # Track if summarize already done this turn
        self._consecutive_failures = 0  # Track consecutive failures
        self._summarization_disabled_until = None  # Timestamp when disabled
        self._is_summarizing = False  # Re-entrancy guard - prevents recursive calls
        self._summarize_call_depth = 0  # Call depth guard - tracks nested calls

    def add_message(self, role: str, content: str) -> dict:
        """
        Add a message to the conversation buffer.
        If buffer exceeds window size, summarizes old messages before dropping.

        Args:
            role: "user" or "assistant"
            content: The message content

        Returns:
            dict with "added_message", "summary" (if any), and "buffer_status"
        """
        message = {"role": role, "content": content}
        self.messages.append(message)

        # Reset flag only when memory is EMPTY (new conversation)
        # This prevents the bug where flag resets on every user message
        if role == "user" and len(self.messages) == 1:
            self._summarize_done = False

        # EMERGENCY CLEANUP: If messages exceed 2x window, force trim
        # This prevents the bug where buffer grows to 16+ messages
        if len(self.messages) > self.window_size * 2:
            self.messages = self.messages[-self.window_size :]
            print(f"[EMERGENCY] Buffer force-trimmed to {self.window_size} messages")

        result = {
            "added_message": message,
            "summary": None,
            "buffer_status": {
                "current_size": len(self.messages),
                "window_size": self.window_size,
                "is_full": len(self.messages) > self.window_size,
            },
        }

        # If buffer exceeds window size, summarize oldest messages
        # Only summarize once per turn (check flag)
        if len(self.messages) > self.window_size and not self._summarize_done:
            # Check if summarization is disabled due to failures
            if self._is_summarization_disabled():
                self._summarize_done = True
                return result

            # RE-ENTRANCY GUARD: Skip if already in progress
            if self._is_summarizing:
                return result

            # CALL DEPTH GUARD: Prevent recursive loops
            if self._summarize_call_depth > 1:
                print(f"[{self.agent_name}] CALL DEPTH EXCEEDED - skipping summarize")
                self._summarize_done = True
                return result

            # Get messages to summarize (all except the last window_size)
            messages_to_summarize = self.messages[: -self.window_size]

            # Check if should summarize (char threshold + meaningful content)
            should_summarize, total_chars = self._should_summarize(
                messages_to_summarize
            )

            # Only attempt if conditions are met - mark done AFTER attempt
            if should_summarize:
                # Set depth guard BEFORE calling
                self._summarize_call_depth += 1
                self._is_summarizing = True

                try:
                    summary = self._summarize_messages(messages_to_summarize)
                    self._summarize_done = (
                        True  # Mark done AFTER attempt (success OR failure)
                    )

                    if summary is not None:
                        # SUCCESS: Store summary and trim messages
                        self.summaries.append(summary)
                        result["summary"] = summary
                        self.messages = self.messages[-self.window_size :]
                        result["buffer_status"]["current_size"] = len(self.messages)
                        self._consecutive_failures = 0
                    else:
                        # FAILURE: Do not store summary, do not trim messages
                        result["summary"] = None
                        self._consecutive_failures += 1
                        # Increased threshold - disable only after 5 failures
                        if self._consecutive_failures >= 5:
                            self._disable_summarization()
                            print(
                                "[INFO] Summarization disabled for 10 min after 5 failures"
                            )
                finally:
                    # Always decrement depth guard
                    self._summarize_call_depth = max(0, self._summarize_call_depth - 1)
                    self._is_summarizing = False
            else:
                # Skip - conditions not met, don't mark done yet
                # Will retry on next message if conditions change
                pass

        return result

    def get_messages(self, include_summary: bool = False) -> list:
        """
        Get all messages in the current buffer.
        Optionally includes context about summarized messages.

        Args:
            include_summary: If True, prepend summary context to messages

        Returns:
            List of messages, optionally with summary context
        """
        messages = self.messages.copy()

        # If there are summaries, add them as context at the beginning
        if include_summary and self.summaries:
            # Create a summary context message
            latest_summary = self.summaries[-1]
            summary_msg = {
                "role": "system",
                "content": f"[CONVERSATION CONTEXT FROM EARLIER]\n{latest_summary}\n[END CONTEXT]\n\nContinuing with recent messages...",
            }
            messages.insert(0, summary_msg)

        return messages

    def get_buffer_info(self) -> dict:
        """Get information about the current buffer state."""
        return {
            "current_size": len(self.messages),
            "window_size": self.window_size,
            "summaries_count": len(self.summaries),
            "is_full": len(self.messages) >= self.window_size,
            "messages": self.messages,
            "summaries": self.summaries,
        }

    def clear(self, full: bool = False):
        """
        Clear all messages and summaries.

        Args:
            If full=True, also reset failure counters and flags.
        """
        self.messages = []
        self.summaries = []

        if full:
            # Full reset - for new conversation
            self._summarize_done = False
            self._consecutive_failures = 0
            self._summarization_disabled_until = None
            self._summarize_call_depth = 0
            self._is_summarizing = False

    def _is_summarization_disabled(self) -> bool:
        """
        Check if summarization is temporarily disabled due to failures.

        Returns:
            True if disabled (failure threshold reached), False otherwise
        """
        if self._summarization_disabled_until is None:
            return False

        from datetime import datetime

        if datetime.now().timestamp() >= self._summarization_disabled_until:
            self._summarization_disabled_until = None
            self._consecutive_failures = 0
            return False

        return True

    def _disable_summarization(self):
        """Disable summarization for 10 minutes after 3 consecutive failures."""
        from datetime import datetime

        self._summarization_disabled_until = (
            datetime.now().timestamp() + 600
        )  # 10 minutes

    def to_dict(self) -> dict:
        """Serialize memory to dict (for state storage)."""
        return {
            "messages": self.messages,
            "summaries": self.summaries,
            "window_size": self.window_size,
            "agent_name": self.agent_name,
            "_consecutive_failures": self._consecutive_failures,
            "_summarization_disabled_until": self._summarization_disabled_until,
            "_summarize_done": self._summarize_done,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ConversationBufferWindowMemory":
        """Deserialize memory from dict (from state storage)."""
        memory = cls(
            window_size=data.get("window_size", 10),
            agent_name=data.get("agent_name", "agent"),
        )
        memory.messages = data.get("messages", [])
        memory.summaries = data.get("summaries", [])
        memory._consecutive_failures = data.get("_consecutive_failures", 0)
        memory._summarization_disabled_until = data.get("_summarization_disabled_until")
        memory._summarize_done = data.get("_summarize_done", False)
        return memory

    def _should_summarize(self, messages: list) -> tuple[bool, int]:
        """
        Check if messages should be summarized based on:
        1. Token/size threshold (at least 150 chars total)
        2. Meaningful content (not just trivial responses)

        Args:
            messages: List of messages to check

        Returns:
            tuple: (should_summarize: bool, total_chars: int)
        """
        MIN_CHARS_THRESHOLD = 300
        TRIVIAL_KEYWORDS = {
            "ok",
            "okay",
            "thanks",
            "thank you",
            "yes",
            "no",
            "sure",
            "great",
            "cool",
            "nice",
            "bye",
            "goodbye",
            "hi",
            "hello",
            "yep",
            "nope",
            "alright",
            "got it",
            "done",
            "k",
            "kk",
        }

        total_chars = sum(len(msg.get("content", "")) for msg in messages)
        if total_chars < MIN_CHARS_THRESHOLD:
            return False, total_chars

        meaningful_count = 0
        for msg in messages:
            content = msg.get("content", "").lower().strip()
            content_words = content.split()
            if not content:
                continue
            if content not in TRIVIAL_KEYWORDS and len(content_words) >= 2:
                meaningful_count += 1

        # Allow summarization if we have enough meaningful content
        # OR if there are fewer messages than the ideal threshold
        min_required = min(2, len(messages))  # Require at least 2, or whatever we have
        should_summarize = (
            meaningful_count >= min_required and total_chars >= MIN_CHARS_THRESHOLD
        )
        return should_summarize, total_chars

    def _summarize_messages(self, messages: list) -> Optional[str]:
        """
        Summarize a list of messages using LLM.

        Returns:
            Summary string on SUCCESS, None on FAILURE
            NEVER returns fallback strings.
        """
        if not messages:
            return None

        print(
            f"[{self.agent_name}] SUMMARIZE CALLED - msgs:{len(self.messages)}, flag:{self._summarize_done}, depth:{self._summarize_call_depth}"
        )

        conversation_text = "\n".join(
            [f"{msg['role'].upper()}: {msg['content']}" for msg in messages]
        )

        summary_prompt = f"""Summarize this conversation for {self.agent_name}.
Focus: key decisions, facts, status, constraints.
Keep to 2-3 sentences.

Conversation:
{conversation_text}

Summary:"""

        try:
            llm_messages = [
                SystemMessage(content=f"You are a conversation summarizer."),
                HumanMessage(content=summary_prompt),
            ]
            response = summarizer_llm.invoke(llm_messages)

            if hasattr(response, "content"):
                content = response.content
            else:
                content = str(response)

            if isinstance(content, list):
                content = " ".join([str(c) for c in content])

            summary = content.strip() if isinstance(content, str) else str(content)

            if summary.startswith("[EARLIER CONTEXT]"):
                print("[WARNING] Fallback rejected")
                return None

            return summary

        except Exception as e:
            error_str = str(e)

            # Rate limit (429) - increment failures but don't disable immediately
            # Let the normal failure counter handle it (will disable after 5 failures)
            if "429" in error_str:
                print(f"[WARNING] Rate limit (429) - will retry on next attempt")
            else:
                print(f"[WARNING] Summarization failed: {error_str[:100]}")

            return None


class MemoryManager:
    """
    Manages memories for all sub-agents.
    Provides utility functions for memory operations.
    """

    def __init__(self):
        """Initialize the memory manager."""
        self.agent_memories = {
            "leave_agent": ConversationBufferWindowMemory(
                window_size=10, agent_name="leave_agent"
            ),
            "email_agent": ConversationBufferWindowMemory(
                window_size=5, agent_name="email_agent"
            ),
            "general_agent": ConversationBufferWindowMemory(
                window_size=7, agent_name="general_agent"
            ),
        }

    def get_memory(self, agent_name: str) -> ConversationBufferWindowMemory:
        """Get memory for a specific agent."""
        return self.agent_memories.get(agent_name)

    def add_to_memory(self, agent_name: str, role: str, content: str) -> dict:
        """Add a message to an agent's memory."""
        memory = self.get_memory(agent_name)
        if memory:
            return memory.add_message(role, content)
        return None

    def get_memory_state(self) -> dict:
        """Get current state of all memories for storage in State."""
        return {
            agent_name: memory.to_dict()
            for agent_name, memory in self.agent_memories.items()
        }

    def restore_memory_state(self, state_dict: dict):
        """Restore memories from stored state."""
        for agent_name, memory_data in state_dict.items():
            if agent_name in self.agent_memories:
                self.agent_memories[agent_name] = (
                    ConversationBufferWindowMemory.from_dict(memory_data)
                )

    def clear_all(self):
        """Clear all memories."""
        for memory in self.agent_memories.values():
            memory.clear()


# Utility functions for use in agents


def create_memory_list_from_dict(
    memory_dict: Optional[dict],
) -> ConversationBufferWindowMemory:
    """Create a memory object from a dict (from state)."""
    if memory_dict is None:
        return ConversationBufferWindowMemory(window_size=10, agent_name="agent")
    return ConversationBufferWindowMemory.from_dict(memory_dict)


def serialize_memory_for_state(memory: ConversationBufferWindowMemory) -> dict:
    """Serialize memory object for storage in state."""
    return memory.to_dict()


def add_user_message_to_memory(
    memory: ConversationBufferWindowMemory, user_input: str
) -> dict:
    """Add user message and return the operation result."""
    if user_input.strip():
        return memory.add_message("user", user_input)
    return {
        "added_message": None,
        "summary": None,
        "buffer_status": memory.get_buffer_info(),
    }


def add_assistant_message_to_memory(
    memory: ConversationBufferWindowMemory, assistant_response: str
) -> dict:
    """Add assistant message and return the operation result."""
    if assistant_response.strip():
        return memory.add_message("assistant", assistant_response)
    return {
        "added_message": None,
        "summary": None,
        "buffer_status": memory.get_buffer_info(),
    }
