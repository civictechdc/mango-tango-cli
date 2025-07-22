# Contributing to Mango Tango CLI

We welcome contributions to the Mango Tango CLI project! This document provides guidelines for contributing to our social media data analysis and visualization tool.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Contribution Workflow](#contribution-workflow)
- [Types of Contributions](#types-of-contributions)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Code Review Process](#code-review-process)
- [Release Process](#release-process)
- [Getting Help](#getting-help)
- [License](#license)

## Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior to [sandobenjamin@gmail.com](mailto:sandobenjamin@gmail.com).

## Getting Started

### Prerequisites

- **Python 3.12** (required for all features to work correctly)
- **Git** for version control
- **Terminal/Command Line** access

### Understanding the Project

Before contributing, familiarize yourself with:

- **Project Overview**: Read the [README.md](README.md) for basic information
- **Architecture**: Review the [Development Guide](docs/dev-guide.md) for architectural understanding
- **AI Documentation**: Check `.ai-context/` for comprehensive project context

The Mango Tango CLI is a modular, extensible Python terminal application for social media data analysis with three main domains:

- **Core Domain**: Application logic, terminal UI, and storage
- **Edge Domain**: Data import/export and preprocessing
- **Content Domain**: Analysis modules and web presenters

## Development Setup

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then clone your fork
git clone https://github.com/YOUR_USERNAME/mango-tango-cli.git
cd mango-tango-cli
```

### 2. Set Up Environment

```bash
# Create virtual environment
python -m venv venv

# Run bootstrap script to install dependencies and set up pre-commit hooks
# macOS/Linux:
./bootstrap.sh
# Windows (PowerShell):
./bootstrap.ps1
```

### 3. Verify Installation

```bash
python -m mangotango --noop
# Should output: "No-op flag detected. Exiting successfully."
```

## Contribution Workflow

We use a **Git Flow** workflow with `develop` as our integration branch:

### 1. Create a Feature Branch

Branch from `develop` (not `main`):

```bash
git checkout develop
git pull origin develop
git checkout -b feature/your-feature-name
# or
git checkout -b bugfix/your-bugfix-name
```

### 2. Make Changes

- Make your changes following our [coding standards](#coding-standards)
- Test your changes thoroughly
- Commit with clear, descriptive messages

```bash
git add .
git commit -m "feat: add hashtag frequency analysis

- Implement frequency calculation for hashtag data
- Add statistical analysis methods
- Include data visualization components"
```

### 3. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

- Create a Pull Request targeting the `develop` branch
- Fill out the PR template completely
- Address any review feedback

### 4. After Merge

```bash
git checkout develop
git pull origin develop
git branch -d feature/your-feature-name
```

## Types of Contributions

### 🔬 Analysis Modules (Analyzers)

**Primary Analyzers**: Core data processing modules

- Input: Preprocessed parquet files
- Output: Normalized analysis results
- Examples: hashtag extraction, n-gram generation, temporal analysis

**Secondary Analyzers**: Result transformation

- Input: Primary analyzer outputs
- Output: User-friendly reports and summaries

**Web Presenters**: Interactive visualization

- Input: Primary + secondary outputs
- Output: Dash/Shiny web applications

See the [analyzer example](analyzers/example/README.md) for implementation guidance.

### 🔧 Core Improvements

- Terminal UI enhancements
- Storage system improvements
- Application workflow optimizations
- Performance improvements

### 📊 Data Import/Export

- New file format support
- Data preprocessing enhancements
- Export format additions

### 📚 Documentation

- Code documentation
- User guides
- API documentation
- Example projects

### 🐛 Bug Fixes

- Bug reports and fixes
- Performance issues
- Compatibility improvements

## Coding Standards

### Code Formatting

We use automated code formatting (enforced by pre-commit hooks):

- **Black**: Code style and formatting
- **isort**: Import organization

```bash
# Manual formatting (if needed)
isort .
black .
```

### Code Quality

- **Type hints**: Use modern Python typing throughout
- **Docstrings**: Document all public functions and classes
- **Error handling**: Implement appropriate exception handling
- **Logging**: Use appropriate logging levels

### Architecture Patterns

- **Context Pattern**: Use dependency injection through context objects
- **Interface-First Design**: Define analyzer interfaces before implementation
- **Domain Separation**: Respect the Core/Edge/Content domain boundaries

### Python Style

- Follow PEP 8 guidelines (automatically enforced by Black)
- Use descriptive variable and function names
- Keep functions focused and small
- Prefer composition over inheritance

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest analyzers/hashtags/test_hashtags_analyzer.py

# Run with verbose output
pytest -v
```

### Test Guidelines

- Write tests for all new functionality
- Place tests co-located with the modules they test
- Use the testing framework provided in the `testing/` module
- Include test data in `test_data/` directories within analyzer modules
- Ensure tests are fast and reliable

### Test Types

- **Unit Tests**: Test individual functions and methods
- **Integration Tests**: Test analyzer workflows
- **End-to-End Tests**: Test complete user workflows

## Submitting Changes

### Pull Request Guidelines

1. **Target Branch**: Always target `develop`, never `main`
2. **Description**: Provide a clear description of changes
3. **Testing**: Include test results and coverage information
4. **Documentation**: Update relevant documentation
5. **Breaking Changes**: Clearly mark any breaking changes

### PR Checklist

- [ ] Code follows project coding standards
- [ ] Tests added for new functionality
- [ ] All tests pass
- [ ] Documentation updated
- [ ] Commit messages are clear and descriptive
- [ ] PR targets `develop` branch
- [ ] Pre-commit hooks pass

### Commit Message Format

Use conventional commit format:

```markdown
type(scope): brief description

Detailed explanation of the change (if needed)

- List specific changes
- Include any breaking changes
- Reference issues if applicable

Fixes #123
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

## Code Review Process

1. **Automated Checks**: CI/CD pipeline runs tests and quality checks
2. **Manual Review**: Project maintainers review code and architecture
3. **Feedback**: Address any requested changes
4. **Approval**: Maintainer approval required before merge

## Release Process

- Features are merged into `develop`
- When `develop` is stable, it's merged into `main` for release
- Releases follow semantic versioning

## Getting Help

### Documentation

- **Development Guide**: [docs/dev-guide.md](docs/dev-guide.md)
- **AI Context Docs**: `.ai-context/` directory
- **Architecture Overview**: `.ai-context/architecture-overview.md`
- **Symbol Reference**: `.ai-context/symbol-reference.md`

### Community Support

- **Slack**: Join the [Civic Tech DC Slack workspace](https://civictechdc.slack.com)
- **Issues**: Use GitHub Issues for bug reports and feature requests

### AI Development Assistance

This project includes comprehensive AI assistant integration:

- **Claude Code users**: See `CLAUDE.md` + Serena MCP integration
- **Cursor users**: See `.cursorrules` + `.ai-context/`
- **Other AI tools**: Start with `.ai-context/README.md`

## License

By contributing, you agree that your contributions will be licensed under the [PolyForm Noncommercial License 1.0.0](LICENSE).

---

Thank you for contributing to Mango Tango CLI! Your contributions help make social media data analysis more accessible and powerful.
