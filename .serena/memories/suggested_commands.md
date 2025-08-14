# Suggested Commands

## Development Environment

```bash
# Setup virtual environment (first time)
python -m venv venv

# Activate environment and install dependencies
./bootstrap.sh          # macOS/Linux
./bootstrap.ps1         # Windows PowerShell
```

## Running the Application

```bash
# Start the application
python -m mangotango

# Run with no-op flag (for testing)
python -m mangotango --noop

# Run with specific log level (DEBUG, INFO, WARNING, ERROR)
python -m mangotango --log-level DEBUG
```

## Development Commands

```bash
# Code formatting (must be run before commits)
isort .
black .

# Run both formatters together
isort . && black .

# Run tests (excludes performance benchmarks by default)
pytest

# Run specific test
pytest analyzers/hashtags/test_hashtags_analyzer.py

# Run verbose tests
pytest -v

# Install development dependencies
pip install -r requirements-dev.txt

# Install production dependencies only
pip install -r requirements.txt
```

## Performance Testing and Benchmarking

### Quick Development Testing

```bash
# Run performance tests (excludes slow benchmarks)
pytest testing/performance/test_chunking_optimization.py -v

# Run functionality tests only (no benchmarks or stress tests)
pytest testing/performance/ -v -k "not benchmark and not stress"

# Run specific performance test categories
pytest testing/performance/ -v -k "memory_detection"
pytest testing/performance/ -v -k "adaptive_chunk"
pytest testing/performance/ -v -k "system_config"
```

### Comprehensive Performance Benchmarking

```bash
# Run ONLY performance benchmarks (slow but comprehensive)
pytest -m performance -v

# Run performance benchmarks from specific file
pytest testing/performance/test_performance_benchmarks.py -m performance -v

# Run enhanced benchmarks with detailed metrics
python testing/performance/run_enhanced_benchmarks.py

# Run all tests INCLUDING performance benchmarks
pytest -m "" -v

# Run comprehensive performance suite with timing
pytest testing/performance/ -m "" -v -s --durations=10
```

### Performance Test Organization

```bash
# Run only fast tests (excludes slow benchmarks)
pytest -m "not slow" -v

# Run only slow tests (includes all benchmarks and stress tests)
pytest -m slow -v

# Run integration validation tests
pytest testing/performance/test_integration_validation.py -v

# Run stress tests (extreme conditions)
pytest -m stress -v
```

## Logging and Debugging

```bash
# View application logs (default location)
# macOS: ~/.local/share/MangoTango/logs/mangotango.log
# Windows: %APPDATA%/Civic Tech DC/MangoTango/logs/mangotango.log
# Linux: ~/.local/share/MangoTango/logs/mangotango.log

# View logs in real-time
tail -f ~/.local/share/MangoTango/logs/mangotango.log  # macOS/Linux

# Run with verbose logging for debugging
python -m mangotango --log-level DEBUG
```

## Git Workflow

```bash
# Create feature branch from develop
git checkout develop
git pull origin develop
git checkout -b feature/new-feature

# Make changes and commit
git add .
git commit -m "Description of changes"
git push origin feature/new-feature

# Create PR to develop branch (not main)
```

## Build Commands

```bash
# Build executable (from GitHub Actions)
pyinstaller pyinstaller.spec
```

## Memory and System Diagnostics

```bash
# Test memory detection
python -c "from app.utils import MemoryManager; mm = MemoryManager(); print(f'Auto-detected: {mm.max_memory_gb}GB')"

# Test adaptive chunking calculation
python -c "from analyzers.ngrams.ngrams_base.main import calculate_optimal_chunk_size; print(f'Optimal chunk size for 1M rows: {calculate_optimal_chunk_size(1000000)}')"

# Check system memory info
python -c "import psutil; print(f'Total RAM: {psutil.virtual_memory().total / 1024**3:.1f}GB')"
```

## Advanced Testing Commands

```bash
# Run tests with specific pytest marks
pytest -m "performance and not stress" -v      # Performance tests excluding stress
pytest -m "not performance and not slow" -v    # Fast functional tests only

# Run tests with coverage reporting
pytest --cov=app --cov=analyzers --cov-report=html

# Run tests with memory profiling (requires memory-profiler)
pytest --profile-mem testing/performance/

# Run specific analyzer tests
pytest analyzers/ngrams/test_ngrams_base.py -v
pytest analyzers/ngrams/test_ngram_stats.py -v
pytest analyzers/hashtags/test_hashtags_analyzer.py -v
```

## Development Utilities

```bash
# Check code style without fixing
black . --check
isort . --check-only

# Find Python files modified recently
find . -name "*.py" -type f -mtime -1

# Search for patterns in code
grep -r "MemoryManager" --include="*.py" .
grep -r "ProgressManager" --include="*.py" .

# Count lines of code by category
find . -name "*.py" -path "./analyzers/*" | xargs wc -l | tail -1
find . -name "*.py" -path "./app/*" | xargs wc -l | tail -1
find . -name "*.py" -path "./testing/*" | xargs wc -l | tail -1
```

## System Commands (macOS)

```bash
# Standard Unix commands work on macOS
ls, cd, find, grep, git

# Use these for file operations
find . -name "*.py" -type f
grep -r "pattern" --include="*.py" .

# Monitor system resources during tests
htop              # Interactive process viewer
iostat 1          # I/O statistics
vm_stat 1         # Memory statistics (macOS)
```
