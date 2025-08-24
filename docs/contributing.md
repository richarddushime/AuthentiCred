# Contributing to AuthentiCred

Thank you for your interest in contributing to AuthentiCred! This guide will help you get started with the project.

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Django 
- Node.js 14+ (for Truffle)
- Git
- Redis (for Celery)
- Ganache (for local blockchain)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/AuthentiCred.git
   cd AuthentiCred
   ```

2. **Set up Python environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Set up database**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   python manage.py createsuperuser
   ```

4. **Deploy smart contracts**
   ```bash
   # Start Ganache first, then:
   python manage.py deploy_contracts
   ```

5. **Start Redis and Celery**
   ```bash
   # Start Redis server
   redis-server

   # In another terminal, start Celery
   celery -A AuthentiCred worker -l info

   # In another terminal, start Celery Beat
   celery -A AuthentiCred beat -l info
   ```

6. **Run the development server**
   ```bash
   python manage.py runserver
   ```

## 🛠️ Development Workflow

### 1. Create a Feature Branch
```bash
git checkout -b feature/your-feature-name
```

### 2. Make Your Changes
- Follow the existing code style
- Add tests for new functionality
- Update documentation if needed

### 3. Test Your Changes
```bash
# Run Django tests
python manage.py test

# Run specific app tests
python manage.py test blockchain
python manage.py test credentials
python manage.py test users
python manage.py test wallets
```

### 4. Commit Your Changes
```bash
git add .
git commit -m "feat: add new feature description"
```

### 5. Push and Create Pull Request
```bash
git push origin feature/your-feature-name
```

## 📁 Project Structure

```
AuthentiCred/
├── AuthentiCred/          # Django project settings
├── blockchain/            # Blockchain integration
│   ├── contracts/         # Smart contracts
│   ├── clients/           # Blockchain clients
│   ├── utils/             # Cryptographic utilities
│   └── tasks.py           # Background tasks
├── credentials/           # Credential management
├── users/                 # User management
├── wallets/               # Digital wallet functionality
├── templates/             # HTML templates
├── media/                 # Uploaded files
└── docs/                  # Documentation
```

## 📝 Code Style

### Python
- Follow PEP 8
- Use meaningful variable names
- Add docstrings for functions
- Keep functions small and focused
- Use consistent indentation
- Add comments for complex logic
- Follow existing naming conventions

### Git Commits
Use conventional commit format:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes
- `refactor:` Code refactoring
- `test:` Adding tests
- `chore:` Maintenance tasks

## 🐛 Reporting Issues

When reporting issues, please include:
- Clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Python version, etc.)
- Screenshots if applicable

## 💡 Feature Requests

For feature requests:
- Describe the use case
- Explain the expected benefit
- Provide examples if possible
- Consider implementation complexity

## 🤝 Getting Help

- Check existing issues and discussions
<!-- - Join our community chat/discord (coming soon) -->
- Review the documentation
- Ask questions in issues

## 📄 License

By contributing to AuthentiCred, you agree that your contributions will be licensed under the [license](../README.md).

## 🙏 Thank You

Thank you for contributing to AuthentiCred! Your help makes the platform better for everyone.
