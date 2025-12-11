# Contributing to Honestly

Thank you for your interest in contributing to Honestly! This document provides guidelines and instructions for contributing to the project.

---

## 🎯 Ways to Contribute

### Code Contributions
- **Bug Fixes** — Fix reported issues
- **Features** — Implement new features
- **Tests** — Improve test coverage
- **Performance** — Optimize existing code
- **Security** — Enhance security features

### Non-Code Contributions
- **Documentation** — Improve guides and docs
- **Bug Reports** — Report issues with detailed info
- **Feature Requests** — Suggest new features
- **Code Reviews** — Review pull requests
- **Community Support** — Help others in discussions

---

## 🚀 Getting Started

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then:
git clone https://github.com/YOUR-USERNAME/honestly.git
cd honestly

# Add upstream remote
git remote add upstream https://github.com/veridicusio/honestly.git
```

### 2. Set Up Development Environment

```bash
# Install all dependencies
make install

# Start development environment
make up

# Verify everything works
make test
```

See [SETUP.md](SETUP.md) for detailed setup instructions.

### 3. Create a Branch

```bash
# Create a feature branch
git checkout -b feature/your-feature-name

# Or for bug fixes
git checkout -b fix/issue-description
```

Branch naming conventions:
- `feature/` — New features
- `fix/` — Bug fixes
- `docs/` — Documentation updates
- `refactor/` — Code refactoring
- `test/` — Test additions or fixes
- `chore/` — Build/tooling changes

---

## 📝 Development Workflow

### Making Changes

1. **Write Code**
   - Follow existing code style
   - Add tests for new features
   - Update documentation as needed

2. **Run Pre-commit Checks**
   ```bash
   # Install pre-commit hooks (first time only)
   pip install pre-commit
   pre-commit install
   
   # Run checks manually
   pre-commit run --all-files
   ```

3. **Run Tests**
   ```bash
   # Python backend tests
   cd backend-python
   pytest tests/ -v --cov
   
   # Frontend tests
   cd frontend-app
   npm test
   
   # E2E tests
   npm run test:e2e
   
   # ZKP tests
   ZK_TESTS=1 pytest tests/test_zk_properties.py -v
   ```

4. **Commit Changes**
   ```bash
   git add .
   git commit -m "feat: add new feature"
   ```

### Commit Message Format

We use [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types:**
- `feat` — New feature
- `fix` — Bug fix
- `docs` — Documentation only
- `style` — Code style changes (formatting)
- `refactor` — Code refactoring
- `test` — Adding or updating tests
- `chore` — Build process or tooling changes
- `perf` — Performance improvements
- `security` — Security improvements

**Examples:**
```bash
feat(vault): add document encryption endpoint
fix(zkp): resolve nullifier tracking issue
docs(api): update API documentation
test(auth): add JWT verification tests
security(api): add rate limiting to upload endpoint
```

---

## 💻 Code Style Guidelines

### Python (Backend)

```python
# Use type hints
def upload_document(doc: DocumentUpload) -> Dict[str, Any]:
    """
    Upload a document to the vault.
    
    Args:
        doc: Document upload request
        
    Returns:
        Dict containing document ID and status
        
    Raises:
        HTTPException: If upload fails
    """
    pass

# Use descriptive variable names
verification_key = load_verification_key("age")  # Good
vk = load_vk("age")  # Bad

# Follow PEP 8, formatted with Black
# Max line length: 100 characters
```

**Key Points:**
- Type hints for all function parameters and returns
- Docstrings for all public functions
- Use async/await for I/O operations
- Handle errors explicitly
- No bare `except:` statements

### JavaScript/TypeScript (Frontend)

```javascript
// Use functional components
import React from 'react';

const DocumentCard = ({ document }) => {
  const { id, type, createdAt } = document;
  
  return (
    <div className="card">
      <h3>{type}</h3>
      <p>{id}</p>
    </div>
  );
};

export default DocumentCard;

// Use descriptive names
const verificationResult = await verifyProof(proof);  // Good
const res = await verify(p);  // Bad

// Use ES6+ features
const { name, age } = user;
const documents = users.map(u => u.documents);
```

**Key Points:**
- Functional components with hooks
- ES6+ syntax (arrow functions, destructuring)
- Meaningful variable names
- Proper error handling
- JSX for React components

### Rust (Solana Program)

```rust
// Use descriptive names and proper error handling
pub fn process_stake(
    ctx: Context<Stake>,
    amount: u64,
) -> Result<()> {
    require!(amount > 0, ErrorCode::InvalidAmount);
    
    // Implementation
    
    Ok(())
}

// Use proper validation
#[account(mut, has_one = authority)]
pub user_account: Account<'info, UserAccount>,
```

**Key Points:**
- Descriptive function and variable names
- Proper error handling with custom errors
- Security checks (require!, has_one, etc.)
- Documentation comments

---

## 🧪 Testing Guidelines

### Unit Tests

```python
# Python unit test example
def test_document_upload():
    """Test document upload endpoint."""
    doc = DocumentUpload(
        type="passport",
        data="encrypted_data",
        metadata={"country": "US"}
    )
    
    result = upload_document(doc)
    
    assert result["status"] == "success"
    assert "id" in result
```

```javascript
// JavaScript unit test example
describe('DocumentCard', () => {
  it('renders document information', () => {
    const doc = { id: '123', type: 'passport', createdAt: '2024-01-01' };
    const { getByText } = render(<DocumentCard document={doc} />);
    
    expect(getByText('passport')).toBeInTheDocument();
    expect(getByText('123')).toBeInTheDocument();
  });
});
```

### Integration Tests

```python
# Test API endpoint integration
async def test_vault_upload_integration(client):
    """Test full vault upload flow."""
    response = await client.post(
        "/vault/upload",
        json={"type": "passport", "data": "encrypted"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
```

### Test Coverage

- **Target**: 80% coverage minimum
- **Required**: All new features must have tests
- **Critical Paths**: 100% coverage for security-critical code

---

## 🔐 Security Considerations

### Before Submitting

- [ ] No hardcoded secrets or credentials
- [ ] Input validation on all user inputs
- [ ] Proper error handling (no information leakage)
- [ ] SQL/Cypher injection prevention
- [ ] XSS prevention
- [ ] Rate limiting considerations
- [ ] Authentication/authorization checks

### Reporting Security Issues

**DO NOT** create public issues for security vulnerabilities.

Instead, email: security@honestly.dev

Include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

---

## 📚 Documentation

### When to Update Documentation

Update docs when you:
- Add new features
- Change existing behavior
- Add new dependencies
- Modify configuration
- Change deployment procedures

### Documentation Standards

1. **README Files**
   - Include purpose, setup, usage, examples
   - Keep concise but comprehensive
   - Add links to related docs

2. **API Documentation**
   - Document all endpoints
   - Include request/response examples
   - List possible error codes
   - Specify authentication requirements

3. **Code Comments**
   - Explain WHY, not WHAT
   - Document complex algorithms
   - Note security considerations
   - Link to external resources

4. **Inline Documentation**
   ```python
   def complex_function(param: str) -> Dict[str, Any]:
       """
       Brief description of function.
       
       Longer explanation if needed, including:
       - Algorithm explanation
       - Performance considerations
       - Security notes
       
       Args:
           param: Description of parameter
           
       Returns:
           Description of return value
           
       Raises:
           ValueError: When param is invalid
       """
   ```

---

## 🔄 Pull Request Process

### Before Submitting

1. **Update from upstream**
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Run all checks**
   ```bash
   make test
   pre-commit run --all-files
   ```

3. **Update documentation**
   - Update relevant README files
   - Add/update code comments
   - Update CHANGELOG.md

### Submitting PR

1. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create Pull Request**
   - Use descriptive title
   - Fill out PR template
   - Link related issues
   - Add screenshots for UI changes

3. **PR Title Format**
   ```
   feat(component): add new feature
   fix(api): resolve error handling
   docs(readme): update setup instructions
   ```

### PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Changes Made
- List of changes
- Another change

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No new warnings generated
- [ ] Tests pass locally
- [ ] Dependent changes merged

## Screenshots (if applicable)
[Add screenshots here]

## Related Issues
Closes #123
```

### Review Process

1. **Automated Checks**
   - CI/CD pipeline runs
   - Tests must pass
   - Linting must pass
   - Coverage requirements met

2. **Code Review**
   - At least one approval required
   - Address review comments
   - Keep discussions professional

3. **Merge**
   - Squash and merge (default)
   - Maintainers will merge approved PRs

---

## 🏆 Recognition

Contributors will be:
- Added to CONTRIBUTORS.md
- Mentioned in release notes
- Credited in relevant documentation

---

## 📞 Getting Help

### Questions?
- [GitHub Discussions](https://github.com/veridicusio/honestly/discussions)
- Discord (coming soon)

### Stuck?
- Check [SETUP.md](SETUP.md) for setup issues
- Review [ARCHITECTURE.md](ARCHITECTURE.md) for design questions
- Search existing [Issues](https://github.com/veridicusio/honestly/issues)

### Want to Help?
Look for issues labeled:
- `good first issue` — Great for newcomers
- `help wanted` — Looking for contributors
- `documentation` — Documentation improvements

---

## 📜 Code of Conduct

### Our Standards

**Positive Behavior:**
- Being respectful and inclusive
- Gracefully accepting criticism
- Focusing on what's best for the community
- Showing empathy towards others

**Unacceptable Behavior:**
- Harassment or discriminatory language
- Trolling or insulting comments
- Personal or political attacks
- Publishing others' private information

### Enforcement

Violations can be reported to: conduct@honestly.dev

Maintainers will review and take appropriate action.

---

## 📄 License

By contributing, you agree that your contributions will be licensed under the AGPL-3.0-only license.

See [LICENSE](LICENSE) for details.

---

<div align="center">

**Thank you for contributing to Honestly!** 🙏

Your contributions help build a more private and secure internet.

[⭐ Star the Project](https://github.com/veridicusio/honestly) • [📖 Read the Docs](https://docs.honestly.dev)

</div>
