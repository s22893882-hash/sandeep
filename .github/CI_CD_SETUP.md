# CI/CD Pipeline Setup Documentation

This document provides an overview of the comprehensive CI/CD pipeline setup for this project.

## 📦 What's Included

### GitHub Actions Workflows

1. **Backend CI** (`.github/workflows/backend-ci.yml`)
   - Triggers: Push to main/develop, Pull Requests
   - Python 3.11 matrix testing
   - Code quality checks (Flake8, Pylint, Black)
   - Pytest with 80% coverage requirement
   - Coverage upload to Codecov
   - PR coverage comments

2. **Frontend CI** (`.github/workflows/frontend-ci.yml`)
   - Triggers: Push to main/develop, Pull Requests
   - Node.js 20 matrix testing
   - ESLint linting
   - TypeScript type checking
   - Prettier formatting checks
   - Vitest with 70% coverage requirement
   - Coverage upload to Codecov

3. **Security Scanning** (`.github/workflows/security-scan.yml`)
   - Triggers: Push, PR, Weekly schedule (Mondays)
   - Trivy container vulnerability scanning
   - Semgrep SAST (Static Application Security Testing)
   - TruffleHog secret scanning
   - Bandit Python security checks
   - Safety dependency vulnerability checks
   - NPM audit for frontend dependencies

4. **Docker Build & Push** (`.github/workflows/docker-build.yml`)
   - Triggers: Push to main branch
   - Multi-platform builds (linux/amd64, linux/arm64)
   - Automatic tagging with commit SHA and latest
   - Push to GitHub Container Registry (ghcr.io)
   - Build caching for faster builds

5. **Deployment** (`.github/workflows/deploy.yml`)
   - Triggers: After successful CI workflows, Manual dispatch
   - Deployment to staging/production
   - Database migrations
   - Health checks
   - Rollback on failure

### Testing Configuration

#### Backend (Python/Pytest)
- **Configuration**: `backend/pytest.ini`
- **Coverage**: 80% minimum (enforced)
- **Test markers**: unit, integration, slow, auth, database, api
- **Fixtures**: Mock database, auth, Redis, Stripe, PayPal, S3, email service
- **Test files**:
  - `tests/conftest.py` - Fixtures and test setup
  - `tests/test_health.py` - Health endpoint tests
  - `tests/test_auth.py` - Authentication tests
  - `tests/test_database.py` - Database operation tests
  - `tests/test_main.py` - Main application tests

#### Frontend (TypeScript/Vitest)
- **Configuration**: `frontend/vitest.config.ts`
- **Coverage**: 70% minimum (enforced)
- **Environment**: jsdom
- **Test setup**: `frontend/src/test/setup.ts`
- **Mocks**: localStorage, sessionStorage, matchMedia, IntersectionObserver
- **Test files**:
  - `src/__tests__/App.test.tsx` - Component tests
  - `src/__tests__/auth.test.ts` - Authentication logic tests
  - `src/__tests__/api.test.ts` - API client tests

### Code Quality Tools

#### Backend
- **Black**: Code formatter (line length: 127)
- **Flake8**: Style guide enforcement
- **Pylint**: Static code analysis
- **MyPy**: Type checking
- **Bandit**: Security linting
- **Safety**: Dependency vulnerability scanning

Configuration files:
- `.pylintrc`
- `.flake8`
- `pyproject.toml`

#### Frontend
- **ESLint**: Linting (with TypeScript support)
- **Prettier**: Code formatting
- **TypeScript**: Strict type checking

Configuration files:
- `.eslintrc.cjs`
- `.prettierrc`
- `tsconfig.json`

### Pre-commit Hooks

**Configuration**: `.pre-commit-config.yaml`

Hooks included:
- Trailing whitespace removal
- End of file fixer
- YAML/JSON/TOML validation
- Large file check
- Merge conflict detection
- Private key detection
- Black formatting (Python)
- Flake8 linting (Python)
- isort import sorting (Python)
- ESLint (TypeScript/React)
- Prettier (TypeScript/React)
- Gitleaks secret scanning
- Bandit security checks

### Dependency Management

**Configuration**: `.github/dependabot.yml`

Automated updates for:
- GitHub Actions (weekly, Mondays)
- Python packages (weekly, Mondays)
- NPM packages (weekly, Mondays)
- Docker base images (weekly, Mondays)

### Code Coverage

**Configuration**: `codecov.yml`

- Project coverage target: 75%
- Backend flag: 80% target
- Frontend flag: 70% target
- PR comments enabled
- Coverage reports on every PR

## 🚀 Usage

### Local Development

#### Setup
```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt

# Frontend
cd frontend
npm install

# Pre-commit hooks
pip install pre-commit
pre-commit install
```

#### Running Tests
```bash
# Backend
cd backend
pytest --cov=. --cov-report=html --cov-report=term-missing

# Frontend
cd frontend
npm run test:coverage
```

#### Code Quality Checks
```bash
# Backend
cd backend
black .
flake8 .
pylint **/*.py --rcfile=.pylintrc

# Frontend
cd frontend
npm run lint
npm run type-check
npm run format
```

### Docker

#### Local Development
```bash
docker-compose up -d
```

#### Build Images
```bash
# Backend
docker build -t backend:latest ./backend

# Frontend
docker build -t frontend:latest ./frontend
```

## 📊 Coverage Requirements

| Component | Minimum Coverage | Enforced By |
|-----------|-----------------|-------------|
| Backend   | 80%             | pytest --cov-fail-under=80 |
| Frontend  | 70%             | vitest coverage thresholds |
| Overall   | 75%             | Codecov status checks |

## 🔒 Security Features

1. **Container Scanning**: Trivy scans for vulnerabilities in Docker images
2. **SAST**: Semgrep performs static application security testing
3. **Secret Scanning**: TruffleHog detects leaked secrets
4. **Dependency Scanning**: Bandit, Safety, and NPM Audit check dependencies
5. **Automated Updates**: Dependabot keeps dependencies up to date

## 🔄 CI/CD Workflow

### On Pull Request
1. Backend CI runs tests and linting
2. Frontend CI runs tests and linting
3. Security scans execute
4. Coverage reports are generated
5. All checks must pass to merge

### On Push to Main
1. All PR checks run again
2. Docker images are built and pushed
3. Deployment workflow triggers
4. Application is deployed to staging/production
5. Health checks verify deployment

## 📝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines on:
- Development setup
- Running tests locally
- Code style guidelines
- PR process
- Code review guidelines

## 🐛 Troubleshooting

### Coverage Below Threshold
```bash
# View missing coverage
pytest --cov=. --cov-report=term-missing

# Generate HTML report
pytest --cov=. --cov-report=html
open htmlcov/index.html
```

### Linting Failures
```bash
# Auto-fix issues
black .  # Backend
npm run lint:fix  # Frontend
```

### Pre-commit Hook Failures
```bash
# Run all hooks manually
pre-commit run --all-files

# Update hook versions
pre-commit autoupdate
```

### Docker Build Failures
```bash
# Check Dockerfile syntax
docker build --no-cache -t test ./backend

# View build logs
docker build --progress=plain -t test ./backend
```

## 📚 Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Pytest Documentation](https://docs.pytest.org/)
- [Vitest Documentation](https://vitest.dev/)
- [Codecov Documentation](https://docs.codecov.com/)
- [Pre-commit Documentation](https://pre-commit.com/)

## 🎯 Next Steps

To complete the setup:

1. **Configure Secrets**:
   - Add `CODECOV_TOKEN` to repository secrets
   - Add deployment credentials (if using deployment workflow)

2. **Update README Badge URLs**:
   - Replace `username/repo` with your GitHub repository path

3. **Customize Deployment**:
   - Update `deploy.yml` with your deployment configuration
   - Configure Kubernetes/Docker deployment commands

4. **Enable Branch Protection**:
   - Require status checks to pass before merging
   - Require code review approvals
   - Require branches to be up to date

5. **Test the Pipeline**:
   - Create a test PR to verify all checks run
   - Verify coverage reports are generated
   - Check that security scans complete successfully

---

**Status**: ✅ CI/CD Pipeline Fully Configured

All workflows, tests, and configurations are in place and ready to use!
