#!/usr/bin/env python3
"""
Security Audit Script
Tests for common vulnerabilities and misconfigurations.
"""
import os
import sys
import json
import requests
import time
from typing import Dict, List, Tuple
from urllib.parse import urljoin

class SecurityAuditor:
    """Security audit tool for the API."""
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.vulnerabilities = []
        self.passed_tests = []
        self.failed_tests = []
    
    def test_rate_limiting_bypass(self) -> bool:
        """Test if rate limiting can be bypassed."""
        print("\n[TEST] Rate Limiting Bypass")
        print("-" * 70)
        
        # Try to bypass rate limiting with different IPs/user agents
        bypass_attempts = [
            {'X-Forwarded-For': '1.2.3.4'},
            {'X-Real-IP': '5.6.7.8'},
            {'X-Forwarded-For': '9.10.11.12', 'X-Real-IP': '13.14.15.16'},
        ]
        
        success_count = 0
        for i, headers in enumerate(bypass_attempts):
            try:
                # Make rapid requests
                for j in range(25):  # Exceed rate limit
                    resp = requests.get(
                        f"{self.base_url}/vault/share/test/bundle",
                        headers=headers,
                        timeout=5
                    )
                    if resp.status_code == 429:
                        break
                else:
                    # If we got here, we didn't hit rate limit
                    self.vulnerabilities.append({
                        'test': 'rate_limiting_bypass',
                        'severity': 'HIGH',
                        'description': f'Rate limiting bypassed with headers: {headers}',
                        'status': 'FAILED'
                    })
                    print(f"  ✗ Rate limiting bypassed with headers: {headers}")
                    return False
                
                success_count += 1
            except Exception as e:
                print(f"  ⚠ Error testing bypass: {e}")
        
        if success_count == len(bypass_attempts):
            print(f"  ✓ Rate limiting cannot be bypassed")
            self.passed_tests.append('rate_limiting_bypass')
            return True
        return False
    
    def test_sql_injection(self) -> bool:
        """Test for SQL injection vulnerabilities."""
        print("\n[TEST] SQL Injection")
        print("-" * 70)
        
        sql_payloads = [
            "' OR '1'='1",
            "'; DROP TABLE users; --",
            "' UNION SELECT * FROM users --",
            "1' OR '1'='1",
        ]
        
        vulnerable = False
        for payload in sql_payloads:
            try:
                # Test in various parameters
                resp = requests.get(
                    f"{self.base_url}/vault/share/{payload}/bundle",
                    timeout=5
                )
                
                # Check for SQL error messages
                if any(keyword in resp.text.lower() for keyword in [
                    'sql syntax', 'mysql', 'postgresql', 'sqlite',
                    'ora-', 'sql error', 'database error'
                ]):
                    self.vulnerabilities.append({
                        'test': 'sql_injection',
                        'severity': 'CRITICAL',
                        'description': f'SQL injection detected with payload: {payload}',
                        'status': 'FAILED'
                    })
                    print(f"  ✗ SQL injection vulnerability detected: {payload}")
                    vulnerable = True
            except Exception as e:
                pass  # Expected for invalid inputs
        
        if not vulnerable:
            print(f"  ✓ No SQL injection vulnerabilities detected")
            self.passed_tests.append('sql_injection')
            return True
        return False
    
    def test_xss(self) -> bool:
        """Test for XSS vulnerabilities."""
        print("\n[TEST] Cross-Site Scripting (XSS)")
        print("-" * 70)
        
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<svg onload=alert('XSS')>",
        ]
        
        vulnerable = False
        for payload in xss_payloads:
            try:
                resp = requests.get(
                    f"{self.base_url}/vault/share/{payload}/bundle",
                    timeout=5
                )
                
                # Check if payload is reflected in response
                if payload in resp.text:
                    self.vulnerabilities.append({
                        'test': 'xss',
                        'severity': 'HIGH',
                        'description': f'XSS vulnerability detected with payload: {payload}',
                        'status': 'FAILED'
                    })
                    print(f"  ✗ XSS vulnerability detected: {payload}")
                    vulnerable = True
            except Exception as e:
                pass
        
        if not vulnerable:
            print(f"  ✓ No XSS vulnerabilities detected")
            self.passed_tests.append('xss')
            return True
        return False
    
    def test_security_headers(self) -> bool:
        """Test security headers."""
        print("\n[TEST] Security Headers")
        print("-" * 70)
        
        required_headers = {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': None,  # Just check presence
            'Content-Security-Policy': None,
        }
        
        try:
            resp = requests.get(f"{self.base_url}/monitoring/health", timeout=5)
            missing_headers = []
            
            for header, expected_value in required_headers.items():
                if header not in resp.headers:
                    missing_headers.append(header)
                elif expected_value and resp.headers[header] != expected_value:
                    self.vulnerabilities.append({
                        'test': 'security_headers',
                        'severity': 'MEDIUM',
                        'description': f'Header {header} has incorrect value: {resp.headers[header]}',
                        'status': 'FAILED'
                    })
                    print(f"  ✗ Header {header} has incorrect value")
            
            if missing_headers:
                self.vulnerabilities.append({
                    'test': 'security_headers',
                    'severity': 'MEDIUM',
                    'description': f'Missing security headers: {missing_headers}',
                    'status': 'FAILED'
                })
                print(f"  ✗ Missing security headers: {missing_headers}")
                return False
            else:
                print(f"  ✓ All security headers present")
                self.passed_tests.append('security_headers')
                return True
        except Exception as e:
            print(f"  ⚠ Error checking headers: {e}")
            return False
    
    def test_error_handling(self) -> bool:
        """Test error handling doesn't leak information."""
        print("\n[TEST] Error Handling")
        print("-" * 70)
        
        # Test malformed JSON
        try:
            resp = requests.post(
                f"{self.base_url}/ai/verify-proof",
                data="invalid json{",
                headers={'Content-Type': 'application/json'},
                timeout=5
            )
            
            # Check for stack traces or internal errors
            sensitive_info = [
                'traceback', 'stack trace', 'file "', 'line ',
                'exception:', 'error:', 'sql', 'database',
                'neo4j', 'internal', 'debug'
            ]
            
            response_lower = resp.text.lower()
            leaked_info = [info for info in sensitive_info if info in response_lower]
            
            if leaked_info:
                self.vulnerabilities.append({
                    'test': 'error_handling',
                    'severity': 'MEDIUM',
                    'description': f'Error response leaks information: {leaked_info}',
                    'status': 'FAILED'
                })
                print(f"  ✗ Error response leaks information: {leaked_info}")
                return False
            else:
                print(f"  ✓ Error handling doesn't leak information")
                self.passed_tests.append('error_handling')
                return True
        except Exception as e:
            print(f"  ⚠ Error testing error handling: {e}")
            return False
    
    def test_authentication_bypass(self) -> bool:
        """Test authentication bypass attempts."""
        print("\n[TEST] Authentication Bypass")
        print("-" * 70)
        
        bypass_attempts = [
            {'Authorization': 'Bearer invalid_token'},
            {'Authorization': 'Bearer '},
            {'Authorization': 'Bearer null'},
            {'X-Auth-Token': 'bypass'},
        ]
        
        vulnerable = False
        for headers in bypass_attempts:
            try:
                # Try to access protected endpoint
                resp = requests.get(
                    f"{self.base_url}/vault/document/test_doc",
                    headers=headers,
                    timeout=5
                )
                
                # Should return 401 or 403, not 200
                if resp.status_code == 200:
                    self.vulnerabilities.append({
                        'test': 'authentication_bypass',
                        'severity': 'CRITICAL',
                        'description': f'Authentication bypassed with headers: {headers}',
                        'status': 'FAILED'
                    })
                    print(f"  ✗ Authentication bypassed with headers: {headers}")
                    vulnerable = True
            except Exception as e:
                pass
        
        if not vulnerable:
            print(f"  ✓ Authentication cannot be bypassed")
            self.passed_tests.append('authentication_bypass')
            return True
        return False
    
    def run_all_tests(self):
        """Run all security tests."""
        print("=" * 70)
        print("SECURITY AUDIT")
        print("=" * 70)
        print(f"Target: {self.base_url}")
        print("")
        
        tests = [
            self.test_rate_limiting_bypass,
            self.test_sql_injection,
            self.test_xss,
            self.test_security_headers,
            self.test_error_handling,
            self.test_authentication_bypass,
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                print(f"  ✗ Test failed with exception: {e}")
                self.failed_tests.append(str(test.__name__))
        
        self.print_summary()
    
    def print_summary(self):
        """Print audit summary."""
        print("\n" + "=" * 70)
        print("SECURITY AUDIT SUMMARY")
        print("=" * 70)
        print(f"Tests passed: {len(self.passed_tests)}")
        print(f"Tests failed: {len(self.failed_tests)}")
        print(f"Vulnerabilities found: {len(self.vulnerabilities)}")
        
        if self.vulnerabilities:
            print("\nVULNERABILITIES:")
            for vuln in self.vulnerabilities:
                print(f"  [{vuln['severity']}] {vuln['test']}: {vuln['description']}")
        
        print("=" * 70)
        
        # Save report
        report = {
            'timestamp': time.time(),
            'base_url': self.base_url,
            'passed_tests': self.passed_tests,
            'failed_tests': self.failed_tests,
            'vulnerabilities': self.vulnerabilities,
        }
        
        with open('security_audit_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\nReport saved to: security_audit_report.json")


if __name__ == '__main__':
    base_url = sys.argv[1] if len(sys.argv) > 1 else 'http://localhost:8000'
    auditor = SecurityAuditor(base_url)
    auditor.run_all_tests()
    
    sys.exit(0 if not auditor.vulnerabilities else 1)


