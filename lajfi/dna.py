# dna.py
# Genetics. Each creature has DNA that determines physical traits.
# Gielis forms + fractal settings + speed.
# When they mate, DNA is combined and mutated.

import random

from .config import (
    MIN_FRACTAL_LEVELS, MAX_FRACTAL_LEVELS,
    MIN_CHILDREN, MAX_CHILDREN,
    MUTATION_RATE, MUTATION_STRENGTH
)

# CENTRALIZED LIST - change here for triad/pentad/etc
# Each gene creates one Gielis supershape that gets merged together
GIELIS_GENES = ['lajfi_1', 'lajfi_2', 'lajfi_3']


def random_gielis_gene():
    """
    Generate a random Gielis gene (8 parameters for one supershape).

    Returns:
        dict: Parameters for a single Gielis form
            m1, m2: Symmetry (3=clover, 14=star)
            n1, n2, n3: Horizontal curvature
            n1b, n2b, n3b: Vertical curvature
    """
    return {
        'm1': random.randint(3, 14),     # Symmetry: 3=clover, 14=star
        'm2': random.randint(2, 12),     # Vertical symmetry
        'n1': random.uniform(0.08, 0.9), # Low=angular, high=rounded
        'n2': random.uniform(0.5, 3.5),  # Broad curvature
        'n3': random.uniform(0.5, 3.5),  # More curvature
        'n1b': random.uniform(0.1, 0.95),# Vertical angularity
        'n2b': random.uniform(0.4, 3.2), # Vertical curve
        'n3b': random.uniform(0.4, 3.2), # More vertical curve
    }


def random_dna():
    """
    Create completely new DNA. Used for fresh creatures.

    Returns:
        dict: Complete DNA with 32 parameters:
            - 3 x 8 = 24 Gielis parameters (for three forms)
            - 3 fractal parameters (levels, children, scale)
            - 3 color parameters (RGB) [reserved]
            - 2 behavior parameters (speed, aggression) [speed used]
    """
    dna = {}

    # Gielis genes from centralized list
    for gene in GIELIS_GENES:
        dna[gene] = random_gielis_gene()

    # Fractal settings
    dna['fractal_levels'] = random.randint(MIN_FRACTAL_LEVELS, MAX_FRACTAL_LEVELS)
    dna['fractal_children'] = random.randint(MIN_CHILDREN, MAX_CHILDREN)
    dna['scale_factor'] = random.uniform(0.45, 0.70)  # Large outgrowths relative to body

    # Movement
    dna['speed'] = random.uniform(0.2, 0.5)

    return dna


def combine_dna(dna1, dna2):
    """
    Combine two parents' DNA. Sexual reproduction.

    Rules:
        - Gielis genes: Entire gene from one parent (mixing internals causes chaos)
        - Integers: Pick from one parent
        - Floats: Interpolate (30-70% mix)

    Args:
        dna1: First parent's DNA
        dna2: Second parent's DNA

    Returns:
        dict: Child's combined DNA
    """
    child_dna = {}

    for key in dna1.keys():
        if isinstance(dna1[key], dict):
            # Gielis genes: entire gene from one parent
            if random.random() < 0.5:
                child_dna[key] = dna1[key].copy()
            else:
                child_dna[key] = dna2[key].copy()

        elif isinstance(dna1[key], int):
            # Integers: pick one
            child_dna[key] = random.choice([dna1[key], dna2[key]])

        else:
            # Floats: blend
            mix = random.uniform(0.3, 0.7)  # Not always 50/50
            child_dna[key] = dna1[key] * mix + dna2[key] * (1 - mix)

    return child_dna


def mutate_dna(dna):
    """
    Apply mutations. Without this, everyone becomes identical.

    Mutation rules:
        - Symmetry (m1, m2): Change by a few steps (discrete)
        - Curvature (n values): Percentage change (continuous)
        - Fractal levels/children: +/- 1 step
        - Other floats: Percentage change

    Args:
        dna: The DNA to mutate

    Returns:
        dict: Mutated DNA
    """
    mutated = {}

    for key, value in dna.items():

        if isinstance(value, dict):
            # Gielis gene: mutate each parameter separately
            new_gene = value.copy()
            for gkey, gval in value.items():
                if random.random() < MUTATION_RATE:
                    if gkey in ['m1', 'm2']:
                        # Symmetry: change by a few steps
                        new_gene[gkey] = max(3, min(12, gval + random.randint(-2, 2)))
                    else:
                        # Curvature: percentage change
                        change = gval * MUTATION_STRENGTH * random.uniform(-1, 1)
                        new_gene[gkey] = max(0.1, min(3.0, gval + change))
            mutated[key] = new_gene

        elif key == 'fractal_levels':
            # Fractal level: change by one step sometimes
            if random.random() < MUTATION_RATE:
                mutated[key] = max(MIN_FRACTAL_LEVELS, min(MAX_FRACTAL_LEVELS,
                    value + random.choice([-1, 0, 1])))
            else:
                mutated[key] = value

        elif key == 'fractal_children':
            # Number of children: change by one step sometimes
            if random.random() < MUTATION_RATE:
                mutated[key] = max(MIN_CHILDREN, min(MAX_CHILDREN,
                    value + random.choice([-1, 0, 1])))
            else:
                mutated[key] = value

        elif isinstance(value, float):
            # Other floats: percentage change
            if random.random() < MUTATION_RATE:
                change = value * MUTATION_STRENGTH * random.uniform(-1, 1)
                mutated[key] = max(0.1, value + change)
            else:
                mutated[key] = value

        else:
            mutated[key] = value

    return mutated


# =============================================================================
# THE GIELIS SUPERFORMULA - Mathematics behind the forms
# =============================================================================
#
# Johan Gielis published the formula in 2003. It describes almost all
# natural forms: leaves, shells, starfish, bacteria...
#
# THE FORMULA (2D):
#
#     r(theta) = ( |cos(m*theta/4)|^n2 + |sin(m*theta/4)|^n3 ) ^ (-1/n1)
#
# PARAMETERS:
#
#     m   = symmetry. How many "arms" or folds.
#           m=5 gives starfish, m=3 gives clover, m=0 gives circle
#
#     n1  = overall shape. Low value = angular, high = rounded
#           n1 < 1 gives star shape, n1 > 1 gives rounded shape
#
#     n2  = curvature for cos term. Affects arm width
#
#     n3  = curvature for sin term. Affects depth between arms
#
# -----------------------------------------------------------------------------
# STEP 1: FROM 2D TO 3D (one gene -> one form)
# -----------------------------------------------------------------------------
#
# Each gene (lajfi_1, lajfi_2, etc) has 8 parameters giving TWO profiles:
#
#     r1 = gielis(theta, m1, n1, n2, n3)      # horizontal profile
#     r2 = gielis(phi, m2, n1b, n2b, n3b)     # vertical profile
#     r  = r1 * r2                             # combine into 3D
#
# Then convert from spherical to Cartesian coordinates:
#
#     x = r * sin(phi) * cos(theta)
#     y = r * sin(phi) * sin(theta)
#     z = r * cos(phi)
#
# -----------------------------------------------------------------------------
# STEP 2: MULTIPLE SEGMENTS (multiple genes -> one creature)
# -----------------------------------------------------------------------------
#
# GIELIS_GENES determines how many 3D forms are merged together:
#
#     TRIAD  = ['lajfi_1', 'lajfi_2', 'lajfi_3']           -> 3 segments
#     PENTAD = [..., 'lajfi_4', 'lajfi_5']                 -> 5 segments
#     HEPTAD = [..., 'lajfi_6', 'lajfi_7']                 -> 7 segments
#
# First segment at center, the rest offset around it.
# All are joined with bpy.ops.object.join() and voxel-remeshed.
#
# -----------------------------------------------------------------------------
# EXAMPLE SHAPES:
#
#     m=4, n1=0.3, n2=n3=1.0  ->  square star
#     m=5, n1=0.2, n2=n3=1.7  ->  starfish
#     m=6, n1=1.0, n2=n3=1.0  ->  hexagon
#     m=0, n1=1.0, n2=n3=1.0  ->  perfect sphere
#
# =============================================================================
