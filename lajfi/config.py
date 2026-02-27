# config.py
# All tunable parameters. Change these to tweak behavior.

import os

# !! HEY CUTIE - change this to your favourite local spot !!
# Or set the LAJFI_OUTPUT environment variable
OUTPUT_DIR = os.environ.get('LAJFI_OUTPUT', '/tmp/lajfi_output')

WORLD_SIZE = 20       # 20x20 plane. Creatures live on this.
MAX_CREATURES = 3     # Triad: en dör, två parar sig, barn föds
MAX_PLANTS = 8        # Respawn when eaten
TICK_SPEED = 0.3      # Seconds between simulation updates

# Energy - enables all processes
START_ENERGY = 40     # What you're born with
MOVEMENT_COST = 0.6   # Moving costs energy
IDLE_COST = 0.2       # Existing costs energy too
PLANT_ENERGY = 25     # One plant gives 25
EAT_RANGE = 2.0       # How close to eat
STARVATION_THRESHOLD = 0  # Below this = death

# Reproduction
MATING_RANGE = 3.0    # How close to mate
MATING_ENERGY = 60    # Need at least this to reproduce
MATING_COST = 30      # Cost of making offspring
MUTATION_RATE = 0.20  # 20% chance per gene
MUTATION_STRENGTH = 0.25  # How much a mutation changes the value

# Combat - everyone can eat everyone
ATTACK_COST = 8       # Attacking costs energy
KILL_ENERGY_GAIN = 0.7  # Gain 70% of victim's energy
CANNIBAL_RANGE = 3.0  # Range for cannibalism
SATISFIED_ENERGY = 70  # Satiated = wants to mate instead

# Fractal - balanced for variety without crashing
MIN_FRACTAL_LEVELS = 2
MAX_FRACTAL_LEVELS = 3   # Max 3 levels (4 was too heavy)
MIN_CHILDREN = 2         # Sometimes fewer outgrowths
MAX_CHILDREN = 5         # Max 5 (7 crashed)

# Export
EXPORT_INTERVAL = 120  # Every 2 minutes, save best as STL
