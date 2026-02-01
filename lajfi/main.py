# main.py
# Entry point. Runs in Blender.
# Clear, setup, spawn, start tick loop.

import bpy
import time

from .config import OUTPUT_DIR, MAX_PLANTS, MAX_CREATURES
from .utils import log
from . import world


def main():
    """Start LAJFI simulation."""

    log("=" * 60)
    log("LAJFI - OMNIVORE EDITION")
    log("=" * 60)
    log("")
    log("Everyone eats everything - plants AND each other")
    log("")
    log("BEHAVIOR:")
    log("  Hungry -> Eat nearest (plant or creature)")
    log("  Satiated -> Mate")
    log("")
    log(f"Max {MAX_CREATURES} creatures, {MAX_PLANTS} plants")
    log("")

    # Clear and setup
    world.clear_scene()
    world.setup_world()

    # Spawn plants
    for _ in range(MAX_PLANTS):
        world.spawn_plant()
    log(f"Spawned {MAX_PLANTS} plants")

    # Spawn creatures
    log("")
    for _ in range(MAX_CREATURES):
        world.spawn_creature()

    # Set export timer
    world.last_export_time = time.time()

    # Start tick loop
    bpy.app.timers.register(world.tick)

    log("")
    log("SIMULATION STARTED!")
    log(f"STL export -> {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
