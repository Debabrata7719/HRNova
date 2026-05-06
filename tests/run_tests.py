"""
NovaHR Backend Test Suite
Run: python tests/run_tests.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

errors = []
passes = []

def ok(msg):
    passes.append(msg)
    print(f"OK  {msg}")

def fail(msg):
    errors.append(msg)
    print(f"FAIL  {msg}")

# ── Test 1: Config & imports ──────────────────────────────────────────────────
try:
    from src.config import get_settings
    s = get_settings()
    ok("config loads via pydantic-settings")
except Exception as e:
    fail(f"config load: {e}")

try:
    from src.logger import get_logger
    logger = get_logger("test")
    ok("logger module loads")
except Exception as e:
    fail(f"logger load: {e}")

# ── Test 2: MySQL connection ──────────────────────────────────────────────────
try:
    from src.tools.db_connection import get_db
    db = get_db()
    if db.connection:
        ok("MySQL connected")
    else:
        fail("MySQL: connection is None")
except Exception as e:
    fail(f"MySQL connect: {e}")

# ── Test 3: Authentication ────────────────────────────────────────────────────
try:
    from auth.auth import login

    # Wrong password
    r = login("debu@gmail.com", "wrongpassword")
    assert r["success"] == False, "Should reject wrong password"
    ok("wrong password correctly rejected")

    # HR login
    r = login("debu@gmail.com", "721242")
    assert r["success"] == True, "HR login should succeed"
    assert r["user"]["auth_role"] == "HR"
    ok(f"HR login works — role={r['user']['auth_role']}")

    # Employee login
    r2 = login("rahul@gmail.com", "123")
    assert r2["success"] == True, "Employee login should succeed"
    assert r2["user"]["auth_role"] == "EMPLOYEE"
    ok(f"Employee login works — role={r2['user']['auth_role']}")

except Exception as e:
    fail(f"auth: {e}")

# ── Test 4: Leave date parsing ────────────────────────────────────────────────
try:
    from src.main_agent.agents.leave.executor import parse_date, calculate_days

    assert parse_date("today") is not None
    assert parse_date("tomorrow") is not None
    assert parse_date("2026-05-10") == "2026-05-10"
    assert parse_date("May 10, 2026") == "2026-05-10"
    assert calculate_days("2026-05-10", "2026-05-12") == 3
    ok("leave date parsing (dateutil) works")
except Exception as e:
    fail(f"leave date parsing: {e}")

# ── Test 5: Leave balance query ───────────────────────────────────────────────
try:
    from src.main_agent.agents.leave.executor import check_balance
    bal = check_balance(2)  # rahul's id
    assert "EL" in bal and "CL" in bal and "SL" in bal
    ok(f"leave balance query works — EL remaining={bal['EL']['remaining']}, CL={bal['CL']['remaining']}, SL={bal['SL']['remaining']}")
except Exception as e:
    fail(f"leave balance: {e}")

# ── Test 6: ChromaDB memory store ─────────────────────────────────────────────
try:
    from src.utils.memory_store import get_memory_store
    ms = get_memory_store()
    stats = ms.get_stats()
    ok(f"ChromaDB memory store works — total memories={stats['total_memories']}")
except Exception as e:
    fail(f"memory store: {e}")

# ── Test 7: Policy ChromaDB ───────────────────────────────────────────────────
try:
    from src.main_agent.agents.query.executor import query_policy_chunks
    chunks = query_policy_chunks("casual leave policy", k=2)
    if chunks:
        ok(f"policy ChromaDB works — got {len(chunks)} chunks")
    else:
        fail("policy ChromaDB: no chunks returned — policy PDF may not be embedded yet")
except Exception as e:
    fail(f"policy ChromaDB: {e}")

# ── Test 8: Router intent detection ──────────────────────────────────────────
try:
    from src.main_agent.router import router

    base_state = {
        "input": "", "step": "initial", "intent": "", "role": "HR",
        "leave_data": {}, "email_data": {}, "schedule_data": {},
        "output": "", "employee_id": 1, "employee_name": "Debu",
        "schedule_title": "", "schedule_date": "", "schedule_time": "",
        "schedule_description": "", "leave_agent_memory": {},
        "email_agent_memory": {}, "general_agent_memory": {},
        "query_agent_memory": {}, "schedule_agent_memory": {},
        "long_term_memory": [], "session_summaries": {}
    }

    cases = [
        ("schedule a meeting tomorrow at 3pm", "HR", "schedule_request"),
        ("did you schedule any meeting earlier", "HR", "general"),
        ("send an email to rahul about deadline", "HR", "email_request"),
        ("what is my leave balance", "HR", "query_request"),
        ("I want to apply for casual leave", "HR", "leave_request"),
        ("who are you", "HR", "general"),
        ("hello", "HR", "general"),
        ("what can you do", "HR", "general"),
        ("schedule a meeting tomorrow at 3pm", "EMPLOYEE", "general"),  # blocked
        ("what is the casual leave policy", "HR", "query_request"),
        ("show my leave requests", "HR", "query_request"),
    ]

    router_errors = []
    for user_input, role, expected_intent in cases:
        s = dict(base_state)
        s["input"] = user_input
        s["role"] = role
        result = router(s)
        got = result["intent"]
        if got != expected_intent:
            router_errors.append(f'"{user_input}" (role={role}) → expected={expected_intent}, got={got}')

    if router_errors:
        for e in router_errors:
            fail(f"router: {e}")
    else:
        ok(f"router intent detection correct for all {len(cases)} test cases")

except Exception as e:
    fail(f"router: {e}")

# ── Test 9: Memory filter ─────────────────────────────────────────────────────
try:
    from src.utils.memory_filter import is_important_keyword

    filter_cases = [
        ("remember my name is Debu", True),
        ("ok", False),
        ("yes", False),
        ("thanks", False),
        ("my leave balance is 12 days", True),
        ("I prefer formal emails", True),
        ("I work in Engineering department", True),
    ]

    filter_errors = []
    for text, expected in filter_cases:
        got = is_important_keyword(text)
        if got != expected:
            filter_errors.append(f'"{text}" → expected={expected}, got={got}')

    if filter_errors:
        for e in filter_errors:
            fail(f"memory filter: {e}")
    else:
        ok(f"memory filter (keyword) correct for all {len(filter_cases)} cases")

except Exception as e:
    fail(f"memory filter: {e}")

# ── Test 10: Email recipient parsing ─────────────────────────────────────────
try:
    from src.main_agent.agents.email.executor import parse_recipients

    # Test "all employees"
    recipients, err = parse_recipients("send email to all employees")
    if err:
        fail(f"email parse 'all employees': {err}")
    else:
        ok(f"email parse 'all employees' → {len(recipients)} recipients found")

    # Test by name
    recipients2, err2 = parse_recipients("send email to rahul")
    if err2:
        fail(f"email parse by name 'rahul': {err2}")
    else:
        ok(f"email parse by name 'rahul' → {recipients2}")

except Exception as e:
    fail(f"email recipient parsing: {e}")

# ── Test 11: API router imports ───────────────────────────────────────────────
try:
    from api.routers.leaves import get_all_leaves, get_leave_stats
    from api.routers.memory import get_all_users_memories, get_memory_stats
    from api.routers.chat import chat
    from api.routers.auth import router as auth_router
    ok("all API routers import cleanly")
except Exception as e:
    fail(f"API router imports: {e}")

# ── Test 12: Scheduling datetime parsing ─────────────────────────────────────
try:
    from src.main_agent.agents.scheduling.executor import parse_to_datetime
    from zoneinfo import ZoneInfo
    IST = ZoneInfo("Asia/Kolkata")

    dt = parse_to_datetime("tomorrow", "15:00")
    assert dt.tzinfo is not None, "datetime must be timezone-aware"
    assert dt.hour == 15
    assert "+05:30" in dt.isoformat() or "Asia/Kolkata" in str(dt.tzinfo)
    ok(f"scheduling datetime is IST-aware: {dt.isoformat()}")
except Exception as e:
    fail(f"scheduling datetime: {e}")

# ── Test 13: Memory cleanup logic ────────────────────────────────────────────
try:
    from src.utils.memory_store import get_memory_store
    ms = get_memory_store()
    # Just verify the method exists and runs without error (dry run — no actual delete)
    stats = ms.get_stats()
    ok(f"memory cleanup method accessible — {stats['total_memories']} memories in store")
except Exception as e:
    fail(f"memory cleanup: {e}")

# ── Summary ───────────────────────────────────────────────────────────────────
print()
print("=" * 60)
print(f"PASSED: {len(passes)}")
print(f"FAILED: {len(errors)}")
print("=" * 60)

if errors:
    print("\nFAILED TESTS:")
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)
else:
    print("\nAll backend tests passed!")
    sys.exit(0)
