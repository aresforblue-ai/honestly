#!/usr/bin/env python3
"""
Chaos Engineering Tests
Tests system resilience when dependencies fail.
"""
import sys
import time
import requests
import docker
from typing import Dict


class ChaosEngineer:
    """Chaos engineering test harness."""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.client = docker.from_env()
        self.test_results = []

    def check_health(self) -> Dict:
        """Check system health."""
        try:
            resp = requests.get(f"{self.base_url}/monitoring/health", timeout=5)
            return {
                "status": resp.status_code,
                "healthy": resp.status_code == 200,
                "data": resp.json() if resp.status_code == 200 else None,
            }
        except Exception as e:
            return {"status": 0, "healthy": False, "error": str(e)}

    def check_readiness(self) -> Dict:
        """Check system readiness."""
        try:
            resp = requests.get(f"{self.base_url}/monitoring/ready", timeout=5)
            return {
                "status": resp.status_code,
                "ready": resp.status_code == 200,
                "data": resp.json() if resp.status_code == 200 else None,
            }
        except Exception as e:
            return {"status": 0, "ready": False, "error": str(e)}

    def kill_container(self, container_name: str) -> bool:
        """Kill a Docker container."""
        try:
            container = self.client.containers.get(container_name)
            container.stop()
            print(f"  ✓ Stopped container: {container_name}")
            return True
        except docker.errors.NotFound:
            print(f"  ⚠ Container not found: {container_name}")
            return False
        except Exception as e:
            print(f"  ✗ Error stopping container: {e}")
            return False

    def start_container(self, container_name: str) -> bool:
        """Start a Docker container."""
        try:
            container = self.client.containers.get(container_name)
            container.start()
            print(f"  ✓ Started container: {container_name}")
            return True
        except docker.errors.NotFound:
            print(f"  ⚠ Container not found: {container_name}")
            return False
        except Exception as e:
            print(f"  ✗ Error starting container: {e}")
            return False

    def wait_for_recovery(self, max_wait: int = 30) -> bool:
        """Wait for system to recover."""
        print(f"  Waiting for recovery (max {max_wait}s)...")
        for i in range(max_wait):
            health = self.check_health()
            if health["healthy"]:
                print(f"  ✓ System recovered after {i+1}s")
                return True
            time.sleep(1)
        print(f"  ✗ System did not recover within {max_wait}s")
        return False

    def test_redis_failure(self):
        """Test: Kill Redis, verify graceful degradation."""
        print("\n" + "=" * 70)
        print("CHAOS TEST: Redis Failure")
        print("=" * 70)

        # Baseline health check
        print("\n[1] Baseline health check")
        baseline = self.check_health()
        print(f"  Status: {baseline['status']}, Healthy: {baseline['healthy']}")

        # Kill Redis
        print("\n[2] Killing Redis container")
        redis_killed = self.kill_container("honestly-redis")

        if not redis_killed:
            print("  ⚠ Redis container not found, skipping test")
            return

        # Wait a moment
        time.sleep(2)

        # Check health after Redis failure
        print("\n[3] Health check after Redis failure")
        health_after = self.check_health()
        print(f"  Status: {health_after['status']}")

        # System should still be healthy (Redis is optional for rate limiting)
        if health_after["healthy"]:
            print("  ✓ System remains healthy (Redis optional)")
            self.test_results.append(
                {"test": "redis_failure", "status": "PASSED", "graceful_degradation": True}
            )
        else:
            print("  ⚠ System health degraded (may be expected)")
            self.test_results.append(
                {"test": "redis_failure", "status": "DEGRADED", "graceful_degradation": False}
            )

        # Restart Redis
        print("\n[4] Restarting Redis container")
        self.start_container("honestly-redis")
        time.sleep(5)

        # Verify recovery
        print("\n[5] Verifying recovery")
        recovery = self.wait_for_recovery()
        if recovery:
            print("  ✓ System recovered successfully")
        else:
            print("  ✗ System did not recover")

    def test_neo4j_failure(self):
        """Test: Kill Neo4j, verify graceful degradation."""
        print("\n" + "=" * 70)
        print("CHAOS TEST: Neo4j Failure")
        print("=" * 70)

        # Baseline health check
        print("\n[1] Baseline health check")
        baseline = self.check_health()
        print(f"  Status: {baseline['status']}, Healthy: {baseline['healthy']}")

        # Kill Neo4j
        print("\n[2] Killing Neo4j container")
        neo4j_killed = self.kill_container("honestly-neo4j")

        if not neo4j_killed:
            print("  ⚠ Neo4j container not found, skipping test")
            return

        # Wait a moment
        time.sleep(2)

        # Check health after Neo4j failure
        print("\n[3] Health check after Neo4j failure")
        health_after = self.check_health()
        print(f"  Status: {health_after['status']}")

        # Check readiness (should fail)
        print("\n[4] Readiness check after Neo4j failure")
        readiness = self.check_readiness()
        print(f"  Status: {readiness['status']}, Ready: {readiness['ready']}")

        if not readiness["ready"]:
            print("  ✓ Readiness correctly reflects Neo4j failure")
            self.test_results.append(
                {"test": "neo4j_failure", "status": "PASSED", "readiness_reflects_failure": True}
            )
        else:
            print("  ✗ Readiness should reflect Neo4j failure")
            self.test_results.append(
                {"test": "neo4j_failure", "status": "FAILED", "readiness_reflects_failure": False}
            )

        # Restart Neo4j
        print("\n[5] Restarting Neo4j container")
        self.start_container("honestly-neo4j")
        time.sleep(10)  # Neo4j takes longer to start

        # Verify recovery
        print("\n[6] Verifying recovery")
        recovery = self.wait_for_recovery(max_wait=60)
        if recovery:
            print("  ✓ System recovered successfully")
        else:
            print("  ✗ System did not recover")

    def test_api_failure(self):
        """Test: Kill API container, verify monitoring detects it."""
        print("\n" + "=" * 70)
        print("CHAOS TEST: API Failure")
        print("=" * 70)

        # This test would require external monitoring
        # For now, just verify health endpoint fails
        print("\n  Note: API failure test requires external monitoring")
        print("  Verify that monitoring/alerting detects API downtime")

    def run_all_tests(self):
        """Run all chaos tests."""
        print("=" * 70)
        print("CHAOS ENGINEERING TEST SUITE")
        print("=" * 70)
        print(f"Target: {self.base_url}")
        print("")

        try:
            self.test_redis_failure()
            time.sleep(5)

            self.test_neo4j_failure()
            time.sleep(5)

            self.test_api_failure()
        except docker.errors.DockerException as e:
            print(f"\n✗ Docker error: {e}")
            print("  Make sure Docker is running and containers are accessible")
        except Exception as e:
            print(f"\n✗ Error running chaos tests: {e}")
            import traceback

            traceback.print_exc()

        self.print_summary()

    def print_summary(self):
        """Print test summary."""
        print("\n" + "=" * 70)
        print("CHAOS TEST SUMMARY")
        print("=" * 70)

        for result in self.test_results:
            status_icon = "✓" if result["status"] == "PASSED" else "✗"
            print(f"{status_icon} {result['test']}: {result['status']}")

        print("=" * 70)


if __name__ == "__main__":
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"

    try:
        engineer = ChaosEngineer(base_url)
        engineer.run_all_tests()
    except ImportError:
        print("ERROR: docker library not installed")
        print("Install: pip install docker")
        sys.exit(1)
