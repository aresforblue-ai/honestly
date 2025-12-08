# Security Policy

## 🔒 Security Features

Honestly implements production-grade security features to protect user data and prevent attacks.

### Threat Detection & Prevention

- **Automatic IP Blocking**: IPs are automatically blocked after 5 suspicious requests
- **Rate Limiting**: Per-endpoint rate limits (20-100 requests/minute)
- **Input Validation**: XSS, SQL injection, and path traversal detection
- **Security Headers**: CSP, HSTS, XSS protection, frame options
- **Request Monitoring**: All requests are logged and monitored

### Security Headers

The application automatically includes:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Strict-Transport-Security: max-age=31536000; includeSubDomains; preload`
- `Content-Security-Policy`: Strict CSP policy
- `Referrer-Policy: strict-origin-when-cross-origin`

### Rate Limiting

Default rate limits per endpoint:
- `/vault/share/*/bundle`: 20 requests/minute
- `/vault/upload`: 10 requests/minute
- `/graphql`: 60 requests/minute
- `/ai/*`: Configurable per endpoint
- `/zkp/artifacts/*`: 100 requests/minute

### Input Validation

All inputs are validated and sanitized:
- Token format validation
- Document ID validation
- XSS pattern detection
- SQL injection detection
- Path traversal prevention

## 🛡️ Supported Versions

| Version | Supported          | Security Updates | End of Life |
| ------- | ------------------ | ---------------- | ----------- |
| 1.0.x   | :white_check_mark: | Active           | TBD         |
| < 1.0   | :x:                | None             | N/A         |

**Current Version**: 1.0.0  
**Last Security Update**: 2024-12-19  
**Next Security Review**: 2025-01-19

We actively support the latest version and provide security updates as needed.

### Dependency Versions

**Backend (Python)**:
- FastAPI: 0.115.5
- Uvicorn: 0.32.0
- Ariadne: 0.23.0
- Py2neo: 2021.2.4
- Cryptography: ≥41.0.0
- PyJWT: ≥2.8.0
- Pydantic: ≥2.0.0
- Redis: ≥5.0.0

**ZK-SNARK Stack**:
- Circom: 2.1.6 (with `-O2` optimization for production)
- snarkjs: 0.7.3
- circomlibjs: 0.0.8
- Powers of Tau: 16 (final)
- Level 3 circuits: `-O2` mandatory (73% constraint reduction)

**Frontend**:
- React: 18.2.0
- Vite: 5.0.8
- snarkjs: 0.7.3

**Infrastructure**:
- Neo4j: 5.x
- Docker: Latest
- Prometheus: Latest
- Grafana: Latest

## 🚨 Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security vulnerability, please follow these steps:

### How to Report

1. **Do NOT** create a public GitHub issue
2. Email security details to: `security@honestly.dev` (or use GitHub Security Advisories)
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

### What to Expect

- **Initial Response**: Within 48 hours
- **Status Updates**: Weekly until resolved
- **Resolution Timeline**: Depends on severity
  - **Critical**: 24-48 hours
  - **High**: 1 week
  - **Medium**: 2-4 weeks
  - **Low**: Next release cycle

### Vulnerability Disclosure Policy

- We will acknowledge receipt of your report within 48 hours
- We will investigate and confirm the vulnerability
- We will work on a fix and keep you updated
- We will credit you in security advisories (if desired)
- We will coordinate public disclosure after a fix is available

### What We Consider a Vulnerability

- Remote code execution
- SQL injection
- Cross-site scripting (XSS)
- Cross-site request forgery (CSRF)
- Authentication/authorization bypass
- Data exposure or leakage
- Denial of service (DoS)
- Cryptographic weaknesses

### What We Don't Consider Vulnerabilities

- Issues requiring physical access
- Issues requiring social engineering
- Denial of service via resource exhaustion (unless severe)
- Missing security headers (unless causing actual vulnerability)
- Issues in third-party dependencies (report to them directly)
- Issues already reported and being worked on

## 🔐 Security Best Practices

### For Users

1. **Use HTTPS**: Always use HTTPS in production
2. **Set Strong Passwords**: Use strong, unique passwords
3. **Rotate API Keys**: Regularly rotate API keys
4. **Monitor Access**: Review access logs regularly
5. **Keep Updated**: Always use the latest version

### For Developers

1. **Never Commit Secrets**: Use environment variables
2. **Validate Input**: Always validate and sanitize inputs
3. **Use HTTPS**: Never expose HTTP in production
4. **Rate Limit**: Implement rate limiting
5. **Log Security Events**: Log all security-relevant events
6. **Keep Dependencies Updated**: Regularly update dependencies
7. **Security Headers**: Always include security headers
8. **Encrypt Sensitive Data**: Encrypt data at rest and in transit

## 🔍 Security Audit Checklist

Before deploying to production:

- [ ] Change default passwords
- [ ] Set `ENABLE_HSTS=true`
- [ ] Set `ENABLE_DOCS=false` in production
- [ ] Configure `ALLOWED_ORIGINS` correctly
- [ ] Set `AI_API_KEY` for AI endpoints
- [ ] Set `VAULT_ENCRYPTION_KEY` (backup securely!)
- [ ] Enable Redis for distributed caching
- [ ] Configure log aggregation
- [ ] Set up monitoring alerts
- [ ] Configure backup strategy
- [ ] Review rate limits
- [ ] Test disaster recovery
- [ ] Enable HTTPS/TLS
- [ ] Review security headers
- [ ] Audit access logs
- [ ] Review dependencies for vulnerabilities

## 📊 Security Monitoring

### Security Events

All security events are logged and available via:
- `GET /monitoring/security/events` - Recent security events
- `GET /monitoring/security/threats` - Threat summary

### Metrics Tracked

- Suspicious input detection
- Rate limit violations
- IP blocking events
- Failed authentication attempts
- Security header compliance

## 🔄 Security Updates

### Update Process

1. Security vulnerabilities are patched immediately
2. Critical fixes are released as hotfixes
3. Non-critical fixes are included in regular releases
4. Security advisories are published for all vulnerabilities

### Staying Updated

- Subscribe to security advisories
- Monitor GitHub releases
- Review changelog for security fixes
- Keep dependencies updated

## 🔐 ZK Circuit Security

### Circuit Optimization

Level 3 verifiers explode constraints via pairing checks and Poseidon hashes. **Always use aggressive optimizations:**

| Flag | Use Case | Constraint Reduction |
|------|----------|---------------------|
| `-O2` | **Production (required)** | ~73% vs `-O0` |
| `-O1` | Development fallback | ~40% |

### Trusted Setup

- Powers of Tau ceremony completed (phase 1)
- Circuit-specific phase 2 contributions required
- Verification key hashes stored in `INTEGRITY.json`
- ETag/SHA256 integrity checking on all served artifacts

### Nullifier Security

- All proofs generate unique nullifiers
- Nullifiers tracked in Redis to prevent replay attacks
- Nullifier derivation: `Poseidon(secret, scope, timestamp)`

### Audit Status

| Circuit | Audited | Notes |
|---------|---------|-------|
| age | ✅ Internal | Ready for external audit |
| authenticity | ✅ Internal | Ready for external audit |
| age_level3 | ✅ Internal | Uses `-O2` optimization |
| level3_inequality | ✅ Internal | Uses `-O2` optimization |
| agent_capability | 🟡 New | AAIP circuit |
| agent_reputation | 🟡 New | AAIP circuit |

---

## 📚 Security Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CWE Top 25](https://cwe.mitre.org/top25/)
- [Security Headers](https://securityheaders.com/)
- [Mozilla Security Guidelines](https://infosec.mozilla.org/guidelines/web_security)

## 📧 Contact

For security-related questions or concerns:
- **Security Email**: `security@honestly.dev`
- **GitHub Security**: Use GitHub Security Advisories
- **General Issues**: [GitHub Issues](https://github.com/aresforblue-ai/honestly/issues)

---

**Last Updated**: 2024-12-19  
**Version**: 1.0.0  
**Security Contact**: security@honestly.dev  
**CVE Database**: https://github.com/aresforblue-ai/honestly/security/advisories
