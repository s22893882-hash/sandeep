# Contributing Guide

Thank you for contributing to this project! This guide will help you get started with development and ensure your contributions meet our standards.

## Table of Contents

- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Running Tests Locally](#running-tests-locally)
- [Code Style Guidelines](#code-style-guidelines)
- [CI/CD Pipeline](#cicd-pipeline)
- [Pull Request Process](#pull-request-process)
- [Code Review Guidelines](#code-review-guidelines)

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/your-username/repo-name.git`
3. Create a new branch: `git checkout -b feature/your-feature-name`
4. Make your changes
5. Push to your fork and submit a pull request

## Development Setup

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Frontend Setup

```bash
cd frontend
npm install
```

### Install Pre-commit Hooks

```bash
pip install pre-commit
pre-commit install
```

## Running Tests Locally

### Backend Tests

```bash
cd backend
pytest --cov=. --cov-report=html --cov-report=term-missing
```

**Requirements:**
- Minimum test coverage: **80%**
- All tests must pass
- No linting errors

Open coverage report:
```bash
open htmlcov/index.html  # On macOS
# or
xdg-open htmlcov/index.html  # On Linux
```

### Frontend Tests

```bash
cd frontend
npm run test:coverage
```

**Requirements:**
- Minimum test coverage: **70%**
- All tests must pass
- No TypeScript errors

View coverage report:
```bash
open coverage/index.html
```

### Running Linters

#### Backend

```bash
cd backend

# Run Black formatter
black .

# Run Flake8
flake8 .

# Run Pylint
pylint **/*.py --rcfile=.pylintrc
```

#### Frontend

```bash
cd frontend

# ESLint
npm run lint

# TypeScript type checking
npm run type-check

# Prettier formatting
npm run format
```

## Code Style Guidelines

### Backend (Python)

- **PEP 8** compliance
- Use **Black** for formatting (line length: 127)
- Use **type hints** where appropriate
- Write **docstrings** for public functions and classes
- Follow **snake_case** naming convention
- Maximum complexity: 10 (enforced by Flake8)

Example:
```python
async def fetch_user_by_id(user_id: int, db: Database) -> Optional[User]:
    """
    Fetch a user by their ID.
    
    Args:
        user_id: The unique identifier of the user
        db: Database connection instance
        
    Returns:
        User object if found, None otherwise
    """
    return await db.fetch_one(f"SELECT * FROM users WHERE id = {user_id}")
```

### Frontend (TypeScript/React)

- Use **TypeScript** strict mode
- Follow **ESLint** and **Prettier** rules
- Use **functional components** with hooks
- Follow **camelCase** for variables/functions, **PascalCase** for components
- Prefer **named exports** over default exports
- Keep components **small and focused**

Example:
```typescript
interface User {
  id: number;
  email: string;
  username: string;
}

export const UserProfile: React.FC<{ user: User }> = ({ user }) => {
  return (
    <div>
      <h2>{user.username}</h2>
      <p>{user.email}</p>
    </div>
  );
};
```

## CI/CD Pipeline

Our CI/CD pipeline runs automatically on every push and pull request.

### Pipeline Stages

1. **Backend CI** (`backend-ci.yml`)
   - Runs on: Push to `main`/`develop`, Pull Requests
   - Steps:
     - Install dependencies
     - Run Flake8 & Pylint
     - Run Black formatter check
     - Run tests with coverage (min 80%)
     - Upload coverage to Codecov

2. **Frontend CI** (`frontend-ci.yml`)
   - Runs on: Push to `main`/`develop`, Pull Requests
   - Steps:
     - Install dependencies
     - Run ESLint
     - Run TypeScript type check
     - Run Prettier check
     - Run tests with coverage (min 70%)
     - Upload coverage to Codecov

3. **Security Scanning** (`security-scan.yml`)
   - Runs on: Push, Pull Requests, Weekly schedule
   - Steps:
     - Trivy container scanning
     - Dependency scanning
     - Semgrep SAST
     - Secret scanning with TruffleHog
     - Python security (Bandit & Safety)
     - NPM audit

4. **Docker Build** (`docker-build.yml`)
   - Runs on: Push to `main`
   - Builds and pushes Docker images with commit SHA tags

5. **Deployment** (`deploy.yml`)
   - Runs on: Successful completion of CI workflows
   - Deploys to staging/production
   - Runs health checks

### CI/CD Expectations

- **All checks must pass** before merging
- **Coverage thresholds** must be met
- **No security vulnerabilities** in dependencies
- **Docker images must build successfully**
- **No linting or formatting errors**

## Pull Request Process

### Before Submitting

1. ✅ All tests pass locally
2. ✅ Code coverage meets minimum requirements (Backend: 80%, Frontend: 70%)
3. ✅ Linters pass without errors
4. ✅ Pre-commit hooks pass
5. ✅ Code is formatted correctly
6. ✅ No console.log or debugging statements
7. ✅ Documentation is updated (if needed)

### PR Guidelines

- **Title**: Use descriptive titles (e.g., "Add user authentication endpoint")
- **Description**: Explain what changes you made and why
- **Link Issues**: Reference any related issues (e.g., "Closes #123")
- **Screenshots**: Add screenshots for UI changes
- **Tests**: Include tests for new features
- **Breaking Changes**: Clearly mark breaking changes

### PR Template

```markdown
## Description
[Describe your changes]

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tests added/updated
- [ ] All tests pass locally
- [ ] Coverage meets minimum requirements

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] No new warnings generated
```

## Code Review Guidelines

### For Authors

- Respond to feedback promptly
- Be open to suggestions
- Keep PRs small and focused
- Update your PR based on feedback

### For Reviewers

- Be constructive and respectful
- Focus on code quality and best practices
- Test the changes locally if needed
- Approve only when all concerns are addressed

### Review Checklist

- [ ] Code is clean and readable
- [ ] Tests are comprehensive
- [ ] Error handling is appropriate
- [ ] Security concerns addressed
- [ ] Performance considerations
- [ ] Documentation is clear
- [ ] No hardcoded values or secrets

## Common Issues

### Coverage Below Threshold

If your PR fails due to low coverage:
1. Add more tests for uncovered lines
2. Run `pytest --cov-report=term-missing` to see what's missing
3. Focus on testing edge cases and error paths

### Linting Errors

```bash
# Auto-fix many issues
black .  # Backend
npm run lint:fix  # Frontend
```

### Pre-commit Hook Failures

```bash
# Run all hooks manually
pre-commit run --all-files

# Skip hooks (not recommended)
git commit --no-verify
```

## Getting Help

- Open an issue for bugs or feature requests
- Ask questions in discussions
- Review existing PRs for examples
- Check the documentation

## Resources

- [Python Style Guide (PEP 8)](https://pep8.org/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [React Best Practices](https://react.dev/)
- [Testing Best Practices](https://kentcdodds.com/blog/common-mistakes-with-react-testing-library)

Thank you for contributing! 🎉
