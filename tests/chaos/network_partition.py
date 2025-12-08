"""
Network Partition Simulation using ToxiProxy
Tests Neo4j reconnection behavior in distributed setups
"""
import requests
import time
import json
from typing import Dict, List, Optional

class NetworkPartitionTester:
    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        toxiproxy_url: str = "http://localhost:8474"
    ):
        self.base_url = base_url
        self.toxiproxy_url = toxiproxy_url
        self.results = []
    
    def check_toxiproxy(self) -> bool:
        """Check if ToxiProxy is available."""
        try:
            res = requests.get(f"{self.toxiproxy_url}/version", timeout=2)
            return res.status_code == 200
        except Exception:
            return False
    
    def create_proxy(self, name: str, listen_port: int, upstream: str) -> Dict:
        """Create a ToxiProxy proxy."""
        proxy_config = {
            "name": name,
            "listen": f"0.0.0.0:{listen_port}",
            "upstream": upstream,
            "enabled": True
        }
        
        res = requests.post(
            f"{self.toxiproxy_url}/proxies",
            json=proxy_config,
            timeout=5
        )
        
        if res.status_code in [200, 201, 409]:  # 409 = already exists
            return {"status": "created", "proxy": name}
        else:
            return {"status": "error", "error": res.text}
    
    def add_toxic(self, proxy_name: str, toxic_type: str, attributes: Dict) -> Dict:
        """Add a toxic (network condition) to a proxy."""
        toxic_config = {
            "type": toxic_type,
            "attributes": attributes
        }
        
        res = requests.post(
            f"{self.toxiproxy_url}/proxies/{proxy_name}/toxics",
            json=toxic_config,
            timeout=5
        )
        
        if res.status_code == 200:
            return {"status": "added", "toxic": toxic_type}
        else:
            return {"status": "error", "error": res.text}
    
    def remove_toxic(self, proxy_name: str, toxic_name: str) -> Dict:
        """Remove a toxic."""
        res = requests.delete(
            f"{self.toxiproxy_url}/proxies/{proxy_name}/toxics/{toxic_name}",
            timeout=5
        )
        
        if res.status_code == 200:
            return {"status": "removed"}
        else:
            return {"status": "error", "error": res.text}
    
    def test_network_partition(self) -> Dict:
        """Test network partition (complete disconnection)."""
        print("Testing network partition...")
        
        if not self.check_toxiproxy():
            return {
                "test": "Network Partition",
                "status": "SKIPPED",
                "reason": "ToxiProxy not available"
            }
        
        # Create proxy for Neo4j
        proxy_result = self.create_proxy(
            name="neo4j_partition",
            listen_port=7688,  # Proxy port
            upstream="neo4j:7687"  # Real Neo4j
        )
        
        if proxy_result.get("status") != "created":
            return {
                "test": "Network Partition",
                "status": "ERROR",
                "error": proxy_result.get("error", "Failed to create proxy")
            }
        
        # Get baseline health
        baseline_health = self._check_api_health()
        
        # Add timeout toxic (simulates partition)
        timeout_result = self.add_toxic(
            proxy_name="neo4j_partition",
            toxic_type="timeout",
            attributes={"timeout": 0}  # Immediate timeout
        )
        
        if timeout_result.get("status") != "added":
            return {
                "test": "Network Partition",
                "status": "ERROR",
                "error": "Failed to add timeout toxic"
            }
        
        # Wait for partition to take effect
        time.sleep(2)
        
        # Check health during partition
        partition_health = self._check_api_health()
        
        # Check if system handles gracefully
        is_graceful = (
            partition_health.get("status_code") in [200, 503] and
            "traceback" not in partition_health.get("response", "").lower()
        )
        
        # Remove toxic (restore connection)
        self.remove_toxic("neo4j_partition", "timeout_downstream")
        time.sleep(5)  # Wait for reconnection
        
        # Check recovery
        recovery_health = self._check_api_health()
        
        recovered = recovery_health.get("status_code") == 200
        
        return {
            "test": "Network Partition",
            "baseline": baseline_health,
            "during_partition": partition_health,
            "after_recovery": recovery_health,
            "is_graceful": is_graceful,
            "recovered": recovered,
            "status": "PASS" if (is_graceful and recovered) else "FAIL"
        }
    
    def test_latency_injection(self) -> Dict:
        """Test high latency (simulates slow network)."""
        print("Testing latency injection...")
        
        if not self.check_toxiproxy():
            return {
                "test": "Latency Injection",
                "status": "SKIPPED",
                "reason": "ToxiProxy not available"
            }
        
        # Create proxy
        self.create_proxy(
            name="neo4j_latency",
            listen_port=7689,
            upstream="neo4j:7687"
        )
        
        # Add latency toxic (500ms delay)
        self.add_toxic(
            proxy_name="neo4j_latency",
            toxic_type="latency",
            attributes={"latency": 500}
        )
        
        time.sleep(2)
        
        # Measure response time
        start = time.time()
        health = self._check_api_health()
        duration = (time.time() - start) * 1000  # ms
        
        # System should still respond (may be slower)
        still_responds = health.get("status_code") in [200, 503]
        
        # Remove latency
        self.remove_toxic("neo4j_latency", "latency_downstream")
        
        return {
            "test": "Latency Injection",
            "response_time_ms": duration,
            "still_responds": still_responds,
            "status": "PASS" if still_responds else "FAIL"
        }
    
    def test_bandwidth_limit(self) -> Dict:
        """Test bandwidth limitation."""
        print("Testing bandwidth limit...")
        
        if not self.check_toxiproxy():
            return {
                "test": "Bandwidth Limit",
                "status": "SKIPPED",
                "reason": "ToxiProxy not available"
            }
        
        # Create proxy
        self.create_proxy(
            name="neo4j_bandwidth",
            listen_port=7690,
            upstream="neo4j:7687"
        )
        
        # Add bandwidth limit (1KB/s)
        self.add_toxic(
            proxy_name="neo4j_bandwidth",
            toxic_type="bandwidth",
            attributes={"rate": 1024}  # 1KB/s
        )
        
        time.sleep(2)
        
        # System should handle gracefully
        health = self._check_api_health()
        handles_gracefully = health.get("status_code") in [200, 503]
        
        # Remove limit
        self.remove_toxic("neo4j_bandwidth", "bandwidth_downstream")
        
        return {
            "test": "Bandwidth Limit",
            "handles_gracefully": handles_gracefully,
            "status": "PASS" if handles_gracefully else "FAIL"
        }
    
    def _check_api_health(self) -> Dict:
        """Check API health endpoint."""
        try:
            res = requests.get(f"{self.base_url}/monitoring/health", timeout=5)
            return {
                "status_code": res.status_code,
                "response": res.text[:500]  # First 500 chars
            }
        except Exception as e:
            return {
                "status_code": 0,
                "error": str(e)
            }
    
    def run_all_tests(self) -> Dict:
        """Run all network partition tests."""
        print("Running network partition tests...")
        print("="*70)
        
        tests = [
            self.test_network_partition(),
            self.test_latency_injection(),
            self.test_bandwidth_limit(),
        ]
        
        summary = {
            "total_tests": len(tests),
            "passed": sum(1 for t in tests if t.get("status") == "PASS"),
            "failed": sum(1 for t in tests if t.get("status") == "FAIL"),
            "skipped": sum(1 for t in tests if t.get("status") == "SKIPPED"),
            "tests": tests
        }
        
        return summary
    
    def print_report(self, summary: Dict):
        """Print test report."""
        print("\n" + "="*70)
        print("NETWORK PARTITION TEST REPORT")
        print("="*70)
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Passed: {summary['passed']} ✅")
        print(f"Failed: {summary['failed']} ❌")
        print(f"Skipped: {summary['skipped']} ⏭️")
        print("="*70)
        
        for test in summary['tests']:
            status_icon = {
                "PASS": "✅",
                "FAIL": "❌",
                "SKIPPED": "⏭️",
                "ERROR": "⚠️"
            }.get(test.get("status", "UNKNOWN"), "❓")
            
            print(f"\n{status_icon} {test.get('test', 'Unknown')}: {test.get('status', 'UNKNOWN')}")
            if test.get("status") == "FAIL":
                print(f"   Details: {json.dumps(test, indent=2)}")

if __name__ == "__main__":
    tester = NetworkPartitionTester()
    summary = tester.run_all_tests()
    tester.print_report(summary)
    
    # Save results
    with open("network-partition-results.json", "w") as f:
        json.dump(summary, f, indent=2)
    
    print("\nResults saved to network-partition-results.json")


