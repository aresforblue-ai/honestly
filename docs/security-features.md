# Security Features Documentation

Comprehensive documentation of Honestly's security features, threat model, and security architecture.

## 🔒 Security Architecture

### Defense in Depth

Honestly implements multiple layers of security:

1. **Network Layer**: CORS, rate limiting, IP blocking
2. **Application Layer**: Input validation, authentication, authorization
3. **Data Layer**: Encryption at rest (AES-256-GCM), encryption in transit (TLS)
4. **Cryptographic Layer**: Zero-knowledge proofs (Groth16), HMAC signatures
5. **Monitoring Layer**: Security event logging, threat detection, audit trails

## 🛡️ Security Features

### 1. Authentication & Authorization

#### JWT Authentication
- **Implementation**: `api/security.py`
- **Algorithm**: RS256 (recommended) or HS256
- **Token Expiry**: Configurable (default: 1 hour)
- **Refresh Tokens**: Supported for long-lived sessions
- **Key Rotation**: Supported via environment variables

#### API Key Authentication
- **Endpoint**: `/ai/*`
- **Header**: `X-API-Key`
- **Storage**: Environment variable `AI_API_KEY`
- **Rate Limiting**: Per-key rate limits

#### HMAC Signature Verification
- **Purpose**: Bundle integrity verification
- **Algorithm**: HMAC-SHA256
- **Secret**: `BUNDLE_HMAC_SECRET` environment variable
- **Usage**: Share bundle signatures

### 2. Rate Limiting

#### Implementation
- **Backend**: Redis (distributed) or in-memory (fallback)
- **Strategy**: Token bucket algorithm
- **Windows**: Configurable per endpoint (default: 60 seconds)

#### Rate Limits by Endpoint

| Endpoint | Limit | Window | Notes |
|----------|-------|--------|-------|
| `/vault/share/*/bundle` | 20 | 60s | Public endpoint |
| `/vault/upload` | 10 | 60s | Requires auth |
| `/graphql` | 60 | 60s | Per IP |
| `/ai/verify-proof` | 100 | 60s | Per API key |
| `/ai/verify-proofs-batch` | 10 | 60s | Per API key |
| `/ai/share-link` | 50 | 60s | Per API key |
| `/zkp/artifacts/*` | 100 | 60s | Static files |

#### Configuration
```bash
RATE_LIMIT_ENABLED=true
RATE_LIMIT_WINDOW=60
RATE_LIMIT_MAX=60
RATE_LIMIT_PATHS=/vault/share,/graphql
```

### 3. Input Validation & Sanitization

#### XSS Prevention
- **Pattern Detection**: Common XSS patterns blocked
- **Output Encoding**: Automatic encoding in templates
- **CSP Headers**: Content Security Policy enforced

#### SQL Injection Prevention
- **Neo4j Parameterization**: All queries use parameterized Cypher
- **Input Sanitization**: String sanitization before database queries
- **Pattern Detection**: SQL injection patterns detected and blocked

#### Path Traversal Prevention
- **Path Validation**: All file paths validated
- **Directory Restrictions**: Access limited to allowed directories
- **Normalization**: Path normalization before access

#### Token Format Validation
- **Format**: Alphanumeric, 32-64 characters
- **Regex**: `^[a-zA-Z0-9]{32,64}$`
- **Validation**: Performed on all token inputs

### 4. Security Headers

#### Implemented Headers

| Header | Value | Purpose |
|--------|-------|---------|
| `X-Content-Type-Options` | `nosniff` | Prevent MIME sniffing |
| `X-Frame-Options` | `DENY` | Prevent clickjacking |
| `X-XSS-Protection` | `1; mode=block` | XSS protection |
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` | Force HTTPS |
| `Content-Security-Policy` | See below | Restrict resource loading |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Control referrer info |

#### Content Security Policy

```
default-src 'self';
connect-src 'self' <allowed-origins>;
img-src 'self' data:;
style-src 'self' 'unsafe-inline';
script-src 'self';
frame-ancestors 'none';
```

**Configuration**:
```bash
ENABLE_SECURITY_HEADERS=true
STRICT_CORS=true
ALLOWED_ORIGINS=https://app.honestly.dev,https://api.honestly.dev
```

### 5. CORS Configuration

#### Strict CORS Mode
- **Purpose**: Fail fast if misconfigured
- **Check**: Validates `ALLOWED_ORIGINS` on startup
- **Error**: Raises `RuntimeError` if `STRICT_CORS=true` and origins not set

#### Configuration
```bash
ENABLE_CORS=true
STRICT_CORS=true
ALLOWED_ORIGINS=https://app.honestly.dev,https://api.honestly.dev
```

### 6. Threat Detection

#### Automatic IP Blocking
- **Threshold**: 5 suspicious requests
- **Duration**: Configurable (default: 1 hour)
- **Detection**: XSS, SQL injection, path traversal attempts

#### Suspicious Input Detection
- **Patterns**: XSS, SQL injection, path traversal
- **Logging**: All detections logged
- **Response**: 400 Bad Request with generic error

#### Security Event Logging
- **Endpoint**: `/monitoring/security/events`
- **Storage**: In-memory (configurable for persistence)
- **Retention**: Configurable (default: 1000 events)

### 7. Encryption

#### Data at Rest
- **Algorithm**: AES-256-GCM
- **Key Management**: Environment variable `VAULT_ENCRYPTION_KEY`
- **Key Format**: Base64-encoded 256-bit key
- **IV**: Random per encryption
- **Storage**: Encrypted documents stored in Neo4j

#### Data in Transit
- **Protocol**: TLS 1.2+ (HTTPS)
- **Certificate**: Valid SSL/TLS certificate required
- **HSTS**: Strict Transport Security enforced

#### Key Rotation
- **Process**: Documented in `docs/key-rotation-guide.md`
- **Zero Downtime**: Supported via key versioning
- **Backup**: Keys must be backed up securely

### 8. Zero-Knowledge Proof Security

#### Circuit Security
- **Proving System**: Groth16 (bn128/BLS12-381)
- **Hash Function**: Poseidon (optimized for circuits)
- **Trusted Setup**: Powers of Tau ceremony (16)
- **Verification Keys**: Immutable, served with ETags

#### Proof Verification
- **Client-Side**: Primary verification method
- **Server-Side**: Optional via `/ai/verify-proof`
- **Performance**: <0.2s verification time target

#### Attack Surface Mitigation
- **Proof Replay**: Nonce-based prevention (see tests)
- **Timestamp Manipulation**: Circuit constraints prevent manipulation
- **Field Overflow**: Circuit constraints prevent overflow
- **Malformed Merkle Paths**: Circuit validation rejects invalid paths

### 9. Audit Logging

#### Logged Events
- **Authentication**: Login attempts, failures, successes
- **Authorization**: Access denied events
- **Security**: Threat detections, IP blocks
- **Operations**: Document uploads, proof generations
- **Errors**: All errors logged with context

#### Audit Trail
- **Storage**: Neo4j graph database
- **Retention**: Configurable (default: 1 year)
- **Access**: Via `/monitoring/security/events`

### 10. Monitoring & Alerting

#### Health Checks
- **Liveness**: `GET /health/live` (<0.05s)
- **Readiness**: `GET /health/ready` (checks dependencies)
- **Comprehensive**: `GET /monitoring/health` (full system check)

#### Metrics
- **Prometheus**: `/metrics` endpoint
- **Grafana**: Pre-configured dashboards
- **Alerts**: Configurable alert rules

#### Security Metrics
- **Threat Count**: Total threats detected
- **Rate Limit Hits**: Rate limit violations
- **Error Rate**: Error percentage
- **Response Times**: P95/P99 response times

## 🔍 Threat Model

### Identified Threats

#### 1. Injection Attacks
- **Risk**: High
- **Mitigation**: Input validation, parameterized queries, CSP headers
- **Status**: ✅ Mitigated

#### 2. Cross-Site Scripting (XSS)
- **Risk**: Medium
- **Mitigation**: Input sanitization, CSP headers, output encoding
- **Status**: ✅ Mitigated

#### 3. Cross-Site Request Forgery (CSRF)
- **Risk**: Low
- **Mitigation**: CORS restrictions, SameSite cookies (if used)
- **Status**: ✅ Mitigated

#### 4. Authentication Bypass
- **Risk**: High
- **Mitigation**: JWT validation, API key verification, HMAC signatures
- **Status**: ✅ Mitigated

#### 5. Rate Limit Bypass
- **Risk**: Medium
- **Mitigation**: Distributed rate limiting (Redis), IP-based limits
- **Status**: ✅ Mitigated

#### 6. Proof Replay Attacks
- **Risk**: Medium
- **Mitigation**: Nonce-based prevention, timestamp validation
- **Status**: ✅ Mitigated (see tests)

#### 7. Timestamp Manipulation
- **Risk**: Medium
- **Mitigation**: Circuit constraints, server-side validation
- **Status**: ✅ Mitigated (see tests)

#### 8. Field Overflow
- **Risk**: Low
- **Mitigation**: Circuit constraints, input validation
- **Status**: ✅ Mitigated (see tests)

#### 9. Malformed Merkle Paths
- **Risk**: Low
- **Mitigation**: Circuit validation, input sanitization
- **Status**: ✅ Mitigated (see tests)

#### 10. Denial of Service (DoS)
- **Risk**: Medium
- **Mitigation**: Rate limiting, connection limits, resource monitoring
- **Status**: ✅ Mitigated

## 🧪 Security Testing

### Automated Tests

#### ZK Attack Surface Tests
- **Location**: `backend-python/zkp/tests/test_circuits.py`
- **Coverage**:
  - Proof replay attacks
  - Timestamp manipulation
  - Field overflow/underflow
  - Malformed Merkle paths
  - Boundary value analysis
  - Integer overflow/underflow
  - Leap year edge cases

#### Security Audit Tests
- **Location**: `backend-python/tests/security/security_audit.py`
- **Coverage**:
  - XSS detection
  - SQL injection detection
  - Path traversal detection
  - Rate limiting
  - Security headers
  - CORS configuration

#### Load Tests
- **Location**: `backend-python/tests/load/load_test.js`
- **Coverage**:
  - Performance under load
  - Rate limit effectiveness
  - Error handling under stress

#### Chaos Tests
- **Location**: `backend-python/tests/chaos/`
- **Coverage**:
  - Network partition simulation
  - Service failure recovery
  - Database reconnection

### Manual Testing

#### DAST (Dynamic Application Security Testing)
- **Tool**: OWASP ZAP
- **Command**: See `AUDIT.md`
- **Frequency**: Before each release

#### Penetration Testing
- **Frequency**: Quarterly
- **Scope**: Full application stack
- **Report**: Stored securely

## 📋 Security Checklist

### Pre-Deployment

- [ ] All dependencies updated and scanned
- [ ] Security headers enabled
- [ ] CORS configured correctly
- [ ] Rate limiting configured
- [ ] Encryption keys set and backed up
- [ ] SSL/TLS certificates valid
- [ ] Security tests passing
- [ ] Audit logging enabled
- [ ] Monitoring configured
- [ ] Backup strategy in place

### Post-Deployment

- [ ] Health checks responding
- [ ] Metrics being collected
- [ ] Alerts configured
- [ ] Logs being aggregated
- [ ] Security events being monitored
- [ ] Performance within targets
- [ ] No security warnings in logs

## 🔗 Related Documentation

- [Security Policy](../SECURITY.md) - Security policy and vulnerability reporting
- [Audit Readiness](../AUDIT.md) - Audit preparation guide
- [Production Deployment](../backend-python/PRODUCTION.md) - Production security considerations
- [Key Rotation Guide](key-rotation-guide.md) - Key rotation procedures
- [ZK-SNARK Security Audit](ZKSNARK-SECURITY-AUDIT.md) - ZK circuit security

---

**Last Updated**: 2024-12-19  
**Version**: 1.0.0  
**Maintainer**: Security Team

