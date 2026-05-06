"""
Memory Filter - Determines what should be stored in long-term memory
Prevents storing trivial or unimportant messages

Now includes:
- LLM-based importance detection (more accurate than keywords)
- Fallback to keyword-based filtering if LLM fails
"""

from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from dotenv import load_dotenv
import os

load_dotenv()

# Initialize LLM for importance detection
try:
    filter_llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0.1,  # Low temperature for consistent decisions
        max_tokens=10,    # Just need "yes" or "no"
        api_key=os.getenv("GROQ_API_KEY"),
    )
    LLM_AVAILABLE = True
except Exception as e:
    print(f"[MEMORY FILTER] LLM not available, using keyword fallback: {e}")
    LLM_AVAILABLE = False


def is_important_llm(text: str, intent: str = None, step: str = None) -> bool:
    """
    Use LLM to determine if a message is important enough to store.
    More accurate than keyword matching.
    """
    if not LLM_AVAILABLE:
        return is_important_keyword(text, intent, step)
    
    if not text or len(text.strip()) < 5:
        return False

    # Fast-path: always store explicit "remember" instructions
    text_lower = text.lower().strip()
    if any(kw in text_lower for kw in ["remember", "don't forget", "note that", "keep in mind"]):
        return True
    
    # Build prompt for LLM
    prompt = f"""You are a memory filter for an HR assistant chatbot called NovaHR.

Decide if this message contains information worth remembering long-term.

STORE if message contains:
- Personal information (name, department, role, preferences)
- Important facts or details about the user
- Completed actions (leave submitted, email sent, meeting scheduled)
- User preferences or habits
- Work-related information
- Instructions to remember something
- Anything the user explicitly wants saved

DO NOT STORE if message is:
- A trivial one-word response (ok, yes, no, thanks, bye, hi)
- A generic greeting with no content
- A very short filler phrase

Message: "{text}"
Intent: {intent or "general"}
Step: {step or "unknown"}

Answer with ONLY "yes" or "no":"""

    try:
        messages = [
            SystemMessage(content="You are a memory filter. Answer only 'yes' or 'no'."),
            HumanMessage(content=prompt)
        ]
        
        response = filter_llm.invoke(messages)
        answer = response.content.strip().lower()
        
        if "yes" in answer:
            return True
        elif "no" in answer:
            return False
        else:
            return is_important_keyword(text, intent, step)
            
    except Exception as e:
        print(f"[MEMORY FILTER] LLM error: {str(e)[:100]}, using keyword fallback")
        return is_important_keyword(text, intent, step)


def is_important_keyword(text: str, intent: str = None, step: str = None) -> bool:
    """
    Keyword-based importance detection (fallback method).
    Check if a message is important enough to store in long-term memory.
    
    Args:
        text: The message text
        intent: The detected intent (optional)
        step: The current step in workflow (optional)
        
    Returns:
        True if message should be stored, False otherwise
    """
    if not text or len(text.strip()) < 5:
        return False
    
    text_lower = text.lower().strip()
    
    # 1. Personal information keywords
    personal_keywords = [
        "my name is",
        "i am",
        "i'm",
        "call me",
        "i prefer",
        "i like",
        "i don't like",
        "i work in",
        "my department",
        "my role",
        "my manager",
        "my team"
    ]
    
    # 2. Leave-related important info
    leave_keywords = [
        "leave",
        "vacation",
        "time off",
        "sick",
        "casual leave",
        "earned leave",
        "emergency",
        "family event",
        "medical",
        "wedding",
        "funeral"
    ]
    
    # 3. Work-related important info
    work_keywords = [
        "project",
        "deadline",
        "meeting",
        "presentation",
        "client",
        "working on",
        "responsible for",
        "assigned to"
    ]
    
    # 4. Preferences and settings
    preference_keywords = [
        "prefer",
        "usually",
        "always",
        "never",
        "typically",
        "normally",
        "generally"
    ]
    
    # 5. Important facts
    fact_keywords = [
        "remember",
        "important",
        "note that",
        "keep in mind",
        "don't forget"
    ]
    
    # Check all keyword categories
    all_keywords = (
        personal_keywords + 
        leave_keywords + 
        work_keywords + 
        preference_keywords + 
        fact_keywords
    )
    
    for keyword in all_keywords:
        if keyword in text_lower:
            return True
    
    # 6. Check based on intent
    if intent in ["leave_request", "email_request", "schedule_request"]:
        # Store if it's a completed action
        if step == "completed":
            return True
        
        # Store if it contains specific details
        if any(word in text_lower for word in ["from", "to", "date", "reason", "days"]):
            return True
    
    # 7. Check message length (longer messages often contain important info)
    if len(text.strip()) > 100:
        # Long messages are likely important
        return True
    
    # 8. Exclude trivial responses
    trivial_phrases = [
        "ok",
        "okay",
        "yes",
        "no",
        "sure",
        "thanks",
        "thank you",
        "bye",
        "goodbye",
        "hi",
        "hello",
        "hey",
        "great",
        "cool",
        "nice",
        "alright",
        "got it",
        "understood",
        "k",
        "kk"
    ]
    
    # If message is ONLY a trivial phrase, don't store
    if text_lower in trivial_phrases:
        return False
    
    # Default: don't store unless it matches criteria above
    return False


def is_important(text: str, intent: str = None, step: str = None, use_llm: bool = True) -> bool:
    """
    Main function to check if message is important.
    Uses LLM by default, falls back to keywords if LLM unavailable.
    
    Args:
        text: The message text
        intent: The detected intent (optional)
        step: The current step in workflow (optional)
        use_llm: Whether to use LLM (default: True)
        
    Returns:
        True if message should be stored, False otherwise
    """
    if use_llm and LLM_AVAILABLE:
        return is_important_llm(text, intent, step)
    else:
        return is_important_keyword(text, intent, step)


def extract_facts(text: str, intent: str = None) -> list:
    """
    Extract specific facts from text that should be remembered.
    
    Args:
        text: The message text
        intent: The detected intent (optional)
        
    Returns:
        List of extracted facts (strings)
    """
    facts = []
    text_lower = text.lower()
    
    # Extract name
    if "my name is" in text_lower:
        # Simple extraction (can be improved with NER)
        parts = text_lower.split("my name is")
        if len(parts) > 1:
            name = parts[1].strip().split()[0]
            facts.append(f"User's name is {name}")
    
    # Extract department
    if "i work in" in text_lower or "my department" in text_lower:
        facts.append(f"User mentioned their department: {text}")
    
    # Extract leave preferences
    if intent == "leave_request" and any(word in text_lower for word in ["prefer", "usually", "typically"]):
        facts.append(f"Leave preference: {text}")
    
    # If no specific facts extracted, return the whole text if it's important
    if not facts and is_important(text, intent):
        facts.append(text)
    
    return facts


def should_store_agent_response(response: str, intent: str = None, step: str = None) -> bool:
    """
    Check if an agent's response should be stored.
    Usually we don't store agent responses, only user inputs.
    But some responses contain important confirmations.
    
    Args:
        response: The agent's response
        intent: The detected intent
        step: The current step
        
    Returns:
        True if response should be stored
    """
    if not response:
        return False
    
    response_lower = response.lower()
    
    # Store confirmations of completed actions
    confirmation_keywords = [
        "successfully submitted",
        "leave approved",
        "leave rejected",
        "email sent",
        "meeting scheduled",
        "your leave id is",
        "confirmation"
    ]
    
    for keyword in confirmation_keywords:
        if keyword in response_lower:
            return True
    
    # Store if step is completed
    if step == "completed":
        return True
    
    return False
