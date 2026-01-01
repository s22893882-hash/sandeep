# Project Name

[![Backend CI](https://github.com/username/repo/actions/workflows/backend-ci.yml/badge.svg)](https://github.com/username/repo/actions/workflows/backend-ci.yml)
[![Frontend CI](https://github.com/username/repo/actions/workflows/frontend-ci.yml/badge.svg)](https://github.com/username/repo/actions/workflows/frontend-ci.yml)
[![Security Scan](https://github.com/username/repo/actions/workflows/security-scan.yml/badge.svg)](https://github.com/username/repo/actions/workflows/security-scan.yml)
[![codecov](https://codecov.io/gh/username/repo/branch/main/graph/badge.svg)](https://codecov.io/gh/username/repo)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A modern full-stack application with automated CI/CD pipeline, comprehensive testing, and security scanning.

## 🚀 Features

- **Backend**: FastAPI with Python 3.11
- **Frontend**: React 18 with TypeScript
- **Testing**: Pytest (Backend) & Vitest (Frontend)
- **Code Quality**: ESLint, Pylint, Black, Prettier
- **Security**: Trivy, Semgrep, Bandit, TruffleHog
- **CI/CD**: GitHub Actions with automated deployment
- **Coverage**: 80% backend, 70% frontend minimum
- **Docker**: Multi-platform images (amd64, arm64)

## 📋 Prerequisites

- Python 3.11+
- Node.js 20+
- Docker (optional)
- Git

## 🛠️ Installation

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

### Pre-commit Hooks

```bash
pip install pre-commit
pre-commit install
```

## 🧪 Running Tests

### Backend Tests

```bash
cd backend
pytest --cov=. --cov-report=html --cov-report=term-missing
```

Coverage report will be available at `backend/htmlcov/index.html`

### Frontend Tests

```bash
cd frontend
npm run test:coverage
```

Coverage report will be available at `frontend/coverage/index.html`

## 🎨 Code Quality

### Backend

```bash
cd backend

# Format code
black .

# Lint
flake8 .
pylint **/*.py --rcfile=.pylintrc
```

### Frontend

```bash
cd frontend

# Lint
npm run lint

# Type check
npm run type-check

# Format
npm run format
```

## 🐳 Docker

### Build Images

```bash
# Backend
docker build -t backend:latest ./backend

# Frontend
docker build -t frontend:latest ./frontend
```

### Run with Docker Compose

```bash
docker-compose up -d
```

## 🔒 Security

Our project includes comprehensive security scanning:

- **Trivy**: Container vulnerability scanning
- **Semgrep**: Static Application Security Testing (SAST)
- **Bandit**: Python security linting
- **TruffleHog**: Secret scanning
- **Dependabot**: Automated dependency updates
- **NPM Audit**: Frontend dependency scanning

Security scans run automatically on every push and weekly.

## 🔄 CI/CD Pipeline

Our CI/CD pipeline ensures code quality and security:

### On Pull Requests & Pushes

1. **Backend CI**
   - Code quality checks (Flake8, Pylint, Black)
   - Test execution with coverage (min 80%)
   - Coverage reporting to Codecov

2. **Frontend CI**
   - Linting (ESLint) and type checking (TypeScript)
   - Test execution with coverage (min 70%)
   - Build verification

3. **Security Scanning**
   - Vulnerability scanning
   - Secret detection
   - Dependency auditing

### On Main Branch

4. **Docker Build & Push**
   - Multi-platform image builds
   - Automated tagging with commit SHA

5. **Deployment**
   - Automated deployment to staging/production
   - Database migrations
   - Health checks

## 📊 Code Coverage

Current coverage status:

- **Backend**: ![Backend Coverage](https://codecov.io/gh/username/repo/branch/main/graphs/tree.svg?flag=backend)
- **Frontend**: ![Frontend Coverage](https://codecov.io/gh/username/repo/branch/main/graphs/tree.svg?flag=frontend)

Minimum requirements:
- Backend: 80%
- Frontend: 70%

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](.github/CONTRIBUTING.md) for details.

### Quick Start

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and ensure coverage meets requirements
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Development Workflow

```bash
# Create a new branch
git checkout -b feature/my-feature

# Make changes and run tests
cd backend && pytest
cd frontend && npm test

# Commit (pre-commit hooks will run automatically)
git commit -m "feat: add new feature"

# Push and create PR
git push origin feature/my-feature
```

## 📁 Project Structure

```
.
├── .github/
│   ├── workflows/          # CI/CD workflows
│   │   ├── backend-ci.yml
│   │   ├── frontend-ci.yml
│   │   ├── security-scan.yml
│   │   ├── docker-build.yml
│   │   └── deploy.yml
│   ├── CONTRIBUTING.md
│   └── dependabot.yml
├── backend/
│   ├── tests/              # Backend tests
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   ├── pytest.ini
│   ├── .pylintrc
│   └── .flake8
├── frontend/
│   ├── src/
│   │   ├── __tests__/      # Frontend tests
│   │   └── test/
│   ├── package.json
│   ├── vitest.config.ts
│   ├── tsconfig.json
│   └── .eslintrc.cjs
├── .pre-commit-config.yaml
├── .gitignore
└── README.md
```

## 🔧 Environment Variables

### Backend

Create a `.env` file in the `backend` directory:

```env
ENVIRONMENT=development
DATABASE_URL=postgresql://user:password@localhost/dbname
REDIS_URL=redis://localhost:6379
SECRET_KEY=your-secret-key
```

### Frontend

Create a `.env` file in the `frontend` directory:

```env
VITE_API_URL=http://localhost:8000
VITE_APP_NAME=MyApp
```

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Team

- [Your Name](https://github.com/username)

## 🙏 Acknowledgments

- FastAPI for the amazing backend framework
- React team for the excellent frontend library
- GitHub Actions for CI/CD automation
- All contributors who help improve this project

## 📞 Support

For support, email support@example.com or open an issue in the repository.

## 🗺️ Roadmap

- [x] Set up CI/CD pipeline
- [x] Implement comprehensive testing
- [x] Add security scanning
- [ ] Add E2E tests
- [ ] Implement monitoring and logging
- [ ] Add API documentation
- [ ] Set up staging environment

---

Made with ❤️ by the team
