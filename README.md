<h2 align="center">CIB Mango Tree</h2>
<h3 align="center">An Interactive Command Line and Dashboard Tool for Detecting Coordinated Inauthentic Behavior Datasets of Online Activity</h3>

<p align="center">
<img src="https://raw.githubusercontent.com/CIB-Mango-Tree/CIB-Mango-Tree-Website/main/assets/images/mango-text.PNG" alt="Mango logo" style="width:200px;"/>
</p>

<p align="center">
<a href="https://www.python.org/"><img alt="code" src="https://img.shields.io/badge/Python-3.12-blue?logo=Python"></a>
<a href="https://docs.astral.sh/ruff/"><img alt="style: black" src="https://img.shields.io/badge/Polars-1.9-skyblue?logo=Polars"></a>
<a href="https://plotly.com/python/"><img alt="style: black" src="https://img.shields.io/badge/Plotly-5.24.1-purple?logo=Plotly"></a>
<a href="https://github.com/Textualize/rich"><img alt="style: black" src="https://img.shields.io/badge/Rich-14.0.0-gold?logo=Rich"></a>
<a href="https://civictechdc.github.io/mango-tango-cli/"><img alt="style: black" src="https://img.shields.io/badge/docs-website-blue"></a>
<a href="https://black.readthedocs.io/en/stable/"><img alt="style: black" src="https://img.shields.io/badge/style-Black-black?logo=Black"></a>
</p>

---

## Technical Documentation

For in-depth technical docs related to this repository please visit: [https://civictechdc.github.io/mango-tango-cli](https://civictechdc.github.io/mango-tango-cli)

## Requirements

- **Python 3.12** - Required for all features
- **UV** - Modern Python package manager (automatically installed by bootstrap scripts)

See [pyproject.toml](pyproject.toml) for complete dependency information.

## Quick Start

### 1. Clone and Setup

```bash
git clone https://github.com/civictechdc/mango-tango-cli.git
cd mango-tango-cli
```

### 2. Bootstrap Development Environment

Run the bootstrap script for your platform:

```bash
# macOS/Linux
./bootstrap.sh

# Windows (PowerShell)
./bootstrap.ps1
```

This will:
- Install UV package manager (if not present)
- Install all project dependencies
- Set up the development environment
- Verify the installation

### 3. Run the Application

```bash
uv run cibmangotree
```

## Project Structure

This is a UV workspace monorepo with the following packages:

```
packages/
├── core/                    # Core application (cibmangotree)
│   ├── src/cibmangotree/   # Main application code
│   │   ├── app/            # Application logic & terminal UI
│   │   ├── storage/        # Data persistence layer
│   │   └── components/     # Terminal UI components
│   └── pyproject.toml
├── importing/              # Data import/export (cibmangotree-importing)
├── services/               # Shared services (cibmangotree-services)
├── testing/                # Testing utilities (cibmangotree-testing)
└── analyzers/              # Analysis modules
    ├── hashtags/           # Hashtag analysis
    ├── ngrams/             # N-gram analysis
    ├── temporal/           # Temporal analysis
    ├── example/            # Example analyzer template
    └── ...
```

## Development Commands

```bash
# Run the application
uv run cibmangotree

# Run tests
uv run pytest                    # All tests
uv run pytest -v                 # Verbose output
uv run pytest packages/analyzers/hashtags/  # Specific package

# Code quality
uv run black .                   # Format code
uv run isort .                   # Sort imports
uv run black --check .           # Check formatting
uv run isort --check .           # Check import order

# Build executable
uv run pyinstaller pyinstaller.spec

# Package management
uv sync                          # Install/sync dependencies
uv sync --all-extras            # Install with all optional dependencies
uv add <package>                # Add a dependency
uv tree                         # Show dependency tree
uv sync --upgrade               # Upgrade dependencies
```

## Development Guide and Documentation

[Development Guide](./docs/dev-guide.md)

## AI Development Assistant Setup

This repository includes hybrid AI documentation enhanced with semantic code analysis:

- **For Claude Code users**: See `CLAUDE.md` + Serena MCP integration
  - **Important**: Always start sessions with "Read the initial instructions"
- **For Cursor users**: See `.cursorrules` + `.ai-context/`
- **For other AI tools**: See `.ai-context/README.md`
- **For deep semantic analysis**: Serena memories in `.serena/memories/`

### Quick Start for Contributors

1. **Claude Code**: Start with "Read the initial instructions", then follow CLAUDE.md
2. **Cursor**: Reference .cursorrules for quick setup
3. **Other tools**: Begin with .ai-context/README.md

The AI documentation provides:

- **Symbol-level code navigation** with precise file locations
- **Architectural insights** from semantic analysis
- **Context-efficient documentation** for faster onboarding
- **Cross-tool compatibility** for different AI assistants

## License

This project is licensed under the [PolyForm Noncommercial License 1.0.0](https://polyformproject.org/licenses/noncommercial/1.0.0/).

### Summary

You are free to use, modify, and distribute this software for **non-commercial purposes**. For **commercial use**, please [contact us](mailto:sandobenjamin@gmail.com) to obtain a commercial license.

### Required Notice

Required Notice: © [CIB Mango Tree](https://github.com/CIB-Mango-Tree)

---

By using this software, you agree to the terms and conditions of the PolyForm Noncommercial License 1.0.0.
