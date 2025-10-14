# Bootstrap development environment for CIB Mango Tree
# PowerShell script

# Check if running in PowerShell
if ($PSVersionTable -eq $null) {
    Write-Host "Please run this script in PowerShell."
    exit 1
}

Write-Host "Setting up CIB Mango Tree development environment..."

# Check for uv
if (-Not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "UV not found. Installing..."
    powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

    # Refresh PATH
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
}

# Sync dependencies
Write-Host "Installing dependencies..."
uv sync --all-extras

# Verify installation
Write-Host "Verifying installation..."
uv run python -c "import cibmangotree; print(f'✅ CIB Mango Tree {cibmangotree.__version__} ready')"

Write-Host ""
Write-Host "✅ Setup complete!"
Write-Host ""
Write-Host "Quick start commands:"
Write-Host "  uv run cibmangotree          # Run the application"
Write-Host "  uv run pytest                # Run tests"
Write-Host "  uv run black .               # Format code"
Write-Host "  uv run pyinstaller pyinstaller.spec  # Build executable"
Write-Host ""
