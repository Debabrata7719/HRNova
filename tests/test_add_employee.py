"""
Tests for Add Employee feature
Covers: password generation, DB insertion, duplicate check, API endpoint,
        and the critical rule: email is NEVER sent before DB insertion succeeds.
"""
import pytest
from unittest.mock import patch, MagicMock


# ── Unit tests: password generation ──────────────────────────────────────────

class TestPasswordGeneration:

    def setup_method(self):
        from api.routers.employees import generate_password
        self.gen = generate_password

    def test_basic_single_word(self):
        pwd = self.gen("Debabrata")
        assert pwd.startswith("Deba")
        assert "@" in pwd
        suffix = pwd.split("@")[1]
        assert len(suffix) == 4
        assert suffix.isdigit()

    def test_two_word_name(self):
        # "raj kumar" → clean = "Rajkumar" → prefix = "Rajk"
        pwd = self.gen("raj kumar")
        assert pwd.startswith("Rajk")
        assert "@" in pwd

    def test_three_word_name(self):
        # "john michael doe" → "Johnmichaeldoe" → "John"
        pwd = self.gen("john michael doe")
        assert pwd.startswith("John")

    def test_short_name_under_4_chars(self):
        # "Ali" → prefix = "Ali" (less than 4)
        pwd = self.gen("Ali")
        assert pwd.startswith("Ali@")
        suffix = pwd.split("@")[1]
        assert len(suffix) == 4

    def test_exactly_4_chars(self):
        pwd = self.gen("Raja")
        assert pwd.startswith("Raja@")

    def test_sayandip_bar(self):
        # "Sayandip Bar" → "Sayandipbar" → "Saya"
        pwd = self.gen("Sayandip Bar")
        assert pwd.startswith("Saya@")

    def test_password_format(self):
        pwd = self.gen("Test User")
        parts = pwd.split("@")
        assert len(parts) == 2
        assert len(parts[1]) == 4
        assert parts[1].isdigit()

    def test_digits_in_range(self):
        for _ in range(20):
            pwd = self.gen("Test User")
            digits = int(pwd.split("@")[1])
            assert 1000 <= digits <= 9999

    def test_title_case_applied(self):
        pwd = self.gen("sayandip bar")
        assert pwd[0].isupper()
        assert pwd.startswith("Saya")

    def test_extra_spaces_handled(self):
        # Extra spaces between words should be ignored
        pwd = self.gen("  raj   kumar  ")
        assert pwd.startswith("Rajk")


# ── Integration tests: DB insertion via API endpoint ─────────────────────────

class TestAddEmployeeAPI:

    def test_add_employee_requires_hr(self, api_client, employee_token):
        """Employee role cannot add employees."""
        res = api_client.post(
            "/api/employees",
            json={"name": "Test User", "email": "test@test.com",
                  "department": "Engineering", "role": "EMPLOYEE"},
            headers={"Authorization": f"Bearer {employee_token}"},
        )
        assert res.status_code == 403

    def test_add_employee_requires_auth(self, api_client):
        """No token returns 401 or 403."""
        res = api_client.post(
            "/api/employees",
            json={"name": "Test User", "email": "test@test.com",
                  "department": "Engineering", "role": "EMPLOYEE"},
        )
        assert res.status_code in (401, 403)

    def test_add_employee_missing_fields(self, api_client, hr_token):
        """Missing required fields returns 422."""
        res = api_client.post(
            "/api/employees",
            json={"name": "Test User"},
            headers={"Authorization": f"Bearer {hr_token}"},
        )
        assert res.status_code == 422

    def test_add_employee_invalid_role(self, api_client, hr_token):
        """Invalid role value returns 400."""
        res = api_client.post(
            "/api/employees",
            json={"name": "Test User", "email": "newtest@test.com",
                  "department": "Engineering", "role": "ADMIN"},
            headers={"Authorization": f"Bearer {hr_token}"},
        )
        assert res.status_code == 400

    @patch("api.routers.employees.send_welcome_email", return_value=True)
    def test_add_employee_success(self, mock_email, api_client, hr_token):
        """
        Full happy path:
        - Employee inserted into DB
        - Password generated in correct format (Pyte@XXXX for 'Pytest Employee')
        - Email called AFTER DB insert
        - Response contains employee data + generated password
        """
        import random
        unique_email = f"pytest_emp_{random.randint(10000, 99999)}@test.com"

        res = api_client.post(
            "/api/employees",
            json={
                "name": "Pytest Employee",
                "email": unique_email,
                "department": "Testing",
                "role": "EMPLOYEE",
            },
            headers={"Authorization": f"Bearer {hr_token}"},
        )

        assert res.status_code == 200
        data = res.json()

        assert data["success"] is True
        assert "employee" in data
        assert "generated_password" in data
        assert "email_sent" in data

        emp = data["employee"]
        assert emp["name"] == "Pytest Employee"
        assert emp["email"] == unique_email
        assert emp["department"] == "Testing"
        assert emp["role"] == "EMPLOYEE"
        assert "id" in emp

        # Password: "Pytestemployee"[:4] = "Pyte" + @ + 4 digits
        pwd = data["generated_password"]
        assert pwd.startswith("Pyte")
        assert "@" in pwd
        suffix = pwd.split("@")[1]
        assert len(suffix) == 4
        assert suffix.isdigit()

        # Email was called exactly once, AFTER DB insert
        mock_email.assert_called_once()

        # Cleanup
        from src.tools.db_connection import get_db
        db = get_db()
        db.execute_query("DELETE FROM employees WHERE email = %s", (unique_email,))

    @patch("api.routers.employees.send_welcome_email", return_value=True)
    def test_duplicate_email_rejected(self, mock_email, api_client, hr_token, employee_employee):
        """
        Duplicate email returns 400.
        Email must NOT be sent — DB insert never happened.
        """
        res = api_client.post(
            "/api/employees",
            json={
                "name": "Duplicate Test",
                "email": employee_employee["email"],
                "department": "Testing",
                "role": "EMPLOYEE",
            },
            headers={"Authorization": f"Bearer {hr_token}"},
        )

        assert res.status_code == 400
        assert "already registered" in res.json()["detail"].lower()
        mock_email.assert_not_called()

    @patch("api.routers.employees.send_welcome_email", return_value=False)
    def test_email_failure_does_not_block_success(self, mock_email, api_client, hr_token):
        """
        If email fails, employee is still created.
        success=True, email_sent=False, message mentions 'manually'.
        """
        import random
        unique_email = f"pytest_noemail_{random.randint(10000, 99999)}@test.com"

        res = api_client.post(
            "/api/employees",
            json={
                "name": "No Email Test",
                "email": unique_email,
                "department": "Testing",
                "role": "EMPLOYEE",
            },
            headers={"Authorization": f"Bearer {hr_token}"},
        )

        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert data["email_sent"] is False
        assert "manually" in data["message"].lower()

        # Cleanup
        from src.tools.db_connection import get_db
        db = get_db()
        db.execute_query("DELETE FROM employees WHERE email = %s", (unique_email,))


# ── Critical rule: email NEVER sent before DB insert ─────────────────────────

class TestEmailOrderGuarantee:

    @patch("api.routers.employees.send_welcome_email")
    def test_email_not_sent_if_db_fails(self, mock_email, api_client, hr_token):
        """
        If DB insertion fails, email must NOT be called.
        Verifies the strict order: DB first, email only after success.
        """
        with patch("api.routers.employees.get_db") as mock_db:
            mock_instance = MagicMock()
            mock_instance.execute_query.return_value = []   # no duplicate found
            mock_instance.insert_query.return_value = None  # insert failed
            mock_db.return_value = mock_instance

            res = api_client.post(
                "/api/employees",
                json={
                    "name": "DB Fail Test",
                    "email": "dbfail@test.com",
                    "department": "Testing",
                    "role": "EMPLOYEE",
                },
                headers={"Authorization": f"Bearer {hr_token}"},
            )

        assert res.status_code == 500
        # Email must NOT have been called
        mock_email.assert_not_called()
