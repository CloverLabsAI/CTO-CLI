#!/bin/bash
# Install script for CTO CLI
# Run: curl -sSL https://raw.githubusercontent.com/CloverLabsAI/CTO-CLI/main/install.sh | bash
# Or:  ./install.sh

set -e

INSTALL_DIR="$HOME/.cto-cli"
BIN_DIR="$HOME/.local/bin"
REPO_URL="https://github.com/CloverLabsAI/CTO-CLI.git"

echo "Installing CTO CLI..."

# Create install directory
mkdir -p "$BIN_DIR"

# Clone or update
if [ -d "$INSTALL_DIR" ]; then
    echo "Updating existing installation..."
    cd "$INSTALL_DIR"
    # Clean up any local changes (pycache, etc.) before pulling
    git reset --hard HEAD
    git clean -fd
    git pull
else
    echo "Cloning repository..."
    git clone "$REPO_URL" "$INSTALL_DIR"
fi

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv "$INSTALL_DIR/.venv"

# Install dependencies
echo "Installing dependencies..."
"$INSTALL_DIR/.venv/bin/pip" install --upgrade pip
"$INSTALL_DIR/.venv/bin/pip" install -e "$INSTALL_DIR"

# Create wrapper script
echo "Creating cto command..."
cat > "$BIN_DIR/cto" << 'EOF'
#!/bin/bash
exec "$HOME/.cto-cli/.venv/bin/python" -m worklog "$@"
EOF
chmod +x "$BIN_DIR/cto"

# Add to PATH if not already there
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    echo ""
    echo "Add this to your shell profile (~/.bashrc, ~/.zshrc, etc.):"
    echo ""
    echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
    echo ""
fi

echo ""
echo "Installation complete!"
echo ""
echo "Run 'cto setup' to configure your API credentials."
echo "Run 'cto --help' to see available commands."
