# Known Issues and Considerations

This document tracks known issues, limitations, and areas for future improvement in the Honestly codebase.

## 📦 Dependency Deprecation Warnings

### Apollo Server v4 (backend-graphql)
- **Status**: Will transition to end-of-life on January 26, 2026
- **Current Version**: 4.9.5 (package.json), 4.12.2 (installed via npm)
- **Impact**: Low (non-security related, plenty of time before EOL)
- **Recommendation**: Upgrade to Apollo Server v5 before EOL date (requires Node.js non-EOL version)
- **Note**: Apollo v5 is available and upgrading typically takes only a few minutes
- **Documentation**: https://www.apollographql.com/docs/apollo-server/previous-versions

### ESLint 8.x (backend-graphql)
- **Status**: No longer supported
- **Current Version**: 8.57.1
- **Impact**: Low (functionally working, security updates unlikely)
- **Recommendation**: Upgrade to ESLint 9.x
- **Note**: May require updating ESLint configuration format

### Other npm Deprecations
The following packages show deprecation warnings but are transitive dependencies:
- `rimraf@3.0.2` - Used by dependencies, no direct impact
- `inflight@1.0.6` - Memory leak in legacy code, consider lru-cache alternative
- `glob@7.2.3` - Used by dependencies, upgrade to v9 if directly used
- `@humanwhocodes/*` - ESLint internal dependencies, will be updated with ESLint upgrade

## 🏗️ Infrastructure & Setup

### ConductMe Dependencies
- **Issue**: `conductme/` and `conductme/core/` directories don't have `node_modules` tracked
- **Status**: Expected behavior (node_modules in .gitignore)
- **Solution**: Run `cd conductme && npm install && cd core && npm install`
- **Documentation Needed**: Add setup instructions to main README.md

### Docker Compose Files
- **Resolved**: Removed incorrect reference to `docker-compose-updated.yml`
- **Available Files**:
  - `docker-compose.yml` - Main orchestration
  - `docker-compose.dev.yml` - Development setup
  - `docker-compose.min.yml` - Minimal stack
  - `docker-compose.monitoring.yml` - Monitoring stack

## 🧪 Testing Infrastructure

### Backend GraphQL Tests
- **Status**: ✅ Fixed - Test infrastructure created
- **Location**: `backend-graphql/tests/`
- **Current State**: Placeholder test exists, real tests should be added as features are developed
- **Next Steps**: Add integration tests for GraphQL resolvers

### Python Backend Tests
- **Status**: ✅ Tests exist and functional
- **Location**: `backend-python/tests/`, `backend-python/*/tests/`
- **Coverage**: Good coverage across API, vault, identity, and ZKP modules

### Frontend Tests
- **Status**: E2E tests exist
- **Location**: `frontend-app/tests/e2e/`
- **Framework**: Playwright
- **Next Steps**: Consider adding unit tests for React components

## 🔐 Security Considerations

### Production Hardening Checklist
All security checks have been reviewed and are properly implemented:
- ✅ No hardcoded credentials found
- ✅ No unsafe eval/exec usage
- ✅ Proper error handling in place
- ✅ Environment variable validation
- ✅ Rate limiting configured
- ✅ Input sanitization implemented
- ✅ Path traversal prevention
- ✅ ZKP circuit integrity checks

### Debug Logging
- Print statements in `backend-python/api/security_checks.py` are intentional for security reports
- Warning in `backend-python/api/app.py` is intentional for missing optional dependencies

## 📝 Code Quality Notes

### Abstract Methods with `pass`
Multiple files contain `pass` statements that are intentional:
- **Abstract base classes**: `identity/cross_chain_bridge.py`
- **Custom exceptions**: `api/cache.py`
- **Intentional silent failures**: `api/vault_routes.py` (JSON parsing fallback)

These are not bugs but proper Python patterns.

### Empty Implementations
Some functions have minimal implementations marked with `pass`:
- These are primarily placeholder methods in abstract classes
- No incomplete feature implementations were found

## 🚀 Future Improvements

### High Priority
1. Add comprehensive GraphQL integration tests
2. Document ConductMe setup process
3. Create upgrade guide for Apollo Server v5 migration

### Medium Priority
1. Upgrade ESLint to v9.x in backend-graphql
2. Add React component unit tests
3. Review and update npm package versions

### Low Priority
1. Consider TypeScript migration for better type safety
2. Evaluate replacing deprecated transitive dependencies
3. Performance profiling and optimization

## 📊 Test Coverage

### Current Status
- **Root Level**: Jest with path utilities tests ✅
- **Backend Python**: pytest with good coverage ✅
- **Backend GraphQL**: Basic placeholder test ⚠️
- **Frontend**: Playwright E2E tests ✅

### Target Goals
- Maintain >80% code coverage across all modules
- Add mutation/integration tests for GraphQL
- Expand E2E test scenarios

## 🔄 CI/CD Status

All CI workflows are functional:
- ✅ Python lint and test
- ✅ Frontend build
- ✅ ConductMe build (requires npm install)
- ✅ ZKP integrity checks
- ✅ Docker build
- ✅ Security scanning

## 📚 Documentation

### Well Documented
- Architecture (ARCHITECTURE.md)
- Security (SECURITY.md)
- Setup (SETUP.md)
- API documentation (docs/)
- Vault quickstart (docs/vault-quickstart.md)

### Areas for Improvement
- ConductMe-specific documentation
- Upgrade/migration guides
- Troubleshooting guide

---

**Last Updated**: 2025-12-08  
**Review Frequency**: Quarterly or when major changes occur
