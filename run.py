#!/usr/bin/env python3
"""
LAJFI Runner
============
Run this file with Blender to start the simulation.

Usage:
    blender --python run.py                    # Background mode
    blender --python run.py -- --gui           # With Blender GUI

Or use the shell script:
    ./lajfi.sh                                 # Background mode
    ./lajfi.sh --gui                           # With GUI
"""

import sys
import os

# Add parent directory to path so lajfi package can be found
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

from lajfi.main import main
main()
