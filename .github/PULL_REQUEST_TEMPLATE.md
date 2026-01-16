---
name: Pull Request
about: Template for pull requests
title: ''
labels: ''
assignees: ''
---

## Description

<!-- Provide a brief description of the changes in this PR -->

## Type of Change

- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Refactoring
- [ ] Performance improvement

## Checklist

- [ ] **No secrets or API keys committed** (checked `.env`, config files, code)
- [ ] All tests pass locally (`pytest -q`)
- [ ] Docker build succeeds (`docker-compose build --no-cache`)
- [ ] CLI mode tested (`python3 auditor_ai.py 10`)
- [ ] Docker mode tested (`docker-compose run --rm contract-auditor python3 auditor_ai.py 10`)
- [ ] Documentation updated (if applicable)
- [ ] CHANGELOG.md updated (if applicable)

### Demo Mode Security (if applicable)

- [ ] `DEMO_MODE` defaults to `false` in `.env.example`
- [ ] No real credentials in `.env.example` (only placeholders)
- [ ] HTTP Basic Auth enforced on all demo endpoints
- [ ] TTL auto-shutdown implemented (3 hours default)
- [ ] Warning banners displayed
- [ ] Demo documentation includes security warnings

### Demo Mode Security (if applicable)

- [ ] `DEMO_MODE` defaults to `false` in `.env.example`
- [ ] No real credentials in `.env.example` (only placeholders)
- [ ] HTTP Basic Auth enforced on all demo endpoints
- [ ] TTL auto-shutdown implemented
- [ ] Warning banners displayed
- [ ] Demo documentation includes security warnings

## Testing

<!-- Describe how you tested these changes -->

## Related Issues

<!-- Link any related issues here -->

## Additional Notes

<!-- Any additional information for reviewers -->
