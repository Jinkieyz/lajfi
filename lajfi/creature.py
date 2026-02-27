# creature.py
# Creatures are omnivores - they eat plants AND each other.
# DNA determines appearance, fractal complexity, speed.
# Satiated = mate. Hungry = eat nearest.

import bpy
import math
import random
from mathutils import Vector

from .config import (
    WORLD_SIZE, START_ENERGY, MOVEMENT_COST, IDLE_COST,
    MATING_ENERGY, MATING_COST, STARVATION_THRESHOLD,
    ATTACK_COST, KILL_ENERGY_GAIN
)
from .dna import random_dna, combine_dna, mutate_dna, GIELIS_GENES
from .gielis import create_gielis_mesh


class TriadCreature:
    """
    A LAJFI creature. Three Gielis forms merged together + fractal outgrowths.

    The name "Triad" comes from the three overlapping supershapes that form
    the body. Each segment uses different DNA parameters, creating unique
    organic forms. Recursive fractal outgrowths add complexity.

    Attributes:
        id: Unique identifier
        name: Generated name (e.g., BOKA, GLIF, ZOMPA)
        dna: Dictionary of genetic parameters
        position: [x, y, z] in world space
        energy: Current energy level
        age: Ticks since birth
        generation: Ancestry depth
    """

    counter = 0  # For unique IDs

    def __init__(self, dna=None, position=None, parents=None):
        """
        Create creature. dna=None gives random DNA.

        Args:
            dna: Optional DNA dictionary
            position: Optional [x, y, z] coordinates
            parents: Optional list of parent names
        """
        TriadCreature.counter += 1
        self.id = TriadCreature.counter
        self.name = self._generate_name()
        self.dna = dna or random_dna()

        # Position - keep within world bounds
        self.position = position or [
            random.uniform(-WORLD_SIZE/2 + 3, WORLD_SIZE/2 - 3),
            random.uniform(-WORLD_SIZE/2 + 3, WORLD_SIZE/2 - 3),
            1.0  # Slightly above floor
        ]

        # Status
        self.energy = START_ENERGY
        self.age = 0
        self.obj = None  # Blender object
        self.generation = 1
        self.parents = parents or []
        self.children_count = 0
        self.meals_eaten = 0
        self.mating_cooldown = 0

    def _generate_name(self):
        """
        Generate name following Swedish name structure.

        Swedish names typically alternate consonants and vowels,
        creating pronounceable syllables. Examples: BOKA, GLIF, ZOMPA, NELA.

        The pattern is: consonant-vowel-consonant-vowel...
        This makes every creature's name feel like it could be
        a real Scandinavian word or name.
        """
        vowels = "aeiou"
        consonants = "bdfgklmnprstvz"
        return ''.join(
            random.choice(consonants if i % 2 == 0 else vowels)
            for i in range(random.randint(3, 5))
        ).upper()

    def build_mesh(self, resolution=20):
        """
        Build body from DNA. This is computationally expensive.

        Process:
            1. Create Gielis forms from each gene
            2. Position them with random attachment points
            3. Add recursive fractal outgrowths
            4. Join all parts
            5. Voxel remesh for manifold mesh (3D printable)

        Args:
            resolution: Mesh resolution (higher = smoother but slower)

        Returns:
            bpy.types.Object: The created Blender mesh object
        """
        all_objects = []
        segment_positions = []
        segment_scales = []

        # Step 1: Gielis forms - connected randomly
        # First at center, rest attach to previous parts

        for i, key in enumerate(GIELIS_GENES):
            params = self.dna[key]

            # Smaller segment = smaller total size
            scale = random.uniform(0.5, 0.85)

            if i == 0:
                # First part at center
                loc = (0, 0, 0)
            else:
                # Attach to a random previous part
                attach_to = random.randint(0, i - 1)
                parent_pos = segment_positions[attach_to]
                parent_scale = segment_scales[attach_to]

                # Random direction from parent part
                angle_h = random.uniform(0, 2 * math.pi)
                angle_v = random.uniform(-0.7, 0.7)  # -40 to +40 degrees

                # Distance = parent size * 0.6 (so they overlap)
                dist = parent_scale * 0.6

                loc = (
                    parent_pos[0] + dist * math.cos(angle_h) * math.cos(angle_v),
                    parent_pos[1] + dist * math.sin(angle_h) * math.cos(angle_v),
                    parent_pos[2] + dist * math.sin(angle_v)
                )

            segment_positions.append(loc)
            segment_scales.append(scale)

            obj = create_gielis_mesh(params, resolution=resolution, scale=scale, location=loc)
            all_objects.append(obj)

        # Join into base
        bpy.ops.object.select_all(action='DESELECT')
        for obj in all_objects:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = all_objects[0]
        bpy.ops.object.join()
        base = bpy.context.active_object

        # Step 2: Fractal outgrowths
        current_level = [base]
        current_scale = 1.0
        all_objects = [base]

        for level in range(1, self.dna['fractal_levels'] + 1):
            current_scale *= self.dna['scale_factor']  # Shrink each level
            level_res = max(10, resolution // (level + 1))  # Lower res deeper
            new_level = []

            for parent in current_level:
                mesh = parent.data
                num_verts = len(mesh.vertices)

                # Select vertices for outgrowths
                step = max(1, num_verts // self.dna['fractal_children'])
                indices = list(range(0, num_verts, step))[:self.dna['fractal_children']]

                for idx in indices:
                    vert = mesh.vertices[idx]
                    pos = parent.matrix_world @ vert.co
                    normal = vert.co.normalized()

                    # Random gene for each outgrowth (more variation!)
                    gene_key = random.choice(GIELIS_GENES)
                    params = self.dna[gene_key]

                    # Random direction (not just along normal)
                    direction = Vector([
                        normal.x + random.uniform(-0.3, 0.3),
                        normal.y + random.uniform(-0.3, 0.3),
                        normal.z + random.uniform(-0.2, 0.2)
                    ]).normalized()

                    # Place with overlap
                    overlap = current_scale * 0.3
                    child_pos = (
                        pos.x + direction.x * overlap,
                        pos.y + direction.y * overlap,
                        pos.z + direction.z * overlap
                    )

                    # Vary size per outgrowth
                    child_scale = current_scale * random.uniform(0.85, 1.15)

                    child = create_gielis_mesh(
                        params, resolution=level_res,
                        scale=child_scale, location=child_pos
                    )
                    all_objects.append(child)
                    new_level.append(child)

            current_level = new_level

        # Step 3: Join everything
        bpy.ops.object.select_all(action='DESELECT')
        for obj in all_objects:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = all_objects[0]
        bpy.ops.object.join()
        joined = bpy.context.active_object

        # Step 4: Voxel remesh for manifold mesh (3D printable)
        remesh = joined.modifiers.new(name="Remesh", type='REMESH')
        remesh.mode = 'VOXEL'
        remesh.voxel_size = 0.05
        remesh.use_smooth_shade = True
        bpy.ops.object.modifier_apply(modifier="Remesh")

        # Save reference
        self.obj = joined
        self.obj.name = f"LAJFI_{self.name}"
        self.obj.location = Vector(self.position)

        # Spawn animation
        self.animate_spawn()

        return self.obj

    def animate_spawn(self):
        """Spawn animation: grow from nothing with bounce."""
        if not self.obj:
            return

        obj = self.obj
        obj.scale = (0.01, 0.01, 0.01)
        step = [0]

        def animate_step():
            if obj.name not in bpy.data.objects:
                return None

            step[0] += 1

            if step[0] <= 6:
                # Phase 1: Grow with overshoot
                progress = step[0] / 6.0
                size = 0.01 + progress * 1.19  # Grow to 1.2
                obj.scale = (size, size, size)
                return 0.04

            elif step[0] <= 10:
                # Phase 2: Settle back to 1.0
                progress = (step[0] - 6) / 4.0
                size = 1.2 - progress * 0.2  # Shrink to 1.0
                obj.scale = (size, size, size)
                return 0.04

            else:
                obj.scale = (1.0, 1.0, 1.0)
                return None

        bpy.app.timers.register(animate_step, first_interval=0.02)

    def animate_death(self):
        """Death animation: flatten like a pancake, then vanish."""
        if not self.obj:
            return

        # Create a ghost copy
        ghost_mesh = self.obj.data.copy()
        ghost = bpy.data.objects.new(f"GHOST_{self.name}", ghost_mesh)
        bpy.context.collection.objects.link(ghost)
        ghost.location = self.obj.location.copy()
        start_z = ghost.location.z
        ghost.rotation_euler = self.obj.rotation_euler.copy()

        # Animation state
        step = [0]

        def animate_step():
            # Check if ghost still exists
            if ghost.name not in bpy.data.objects:
                return None

            step[0] += 1

            if step[0] <= 6:
                # Phase 1: Flatten (6 steps)
                progress = step[0] / 6.0
                ghost.scale = (
                    1.0 + progress * 0.8,   # X grows to 1.8
                    1.0 + progress * 0.8,   # Y grows to 1.8
                    1.0 - progress * 0.98   # Z shrinks to 0.02
                )
                ghost.location.z = start_z - progress * 0.3
                return 0.05  # Next step in 50ms

            elif step[0] <= 10:
                # Phase 2: Shrink to nothing (4 steps)
                progress = (step[0] - 6) / 4.0
                size = 1.8 * (1.0 - progress)
                ghost.scale = (size, size, 0.02 * (1.0 - progress))
                return 0.05

            else:
                # Done - remove ghost
                if ghost.name in bpy.data.objects:
                    bpy.data.objects.remove(ghost, do_unlink=True)
                return None

        # Start animation
        bpy.app.timers.register(animate_step, first_interval=0.03)

    def update(self):
        """Tick. Age, consume energy, decrease cooldown."""
        self.age += 1
        self.energy -= IDLE_COST  # Existing costs energy

        if self.mating_cooldown > 0:
            self.mating_cooldown -= 1

    def move_towards(self, target_pos):
        """Move towards target. Costs energy."""
        if not self.obj:
            return

        direction = Vector(target_pos) - Vector(self.position)
        direction.z *= 0.2  # Limit vertical movement

        if direction.length > 0.1:
            direction.normalize()
            speed = self.dna['speed']
            self.obj.location += direction * speed
            self.position = list(self.obj.location)
            self.energy -= MOVEMENT_COST

        self._clamp_to_world()

    def move_random(self):
        """Wander randomly. Half cost."""
        if not self.obj:
            return

        direction = Vector([random.uniform(-1, 1) for _ in range(3)])
        direction.z *= 0.1  # Almost no vertical

        if direction.length > 0:
            direction.normalize()
            self.obj.location += direction * self.dna['speed'] * 0.5
            self.position = list(self.obj.location)
            self.energy -= MOVEMENT_COST * 0.5

        self._clamp_to_world()

    def _clamp_to_world(self):
        """Keep within boundaries."""
        if not self.obj:
            return

        boundary = WORLD_SIZE / 2 - 2
        changed = False

        for i in range(2):  # x and y
            if self.position[i] > boundary:
                self.position[i] = boundary
                changed = True
            elif self.position[i] < -boundary:
                self.position[i] = -boundary
                changed = True

        # z near floor
        if self.position[2] < 0.5:
            self.position[2] = 0.5
            changed = True
        elif self.position[2] > 3:
            self.position[2] = 3
            changed = True

        if changed:
            self.obj.location = Vector(self.position)

    def eat(self, plant):
        """Eat plant."""
        self.energy += plant.energy
        self.meals_eaten += 1

    def get_strength(self):
        """Strength for combat. Energy + complexity."""
        base = self.energy * 0.5
        complexity_bonus = self.dna['fractal_levels'] * 5
        size_bonus = self.dna['fractal_children'] * 2
        return base + complexity_bonus + size_bonus

    def attack(self, prey):
        """Attack. Costs energy. Returns True if won."""
        self.energy -= ATTACK_COST

        my_strength = self.get_strength()
        their_strength = prey.get_strength()

        # Randomness so weaker can win sometimes
        my_roll = my_strength * random.uniform(0.8, 1.2)
        their_roll = their_strength * random.uniform(0.6, 1.4)

        return my_roll > their_roll

    def devour(self, victim):
        """Eat defeated prey. Gain 70% of their energy."""
        energy_gained = victim.energy * KILL_ENERGY_GAIN
        self.energy += energy_gained
        self.meals_eaten += 1
        return energy_gained

    def can_mate(self):
        """Can reproduce? Enough energy, no cooldown, not newborn."""
        return (
            self.energy >= MATING_ENERGY and
            self.mating_cooldown == 0 and
            self.age > 20
        )

    def mate_with(self, partner):
        """
        Reproduce. Both pay energy. Child gets mixed DNA.

        Args:
            partner: The other creature

        Returns:
            TriadCreature: The offspring
        """
        # Both pay
        self.energy -= MATING_COST
        partner.energy -= MATING_COST
        self.mating_cooldown = 50
        partner.mating_cooldown = 50

        # Mix DNA and mutate
        child_dna = combine_dna(self.dna, partner.dna)
        child_dna = mutate_dna(child_dna)

        # Child born between parents
        child_pos = [
            (self.position[0] + partner.position[0]) / 2 + random.uniform(-1, 1),
            (self.position[1] + partner.position[1]) / 2 + random.uniform(-1, 1),
            1.0
        ]

        child = TriadCreature(
            dna=child_dna,
            position=child_pos,
            parents=[self.name, partner.name]
        )
        child.generation = max(self.generation, partner.generation) + 1

        # Statistics
        self.children_count += 1
        partner.children_count += 1

        return child

    def is_dead(self):
        """Dead? Energy below threshold."""
        return self.energy <= STARVATION_THRESHOLD

    def destroy(self):
        """Remove from scene."""
        if self.obj:
            bpy.data.objects.remove(self.obj, do_unlink=True)
