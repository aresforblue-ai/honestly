"""
Startup Security Validation

Runs on application startup to ensure security configuration is correct.
Blocks startup in production if critical security requirements are not met.

Checks:
1. JWT_SECRET is not default
2. CORS origins are properly configured
3. HSTS is enabled in production
4. Rate limiting is configured
5. Debug mode is disabled in production
6. Required environment variables are set
7. Database connections are secure (TLS)
8. Secrets are not exposed in logs
"""

import os
import sys
import logging
from typing import List, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class Severity(Enum):
    CRITICAL = "CRITICAL"  # Blocks startup in production
    HIGH = "HIGH"          # Warning in dev, blocks in prod
    MEDIUM = "MEDIUM"      # Warning only
    LOW = "LOW"            # Info only

@dataclass
class SecurityCheck:
    name: str
    severity: Severity
    passed: bool
    message: str
    remediation: str = ""

class SecurityValidator:
    """
    Validates security configuration at startup.
    """
    
    def __init__(self):
        self.checks: List[SecurityCheck] = []
        self.is_production = os.getenv("ENVIRONMENT", "development").lower() == "production"
    
    def run_all_checks(self) -> Tuple[bool, List[SecurityCheck]]:
        """Run all security checks and return results"""
        self.checks = []
        
        self._check_jwt_secret()
        self._check_cors_config()
        self._check_hsts()
        self._check_rate_limiting()
        self._check_debug_mode()
        self._check_required_env_vars()
        self._check_database_security()
        self._check_secrets_exposure()
        self._check_allowed_hosts()
        self._check_ssl_redirect()
        
        # Determine if startup should be blocked
        critical_failures = [
            c for c in self.checks 
            if not c.passed and c.severity in (Severity.CRITICAL, Severity.HIGH)
        ]
        
        should_block = self.is_production and len(critical_failures) > 0
        
        return (not should_block, self.checks)
    
    def _add_check(self, name: str, severity: Severity, passed: bool, 
                   message: str, remediation: str = ""):
        self.checks.append(SecurityCheck(
            name=name,
            severity=severity,
            passed=passed,
            message=message,
            remediation=remediation,
        ))
    
    def _check_jwt_secret(self):
        """Ensure JWT_SECRET is properly configured"""
        secret = os.getenv("JWT_SECRET", "")
        default_secret = "CHANGE_ME_IN_PRODUCTION_use_openssl_rand_hex_32"
        
        if not secret:
            self._add_check(
                "JWT_SECRET",
                Severity.CRITICAL,
                False,
                "JWT_SECRET environment variable is not set",
                "Set JWT_SECRET to a random 32+ character string: openssl rand -hex 32"
            )
        elif secret == default_secret:
            self._add_check(
                "JWT_SECRET",
                Severity.CRITICAL if self.is_production else Severity.MEDIUM,
                not self.is_production,
                "JWT_SECRET is using default value",
                "Set JWT_SECRET to a random 32+ character string: openssl rand -hex 32"
            )
        elif len(secret) < 32:
            self._add_check(
                "JWT_SECRET",
                Severity.HIGH,
                False,
                f"JWT_SECRET is too short ({len(secret)} chars, need 32+)",
                "Use a longer secret: openssl rand -hex 32"
            )
        else:
            self._add_check(
                "JWT_SECRET",
                Severity.CRITICAL,
                True,
                "JWT_SECRET is properly configured"
            )
    
    def _check_cors_config(self):
        """Ensure CORS is properly configured"""
        allowed_origins = os.getenv("ALLOWED_ORIGINS", "")
        enable_cors = os.getenv("ENABLE_CORS", "true").lower() == "true"
        strict_cors = os.getenv("STRICT_CORS", "false").lower() == "true"
        
        if not enable_cors:
            self._add_check(
                "CORS",
                Severity.MEDIUM,
                True,
                "CORS is disabled"
            )
            return
        
        if "*" in allowed_origins:
            self._add_check(
                "CORS",
                Severity.HIGH if self.is_production else Severity.MEDIUM,
                not self.is_production,
                "CORS allows all origins (*)",
                "Set ALLOWED_ORIGINS to specific domains in production"
            )
        elif not allowed_origins and self.is_production:
            self._add_check(
                "CORS",
                Severity.HIGH,
                False,
                "ALLOWED_ORIGINS not set in production",
                "Set ALLOWED_ORIGINS=https://yourdomain.com"
            )
        else:
            self._add_check(
                "CORS",
                Severity.HIGH,
                True,
                f"CORS configured: {allowed_origins[:50]}..."
            )
    
    def _check_hsts(self):
        """Ensure HSTS is enabled in production"""
        enable_hsts = os.getenv("ENABLE_SECURITY_HEADERS", "true").lower() == "true"
        hsts_max_age = int(os.getenv("HSTS_MAX_AGE", "0"))
        
        if self.is_production:
            if not enable_hsts:
                self._add_check(
                    "HSTS",
                    Severity.HIGH,
                    False,
                    "Security headers disabled in production",
                    "Set ENABLE_SECURITY_HEADERS=true"
                )
            elif hsts_max_age < 31536000:  # 1 year
                self._add_check(
                    "HSTS",
                    Severity.MEDIUM,
                    False,
                    f"HSTS max-age too short ({hsts_max_age}s, recommend 31536000)",
                    "Set HSTS_MAX_AGE=31536000"
                )
            else:
                self._add_check(
                    "HSTS",
                    Severity.HIGH,
                    True,
                    f"HSTS enabled with max-age={hsts_max_age}"
                )
        else:
            self._add_check(
                "HSTS",
                Severity.LOW,
                True,
                "HSTS check skipped (development mode)"
            )
    
    def _check_rate_limiting(self):
        """Ensure rate limiting is configured"""
        rate_limit_enabled = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
        rate_limit_max = int(os.getenv("RATE_LIMIT_MAX", "100"))
        
        if not rate_limit_enabled:
            self._add_check(
                "Rate Limiting",
                Severity.HIGH if self.is_production else Severity.MEDIUM,
                not self.is_production,
                "Rate limiting is disabled",
                "Set RATE_LIMIT_ENABLED=true"
            )
        elif rate_limit_max > 1000:
            self._add_check(
                "Rate Limiting",
                Severity.MEDIUM,
                False,
                f"Rate limit too high ({rate_limit_max}/window)",
                "Consider lowering RATE_LIMIT_MAX"
            )
        else:
            self._add_check(
                "Rate Limiting",
                Severity.HIGH,
                True,
                f"Rate limiting enabled: {rate_limit_max}/window"
            )
    
    def _check_debug_mode(self):
        """Ensure debug mode is disabled in production"""
        debug = os.getenv("DEBUG", "false").lower() == "true"
        
        if debug and self.is_production:
            self._add_check(
                "Debug Mode",
                Severity.CRITICAL,
                False,
                "DEBUG=true in production environment",
                "Set DEBUG=false in production"
            )
        else:
            self._add_check(
                "Debug Mode",
                Severity.CRITICAL,
                True,
                "Debug mode properly configured"
            )
    
    def _check_required_env_vars(self):
        """Check required environment variables are set"""
        required_vars = [
            ("NEO4J_URI", Severity.HIGH),
            ("NEO4J_USER", Severity.HIGH),
            ("NEO4J_PASSWORD", Severity.HIGH),
        ]
        
        if self.is_production:
            required_vars.extend([
                ("JWT_SECRET", Severity.CRITICAL),
                ("ALLOWED_ORIGINS", Severity.HIGH),
            ])
        
        missing = []
        for var, severity in required_vars:
            if not os.getenv(var):
                missing.append((var, severity))
        
        if missing:
            for var, severity in missing:
                self._add_check(
                    f"Env: {var}",
                    severity,
                    False,
                    f"Required environment variable {var} is not set",
                    f"Set {var} in your environment or .env file"
                )
        else:
            self._add_check(
                "Required Env Vars",
                Severity.HIGH,
                True,
                "All required environment variables are set"
            )
    
    def _check_database_security(self):
        """Check database connection security"""
        neo4j_uri = os.getenv("NEO4J_URI", "")
        
        if self.is_production:
            if neo4j_uri.startswith("bolt://") and not neo4j_uri.startswith("bolt+s://"):
                self._add_check(
                    "Database TLS",
                    Severity.HIGH,
                    False,
                    "Neo4j connection is not using TLS",
                    "Use bolt+s:// or neo4j+s:// for encrypted connections"
                )
            else:
                self._add_check(
                    "Database TLS",
                    Severity.HIGH,
                    True,
                    "Database connection appears secure"
                )
        else:
            self._add_check(
                "Database TLS",
                Severity.LOW,
                True,
                "Database TLS check skipped (development mode)"
            )
    
    def _check_secrets_exposure(self):
        """Check that secrets aren't logged"""
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        
        if log_level == "DEBUG" and self.is_production:
            self._add_check(
                "Log Level",
                Severity.MEDIUM,
                False,
                "DEBUG logging in production may expose secrets",
                "Set LOG_LEVEL=INFO or LOG_LEVEL=WARNING"
            )
        else:
            self._add_check(
                "Log Level",
                Severity.MEDIUM,
                True,
                f"Log level: {log_level}"
            )
    
    def _check_allowed_hosts(self):
        """Check ALLOWED_HOSTS configuration"""
        allowed_hosts = os.getenv("ALLOWED_HOSTS", "")
        
        if self.is_production and not allowed_hosts:
            self._add_check(
                "Allowed Hosts",
                Severity.MEDIUM,
                False,
                "ALLOWED_HOSTS not set (recommend setting in production)",
                "Set ALLOWED_HOSTS=yourdomain.com,api.yourdomain.com"
            )
        else:
            self._add_check(
                "Allowed Hosts",
                Severity.MEDIUM,
                True,
                f"Allowed hosts: {allowed_hosts or 'not restricted'}"
            )
    
    def _check_ssl_redirect(self):
        """Check SSL redirect configuration"""
        ssl_redirect = os.getenv("SSL_REDIRECT", "false").lower() == "true"
        
        if self.is_production and not ssl_redirect:
            self._add_check(
                "SSL Redirect",
                Severity.MEDIUM,
                False,
                "SSL redirect not enabled in production",
                "Set SSL_REDIRECT=true to force HTTPS"
            )
        else:
            self._add_check(
                "SSL Redirect",
                Severity.MEDIUM,
                True,
                "SSL redirect properly configured"
            )
    
    def print_report(self):
        """Print a formatted security report"""
        print("\n" + "="*70)
        print("🔒 SECURITY VALIDATION REPORT")
        print("="*70)
        print(f"Environment: {'PRODUCTION' if self.is_production else 'DEVELOPMENT'}")
        print("-"*70)
        
        passed = [c for c in self.checks if c.passed]
        failed = [c for c in self.checks if not c.passed]
        
        if failed:
            print("\n❌ FAILED CHECKS:")
            for check in failed:
                icon = "🚨" if check.severity == Severity.CRITICAL else "⚠️"
                print(f"  {icon} [{check.severity.value}] {check.name}")
                print(f"      {check.message}")
                if check.remediation:
                    print(f"      → {check.remediation}")
        
        if passed:
            print("\n✅ PASSED CHECKS:")
            for check in passed:
                print(f"  ✓ {check.name}: {check.message}")
        
        print("\n" + "-"*70)
        print(f"Total: {len(passed)} passed, {len(failed)} failed")
        print("="*70 + "\n")


def validate_security_on_startup():
    """
    Run security validation on application startup.
    Call this in your FastAPI app startup event.
    """
    validator = SecurityValidator()
    passed, checks = validator.run_all_checks()
    validator.print_report()
    
    if not passed:
        logger.critical("Security validation failed! Fix issues before deploying to production.")
        if validator.is_production:
            sys.exit(1)
    else:
        logger.info("✅ Security validation passed")
    
    return passed


# Run if executed directly
if __name__ == "__main__":
    validate_security_on_startup()

