# Security Guide

## Overview

This document outlines security practices, tools, and procedures for the RAG system. Security is implemented at multiple layers including pre-commit hooks, secrets management, input validation, and dependency scanning.

## Table of Contents

- [Pre-commit Hooks Setup](#pre-commit-hooks-setup)
- [Secrets Management](#secrets-management)
- [Security Scanning Tools](#security-scanning-tools)
- [Input Validation & XSS Prevention](#input-validation--xss-prevention)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

---

## Pre-commit Hooks Setup

Pre-commit hooks provide automated security checks before every commit, preventing vulnerabilities from entering the codebase.

### Installation

```bash
# Install pre-commit hooks
uv run pre-commit install

# Verify installation
uv run pre-commit --version
```

### Configured Hooks

The following security hooks are configured in `.pre-commit-config.yaml`:

#### 1. **detect-secrets** - Secret Detection

Scans for accidentally committed secrets (API keys, passwords, tokens).

```yaml
- repo: https://github.com/Yelp/detect-secrets
  hooks:
    - id: detect-secrets
      args: ['--baseline', '.secrets.baseline']
```

**What it catches:**

- API keys (AWS, Azure, Anthropic, etc.)
- Private keys and certificates
- Passwords and tokens
- High-entropy strings that look like secrets

#### 2. **Bandit** - Python Security Linter

Static analysis tool that finds common security issues in Python code.

```yaml
- repo: https://github.com/PyCQA/bandit
  hooks:
    - id: bandit
      args: ['-c', 'pyproject.toml']
```

**What it catches:**

- SQL injection vulnerabilities
- Use of `eval()` or `exec()`
- Weak cryptography
- Hardcoded passwords
- Shell injection risks

#### 3. **Ruff** - Fast Linter with Security Rules

Modern Python linter with built-in security checks.

```yaml
- repo: https://github.com/astral-sh/ruff-pre-commit
  hooks:
    - id: ruff
      args: [--fix, --exit-non-zero-on-fix]
```

**Security rules enabled:**

- S (flake8-bandit) - Security issues
- Code quality checks that prevent bugs

#### 4. **MyPy** - Type Checking

Strict type checking prevents type-related security issues.

```yaml
- repo: https://github.com/pre-commit/mirrors-mypy
  hooks:
    - id: mypy
      args: [--ignore-missing-imports]
```

### Running Hooks

```bash
# Run all hooks on staged files
git commit -m "your message"

# Run all hooks on all files
uv run pre-commit run --all-files

# Run specific hook
uv run pre-commit run detect-secrets --all-files

# Skip hooks (emergency only - NOT recommended)
git commit --no-verify -m "emergency fix"
```

### Updating Hooks

```bash
# Update all hooks to latest versions
uv run pre-commit autoupdate

# Clean and reinstall hooks
uv run pre-commit clean
uv run pre-commit install --install-hooks
```

---

## Secrets Management

### Never Commit Secrets

**NEVER commit these files:**

- `.env` (contains API keys)
- `credentials.json`
- `*.pem`, `*.key` (private keys)
- Any file with passwords or tokens

### Secrets Baseline

The `.secrets.baseline` file tracks known false positives to reduce noise.

#### Creating the Baseline

```bash
# Initial baseline creation
uv run detect-secrets scan > .secrets.baseline

# Review the baseline
cat .secrets.baseline

# Audit interactively (mark real secrets vs false positives)
uv run detect-secrets audit .secrets.baseline
```

**Interactive audit commands:**

- Press `y` - Mark as real secret (will fail commits)
- Press `n` - Mark as false positive (will be allowed)
- Press `s` - Skip (decide later)

#### Updating the Baseline

When adding new code that triggers false positives:

```bash
# Regenerate baseline with new code
uv run detect-secrets scan > .secrets.baseline

# Audit new findings
uv run detect-secrets audit .secrets.baseline

# Commit the updated baseline
git add .secrets.baseline
git commit -m "chore: update secrets baseline"
```

### Centralized Secrets Management

All secrets are loaded through `config/secrets.py`:

```python
from config.secrets import get_secrets

secrets = get_secrets()
api_key = secrets.anthropic_api_key
```

**Benefits:**

- Single source of truth
- Type-safe access
- Validation on load
- Easy to mock in tests

### Environment Variables

Store secrets in `.env` file (not committed):

```bash
# .env (NOT committed to git)
ANTHROPIC_API_KEY=sk-ant-api03-xxx
```

Use `.env.example` as template (committed):

```bash
# .env.example (committed to git)
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
```

### API Key Rotation

If a secret is accidentally committed:

1. **Immediately rotate the key:**

   ```bash
   # Generate new API key from provider
   # Update .env with new key
   ```

2. **Clean git history (if not pushed):**

   ```bash
   # Remove from last commit
   git reset HEAD~1
   git add -A
   git commit -m "fix: proper secrets handling"
   ```

3. **If already pushed, notify team:**
   - Revoke compromised key immediately
   - Generate new key
   - Update deployment secrets
   - Consider: `git filter-branch` or `BFG Repo-Cleaner`

---

## Security Scanning Tools

### 1. Bandit Configuration

Located in `pyproject.toml`:

```toml
[tool.bandit]
exclude_dirs = ["tests", ".venv", "__pycache__"]
skips = ["B101"]  # Skip assert_used in tests

[tool.bandit.assert_used]
skips = ["*/test_*.py", "*/tests/*"]
```

**Common Bandit Issues:**

| Code | Issue | Solution |
|------|-------|----------|
| B101 | `assert` used | OK in tests, use proper error handling in prod |
| B201 | `flask_debug_true` | Disable debug in production |
| B301 | Pickle usage | Use JSON or safer serialization |
| B303 | MD5/SHA1 usage | Use SHA256 or stronger |
| B501 | Weak SSL/TLS | Use modern TLS versions |

**Suppress false positives:**

```python
# Option 1: Inline suppression
result = eval(safe_expression)  # nosec B307

# Option 2: Skip in config
# [tool.bandit]
# skips = ["B307"]
```

### 2. Safety - Dependency Vulnerability Scanner

Scans dependencies for known vulnerabilities.

```bash
# Manual scan
uv run safety check

# Auto-scan in pre-commit (configured)
```

**When vulnerabilities found:**

1. Review the CVE details
2. Update vulnerable package: `uv add "package>=safe_version"`
3. Test that update doesn't break functionality
4. Commit the update

### 3. Ruff Security Rules

Enabled security rules (in `pyproject.toml`):

```toml
[tool.ruff.lint]
select = [
    "S",   # flake8-bandit (security)
    # ... other rules
]
```

**Example security issues caught:**

- Use of `eval()` or `exec()`
- Weak random number generation
- SQL injection patterns
- Subprocess shell injection

---

## Input Validation & XSS Prevention

### Query Validation

All user queries are validated through Pydantic schemas:

```python
from schemas.validation import QueryRequest

# Automatic validation
request = QueryRequest(query=user_input)
# Raises ValidationError if dangerous content detected
```

### XSS Protection

The `QueryRequest` schema automatically detects and rejects:

**1. Script Tags:**

```python
# REJECTED
QueryRequest(query="<script>alert('xss')</script>")
# Raises: ValueError("dangerous content")
```

**2. JavaScript Protocol:**

```python
# REJECTED
QueryRequest(query="javascript:alert('xss')")
# Raises: ValueError("dangerous content")
```

**3. HTML Event Handlers:**

```python
# REJECTED
QueryRequest(query="<img onerror='alert(1)'>")
# Raises: ValueError("dangerous content")
```

### Whitespace Normalization

Excessive whitespace is automatically normalized:

```python
request = QueryRequest(query="Who   is    Rudeus?")
# Result: "Who is Rudeus?"
```

### Safe Content

These are SAFE and allowed:

```python
# Mathematical operators
QueryRequest(query="What is x < y?")  # ✓ OK

# Generic brackets
QueryRequest(query="What is a <vector>?")  # ✓ OK

# Special characters
QueryRequest(query="What is $100?")  # ✓ OK
```

---

## Best Practices

### 1. Environment Separation

Use different secrets for each environment:

```bash
# Development
ANTHROPIC_API_KEY=sk-ant-dev-xxx

# Production
ANTHROPIC_API_KEY=sk-ant-prod-xxx

# Testing
ANTHROPIC_API_KEY=sk-ant-test-xxx
```

### 2. Principle of Least Privilege

- Use read-only API keys when possible
- Limit API key scopes to minimum required
- Rotate keys regularly (e.g., every 90 days)

### 3. Logging Security

**Never log secrets:**

```python
# BAD
logger.info(f"API key: {api_key}")

# GOOD
logger.info("API key loaded successfully")
```

**Sanitize user input in logs:**

```python
# BAD
logger.error(f"Query failed: {user_query}")

# GOOD
logger.error(f"Query failed: {sanitize(user_query)}")
```

### 4. Error Messages

**Don't expose sensitive details:**

```python
# BAD
raise Exception(f"Auth failed with key: {api_key}")

# GOOD
raise LLMAPIError("Authentication failed", details={"key_length": len(api_key)})
```

### 5. Dependency Management

```bash
# Audit dependencies regularly
uv run safety check

# Keep dependencies updated
uv sync --upgrade

# Review dependency changes
git diff uv.lock
```

### 6. Code Review Checklist

Before merging, verify:

- [ ] No hardcoded secrets
- [ ] All user input validated
- [ ] No SQL/command injection vectors
- [ ] Error messages don't leak sensitive data
- [ ] All pre-commit hooks passing
- [ ] No new Bandit warnings
- [ ] Dependencies scanned for vulnerabilities

---

## Troubleshooting

### Pre-commit Hook Failures

**Issue: detect-secrets fails**

```bash
# View what was detected
uv run detect-secrets scan

# If false positive, update baseline
uv run detect-secrets scan > .secrets.baseline
uv run detect-secrets audit .secrets.baseline
```

**Issue: Bandit fails**

```bash
# See specific issue
uv run bandit -r . -f screen

# Suppress if false positive
# Add # nosec comment or update pyproject.toml
```

**Issue: MyPy fails**

```bash
# See type errors
uv run mypy .

# Fix by adding type hints or # type: ignore
```

### Cleaning Hook Cache

```bash
# If hooks behave strangely
uv run pre-commit clean
uv run pre-commit install --install-hooks
uv run pre-commit run --all-files
```

### Emergency Bypass

**Only in extreme emergencies:**

```bash
# Skip all hooks (NOT RECOMMENDED)
git commit --no-verify -m "emergency hotfix"

# Better: Fix the issue, then commit normally
```

### Secrets Already Committed

If secrets were committed and pushed:

1. **Rotate immediately** - Generate new key
2. **Notify team** - Security incident
3. **Clean history** (complex):

   ```bash
   # Use BFG Repo-Cleaner or git filter-branch
   # This rewrites history - coordinate with team!
   ```

4. **Force push** (if agreed):

   ```bash
   git push --force
   ```

---

## Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Bandit Documentation](https://bandit.readthedocs.io/)
- [detect-secrets Guide](https://github.com/Yelp/detect-secrets)
- [Python Security Best Practices](https://python.readthedocs.io/en/stable/library/security_warnings.html)

---

## Security Contact

For security issues, please:

1. Do NOT open a public issue
2. Email: [your-security-contact]
3. Use encrypted communication if possible
