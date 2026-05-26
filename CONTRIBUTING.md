# Contributing to Auto-Flipper-Tools

Thank you for your interest in contributing! We welcome contributions from developers, security researchers, and enthusiasts at all skill levels.

## Code of Conduct

Be respectful, inclusive, and constructive. We're building tools to help the security community.

## Getting Started

1. **Fork** the repository on GitHub
2. **Clone** your fork locally
3. **Create** a feature branch (`git checkout -b feature/your-feature-name`)
4. **Make** your changes
5. **Test** thoroughly
6. **Commit** with clear messages
7. **Push** to your fork
8. **Open** a Pull Request

## Development Setup

```bash
# Clone your fork
git clone https://github.com/TFD-42/Auto-Flipper-Tools.git
cd Auto-Flipper-Tools

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install development tools
pip install -r requirements.txt
pip install pytest black pylint flake8
```

## Code Standards

### Python Style

- Follow **PEP 8** guidelines
- Use **type hints** for functions
- Write **docstrings** for public functions
- Maximum line length: 100 characters
- Use meaningful variable names

### Example

```python
def classify_payload(content: str) -> Optional[str]:
    """
    Classify a BadUSB payload.
    
    Args:
        content: Script content to classify
        
    Returns:
        Category name or None if unclassified
    """
    # Implementation here
    pass
```

### Testing

- Write tests for new features
- Maintain >80% code coverage
- Test edge cases and error conditions

```bash
# Run tests
pytest

# Check coverage
pytest --cov=Bad_USB_Classifier

# Format code
black .

# Lint code
pylint Bad_USB_Classifier/
```

## Pull Request Process

1. **Update documentation** if adding features
2. **Add tests** for new functionality
3. **Run tests locally** before submitting
4. **Write clear PR description** explaining changes
5. **Link related issues** if applicable
6. **Request review** from maintainers

### PR Title Format

- `feat: Add new feature description`
- `fix: Fix bug description`
- `docs: Update documentation`
- `refactor: Improve code structure`
- `test: Add test coverage`
- `perf: Improve performance`

### PR Description Template

```markdown
## Description
Brief description of changes.

## Type of Change
- [ ] New feature
- [ ] Bug fix
- [ ] Documentation
- [ ] Performance improvement
- [ ] Code refactoring

## Changes Made
- Specific change 1
- Specific change 2

## Testing
How to test the changes.

## Checklist
- [ ] Code follows style guidelines
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] No security issues introduced
```

## Areas for Contribution

### High Priority
- 🚀 Performance optimizations
- 🔒 Security enhancements
- 📝 Documentation improvements
- 🧪 Test coverage expansion

### Medium Priority
- 🎯 New features
- 🐛 Bug fixes
- ♻️ Code refactoring
- 📊 Analytics improvements

### Lower Priority
- 🎨 UI/UX improvements (future)
- 💬 Example scripts
- 📚 Tutorial content

## Reporting Issues

### Bug Reports

Include:
- **Description**: What's the problem?
- **Steps to Reproduce**: How to trigger it?
- **Expected Behavior**: What should happen?
- **Actual Behavior**: What actually happens?
- **Environment**: Python version, OS, etc.
- **Logs**: Relevant error messages

### Feature Requests

Include:
- **Use Case**: Why is this needed?
- **Proposed Solution**: How should it work?
- **Alternatives**: Other approaches considered?
- **Example**: How would you use it?

## Security

### Reporting Vulnerabilities

⚠️ **Do NOT open public issues for security vulnerabilities**

Instead, please email security details privately. Details will be handled confidentially.

### Security Guidelines

- No hardcoded credentials
- Validate all inputs
- Handle errors safely
- Use secure defaults
- Keep dependencies updated

## Documentation

Help improve documentation! We need:
- **README improvements**
- **API documentation**
- **Usage examples**
- **Troubleshooting guides**
- **Architecture docs**

## Review Process

1. **Automated Checks**
   - Tests must pass
   - Security scanning enabled
   - Code quality checks

2. **Manual Review**
   - Code review by maintainers
   - Design consistency
   - Documentation quality

3. **Feedback**
   - Constructive comments
   - Requests for changes
   - Approval when ready

## Commit Messages

Write clear, descriptive commit messages:

```
feat: Add Ollama timeout error handling

- Distinguish timeout from other errors
- Log appropriate messages
- Return None instead of raising
- Improves resilience in slow environments
```

### Message Format

```
[type]: [subject]

[body - optional, explain why not what]

[footer - reference issues if applicable]
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

## Recognition

Contributors are recognized for their work! We'll list you in:
- README.md contributors section
- Release notes
- GitHub contributors list

## Questions?

- 📖 Check the documentation in `/docs`
- 💬 Open a discussion
- 🐛 Check existing issues
- 📧 Ask in comments on related issues

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for helping make Auto-Flipper-Tools better! 🎉
