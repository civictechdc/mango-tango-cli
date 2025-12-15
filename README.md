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
<a href="https://black.readthedocs.io/en/stable/"><img alt="license: MIT" src="https://img.shields.io/badge/license-MIT-green"></a>
</p>

---

## Technical Documentation

For in-depth technical docs related to this repository please visit: [https://civictechdc.github.io/cib-mango-tree](https://civictechdc.github.io/cib-mango-tree)

## Requirements

Python 3.12 (see [requirements.txt](https://github.com/civictechdc/mango-tango-cli/blob/main/requirements.txt))

## Setting up

- Make sure you have Python 3.12 installed on your system.
- Create the virtual environment at `venv` using the following command:

```shell
python -m venv venv
```

- Activate the bootstrap script for your shell environmennt:
  - PS1: `./bootstrap.ps1`
  - Bash: `./bootstrap.sh`

  This will install the required dependencies for project development,
  activate a pre-commit hook that will format the code using `isort` and
  `black`.

## Starting the application

```shell
python -m cibmangotree
```

## Development Guide and Documentation

[Development Guide](./docs/guides/contributing/contributing.md)

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

This project is licensed under the [MIT License](https://opensource.org/license/mit).

### Required Notice

Required Notice: © [CIB Mango Tree](https://github.com/CIB-Mango-Tree)
