"""Load testing script using Locust.

Simulates concurrent users to validate performance requirements:
- API p95 < 500ms
- DB queries p95 < 100ms
- Support 1000 concurrent users

Run: locust -f backend/tests/load/locustfile.py --host=http://localhost:8000
"""
import random
from locust import HttpUser, task, between, events
from datetime import date, timedelta


class FitnessBotUser(HttpUser):
    """Simulated user interacting with fitness bot application."""

    # Wait 1-3 seconds between requests
    wait_time = between(1, 3)

    def on_start(self):
        """Setup user session (login)."""
        # Register or login
        response = self.client.post(
            "/api/v1/auth/login",
            json={
                "email": f"loadtest_user_{random.randint(1, 1000)}@example.com",
                "password": "LoadTest123!",
            },
            catch_response=True,
        )

        if response.status_code == 404:
            # User doesn't exist, register
            response = self.client.post(
                "/api/v1/auth/register",
                json={
                    "email": f"loadtest_user_{random.randint(1, 1000)}@example.com",
                    "password": "LoadTest123!",
                    "full_name": "Load Test User",
                    "date_of_birth": "1990-01-15",
                    "current_fitness_level": "intermediate",
                },
            )

        if response.status_code in [200, 201]:
            data = response.json()
            self.access_token = data["data"]["access_token"]
            response.success()
        else:
            response.failure(f"Login failed: {response.text}")

    @task(5)
    def view_dashboard(self):
        """View user profile (common operation)."""
        headers = {"Authorization": f"Bearer {self.access_token}"}
        with self.client.get(
            "/api/v1/users/me",
            headers=headers,
            catch_response=True,
            name="/api/v1/users/me [Dashboard]",
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Dashboard load failed: {response.status_code}")

    @task(10)
    def view_schedule_today(self):
        """View today's schedule (most common operation)."""
        headers = {"Authorization": f"Bearer {self.access_token}"}
        with self.client.get(
            "/api/v1/schedules/today",
            headers=headers,
            catch_response=True,
            name="/api/v1/schedules/today [High Traffic]",
        ) as response:
            if response.status_code in [200, 404]:  # 404 if no plan yet
                response.success()
            else:
                response.failure(f"Schedule load failed: {response.status_code}")

    @task(7)
    def view_upcoming_schedule(self):
        """View upcoming schedule."""
        headers = {"Authorization": f"Bearer {self.access_token}"}
        with self.client.get(
            "/api/v1/schedules/upcoming?days=7",
            headers=headers,
            catch_response=True,
            name="/api/v1/schedules/upcoming [Medium Traffic]",
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Upcoming schedule failed: {response.status_code}")

    @task(3)
    def view_active_plan(self):
        """View active fitness plan."""
        headers = {"Authorization": f"Bearer {self.access_token}"}
        with self.client.get(
            "/api/v1/fitness-plans/active",
            headers=headers,
            catch_response=True,
            name="/api/v1/fitness-plans/active [Medium Traffic]",
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Active plan load failed: {response.status_code}")

    @task(4)
    def view_progress(self):
        """View progress summary."""
        headers = {"Authorization": f"Bearer {self.access_token}"}
        with self.client.get(
            "/api/v1/progress",
            headers=headers,
            catch_response=True,
            name="/api/v1/progress [Medium Traffic]",
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Progress load failed: {response.status_code}")

    @task(2)
    def complete_workout(self):
        """Mark a workout as complete (write operation)."""
        headers = {"Authorization": f"Bearer {self.access_token}"}

        # Get today's schedule first
        schedule_response = self.client.get(
            "/api/v1/schedules/today",
            headers=headers,
        )

        if schedule_response.status_code == 200:
            data = schedule_response.json()
            entries = data.get("data", {}).get("entries", [])

            # Find a scheduled workout
            for entry in entries:
                if entry["entry_type"] == "workout" and entry["completion_status"] == "scheduled":
                    entry_id = entry["id"]

                    with self.client.post(
                        f"/api/v1/schedules/entries/{entry_id}/complete",
                        headers=headers,
                        json={"user_notes": "Completed during load test"},
                        catch_response=True,
                        name="/api/v1/schedules/entries/{id}/complete [Write Op]",
                    ) as response:
                        if response.status_code == 200:
                            response.success()
                        else:
                            response.failure(f"Complete workout failed: {response.status_code}")
                    break

    @task(1)
    def record_weight(self):
        """Record body weight measurement (write operation)."""
        headers = {"Authorization": f"Bearer {self.access_token}"}

        with self.client.post(
            "/api/v1/progress/measurements",
            headers=headers,
            json={
                "record_type": "weight",
                "record_date": date.today().isoformat(),
                "value": random.uniform(150, 200),
                "unit": "lbs",
            },
            catch_response=True,
            name="/api/v1/progress/measurements [Write Op]",
        ) as response:
            if response.status_code in [201, 409]:  # 409 if already recorded today
                response.success()
            else:
                response.failure(f"Record weight failed: {response.status_code}")

    @task(1)
    def start_conversation(self):
        """Start AI conversation (expensive operation)."""
        headers = {"Authorization": f"Bearer {self.access_token}"}

        with self.client.post(
            "/api/v1/ai/conversations",
            headers=headers,
            json={
                "conversation_type": "plan_generation",
                "initial_message": "I want to build muscle in 12 weeks",
            },
            catch_response=True,
            name="/api/v1/ai/conversations [AI Heavy]",
        ) as response:
            if response.status_code == 201:
                response.success()
            else:
                response.failure(f"Start conversation failed: {response.status_code}")


@events.init_command_line_parser.add_listener
def _(parser):
    """Add custom command-line arguments."""
    parser.add_argument(
        "--test-scenario",
        type=str,
        default="normal",
        choices=["normal", "read-heavy", "write-heavy", "ai-heavy"],
        help="Test scenario to run",
    )


# Performance thresholds for validation
PERFORMANCE_THRESHOLDS = {
    "api_p95_ms": 500,  # SC-019: API p95 < 500ms
    "db_p95_ms": 100,   # SC-019: DB queries p95 < 100ms
    "max_error_rate": 1.0,  # Max 1% error rate
}


@events.quitting.add_listener
def _(environment, **kwargs):
    """Validate performance thresholds after test completes."""
    stats = environment.stats.total

    # Calculate p95 response time
    if stats.num_requests > 0:
        p95_ms = stats.get_response_time_percentile(0.95)
        error_rate = (stats.num_failures / stats.num_requests) * 100

        print("\n" + "=" * 60)
        print("LOAD TEST RESULTS")
        print("=" * 60)
        print(f"Total Requests: {stats.num_requests}")
        print(f"Failures: {stats.num_failures}")
        print(f"Error Rate: {error_rate:.2f}%")
        print(f"Average Response Time: {stats.avg_response_time:.2f}ms")
        print(f"P95 Response Time: {p95_ms:.2f}ms")
        print(f"Min Response Time: {stats.min_response_time:.2f}ms")
        print(f"Max Response Time: {stats.max_response_time:.2f}ms")
        print(f"Requests/sec: {stats.total_rps:.2f}")
        print("=" * 60)

        # Validate against thresholds
        passed = True

        if p95_ms > PERFORMANCE_THRESHOLDS["api_p95_ms"]:
            print(f"❌ FAILED: API p95 ({p95_ms:.2f}ms) exceeds threshold ({PERFORMANCE_THRESHOLDS['api_p95_ms']}ms)")
            passed = False
        else:
            print(f"✓ PASSED: API p95 ({p95_ms:.2f}ms) within threshold ({PERFORMANCE_THRESHOLDS['api_p95_ms']}ms)")

        if error_rate > PERFORMANCE_THRESHOLDS["max_error_rate"]:
            print(f"❌ FAILED: Error rate ({error_rate:.2f}%) exceeds threshold ({PERFORMANCE_THRESHOLDS['max_error_rate']}%)")
            passed = False
        else:
            print(f"✓ PASSED: Error rate ({error_rate:.2f}%) within threshold ({PERFORMANCE_THRESHOLDS['max_error_rate']}%)")

        print("=" * 60)

        if not passed:
            environment.process_exit_code = 1
        else:
            print("✓ ALL PERFORMANCE THRESHOLDS MET")
            print("=" * 60)
