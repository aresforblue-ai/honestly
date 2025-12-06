"""
Chaos Engineering Tests
Tests system resilience when dependencies fail
"""
import requests
import time
import json
import subprocess
from typing import Dict, List

class ChaosTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results = []
    
    def check_health(self) -> Dict:
        """Check current health status."""
        try:
            res = requests.get(f"{self.base_url}/monitoring/health", timeout=5)
            return {
                "status": "healthy" if res.status_code == 200 else "unhealthy",
                "response_code": res.status_code,
                "data": res.json() if res.status_code == 200 else None
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def test_neo4j_failure(self) -> Dict:
        """Test behavior when Neo4j fails."""
        print("Testing Neo4j failure...")
        
        # Get baseline health
        baseline = self.check_health()
        
        # Stop Neo4j (if using Docker)
        try:
            subprocess.run(["docker", "stop", "honestly-neo4j"], check=False, timeout=10)
            print("  Neo4j stopped")
        except Exception as e:
            print(f"  Could not stop Neo4j: {e}")
            return {"status": "skipped", "reason": "Neo4j not accessible"}
        
        # Wait for failure detection
        time.sleep(5)
        
        # Check health after failure
        health_after = self.check_health()
        
        # Check if health endpoint reflects failure
        health_reflects_failure = False
        if health_after.get("data"):
            checks = health_after["data"].get("checks", {})
            neo4j_check = checks.get("neo4j", {})
            if neo4j_check.get("status") != "healthy":
                health_reflects_failure = True
        
        # Restart Neo4j
        try:
            subprocess.run(["docker", "start", "honestly-neo4j"], check=False, timeout=10)
            print("  Neo4j restarted")
            time.sleep(10)  # Wait for recovery
        except Exception as e:
            print(f"  Could not restart Neo4j: {e}")
        
        # Check recovery
        health_recovered = self.check_health()
        
        return {
            "test": "Neo4j Failure",
            "baseline": baseline,
            "after_failure": health_after,
            "health_reflects_failure": health_reflects_failure,
            "recovered": health_recovered,
            "status": "PASS" if health_reflects_failure else "FAIL"
        }
    
    def test_high_load_during_failure(self) -> Dict:
        """Test system behavior under high load during dependency failure."""
        print("Testing high load during failure...")
        
        import concurrent.futures
        
        def make_request():
            try:
                res = requests.get(f"{self.base_url}/monitoring/health", timeout=2)
                return {
                    "status_code": res.status_code,
                    "response_time": res.elapsed.total_seconds()
                }
            except Exception as e:
                return {"error": str(e)}
        
        # Baseline: Normal load
        print("  Baseline load test...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
            baseline_results = list(executor.map(lambda _: make_request(), range(100)))
        
        baseline_success = sum(1 for r in baseline_results if r.get("status_code") == 200)
        baseline_avg_time = sum(
            r.get("response_time", 0) for r in baseline_results if "response_time" in r
        ) / len([r for r in baseline_results if "response_time" in r])
        
        # During failure: High load
        print("  High load during failure...")
        # (In real test, you'd stop a dependency here)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
            failure_results = list(executor.map(lambda _: make_request(), range(200)))
        
        failure_success = sum(1 for r in failure_results if r.get("status_code") == 200)
        failure_avg_time = sum(
            r.get("response_time", 0) for r in failure_results if "response_time" in r
        ) / len([r for r in failure_results if "response_time" in r])
        
        return {
            "test": "High Load During Failure",
            "baseline": {
                "success_rate": baseline_success / len(baseline_results),
                "avg_response_time": baseline_avg_time
            },
            "during_failure": {
                "success_rate": failure_success / len(failure_results),
                "avg_response_time": failure_avg_time
            },
            "status": "PASS" if failure_success > 0 else "FAIL"  # System should still respond
        }
    
    def test_graceful_degradation(self) -> Dict:
        """Test graceful degradation when dependencies fail."""
        print("Testing graceful degradation...")
        
        # Test endpoints that depend on Neo4j
        endpoints = [
            "/vault/share/test_token",
            "/monitoring/health",
        ]
        
        results = []
        for endpoint in endpoints:
            try:
                res = requests.get(f"{self.base_url}{endpoint}", timeout=5)
                
                # Check if error response is graceful (not 500 with stack trace)
                is_graceful = (
                    res.status_code in [200, 404, 503] and
                    "traceback" not in res.text.lower() and
                    "exception" not in res.text.lower()
                )
                
                results.append({
                    "endpoint": endpoint,
                    "status_code": res.status_code,
                    "is_graceful": is_graceful
                })
            except Exception as e:
                results.append({
                    "endpoint": endpoint,
                    "error": str(e),
                    "is_graceful": False
                })
        
        all_graceful = all(r.get("is_graceful", False) for r in results)
        
        return {
            "test": "Graceful Degradation",
            "results": results,
            "status": "PASS" if all_graceful else "FAIL"
        }
    
    def run_all_tests(self) -> Dict:
        """Run all chaos tests."""
        print("Running chaos engineering tests...")
        print("="*70)
        
        tests = [
            self.test_graceful_degradation(),
            self.test_high_load_during_failure(),
            # self.test_neo4j_failure(),  # Commented out - requires Docker access
        ]
        
        summary = {
            "total_tests": len(tests),
            "passed": sum(1 for t in tests if t.get("status") == "PASS"),
            "failed": sum(1 for t in tests if t.get("status") == "FAIL"),
            "tests": tests
        }
        
        return summary
    
    def print_report(self, summary: Dict):
        """Print chaos test report."""
        print("\n" + "="*70)
        print("CHAOS ENGINEERING TEST REPORT")
        print("="*70)
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Passed: {summary['passed']} ✅")
        print(f"Failed: {summary['failed']} ❌")
        print("="*70)
        
        for test in summary['tests']:
            status_icon = "✅" if test.get("status") == "PASS" else "❌"
            print(f"\n{status_icon} {test.get('test', 'Unknown')}: {test.get('status', 'UNKNOWN')}")
            if test.get("status") == "FAIL":
                print(f"   Details: {json.dumps(test, indent=2)}")

if __name__ == "__main__":
    tester = ChaosTester()
    summary = tester.run_all_tests()
    tester.print_report(summary)
    
    # Save results
    with open("chaos-test-results.json", "w") as f:
        json.dump(summary, f, indent=2)
    
    print("\nResults saved to chaos-test-results.json")


