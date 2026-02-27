# world.py
# World logic. Spawning, tick loop, export.
# This is the game loop. Runs at TICK_SPEED intervals.

import bpy
import math
import random
import os
import time
from datetime import datetime

from .config import (
    OUTPUT_DIR, WORLD_SIZE, MAX_CREATURES, MAX_PLANTS,
    TICK_SPEED, EAT_RANGE, CANNIBAL_RANGE, MATING_RANGE,
    SATISFIED_ENERGY, EXPORT_INTERVAL
)
from .utils import log
from .dna import random_dna
from .creature import TriadCreature
from .plant import Plant


# Global lists. Blender timer needs access to these.
creatures = []
plants = []
last_export_time = 0
generation_record = 1


def clear_scene():
    """Clear everything in Blender."""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

    # Orphan data cleanup
    for mesh in list(bpy.data.meshes):
        if mesh.users == 0:
            bpy.data.meshes.remove(mesh)
    for mat in list(bpy.data.materials):
        if mat.users == 0:
            bpy.data.materials.remove(mat)


def setup_world():
    """Set up camera, lights, floor."""

    # Dark background
    bpy.context.scene.world.use_nodes = True
    bg = bpy.context.scene.world.node_tree.nodes.get('Background')
    if bg:
        bg.inputs['Color'].default_value = (0.02, 0.02, 0.06, 1)

    # Camera from above at angle
    bpy.ops.object.camera_add(location=(0, -30, 20))
    cam = bpy.context.active_object
    cam.rotation_euler = (math.radians(55), 0, 0)
    bpy.context.scene.camera = cam

    # Sun light
    bpy.ops.object.light_add(type='SUN', location=(10, 10, 25))
    bpy.context.active_object.data.energy = 1.5

    # Floor
    bpy.ops.mesh.primitive_plane_add(size=WORLD_SIZE, location=(0, 0, 0))
    floor = bpy.context.active_object
    floor.name = "Floor"
    mat = bpy.data.materials.new("FloorMat")
    mat.use_nodes = True
    mat.node_tree.nodes["Principled BSDF"].inputs['Base Color'].default_value = (0.05, 0.05, 0.08, 1)
    floor.data.materials.append(mat)


def spawn_creature(dna=None, position=None):
    """Spawn a creature."""
    if dna is None:
        dna = random_dna()

    c = TriadCreature(dna=dna, position=position)
    c.build_mesh()
    creatures.append(c)
    log(f"SPAWN: {c.name} - {c.dna['fractal_levels']} levels, {c.dna['fractal_children']} children")
    return c


def spawn_plant():
    """Spawn a plant."""
    p = Plant()
    p.build_mesh()
    plants.append(p)
    return p


def distance_sq(pos1, pos2):
    """Squared distance. Faster than sqrt."""
    return sum((a - b) ** 2 for a, b in zip(pos1, pos2))


def find_nearest(creature, targets):
    """Find nearest target. Returns (object, distance)."""
    if not targets:
        return None, float('inf')

    nearest = None
    min_dist_sq = float('inf')
    c_pos = creature.position

    for t in targets:
        dist_sq = distance_sq(c_pos, t.position)
        if dist_sq < min_dist_sq:
            min_dist_sq = dist_sq
            nearest = t

    return nearest, math.sqrt(min_dist_sq)


def export_champion():
    """Export best creature as STL."""
    global OUTPUT_DIR

    if not creatures:
        return

    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Best = highest generation + energy
    champion = max(creatures, key=lambda c: c.generation * 10 + c.energy)

    # Filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"lajfi_{champion.name}_gen{champion.generation}_{timestamp}.stl"
    filepath = os.path.join(OUTPUT_DIR, filename)

    # Select object
    bpy.ops.object.select_all(action='DESELECT')
    champion.obj.select_set(True)
    bpy.context.view_layer.objects.active = champion.obj

    # Export
    try:
        bpy.ops.wm.stl_export(filepath=filepath, export_selected_objects=True)
        log(f"SAVED! {champion.name} gen{champion.generation} -> {filename}")
    except Exception:
        # Fallback manual export
        import struct
        mesh = champion.obj.data
        mesh.calc_loop_triangles()
        with open(filepath, 'wb') as f:
            f.write(b'\x00' * 80)
            f.write(struct.pack('<I', len(mesh.loop_triangles)))
            for tri in mesh.loop_triangles:
                n = tri.normal
                f.write(struct.pack('<fff', n.x, n.y, n.z))
                for vi in tri.vertices:
                    v = mesh.vertices[vi].co
                    f.write(struct.pack('<fff', v.x, v.y, v.z))
                f.write(struct.pack('<H', 0))
        log(f"SAVED! {champion.name} (fallback) -> {filename}")


def tick():
    """
    Main loop. Runs every TICK_SPEED seconds.

    Behavior:
        - Satiated creatures seek mates
        - Hungry creatures eat nearest (plant or other creature)
        - Dead creatures are removed
        - Population is maintained at MAX_CREATURES
        - Best creature is exported every EXPORT_INTERVAL
    """
    global last_export_time, generation_record

    current_time = time.time()

    # Update plants
    for plant in plants:
        plant.update()

    # Spawn plants if too few
    while len(plants) < MAX_PLANTS:
        spawn_plant()

    # Handle creatures
    dead = []
    eaten_plants = []
    new_children = []
    killed = []

    for c in creatures:
        if c in killed:
            continue

        c.update()

        # Find nearest food
        nearest_plant, plant_dist = find_nearest(c, plants)
        other_creatures = [x for x in creatures if x is not c and x not in killed]
        nearest_other, other_dist = find_nearest(c, other_creatures)

        # SATIATED = mate
        if c.energy >= SATISFIED_ENERGY:
            can_breed = (
                c.can_mate() and
                len(creatures) + len(new_children) - len(killed) <= MAX_CREATURES
            )

            if can_breed:
                # Find satiated partners
                potential_mates = [
                    x for x in other_creatures
                    if x.can_mate() and x.energy >= SATISFIED_ENERGY
                ]

                if potential_mates:
                    mate, dist = find_nearest(c, potential_mates)

                    if mate and dist < MATING_RANGE:
                        # MATE
                        child = c.mate_with(mate)
                        new_children.append(child)

                        if child.generation > generation_record:
                            generation_record = child.generation

                        log(f"BABY! {c.name} + {mate.name} = {child.name} (gen {child.generation})")

                    elif mate:
                        c.move_towards(mate.position)
                else:
                    c.move_random()
            else:
                c.move_random()

        # HUNGRY = eat nearest
        else:
            target_plant = nearest_plant and (not nearest_other or plant_dist < other_dist)
            target_creature = nearest_other and (not nearest_plant or other_dist <= plant_dist)

            # Eat plant
            if target_plant and plant_dist < EAT_RANGE:
                c.eat(nearest_plant)
                eaten_plants.append(nearest_plant)
                log(f"NOM: {c.name} ate plant! E={c.energy:.0f}")

            # Eat other creature
            elif target_creature and other_dist < CANNIBAL_RANGE:
                won = c.attack(nearest_other)
                if won:
                    energy = c.devour(nearest_other)
                    killed.append(nearest_other)
                    log(f"CANNIBAL! {c.name} ate {nearest_other.name}! +{energy:.0f}")
                else:
                    log(f"FIGHT: {c.name} vs {nearest_other.name} - {nearest_other.name} won!")

            # Move towards food
            elif target_plant and nearest_plant:
                c.move_towards(nearest_plant.position)
            elif target_creature and nearest_other:
                c.move_towards(nearest_other.position)
            else:
                c.move_random()

        # Check if dead
        if c.is_dead():
            dead.append(c)

    # Add killed to dead
    for victim in killed:
        if victim not in dead:
            dead.append(victim)

    # Remove eaten plants
    for plant in eaten_plants:
        plant.destroy()
        if plant in plants:
            plants.remove(plant)

    # Add newborns
    for child in new_children:
        child.build_mesh()
        creatures.append(child)

    # Remove dead
    for c in dead:
        legacy = f"{c.children_count} kids" if c.children_count > 0 else "no kids"
        log(f"RIP: {c.name} age={c.age} gen={c.generation} ({legacy})")
        c.animate_death()
        c.destroy()
        creatures.remove(c)

    # Spawn if too few
    while len(creatures) < MAX_CREATURES:
        spawn_creature()

    # Export every 2 minutes
    if current_time - last_export_time > EXPORT_INTERVAL:
        export_champion()
        last_export_time = current_time

    # Status occasionally
    if random.random() < 0.05:
        avg_gen = sum(c.generation for c in creatures) / len(creatures) if creatures else 0
        names = ", ".join(c.name for c in creatures)
        log(f"[{len(creatures)} alive] {names} | avg gen {avg_gen:.1f} | record {generation_record}")

    return TICK_SPEED
