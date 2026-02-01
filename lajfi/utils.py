# utils.py
# Helper functions. Currently just logging.

import sys


def log(msg):
    """Print timestamped message to stdout."""
    sys.stdout.write(f"[LAJFI] {msg}\n")
    sys.stdout.flush()
