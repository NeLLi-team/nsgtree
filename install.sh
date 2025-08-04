#!/bin/bash
# NSGTree installation script

echo "Installing NSGTree..."

# Install the package in development mode
pip install -e .

echo "NSGTree installed! You can now use these commands:"
echo ""
echo "Direct command (after installation):"
echo "  nsgtree --help"
echo "  nsgtree run example resources/models/rnapol.hmm"
echo ""
echo "Or using pixi shortcuts:"
echo "  pixi run help"
echo "  pixi run run example resources/models/rnapol.hmm"
echo "  pixi run test-rnapol    # Quick test"
echo ""
