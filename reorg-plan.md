# CIB Mango Tree CLI - Monorepo Reorganization Plan

**Status**: Ready for Implementation
**Date**: 2025-10-09
**Goal**: Transform current flat structure into modern Python monorepo with plugin architecture

---

## Table of Contents

- [Overview](#overview)
- [Proposed Structure](#proposed-structure)
- [Package Organization](#package-organization)
- [Plugin Architecture](#plugin-architecture)
- [Configuration Strategy](#configuration-strategy)
- [Import Path Migration](#import-path-migration)
- [PyInstaller Compatibility](#pyinstaller-compatibility)
- [Migration Steps](#migration-steps)
- [Testing Strategy](#testing-strategy)
- [Risk Mitigation](#risk-mitigation)
- [Success Criteria](#success-criteria)

---

## Overview

### Goals

1. **Modularization**: Organize code into logical packages with clear boundaries
2. **Plugin System**: Enable external analyzer/tokenizer contributions without core changes
3. **Modern Tooling**: Adopt `uv` for fast, reliable dependency management
4. **Clean Architecture**: Separate concerns (core, ui, services, plugins)
5. **Maintainability**: Improve contributor experience and code navigation
6. **PyInstaller Compatible**: Maintain binary build support for releases

### Key Changes

- **Directory Structure**: Move to `packages/` with plugin architecture
- **Build System**: Modern `pyproject.toml` with workspace configuration
- **Package Manager**: Migrate from `pip` + `requirements.txt` to `uv` workspace
- **Plugin Discovery**: Hybrid system (entry points + registry for frozen builds)
- **UI Organization**: Consolidate terminal UI under `tui/`, prepare for `gui/` (NiceGUI)
- **Simplified Naming**: Analyzer subdirectories use `base/`, `stats/`, `web/`

### Design Constraints

- **PyInstaller**: Must work in frozen executable builds
- **Volunteer-Friendly**: Clear structure for contributors of all skill levels
- **Backward Compatible**: Existing data and workflows must continue working

---

## Proposed Structure

```bash
cibmangotree/
├── pyproject.toml              # Root workspace config (centralized)
├── uv.lock                     # Unified dependency lock
├── README.md
├── CONTRIBUTING.md
├── LICENSE
├── bootstrap.sh                # Updated to use `uv sync`
├── cibmangotree.py            # Backward-compat stub for PyInstaller
├── pyinstaller.spec            # Updated build spec
├── .gitignore
├── .github/workflows/
├── docs/
├── sample_data/
└── packages/
    │
    ├── core/                   # Core application & framework
    │   ├── pyproject.toml
    │   ├── tests/
    │   └── src/
    │       └── cibmangotree/       # Package name defines import path
    │           ├── __init__.py
    │           ├── __main__.py     # Entry point
    │           ├── _frozen_plugins.py  # Auto-generated (pyinstaller.spec)
    │           │
    │           ├── app/            # Main application
    │           │   ├── __init__.py
    │           │   ├── app.py
    │           │   ├── logger.py
    │           │   ├── app_context.py
    │           │   ├── project_context.py
    │           │   ├── analysis_context.py
    │           │   ├── analysis_output_context.py
    │           │   ├── analysis_webserver_context.py
    │           │   ├── settings_context.py
    │           │   ├── shiny.py
    │           │   └── utils.py
    │           │
    │           ├── analyzer_interface/  # Analyzer framework
    │           │   ├── __init__.py
    │           │   ├── column_automap.py
    │           │   ├── context.py
    │           │   ├── data_type_compatibility.py
    │           │   ├── declaration.py
    │           │   ├── interface.py
    │           │   ├── params.py
    │           │   └── suite.py
    │           │
    │           ├── tui/            # Terminal User Interface
    │           │   ├── __init__.py
    │           │   │
    │           │   ├── components/  # Was: components/
    │           │   │   ├── __init__.py
    │           │   │   ├── main_menu.py
    │           │   │   ├── analysis_main.py
    │           │   │   ├── analysis_params.py
    │           │   │   ├── analysis_web_server.py
    │           │   │   ├── context.py
    │           │   │   ├── export_outputs.py
    │           │   │   ├── new_analysis.py
    │           │   │   ├── new_project.py
    │           │   │   ├── project_main.py
    │           │   │   ├── select_analysis.py
    │           │   │   ├── select_project.py
    │           │   │   └── splash.py
    │           │   │
    │           │   └── tools/       # Was: terminal_tools/
    │           │       ├── __init__.py
    │           │       ├── inception.py
    │           │       ├── progress.py
    │           │       ├── prompts.py
    │           │       └── utils.py
    │           │
    │           ├── gui/            # Future: NiceGUI interface
    │           │   └── __init__.py  # Placeholder
    │           │
    │           ├── services/       # Core services
    │           │   ├── __init__.py
    │           │   │
    │           │   ├── storage/    # Was: storage/
    │           │   │   ├── __init__.py
    │           │   │   └── file_selector.py
    │           │   │
    │           │   ├── importing/  # Was: importing/
    │           │   │   ├── __init__.py
    │           │   │   ├── importer.py
    │           │   │   ├── csv.py
    │           │   │   └── excel.py
    │           │   │
    │           │   ├── preprocessing/  # Was: preprocessing/
    │           │   │   ├── __init__.py
    │           │   │   └── series_semantic.py
    │           │   │
    │           │   └── tokenizer/  # Abstract interfaces only
    │           │       ├── __init__.py
    │           │       ├── types.py
    │           │       └── base.py
    │           │
    │           ├── context/        # Context objects
    │           │   └── __init__.py
    │           │
    │           ├── meta/           # Version & metadata
    │           │   ├── __init__.py
    │           │   └── get_version.py
    │           │
    │           └── plugin_system/  # Plugin discovery
    │               ├── __init__.py
    │               └── discovery.py
    │
    ├── tokenizers/
    │   └── basic/                  # Plugin: basic tokenizer
    │       ├── pyproject.toml
    │       ├── tests/
    │       │   └── test_basic_tokenizer.py
    │       └── src/
    │           └── cibmangotree_tokenizer_basic/
    │               ├── __init__.py
    │               ├── tokenizer.py
    │               └── patterns.py
    │
    ├── analyzers/
    │   ├── example/                # Plugin: example analyzer
    │   │   ├── pyproject.toml
    │   │   ├── tests/
    │   │   │   ├── test_data/
    │   │   │   ├── test_example_base.py
    │   │   │   └── test_example_report.py
    │   │   └── src/
    │   │       └── cibmangotree_analyzer_example/
    │   │           ├── __init__.py
    │   │           │
    │   │           ├── base/       # Was: example_base/
    │   │           │   ├── __init__.py
    │   │           │   ├── interface.py
    │   │           │   ├── main.py
    │   │           │   └── default_params.py
    │   │           │
    │   │           ├── report/     # Was: example_report/
    │   │           │   ├── __init__.py
    │   │           │   ├── interface.py
    │   │           │   └── main.py
    │   │           │
    │   │           └── web/        # Was: example_web/
    │   │               ├── __init__.py
    │   │               ├── interface.py
    │   │               └── factory.py
    │   │
    │   ├── hashtags/               # Plugin: hashtags analyzer
    │   │   ├── pyproject.toml
    │   │   ├── tests/
    │   │   │   ├── test_data/
    │   │   │   └── test_hashtags_base.py
    │   │   └── src/
    │   │       └── cibmangotree_analyzer_hashtags/
    │   │           ├── __init__.py
    │   │           │
    │   │           ├── base/       # Was: hashtags_base/
    │   │           │   ├── __init__.py
    │   │           │   ├── interface.py
    │   │           │   └── main.py
    │   │           │
    │   │           └── web/        # Was: hashtags_web/
    │   │               ├── __init__.py
    │   │               ├── interface.py
    │   │               ├── factory.py
    │   │               ├── app.py
    │   │               ├── analysis.py
    │   │               └── plots.py
    │   │
    │   ├── ngrams/                 # Plugin: n-grams analyzer
    │   │   ├── pyproject.toml
    │   │   ├── tests/
    │   │   │   ├── test_data/
    │   │   │   ├── test_ngrams_base.py
    │   │   │   └── test_ngram_stats.py
    │   │   └── src/
    │   │       └── cibmangotree_analyzer_ngrams/
    │   │           ├── __init__.py
    │   │           │
    │   │           ├── base/       # Was: ngrams_base/
    │   │           │   ├── __init__.py
    │   │           │   ├── interface.py
    │   │           │   └── main.py
    │   │           │
    │   │           ├── stats/      # Was: ngram_stats/
    │   │           │   ├── __init__.py
    │   │           │   ├── interface.py
    │   │           │   └── main.py
    │   │           │
    │   │           └── web/        # Was: ngram_web/
    │   │               ├── __init__.py
    │   │               ├── interface.py
    │   │               ├── factory.py
    │   │               └── app.py
    │   │
    │   ├── temporal/               # Plugin: temporal analyzer
    │   │   ├── pyproject.toml
    │   │   ├── tests/
    │   │   └── src/
    │   │       └── cibmangotree_analyzer_temporal/
    │   │           ├── __init__.py
    │   │           │
    │   │           ├── base/       # Was: temporal_base/
    │   │           │   ├── __init__.py
    │   │           │   ├── interface.py
    │   │           │   └── main.py
    │   │           │
    │   │           └── web/        # Was: temporal_web/
    │   │               ├── __init__.py
    │   │               └── interface.py
    │   │
    │   └── time_coordination/      # Plugin: time coordination
    │       ├── pyproject.toml
    │       ├── tests/
    │       └── src/
    │           └── cibmangotree_analyzer_time_coordination/
    │               ├── __init__.py
    │               ├── interface.py
    │               └── main.py
    │
    └── testing/                    # Test utilities
        ├── pyproject.toml
        ├── tests/
        └── src/
            └── cibmangotree_testing/
                ├── __init__.py
                ├── comparers.py
                ├── context.py
                ├── testdata.py
                └── testers.py
```

---

## Package Organization

### Package Count: ~10 Packages

1. **core** - Framework, app, UI, services
2. **tokenizers/basic** - Basic tokenizer implementation
3. **analyzers/example** - Example analyzer for contributors
4. **analyzers/hashtags** - Hashtag analysis
5. **analyzers/ngrams** - N-gram analysis
6. **analyzers/temporal** - Temporal pattern analysis
7. **analyzers/time_coordination** - Time coordination detection
8. **testing** - Test utilities

### Package Dependency Graph

```text
cibmangotree (core)
    ↓
├── cibmangotree_tokenizer_basic
├── cibmangotree_testing
    ↓
└── cibmangotree_analyzer_* (all analyzers)
    ├── example
    ├── hashtags
    ├── ngrams (also depends on tokenizer_basic)
    ├── temporal
    └── time_coordination
```

---

## Plugin Architecture

### Design: Hybrid Discovery System

**Challenge**: Entry points don't work in PyInstaller frozen builds
**Solution**: Hybrid system that works in both development and frozen modes, with **dynamic generation** at build time

### Implementation

#### 1. Plugin Registry

```python
# cibmangotree/plugin_system/discovery.py

import sys
import importlib.metadata
from typing import List
from cibmangotree.analyzer_interface import AnalyzerDeclaration

class AnalyzerRegistry:
    """Central registry that works in both frozen and installed modes."""
    _analyzers: List[AnalyzerDeclaration] = []

    @classmethod
    def register(cls, analyzer: AnalyzerDeclaration) -> AnalyzerDeclaration:
        """Register an analyzer (used in frozen builds)."""
        cls._analyzers.append(analyzer)
        return analyzer

    @classmethod
    def discover(cls) -> List[AnalyzerDeclaration]:
        """Discover analyzers - works in both modes."""
        if getattr(sys, 'frozen', False):
            # Frozen (PyInstaller): use explicit registry
            return cls._analyzers
        else:
            # Installed: auto-discover via entry points
            from cibmangotree.app.logger import get_logger
            logger = get_logger(__name__)

            analyzers = []
            for ep in importlib.metadata.entry_points(group='cibmangotree.analyzers'):
                try:
                    analyzer = ep.load()
                    analyzers.append(analyzer)
                except Exception as e:
                    logger.warning(f"Failed to load analyzer {ep.name}: {e}")
            return analyzers
```

#### 2. Dynamic Frozen Plugin Generation (Build-Time)

The `pyinstaller.spec` file automatically generates `_frozen_plugins.py` based on installed packages with entry points. **No manual maintenance required!**

The spec file:

1. Discovers all plugins via entry points at build time
2. Auto-generates `_frozen_plugins.py` with appropriate imports
3. Auto-generates `hiddenimports` list for PyInstaller
4. Prints build report showing what's being bundled

```python
# Excerpt from pyinstaller.spec (see full version in PyInstaller Compatibility section)

def discover_plugins(group):
    """Discover all plugins for a given entry point group."""
    plugins = []
    for ep in importlib.metadata.entry_points(group=group):
        module_path, attr_name = ep.value.split(':')
        package_name = module_path.split('.')[0]
        plugins.append({
            'name': ep.name,
            'module': module_path,
            'attr': attr_name,
            'package': package_name,
        })
    return plugins

# Discover plugins at build time
analyzers = discover_plugins('cibmangotree.analyzers')
tokenizers = discover_plugins('cibmangotree.tokenizers')

# Generate _frozen_plugins.py automatically
frozen_plugins_path = generate_frozen_plugins(
    analyzers, tokenizers,
    'packages/core/src/cibmangotree/_frozen_plugins.py'
)

# Generate hiddenimports automatically
plugin_hiddenimports = get_plugin_hiddenimports(analyzers + tokenizers)
```

**Auto-generated `_frozen_plugins.py` example:**

```python
"""
Auto-generated frozen plugin loader for PyInstaller.
Generated during build - DO NOT EDIT MANUALLY.

This file is automatically generated by pyinstaller.spec based on
installed packages with cibmangotree plugin entry points.
"""

from cibmangotree.plugin_system.discovery import AnalyzerRegistry

# Import all bundled analyzers
from cibmangotree_analyzer_hashtags.base import hashtags
from cibmangotree_analyzer_hashtags.web import hashtags_web
from cibmangotree_analyzer_ngrams.base import ngrams
from cibmangotree_analyzer_ngrams.stats import ngram_stats
from cibmangotree_analyzer_ngrams.web import ngrams_web
# ... etc

# Register all analyzers
_analyzers = [
    hashtags,  # hashtags
    hashtags_web,  # hashtags_web
    ngrams,  # ngrams
    # ... etc
]

for analyzer in _analyzers:
    AnalyzerRegistry.register(analyzer)
```

#### 3. Application Startup

```python
# cibmangotree/__main__.py

import sys
from cibmangotree.plugin_system.discovery import AnalyzerRegistry
from cibmangotree.analyzer_interface import AnalyzerSuite

def main():
    # Load frozen plugins if running as executable
    if getattr(sys, 'frozen', False):
        import cibmangotree._frozen_plugins

    # Discover analyzers (uses registry in frozen mode, entry points otherwise)
    analyzers = AnalyzerRegistry.discover()
    suite = AnalyzerSuite(all_analyzers=analyzers)

    # ... rest of application initialization
```

### Benefits

✅ **Zero Maintenance** - Automatically discovers and bundles all installed plugins
✅ **No Hardcoding** - Entry points are single source of truth
✅ **Development Mode** - Auto-discovery via entry points, install only what you need
✅ **Frozen Mode** - Auto-generated imports, PyInstaller bundles correctly
✅ **External Plugins** - Contributors can create separate packages
✅ **Selective Bundling** - Only bundles analyzers installed during build
✅ **Build Reports** - Shows exactly what's being bundled

### Adding New Plugins

**Developer workflow:**

```bash
# 1. Create analyzer package with entry points in pyproject.toml
# 2. Install it in workspace
uv sync

# 3. Build - automatically discovered and bundled!
uv run pyinstaller pyinstaller.spec
```

**No changes to spec file or frozen plugins needed!** Everything is discovered and generated automatically at build time.

---

## Configuration Strategy

### Centralized Configuration (Root `pyproject.toml`)

All tool configurations, version constraints, and dev dependencies defined once at root.

```toml
[project]
name = "cibmangotree-workspace"
version = "0.1.0"
requires-python = ">=3.12"
description = "CIB Mango Tree CLI - Social Media Data Analysis Tool"

[tool.uv.workspace]
members = [
    "packages/core",
    "packages/testing",
    "packages/tokenizers/basic",
    "packages/analyzers/example",
    "packages/analyzers/hashtags",
    "packages/analyzers/ngrams",
    "packages/analyzers/temporal",
    "packages/analyzers/time_coordination",
]

# Centralized version constraints - all packages inherit these
[tool.uv.workspace.dependencies]
# Data processing
polars = ">=1.9.0"
pandas = ">=2.2.3"
pyarrow = ">=17.0.0"

# Models & validation
pydantic = ">=2.9.1"

# Storage
tinydb = ">=4.8.0"
platformdirs = ">=4.3.6"
filelock = ">=3.16.1"

# Terminal UI
inquirer = ">=3.4.0"
rich = ">=14.0.0"
colorama = ">=0.4.6"

# Web frameworks
dash = ">=2.18.1"
plotly = ">=5.24.1"
shiny = ">=1.4.0"
shinywidgets = ">=0.6.2"
starlette = ">=0.47.1"
uvicorn = ">=0.34.3"

# Import/Export
xlsxwriter = ">=3.2.0"
fastexcel = ">=0.13.0"

# Text processing
regex = ">=2025.9.1"

# Utilities
python-json-logger = ">=2.0.7"
a2wsgi = ">=1.10.10"

# Development tools
[tool.uv]
dev-dependencies = [
    "black>=24.10.0",
    "isort>=5.13.2",
    "pytest>=8.3.4",
    "pytest-benchmark>=5.1.0",
    "pyinstaller>=6.14.1",
    "pyarrow-stubs>=17.13",
]

# Tool configurations - inherited by all packages
[tool.black]
line-length = 88
target-version = ["py312"]

[tool.isort]
profile = "black"

[tool.pytest.ini_options]
pythonpath = ["."]
testpaths = ["packages"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

### Package-Specific Configuration (Minimal)

Each package only defines: name, version, description, dependencies, and entry points.

#### Core Package

```toml
# packages/core/pyproject.toml

[project]
name = "cibmangotree"
version = "0.1.0"
description = "CIB Mango Tree CLI - Social Media Analysis Tool"
requires-python = ">=3.12"
dependencies = [
    # Data
    "polars",
    "pandas",
    "pyarrow",

    # Models
    "pydantic",
    "platformdirs",

    # Storage
    "tinydb",
    "filelock",

    # Terminal UI
    "inquirer",
    "rich",
    "colorama",

    # Web frameworks
    "dash",
    "plotly",
    "shiny",
    "shinywidgets",
    "starlette",
    "uvicorn",

    # Import/Export
    "xlsxwriter",
    "fastexcel",

    # Utils
    "python-json-logger",
    "regex",
    "a2wsgi",
]

[project.scripts]
cibmangotree = "cibmangotree.__main__:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

#### Tokenizer Plugin

```toml
# packages/tokenizers/basic/pyproject.toml

[project]
name = "cibmangotree-tokenizer-basic"
version = "0.1.0"
description = "Basic tokenizer implementation"
requires-python = ">=3.12"
dependencies = [
    "cibmangotree",
    "regex",
]

# Plugin entry points - auto-discovered by core in dev mode
[project.entry-points."cibmangotree.tokenizers"]
basic = "cibmangotree_tokenizer_basic:BasicTokenizer"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

#### Analyzer Plugin (with Entry Points)

```toml
# packages/analyzers/hashtags/pyproject.toml

[project]
name = "cibmangotree-analyzer-hashtags"
version = "0.1.0"
description = "Hashtag analysis for CIB Mango Tree"
requires-python = ">=3.12"
dependencies = [
    "cibmangotree",
    "cibmangotree-testing",
    "polars",
]

# Plugin entry points - auto-discovered by core in dev mode
[project.entry-points."cibmangotree.analyzers"]
hashtags = "cibmangotree_analyzer_hashtags.base:hashtags"
hashtags_web = "cibmangotree_analyzer_hashtags.web:hashtags_web"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

#### Testing Utilities

```toml
# packages/testing/pyproject.toml

[project]
name = "cibmangotree-testing"
version = "0.1.0"
description = "Testing utilities for CIB Mango Tree"
requires-python = ">=3.12"
dependencies = [
    "cibmangotree",
    "polars",
    "pytest",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

---

## Import Path Migration

### Core Package Imports

**Before:**

```python
from app import App
from app.logger import get_logger
from analyzer_interface import AnalyzerInterface, AnalyzerSuite
from analyzer_interface.context import PrimaryAnalyzerContext
from context import AnalysisContext
from meta import get_version
```

**After:**

```python
from cibmangotree.app import App
from cibmangotree.app.logger import get_logger
from cibmangotree.analyzer_interface import AnalyzerInterface, AnalyzerSuite
from cibmangotree.analyzer_interface.context import PrimaryAnalyzerContext
from cibmangotree.context import AnalysisContext
from cibmangotree.meta import get_version
```

### Service Imports

**Before:**

```python
from storage import Storage
from services.tokenizer.core import AbstractTokenizer
from services.tokenizer.basic import BasicTokenizer
from preprocessing import series_semantic
from preprocessing.series_semantic import infer_series_semantic
from importing import ImporterSession
```

**After:**

```python
from cibmangotree.services.storage import Storage
from cibmangotree.services.tokenizer.core import AbstractTokenizer
from cibmangotree_tokenizer_basic import BasicTokenizer
from cibmangotree.services.preprocessing import series_semantic
from cibmangotree.services.preprocessing.series_semantic import infer_series_semantic
from cibmangotree.services.importing import ImporterSession
```

### UI Imports

**Before:**

```python
from components import main_menu, splash
from components.main_menu import main_menu
from terminal_tools import ProgressReporter
from terminal_tools.inception import TerminalContext
```

**After:**

```python
from cibmangotree.tui.components import main_menu, splash
from cibmangotree.tui.components.main_menu import main_menu
from cibmangotree.tui.tools import ProgressReporter
from cibmangotree.tui.tools.inception import TerminalContext
```

### Testing Imports

**Before:**

```python
from testing import test_primary_analyzer, CsvTestData
from testing.testdata import PolarsTestData
from testing.comparers import compare_dfs
```

**After:**

```python
from cibmangotree_testing import test_primary_analyzer, CsvTestData
from cibmangotree_testing.testdata import PolarsTestData
from cibmangotree_testing.comparers import compare_dfs
```

### Analyzer Internal Imports (Simplified Names)

**Before (inside `analyzers/hashtags/`):**

```python
from .hashtags_base import hashtags
from .hashtags_web import hashtags_web
from .hashtags_base.interface import COL_TEXT, COL_TIMESTAMP
```

**After (inside `packages/analyzers/hashtags/src/cibmangotree_analyzer_hashtags/`):**

```python
from .base import hashtags
from .web import hashtags_web
from .base.interface import COL_TEXT, COL_TIMESTAMP
```

**Before (inside `analyzers/ngrams/`):**

```python
from .ngrams_base import ngrams
from .ngram_stats import ngram_stats
from .ngram_web import ngrams_web
```

**After (inside `packages/analyzers/ngrams/src/cibmangotree_analyzer_ngrams/`):**

```python
from .base import ngrams
from .stats import ngram_stats
from .web import ngrams_web
```

---

## PyInstaller Compatibility

### Challenge

PyInstaller bundles Python code into a single executable. Standard plugin discovery mechanisms (entry points via `importlib.metadata`) don't work because:

- No package metadata available at runtime
- No `site-packages` directory
- Entry points aren't accessible

### Solution: Hybrid Discovery + Dynamic Generation

The spec file dynamically discovers all plugins and generates the frozen plugin loader at build time.

#### 1. Dynamic PyInstaller Spec

```python
# pyinstaller.spec

from PyInstaller.utils.hooks import copy_metadata
from PyInstaller.building.api import EXE, PYZ
from PyInstaller.building.build_main import Analysis
import sys
import os
import site
import importlib.metadata
from pathlib import Path

site_packages_path = None
block_cipher = None

for site_path in site.getsitepackages():
    if 'site-packages' in site_path:
        site_packages_path = site_path
        break

if site_packages_path is None:
    raise RuntimeError("site-packages directory not found")


# ============================================================================
# DYNAMIC PLUGIN DISCOVERY
# ============================================================================

def discover_plugins(group):
    """
    Discover all plugins for a given entry point group.
    Returns list of dicts with plugin metadata.
    """
    plugins = []
    try:
        for ep in importlib.metadata.entry_points(group=group):
            module_path, attr_name = ep.value.split(':')
            package_name = module_path.split('.')[0]

            plugins.append({
                'name': ep.name,
                'module': module_path,
                'attr': attr_name,
                'package': package_name,
                'value': ep.value,
            })
    except Exception as e:
        print(f"Warning: Failed to discover plugins for {group}: {e}")

    return plugins


def generate_frozen_plugins(analyzers, tokenizers, output_path):
    """
    Generate the frozen plugins loader file dynamically.
    This file imports and registers all plugins.
    """
    lines = [
        '"""',
        'Auto-generated frozen plugin loader for PyInstaller.',
        'Generated during build - DO NOT EDIT MANUALLY.',
        '',
        'This file is automatically generated by pyinstaller.spec based on',
        'installed packages with cibmangotree plugin entry points.',
        '"""',
        '',
        'from cibmangotree.plugin_system.discovery import AnalyzerRegistry',
        '',
    ]

    # Import analyzers
    if analyzers:
        lines.append('# Import all bundled analyzers')
        for plugin in analyzers:
            lines.append(f"from {plugin['module']} import {plugin['attr']}")
        lines.append('')

    # Import tokenizers (if we add tokenizer registry later)
    if tokenizers:
        lines.append('# Import all bundled tokenizers')
        for plugin in tokenizers:
            lines.append(f"from {plugin['module']} import {plugin['attr']}")
        lines.append('')

    # Register analyzers
    if analyzers:
        lines.append('# Register all analyzers')
        lines.append('_analyzers = [')
        for plugin in analyzers:
            lines.append(f"    {plugin['attr']},  # {plugin['name']}")
        lines.append(']')
        lines.append('')
        lines.append('for analyzer in _analyzers:')
        lines.append('    AnalyzerRegistry.register(analyzer)')
        lines.append('')

    # Write file
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        f.write('\n'.join(lines))

    print(f"Generated frozen plugins loader: {output_path}")
    print(f"  - {len(analyzers)} analyzers")
    print(f"  - {len(tokenizers)} tokenizers")

    return output_path


def get_plugin_hiddenimports(plugins):
    """
    Generate hiddenimports list for PyInstaller from plugin metadata.
    """
    imports = []
    for plugin in plugins:
        # Add main package
        imports.append(plugin['package'])
        # Add specific module
        imports.append(plugin['module'])

        # Add common submodules for analyzers
        if 'analyzer' in plugin['package']:
            base_pkg = plugin['package']
            # Try to add common submodules
            for submodule in ['base', 'stats', 'web', 'report']:
                imports.append(f"{base_pkg}.{submodule}")

    return imports


# Discover all plugins from installed packages
print("Discovering plugins...")
analyzers = discover_plugins('cibmangotree.analyzers')
tokenizers = discover_plugins('cibmangotree.tokenizers')

print(f"Found {len(analyzers)} analyzer(s):")
for a in analyzers:
    print(f"  - {a['name']}: {a['value']}")

print(f"Found {len(tokenizers)} tokenizer(s):")
for t in tokenizers:
    print(f"  - {t['name']}: {t['value']}")

# Generate frozen plugins file
frozen_plugins_path = generate_frozen_plugins(
    analyzers,
    tokenizers,
    'packages/core/src/cibmangotree/_frozen_plugins.py'
)

# Generate hiddenimports
plugin_hiddenimports = []
plugin_hiddenimports.extend(get_plugin_hiddenimports(analyzers))
plugin_hiddenimports.extend(get_plugin_hiddenimports(tokenizers))

print(f"\nGenerated {len(plugin_hiddenimports)} hidden imports")

# ============================================================================
# PYINSTALLER CONFIGURATION
# ============================================================================

a = Analysis(
    ['cibmangotree.py'],
    pathex=['packages/core/src'],
    binaries=[],
    datas=[
        # Version file
        *(
            [('./VERSION', '.')]
            if os.path.exists('VERSION') else []
        ),

        # Metadata
        *copy_metadata('readchar'),

        # Static assets
        (os.path.join(site_packages_path, 'shiny/www'), 'shiny/www'),
        (os.path.join(site_packages_path, 'shinywidgets/static'), 'shinywidgets/static'),

        # App assets
        ('packages/core/src/cibmangotree/app/web_static', 'cibmangotree/app/web_static'),
        ('packages/core/src/cibmangotree/app/web_templates', 'cibmangotree/app/web_templates'),
    ],
    hiddenimports=[
        # Standard hidden imports
        'readchar',
        'numpy',
        'numpy.core.multiarray',
        'shiny',
        'shiny.ui',
        'shiny.server',
        'htmltools',
        'starlette',
        'uvicorn',
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'asyncio',
        'websockets',
        'websockets.legacy',
        'websockets.legacy.server',
        'polars',
        'plotly',
        'linkify_it',
        'markdown_it',
        'mdit_py_plugins',
        'mdurl',
        'uc_micro',
        'pythonjsonlogger',
        'pythonjsonlogger.jsonlogger',

        # Core package
        'cibmangotree',
        'cibmangotree.app',
        'cibmangotree.analyzer_interface',
        'cibmangotree.tui.components',
        'cibmangotree.tui.tools',
        'cibmangotree.services.storage',
        'cibmangotree.services.importing',
        'cibmangotree.services.preprocessing',
        'cibmangotree.plugin_system',

        # Frozen plugin loader (auto-generated)
        'cibmangotree._frozen_plugins',

        # Testing utilities (if bundled)
        'cibmangotree_testing',

        # DYNAMICALLY DISCOVERED PLUGINS
        *plugin_hiddenimports,
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

if sys.platform == "darwin":
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        name='cibmangotree',
        debug=False,
        strip=True,
        upx=True,
        console=True,
        entitlements_file="./mango.entitlements",
        codesign_identity=os.getenv('APPLE_APP_CERT_ID'),
    )
else:
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        name='cibmangotree',
        debug=False,
        strip=False,
        upx=True,
        console=True,
    )
```

#### 2. Backward Compatibility Stub

Keep root-level `cibmangotree.py` for PyInstaller entry point:

```python
# cibmangotree.py
"""
Entry point stub for backward compatibility with PyInstaller.
"""

from cibmangotree.__main__ import main

if __name__ == "__main__":
    main()
```

---

## Migration Steps

### Phase 1: Setup Monorepo Structure

**Tasks:**

1. Create `packages/` directory at root
2. Create root `pyproject.toml` with workspace configuration:
   - Define workspace members
   - Add centralized dependency versions
   - Configure tools (black, isort, pytest)
   - Add dev dependencies

3. Test workspace setup:

   ```bash
   uv sync --dry-run
   ```

**Success Criteria:**

- `packages/` directory exists
- Root `pyproject.toml` is valid
- `uv` command available and functional

---

### Phase 2: Extract Core Package

**Tasks:**

1. Create directory structure:

   ```bash
   mkdir -p packages/core/src/cibmangotree
   mkdir -p packages/core/tests
   ```

2. Move and reorganize core modules:
   - `app/` → `packages/core/src/cibmangotree/app/`
   - `analyzer_interface/` → `packages/core/src/cibmangotree/analyzer_interface/`
   - `components/` → `packages/core/src/cibmangotree/tui/components/`
   - `terminal_tools/` → `packages/core/src/cibmangotree/tui/tools/`
   - `context/` → `packages/core/src/cibmangotree/context/`
   - `meta/` → `packages/core/src/cibmangotree/meta/`
   - `storage/` → `packages/core/src/cibmangotree/services/storage/`
   - `importing/` → `packages/core/src/cibmangotree/services/importing/`
   - `preprocessing/` → `packages/core/src/cibmangotree/services/preprocessing/`
   - `services/tokenizer/core/` → `packages/core/src/cibmangotree/services/tokenizer/core/`

3. Create placeholder:

   ```bash
   mkdir -p packages/core/src/cibmangotree/gui
   touch packages/core/src/cibmangotree/gui/__init__.py
   ```

4. Create plugin system:

   ```bash
   mkdir -p packages/core/src/cibmangotree/plugin_system
   ```

   Create `discovery.py` with `AnalyzerRegistry` class (see Plugin Architecture section)

5. Note: `_frozen_plugins.py` will be auto-generated by `pyinstaller.spec` during builds
   - Do not create this file manually
   - Add to `.gitignore` (see Phase 6)

6. Create `packages/core/pyproject.toml` (see Configuration Strategy section)

7. Update `__main__.py` to use plugin discovery

8. Update internal imports within core package

**Success Criteria:**

- Core package structure complete
- `uv sync` installs core package
- Can import `cibmangotree.*` modules

---

### Phase 3: Extract Plugin Packages

**For each plugin (tokenizer, analyzers):**

#### 3.1 Basic Tokenizer

```bash
mkdir -p packages/tokenizers/basic/src/cibmangotree_tokenizer_basic
mkdir -p packages/tokenizers/basic/tests
```

Move:

- `services/tokenizer/basic/` → `packages/tokenizers/basic/src/cibmangotree_tokenizer_basic/`
- `services/tokenizer/basic/test_*.py` → `packages/tokenizers/basic/tests/`

Create `packages/tokenizers/basic/pyproject.toml`

#### 3.2 Example Analyzer

```bash
mkdir -p packages/analyzers/example/src/cibmangotree_analyzer_example/{base,report,web}
mkdir -p packages/analyzers/example/tests/test_data
```

Move and rename:

- `analyzers/example/example_base/` → `packages/analyzers/example/src/cibmangotree_analyzer_example/base/`
- `analyzers/example/example_report/` → `packages/analyzers/example/src/cibmangotree_analyzer_example/report/`
- `analyzers/example/example_web/` → `packages/analyzers/example/src/cibmangotree_analyzer_example/web/`
- `analyzers/example/test_*.py` → `packages/analyzers/example/tests/`
- `analyzers/example/test_data/` → `packages/analyzers/example/tests/test_data/`

Update internal imports:

```python
# Change from:
from .example_base import example_base

# To:
from .base import example_base
```

Create `packages/analyzers/example/pyproject.toml` with entry points

#### 3.3 Hashtags Analyzer

Similar process:

```bash
mkdir -p packages/analyzers/hashtags/src/cibmangotree_analyzer_hashtags/{base,web}
mkdir -p packages/analyzers/hashtags/tests/test_data
```

Move and rename subdirectories, update imports, create pyproject.toml

#### 3.4 Ngrams Analyzer

```bash
mkdir -p packages/analyzers/ngrams/src/cibmangotree_analyzer_ngrams/{base,stats,web}
mkdir -p packages/analyzers/ngrams/tests/test_data
```

Move and rename subdirectories, update imports, create pyproject.toml

#### 3.5 Temporal Analyzer

```bash
mkdir -p packages/analyzers/temporal/src/cibmangotree_analyzer_temporal/{base,web}
mkdir -p packages/analyzers/temporal/tests
```

Move and rename subdirectories, update imports, create pyproject.toml

#### 3.6 Time Coordination Analyzer

```bash
mkdir -p packages/analyzers/time_coordination/src/cibmangotree_analyzer_time_coordination
mkdir -p packages/analyzers/time_coordination/tests
```

Move files, update imports, create pyproject.toml

**Success Criteria:**

- All plugin packages created
- Entry points defined
- `uv sync` completes successfully
- Can import plugins from new paths

---

### Phase 4: Extract Testing Package

**Tasks:**

```bash
mkdir -p packages/testing/src/cibmangotree_testing
mkdir -p packages/testing/tests
```

Move:

- `testing/` → `packages/testing/src/cibmangotree_testing/`

Create `packages/testing/pyproject.toml`

**Success Criteria:**

- Testing package created
- Can import from `cibmangotree_testing`

---

### Phase 5: Update All Imports

**Systematic Import Updates:**

1. Create search/replace mapping document
2. Use automated tools where possible:

   ```bash
   # Example: update app imports
   find packages -name "*.py" -type f -exec sed -i.bak \
     's/from app import/from cibmangotree.app import/g' {} +

   # Example: update component imports
   find packages -name "*.py" -type f -exec sed -i.bak \
     's/from components import/from cibmangotree.tui.components import/g' {} +
   ```

3. Manual review for complex cases:
   - Relative imports
   - Dynamic imports
   - String-based imports

4. Update imports in each package:
   - Core package
   - Each plugin package
   - Testing package

**Success Criteria:**

- No import errors when running `uv run cibmangotree --help`
- All tests can import required modules

---

### Phase 6: Update PyInstaller Spec for Dynamic Plugin Discovery

**Tasks:**

1. Update `pyinstaller.spec` with dynamic plugin discovery functions (see PyInstaller Compatibility section):
   - Add `discover_plugins()` function
   - Add `generate_frozen_plugins()` function
   - Add `get_plugin_hiddenimports()` function
   - Add plugin discovery calls at build time
   - Update `hiddenimports` to include `*plugin_hiddenimports`

2. Create/keep root `cibmangotree.py` stub for backward compatibility

3. Add `.gitignore` entry for auto-generated file:

   ```gitignore
   # Auto-generated by pyinstaller.spec
   packages/core/src/cibmangotree/_frozen_plugins.py
   ```

**Success Criteria:**

- PyInstaller spec auto-discovers plugins at build time
- Generates `_frozen_plugins.py` automatically
- Generates `hiddenimports` list automatically
- Build outputs show discovered plugins
- Root stub exists

**Estimated Time:** 1 hour

---

### Phase 7: Update CI/CD & Development Tooling

**Tasks:**

1. Update GitHub Actions workflows (`.github/workflows/*.yml`):

   ```yaml
   - name: Install uv
     run: curl -LsSf https://astral.sh/uv/install.sh | sh

   - name: Install dependencies
     run: uv sync

   - name: Run tests
     run: uv run pytest

   - name: Format check
     run: |
       uv run black --check packages/
       uv run isort --check packages/

   - name: Build executable
     run: uv run pyinstaller pyinstaller.spec
   ```

2. Update `bootstrap.sh`:

   ```bash
   #!/bin/bash

   # Install uv if not present
   if ! command -v uv &> /dev/null; then
       echo "Installing uv..."
       curl -LsSf https://astral.sh/uv/install.sh | sh
   fi

   # Sync all workspace packages
   echo "Syncing workspace..."
   uv sync

   echo "Bootstrap complete. Run 'uv run cibmangotree' to start."
   ```

3. Update `.gitignore`:

   ```gitignore
   # uv
   .venv/
   uv.lock

   # Python
   __pycache__/
   *.py[cod]
   *$py.class
   *.so
   .Python
   build/
   develop-eggs/
   dist/
   downloads/
   eggs/
   .eggs/
   lib/
   lib64/
   parts/
   sdist/
   var/
   wheels/
   *.egg-info/
   .installed.cfg
   *.egg

   # Project specific
   venv/
   __private__
   /analysis_outputs
   /site
   VERSION
   *.DS_Store
   .env*
   ```

4. Update documentation:
   - `README.md` - Installation and setup
   - `CLAUDE.md` - Code navigation examples
   - `GUIDE.md` - Architecture references
   - `.ai-context/README.md` - Structure overview
   - `.ai-context/architecture-overview.md` - Package structure
   - Create `CONTRIBUTING.md` - Contributor guide

**Success Criteria:**

- CI/CD pipeline passes
- Bootstrap script works
- Documentation accurate and complete

---

### Phase 8: Testing & Validation

**Tasks:**

1. **Unit Testing:**

   ```bash
   # Test entire workspace
   uv run pytest

   # Test specific packages
   uv run pytest packages/core/tests
   uv run pytest packages/analyzers/hashtags/tests
   ```

2. **Integration Testing:**

   ```bash
   # Run application
   uv run cibmangotree --help
   uv run cibmangotree --noop
   ```

3. **PyInstaller Build Testing:**

   ```bash
   # Build executable
   uv run pyinstaller pyinstaller.spec

   # Test executable
   dist/cibmangotree --help
   dist/cibmangotree --noop
   ```

4. **Manual Testing:**
   - Launch application
   - Create new project
   - Import sample data
   - Run each analyzer
   - Export results
   - Launch web presenters

5. **Cross-Platform Testing:**
   - Test on Windows (via CI or local)
   - Test on macOS (via CI or local)
   - Test on Linux (via CI or local)

6. **Fix Issues:**
   - Import errors
   - Path resolution issues
   - Plugin discovery problems
   - PyInstaller build failures

**Success Criteria:**

- All tests pass
- Application runs successfully
- All analyzers work
- Web presenters launch
- PyInstaller builds work on all platforms

---

### Phase 9: Cleanup & Documentation

**Tasks:**

1. Remove old directory structure:

   ```bash
   # Remove old directories (MUST BE EMPTY OR ONLY CONTAIN UNUSED FILES)
   trash app/ analyzer_interface/ components/ terminal_tools/
   trash analyzers/ storage/ importing/ preprocessing/ services/
   trash testing/ context/ meta/
   ```

2. Update all documentation references

3. Create migration guide for contributors

4. Update `.ai-context/` files

5. Final review of all changes

**Success Criteria:**

- Old structure removed
- Documentation complete
- No broken references

---

**Recommended Approach:** Work in feature branch, commit after each phase

---

## Testing Strategy

### Unit Tests

```bash
# Run all tests
uv run pytest

# Run tests for specific package
uv run pytest packages/core/tests
uv run pytest packages/analyzers/hashtags/tests

# Run specific test file
uv run pytest packages/analyzers/hashtags/tests/test_hashtags_base.py

# Run with coverage
uv run pytest --cov=cibmangotree --cov-report=html
```

### Integration Tests

```bash
# Test CLI entry point
uv run cibmangotree --help
uv run cibmangotree --noop

# Test in development mode
uv run python -m cibmangotree

# Test plugin discovery
uv run python -c "from cibmangotree.plugin_system import AnalyzerRegistry; print(len(AnalyzerRegistry.discover()))"
```

### Build Tests

```bash
# Test PyInstaller build
uv run pyinstaller pyinstaller.spec

# Test frozen executable
dist/cibmangotree --help
dist/cibmangotree --noop

# Test on all platforms (via CI)
# - Windows 2022
# - macOS 13 (x86)
# - macOS 15 (arm64)
```

### Manual Testing Checklist

- [ ] Launch application
- [ ] Create new project
- [ ] Import CSV data
- [ ] Import Excel data
- [ ] Run hashtags analyzer
- [ ] Run ngrams analyzer
- [ ] Run temporal analyzer
- [ ] Run time coordination analyzer
- [ ] View analysis results
- [ ] Export results to XLSX
- [ ] Export results to CSV
- [ ] Launch hashtags web presenter
- [ ] Launch ngrams web presenter
- [ ] Launch temporal web presenter
- [ ] All web presenters display correctly

---

## Risk Mitigation

### Import Rewrites

**Risk:** Breaking imports during migration

**Mitigation:**

- Work in feature branch
- Commit after each package migration
- Use automated search/replace tools
- Manual review of complex imports
- Test after each phase
- Keep import mapping document

### PyInstaller Compatibility

**Risk:** Frozen builds not working

**Mitigation:**

- Hybrid plugin discovery system
- Explicit imports in `_frozen_plugins.py`
- Comprehensive `hiddenimports` list
- Test builds frequently during migration
- Keep backward-compatible entry point

### Dependency Conflicts

**Risk:** Version conflicts between packages

**Mitigation:**

- Centralized version constraints
- Workspace-level dependency resolution
- Test `uv sync` frequently
- Document any version-specific requirements

### Testing Gaps

**Risk:** Missing test coverage during migration

**Mitigation:**

- Run full test suite after each phase
- Test at package and workspace level
- Manual testing of critical workflows
- Compare test coverage before/after

### CI/CD Breaking

**Risk:** GitHub Actions workflows fail

**Mitigation:**

- Update CI/CD in same commit as migration
- Test workflows in feature branch
- Have rollback plan ready
- Document new CI/CD setup

### Contributor Confusion

**Risk:** Contributors struggle with new structure

**Mitigation:**

- Update documentation immediately
- Create migration guide
- Update AI context files
- Clear package boundaries and naming
- Include example analyzer for reference

### Data Compatibility

**Risk:** Breaking existing user data

**Mitigation:**

- Keep storage format unchanged
- Test with existing projects
- Maintain backward compatibility
- Document any breaking changes

---

## Success Criteria

### Technical Metrics

- ✅ All packages have valid `pyproject.toml`
- ✅ `uv sync` completes without errors
- ✅ Full test suite passes (maintain 100% coverage)
- ✅ `uv run cibmangotree` launches successfully
- ✅ All analyzers auto-discovered (dev mode)
- ✅ All analyzers bundled correctly (frozen mode)
- ✅ CI/CD pipeline passes on all platforms
- ✅ PyInstaller builds work on Windows/macOS/Linux

### Code Quality Metrics

- ✅ Black and isort pass on all code
- ✅ No circular dependencies
- ✅ Clear import paths
- ✅ Each package has minimal dependencies
- ✅ Plugin architecture works in both modes

### Functional Metrics

- ✅ Can import CSV/Excel data
- ✅ Can run all existing analyzers
- ✅ Can export results in all formats
- ✅ Web presenters launch correctly
- ✅ All existing features work as before
- ✅ No data loss or corruption

### Developer Experience Metrics

- ✅ Bootstrap time < 2 minutes
- ✅ Clear package boundaries
- ✅ Simple pyproject.toml files (< 30 lines)
- ✅ Documentation updated and accurate
- ✅ Easy to understand structure for new contributors

---

## Development Workflow (Post-Migration)

### Initial Setup

```bash
# Clone repository
git clone https://github.com/civictech/cibmangotree.git
cd cibmangotree

# Run bootstrap script
./bootstrap.sh

# Or manually:
curl -LsSf https://astral.sh/uv/install.sh | sh
uv sync
```

### Daily Development

```bash
# Sync workspace (after pulling changes)
uv sync

# Run application
uv run cibmangotree

# Run tests
uv run pytest

# Run specific test
uv run pytest packages/analyzers/hashtags/tests/test_hashtags_base.py

# Format code
uv run black packages/
uv run isort packages/

# Build executable
uv run pyinstaller pyinstaller.spec
```

### Adding New Analyzer

1. Create package structure:

   ```bash
   mkdir -p packages/analyzers/my_analyzer/src/cibmangotree_analyzer_my_analyzer/{base,web}
   mkdir -p packages/analyzers/my_analyzer/tests
   ```

2. Create `packages/analyzers/my_analyzer/pyproject.toml`:

   ```toml
   [project]
   name = "cibmangotree-analyzer-my-analyzer"
   version = "0.1.0"
   description = "My analyzer"
   dependencies = [
       "cibmangotree",
       "cibmangotree-testing",
       "polars",
   ]

   [project.entry-points."cibmangotree.analyzers"]
   my_analyzer = "cibmangotree_analyzer_my_analyzer.base:my_analyzer"
   ```

3. Add to root workspace:

   ```toml
   # Edit pyproject.toml
   [tool.uv.workspace]
   members = [
       # ... existing ...
       "packages/analyzers/my_analyzer",
   ]
   ```

4. Sync workspace:

   ```bash
   uv sync
   ```

5. Implement analyzer following existing patterns

6. Add to frozen plugins (for releases):

   ```python
   # Edit cibmangotree/_frozen_plugins.py
   from cibmangotree_analyzer_my_analyzer.base import my_analyzer
   AnalyzerRegistry.register(my_analyzer)
   ```

7. Add to PyInstaller spec:

   ```python
   # Edit pyinstaller.spec hiddenimports
   'cibmangotree_analyzer_my_analyzer',
   'cibmangotree_analyzer_my_analyzer.base',
   ```

---

## Appendix: Quick Reference

### Package Structure

| Package | Path | Purpose |
|---------|------|---------|
| core | `packages/core/` | Framework, app, UI, services |
| tokenizer-basic | `packages/tokenizers/basic/` | Basic tokenizer implementation |
| analyzer-example | `packages/analyzers/example/` | Example for contributors |
| analyzer-hashtags | `packages/analyzers/hashtags/` | Hashtag analysis |
| analyzer-ngrams | `packages/analyzers/ngrams/` | N-gram analysis |
| analyzer-temporal | `packages/analyzers/temporal/` | Temporal patterns |
| analyzer-time-coordination | `packages/analyzers/time_coordination/` | Coordination detection |
| testing | `packages/testing/` | Test utilities |

### Import Cheat Sheet

```python
# Core
from cibmangotree.app import App
from cibmangotree.app.logger import get_logger

# Analyzer framework
from cibmangotree.analyzer_interface import AnalyzerInterface

# UI
from cibmangotree.tui.components.main_menu import main_menu
from cibmangotree.tui.tools import ProgressReporter

# Services
from cibmangotree.services.storage import Storage
from cibmangotree.services.importing import ImporterSession

# Plugins
from cibmangotree_tokenizer_basic import BasicTokenizer
from cibmangotree_analyzer_hashtags.base import hashtags

# Testing
from cibmangotree_testing import test_primary_analyzer
```

### Common Commands

```bash
# Setup
uv sync

# Run
uv run cibmangotree

# Test
uv run pytest
uv run pytest packages/core/tests
uv run pytest -k test_hashtags

# Format
uv run black packages/
uv run isort packages/

# Build
uv run pyinstaller pyinstaller.spec

# Build specific package
uv build -p packages/core
```

---

**Document Version**: 2.0
**Last Updated**: 2025-10-09
**Status**: Ready for Implementation
