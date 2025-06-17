# Getting Started

## Requirements
- Python (3.12)
- Node.JS (20.0.0 or above)
- Git (latest version)

## Setting up
If you haven't installed git, node.js, and python yet refer to the following links to start installing said packages:
- [https://codefinity.com/blog/A-step-by-step-guide-to-Git-installation](https://codefinity.com/blog/A-step-by-step-guide-to-Git-installation)
- [https://nodejs.org/en/download](https://nodejs.org/en/download)
- [https://realpython.com/installing-python/](https://realpython.com/installing-python/)

If you're not sure which packages you already have installed on your system, the following commands can be used to figure what packages you already installed:

#### Linux & Mac OS
```shell
which <program_name_here>
```

#### Windows
```shell
where.exe python
```

## Setting Up Environment
Next step is to create the virtual environment at `venv` using the following command

```shell
python -m venv venv
```

Once the virtual environment with `venv` is created the next can be used to active the environment

- Activate the virtual environment after creating the `venv` directory:
  - Bash (Linux / Mac OS): `source ./venv/bin/activate`
  - PS1 (Windows): `./env/bin/Activate.ps1`


- Run the bootstrap script for your shell environment:
  - Bash (Linux / Mac OS): `./bootstrap.sh`
  - PS1 (Windows): `./bootstrap.ps1`

This will install the required dependencies for project development.

## Starting Services

### Starting CLI App
```shell
python -m mangotango
```

### Starting the Development Server for The Dashboards
```shell
cd ./app/web_templates
npm run dev
```

It should be noted that running the development server is only required if you're working on the dashboard while debug mode is enabled for the CLI app web server. Setting the environment variable `FLASK_DEBUG` to `1` in your shell environment is enough to put the server into debug mode. For example:

#### Linux & Mac OS
```shell
export FLASK_DEBUG=1
```

#### Windows
```shell
$env:FLASK_DEBUG = "1"
```

## Version Management
If you already have Python and Node.JS installed but are on different versions from the versions outlined in the [requirements](#requirements) above you can switch to the correct versions for both languages for the project using version managers. The version manager for python is [pyenv](https://github.com/pyenv/pyenv). Where the version manager that is recommended for Node is [nvm](https://github.com/nvm-sh/nvm). Guides for installing both version managers are linked down below if you need references to go off of

- [https://www.freecodecamp.org/news/node-version-manager-nvm-install-guide/](https://www.freecodecamp.org/news/node-version-manager-nvm-install-guide/)
- [https://github.com/pyenv/pyenv?tab=readme-ov-file#installation](https://github.com/pyenv/pyenv?tab=readme-ov-file#installation)
- [https://github.com/pyenv-win/pyenv-win?tab=readme-ov-file#installation](https://github.com/pyenv-win/pyenv-win?tab=readme-ov-file#installation)(If you're on windows and want to install pyenv)

Once you have both version managers installed the following commands can be used to switch versions

### pyenv
```shell
pyenv install 3.12
pyenv local 3.12
```

### nvm
```shell
nvm install v21.0.0
nvm use v21.0.0
```

## Common Dependency Issues
One common issue when installing the dependencies for python is the installation failing due to compatibility issues with the python package `pyarrow`. The compatibility issues are due to a version mismatch between pyarrow any python itself. To resolve this issue, you MUST be on version 3.12 for python. Refer to [commands above](#pyenv) to switch to the correct version.

Similarly, the installation for node dependencies has been known to fail for some developers due to a version mismatch caused by the underlying dependencies for the package `@glideapps/glide-data-grid`. However, getting around this issue is more straightforward with node packages. Running the installation command for node with the flag `--legacy-peer-deps` is enough for the installation to work if you run into this issue. The commands needed to run the installation manually are as such.

```shell
cd ./app/web_templates
npm install --legacy-peer-deps
```


# Next Steps
Once you have everything installed and running without any problems
[Development Guide](./dev-guide.md)
