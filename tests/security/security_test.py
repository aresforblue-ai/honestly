"""
Security Testing Suite
Tests for XSS, injection, rate limiting bypass, error handling
"""
import requests
import json
import time
from typing import Dict, List, Tuple

class SecurityTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results = []
    
    def test_xss_injection(self) -> List[Dict]:
        """Test for XSS vulnerabilities."""
        results = []
        
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src=x onerror=alert('XSS')>",
            "'; DROP TABLE users; --",
            "<svg onload=alert('XSS')>",
        ]
        
        endpoints = [
            "/vault/share/test_token",
            "/vault/document/doc_123",
        ]
        
        for endpoint in endpoints:
            for payload in xss_payloads:
                try:
                    # Test in query params
                    res = requests.get(f"{self.base_url}{endpoint}?input={payload}", timeout=5)
                    
                    # Check if payload appears in response
                    if payload in res.text:
                        results.append({
                            "test": "XSS Injection",
                            "endpoint": endpoint,
                            "payload": payload,
                            "status": "VULNERABLE",
                            "response_code": res.status_code
                        })
                    else:
                        results.append({
                            "test": "XSS Injection",
                            "endpoint": endpoint,
                            "payload": payload,
                            "status": "SAFE",
                            "response_code": res.status_code
                        })
                except Exception as e:
                    results.append({
                        "test": "XSS Injection",
                        "endpoint": endpoint,
                        "payload": payload,
                        "status": "ERROR",
                        "error": str(e)
                    })
        
        return results
    
    def test_rate_limit_bypass(self) -> List[Dict]:
        """Test rate limiting effectiveness."""
        results = []
        
        # Test 1: Rapid requests from same IP
        endpoint = "/vault/share/test_token/bundle"
        rate_limit_hits = 0
        successful_requests = 0
        
        for i in range(25):  # Should hit rate limit at 20
            res = requests.get(f"{self.base_url}{endpoint}")
            if res.status_code == 429:
                rate_limit_hits += 1
                # Check for rate limit headers
                if "Retry-After" in res.headers:
                    results.append({
                        "test": "Rate Limit Bypass",
                        "method": "Rapid requests",
                        "status": "PROTECTED",
                        "rate_limit_hits": rate_limit_hits,
                        "has_retry_after": True
                    })
            else:
                successful_requests += 1
            time.sleep(0.1)
        
        # Test 2: Distributed requests (simulate multiple IPs)
        # This would require multiple IPs or proxy rotation
        
        return results
    
    def test_error_handling(self) -> List[Dict]:
        """Test error handling doesn't leak information."""
        results = []
        
        # Test malformed JSON
        try:
            res = requests.post(
                f"{self.base_url}/vault/upload",
                data="invalid json",
                headers={"Content-Type": "application/json"}
            )
            
            # Check for stack traces or sensitive info
            response_text = res.text.lower()
            dangerous_patterns = [
                "traceback",
                "file \"/",
                "line ",
                "exception:",
                "error at",
                "stack trace",
                "neo4j",
                "password",
                "secret",
            ]
            
            leaks = [p for p in dangerous_patterns if p in response_text]
            
            results.append({
                "test": "Error Handling",
                "method": "Malformed JSON",
                "status": "SAFE" if not leaks else "VULNERABLE",
                "leaked_info": leaks,
                "response_code": res.status_code
            })
        except Exception as e:
            results.append({
                "test": "Error Handling",
                "method": "Malformed JSON",
                "status": "ERROR",
                "error": str(e)
            })
        
        # Test invalid endpoints
        try:
            res = requests.get(f"{self.base_url}/nonexistent/endpoint")
            if res.status_code == 404:
                results.append({
                    "test": "Error Handling",
                    "method": "Invalid endpoint",
                    "status": "SAFE",
                    "response_code": 404
                })
        except Exception as e:
            results.append({
                "test": "Error Handling",
                "method": "Invalid endpoint",
                "status": "ERROR",
                "error": str(e)
            })
        
        return results
    
    def test_sql_injection(self) -> List[Dict]:
        """Test for SQL injection (Neo4j Cypher injection)."""
        results = []
        
        # Neo4j uses Cypher, not SQL, but similar injection patterns
        injection_payloads = [
            "' OR '1'='1",
            "'; DROP MATCH (n) DETACH DELETE n; --",
            "1' UNION SELECT * FROM users--",
            "admin'--",
        ]
        
        endpoints = [
            "/vault/document/doc_123",
            "/vault/share/test_token",
        ]
        
        for endpoint in endpoints:
            for payload in injection_payloads:
                try:
                    # Test in path parameters
                    test_endpoint = endpoint.replace("doc_123", payload).replace("test_token", payload)
                    res = requests.get(f"{self.base_url}{test_endpoint}", timeout=5)
                    
                    # Check for error messages that might indicate injection
                    if res.status_code == 500:
                        # Could indicate injection attempt
                        results.append({
                            "test": "SQL/Cypher Injection",
                            "endpoint": endpoint,
                            "payload": payload,
                            "status": "POTENTIALLY_VULNERABLE",
                            "response_code": 500
                        })
                    else:
                        results.append({
                            "test": "SQL/Cypher Injection",
                            "endpoint": endpoint,
                            "payload": payload,
                            "status": "SAFE",
                            "response_code": res.status_code
                        })
                except Exception as e:
                    results.append({
                        "test": "SQL/Cypher Injection",
                        "endpoint": endpoint,
                        "payload": payload,
                        "status": "ERROR",
                        "error": str(e)
                    })
        
        return results
    
    def test_security_headers(self) -> List[Dict]:
        """Test security headers are present."""
        results = []
        
        required_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options",
            "X-XSS-Protection",
            "Strict-Transport-Security",
            "Content-Security-Policy",
        ]
        
        res = requests.get(f"{self.base_url}/monitoring/health")
        
        missing_headers = []
        for header in required_headers:
            if header not in res.headers:
                missing_headers.append(header)
        
        results.append({
            "test": "Security Headers",
            "status": "SAFE" if not missing_headers else "VULNERABLE",
            "missing_headers": missing_headers,
            "present_headers": [h for h in required_headers if h in res.headers]
        })
        
        return results
    
    def run_all_tests(self) -> Dict:
        """Run all security tests."""
        print("Running security tests...")
        
        all_results = {
            "xss_tests": self.test_xss_injection(),
            "rate_limit_tests": self.test_rate_limit_bypass(),
            "error_handling_tests": self.test_error_handling(),
            "injection_tests": self.test_sql_injection(),
            "security_headers_tests": self.test_security_headers(),
        }
        
        # Summary
        total_tests = sum(len(results) for results in all_results.values())
        vulnerable_tests = sum(
            len([r for r in results if r.get("status") == "VULNERABLE"])
            for results in all_results.values()
        )
        safe_tests = sum(
            len([r for r in results if r.get("status") == "SAFE"])
            for results in all_results.values()
        )
        
        summary = {
            "total_tests": total_tests,
            "vulnerable": vulnerable_tests,
            "safe": safe_tests,
            "error_rate": (total_tests - vulnerable_tests - safe_tests) / total_tests if total_tests > 0 else 0,
            "results": all_results
        }
        
        return summary
    
    def print_report(self, summary: Dict):
        """Print security test report."""
        print("\n" + "="*70)
        print("SECURITY TEST REPORT")
        print("="*70)
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Safe: {summary['safe']} ✅")
        print(f"Vulnerable: {summary['vulnerable']} ❌")
        print(f"Errors: {summary['total_tests'] - summary['safe'] - summary['vulnerable']}")
        print("="*70)
        
        for test_category, results in summary['results'].items():
            print(f"\n{test_category.upper()}:")
            for result in results:
                status_icon = "✅" if result.get("status") == "SAFE" else "❌"
                print(f"  {status_icon} {result.get('test', 'Unknown')}: {result.get('status', 'UNKNOWN')}")
                if result.get("status") == "VULNERABLE":
                    print(f"     ⚠️  Details: {result}")

if __name__ == "__main__":
    tester = SecurityTester()
    summary = tester.run_all_tests()
    tester.print_report(summary)
    
    # Save results
    with open("security-test-results.json", "w") as f:
        json.dump(summary, f, indent=2)
    
    print("\nResults saved to security-test-results.json")


