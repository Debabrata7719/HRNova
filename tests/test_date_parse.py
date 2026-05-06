import sys; sys.path.insert(0,'.')
from src.main_agent.agents.leave.executor import parse_date
from datetime import datetime, timedelta

today = datetime.now()
tomorrow = (today + timedelta(days=1)).strftime('%Y-%m-%d')

tests = [
    ('today',          today.strftime('%Y-%m-%d'), True),
    ('tomorrow',       tomorrow,                   True),
    ('tmrw',           tomorrow,                   True),
    ('next day',       tomorrow,                   True),
    ('2026-05-10',     '2026-05-10',               True),
    ('2026-01-15',     '2026-01-15',               True),
    ('May 10 2026',    '2026-05-10',               True),
    ('15/05/2026',     '2026-05-15',               True),
    ('next friday',    None,                        False),
    ('next monday',    None,                        False),
    ('this friday',    None,                        False),
    ('coming tuesday', None,                        False),
    ('next week',      None,                        False),
]

all_ok = True
for inp, expected, exact in tests:
    result = parse_date(inp)
    if exact:
        ok = result == expected
    else:
        ok = result is not None and len(result) == 10
    status = 'OK  ' if ok else 'FAIL'
    if not ok:
        all_ok = False
    exp_str = expected if exact else 'valid date'
    print(status + '  ' + repr(inp).ljust(25) + ' -> ' + str(result) + '  (expected ' + exp_str + ')')

print()
print('All pass!' if all_ok else 'Some failed.')
