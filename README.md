<h3 align="center">mango-tango-cli</h3>
<h4 align="center">A Python command-line tool for detecting coordinated inauthentic behavior</h4>

<p align="center">
<img src="https://raw.githubusercontent.com/CIB-Mango-Tree/CIB-Mango-Tree-Website/main/docs/images/mango-text.PNG" alt="Mango logo" style="width:200px;"/>
</p>

<p align="center">
<a href="https://www.python.org/"><img alt="code" src="https://img.shields.io/badge/code-Python%203.12-blue?logo=Python"></a>
<a href="https://black.readthedocs.io/en/stable/"><img alt="style: black" src="https://img.shields.io/badge/style-Black-black?logo=Black"></a>
<a href="https://docs.astral.sh/ruff/"><img alt="style: black" src="https://img.shields.io/badge/tool-Polars-skyblue?logo=Polars"></a>
</p>

---

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

## License

This project is licensed under the [PolyForm Noncommercial License 1.0.0](https://polyformproject.org/licenses/noncommercial/1.0.0/).

### Summary

You are free to use, modify, and distribute this software for **non-commercial purposes**. For **commercial use**, please [contact us](mailto:sandobenjamin@gmail.com) to obtain a commercial license.

### Required Notice

Required Notice: © CIB Mango Tree ([https://github.com/CIB-Mango-Tree])

---

By using this software, you agree to the terms and conditions of the PolyForm Noncommercial License 1.0.0.
