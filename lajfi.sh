#!/bin/bash
# LAJFI - Evolutionary Life Simulation
# Run with: ./lajfi.sh or ./lajfi.sh --gui

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "LAJFI - Evolutionary Life Simulation"
echo ""

# Detect Blender
if flatpak list 2>/dev/null | grep -q org.blender.Blender; then
    BLENDER="flatpak run org.blender.Blender"
elif command -v blender &> /dev/null; then
    BLENDER="blender"
else
    echo "ERROR: Blender not found!"
    echo "Install Blender from https://www.blender.org/ or via Flatpak"
    exit 1
fi

# Run
if [ "$1" == "--gui" ]; then
    echo "Starting with GUI..."
    $BLENDER --python "$SCRIPT_DIR/run.py"
else
    echo "Starting in background mode..."
    echo "(Use --gui flag for visual mode)"
    $BLENDER --background --python "$SCRIPT_DIR/run.py"
fi
