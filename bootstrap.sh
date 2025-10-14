#!/bin/bash
# Bootstrap development environment for CIB Mango Tree

set -e

echo "Setting up CIB Mango Tree development environment..."

# Check for uv
if ! command -v uv &> /dev/null; then
    echo "UV not found. Installing..."
    curl -LsSf https://astral.sh/uv/install.sh | sh

    # Source the uv environment
    if [ -f "$HOME/.cargo/env" ]; then
        source "$HOME/.cargo/env"
    fi
fi

# Sync dependencies
echo "Installing dependencies..."
uv sync --all-extras

# Verify installation
echo "Verifying installation..."
uv run python -c "import cibmangotree; print(f'✅ CIB Mango Tree {cibmangotree.__version__} ready')"

echo ""
echo "✅ Setup complete!"
echo ""
echo "Quick start commands:"
echo "  uv run cibmangotree          # Run the application"
echo "  uv run pytest                # Run tests"
echo "  uv run black .               # Format code"
echo "  uv run pyinstaller pyinstaller.spec  # Build executable"
echo ""
