# mango-tango-cli: A python terminal wrapper for CIB Mango Tree analyzers

## Requirements

Python 3.12

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
python -m mangotango
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
