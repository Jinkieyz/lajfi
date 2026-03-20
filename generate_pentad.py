#!/usr/bin/env python3
"""
generate_pentad.py - Generate PENTAD creatures (5 Gielis segments)

PENTAD extends TRIAD by using 5 overlapping Gielis supershapes instead of 3.
This creates more complex, asymmetric organic forms with richer surface detail.

Usage:
    blender --background --python generate_pentad.py -- --count 10
    blender --python generate_pentad.py -- --count 1 --screenshot
"""

import bpy
import sys
import os
import random
import math
from datetime import datetime
from mathutils import Vector

# Add lajfi to path
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

from lajfi.gielis import create_gielis_mesh
from lajfi.config import MIN_FRACTAL_LEVELS, MAX_FRACTAL_LEVELS, MIN_CHILDREN, MAX_CHILDREN

# PENTAD configuration - 5 segments instead of 3
PENTAD_GENES = ['lajfi_1', 'lajfi_2', 'lajfi_3', 'lajfi_4', 'lajfi_5']

OUTPUT_DIR = os.path.join(script_dir, 'output', 'pentad')


def random_gielis_gene():
    """Generate random Gielis parameters for one supershape."""
    return {
        'm1': random.randint(3, 14),
        'm2': random.randint(2, 12),
        'n1': random.uniform(0.08, 0.9),
        'n2': random.uniform(0.5, 3.5),
        'n3': random.uniform(0.5, 3.5),
        'n1b': random.uniform(0.1, 0.95),
        'n2b': random.uniform(0.4, 3.2),
        'n3b': random.uniform(0.4, 3.2),
    }


def random_pentad_dna():
    """Create DNA for a PENTAD creature (5 Gielis genes + fractal settings)."""
    dna = {}
    for gene in PENTAD_GENES:
        dna[gene] = random_gielis_gene()

    dna['fractal_levels'] = random.randint(MIN_FRACTAL_LEVELS, MAX_FRACTAL_LEVELS)
    dna['fractal_children'] = random.randint(MIN_CHILDREN, MAX_CHILDREN)
    dna['scale_factor'] = random.uniform(0.45, 0.70)

    return dna


def generate_name():
    """Generate Swedish-style name (consonant-vowel pattern)."""
    vowels = "aeiou"
    consonants = "bdfgklmnprstvz"
    return ''.join(
        random.choice(consonants if i % 2 == 0 else vowels)
        for i in range(4)
    ).upper()


def build_pentad_mesh(dna, name, resolution=20):
    """
    Build a PENTAD creature from DNA.

    Five Gielis forms are merged together, then fractal outgrowths added,
    then the whole thing is voxel-remeshed for a manifold (3D printable) mesh.
    """
    all_objects = []
    segment_positions = []
    segment_scales = []

    # Build 5 Gielis segments
    for i, key in enumerate(PENTAD_GENES):
        params = dna[key]
        scale = random.uniform(0.5, 0.85)

        if i == 0:
            loc = (0, 0, 0)
        else:
            # Attach to a random previous segment
            attach_to = random.randint(0, i - 1)
            parent_pos = segment_positions[attach_to]
            parent_scale = segment_scales[attach_to]

            angle_h = random.uniform(0, 2 * math.pi)
            angle_v = random.uniform(-0.7, 0.7)
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

    # Join base segments
    bpy.ops.object.select_all(action='DESELECT')
    for obj in all_objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = all_objects[0]
    bpy.ops.object.join()
    base = bpy.context.active_object

    # Add fractal outgrowths
    current_level = [base]
    current_scale = 1.0
    all_objects = [base]

    for level in range(1, dna['fractal_levels'] + 1):
        current_scale *= dna['scale_factor']
        level_res = max(10, resolution // (level + 1))
        new_level = []

        for parent in current_level:
            mesh = parent.data
            num_verts = len(mesh.vertices)

            step = max(1, num_verts // dna['fractal_children'])
            indices = list(range(0, num_verts, step))[:dna['fractal_children']]

            for idx in indices:
                vert = mesh.vertices[idx]
                pos = parent.matrix_world @ vert.co
                normal = vert.co.normalized()

                gene_key = random.choice(PENTAD_GENES)
                params = dna[gene_key]

                direction = Vector([
                    normal.x + random.uniform(-0.3, 0.3),
                    normal.y + random.uniform(-0.3, 0.3),
                    normal.z + random.uniform(-0.2, 0.2)
                ]).normalized()

                overlap = current_scale * 0.3
                child_pos = (
                    pos.x + direction.x * overlap,
                    pos.y + direction.y * overlap,
                    pos.z + direction.z * overlap
                )

                child_scale = current_scale * random.uniform(0.85, 1.15)

                child = create_gielis_mesh(
                    params, resolution=level_res,
                    scale=child_scale, location=child_pos
                )
                all_objects.append(child)
                new_level.append(child)

        current_level = new_level

    # Join everything
    bpy.ops.object.select_all(action='DESELECT')
    for obj in all_objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = all_objects[0]
    bpy.ops.object.join()
    joined = bpy.context.active_object

    # Voxel remesh for manifold mesh
    remesh = joined.modifiers.new(name="Remesh", type='REMESH')
    remesh.mode = 'VOXEL'
    remesh.voxel_size = 0.05
    remesh.use_smooth_shade = True
    bpy.ops.object.modifier_apply(modifier="Remesh")

    joined.name = f"pentad_{name}"
    return joined


def setup_scene():
    """Clear scene and set up lighting for screenshots."""
    # Clear existing objects
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

    # Add light
    bpy.ops.object.light_add(type='SUN', location=(5, 5, 10))
    sun = bpy.context.active_object
    sun.data.energy = 3

    # Add camera (zoomed out to see whole creature)
    bpy.ops.object.camera_add(location=(8, -8, 6))
    camera = bpy.context.active_object
    camera.rotation_euler = (math.radians(55), 0, math.radians(45))
    bpy.context.scene.camera = camera

    # Add fill light
    bpy.ops.object.light_add(type='AREA', location=(-4, 4, 5))
    fill = bpy.context.active_object
    fill.data.energy = 100


def export_stl(obj, output_dir, name):
    """Export object as STL file."""
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"pentad_{name}_gen1_{timestamp}.stl"
    filepath = os.path.join(output_dir, filename)

    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    bpy.ops.wm.stl_export(
        filepath=filepath,
        export_selected_objects=True,
        ascii_format=False
    )

    return filepath


def render_screenshot(output_dir, name):
    """Render a screenshot of the current view."""
    os.makedirs(output_dir, exist_ok=True)

    # Set render settings
    bpy.context.scene.render.engine = 'BLENDER_EEVEE'
    bpy.context.scene.render.resolution_x = 1920
    bpy.context.scene.render.resolution_y = 1080
    bpy.context.scene.render.film_transparent = True

    filepath = os.path.join(output_dir, f"pentad_{name}.png")
    bpy.context.scene.render.filepath = filepath
    bpy.ops.render.render(write_still=True)

    return filepath


def main():
    # Parse arguments after --
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        argv = []

    count = 1
    screenshot = False

    i = 0
    while i < len(argv):
        if argv[i] == "--count" and i + 1 < len(argv):
            count = int(argv[i + 1])
            i += 2
        elif argv[i] == "--screenshot":
            screenshot = True
            i += 1
        else:
            i += 1

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print(f"\n=== Generating {count} PENTAD creature(s) ===\n")

    for n in range(count):
        setup_scene()

        name = generate_name()
        dna = random_pentad_dna()

        print(f"[{n+1}/{count}] Creating pentad_{name}...")

        obj = build_pentad_mesh(dna, name)

        # Export STL
        stl_path = export_stl(obj, OUTPUT_DIR, name)
        print(f"  Exported: {stl_path}")

        # Take screenshot if requested
        if screenshot:
            img_path = render_screenshot(OUTPUT_DIR, name)
            print(f"  Screenshot: {img_path}")

    print(f"\n=== Done! {count} PENTAD creature(s) saved to {OUTPUT_DIR} ===\n")


if __name__ == "__main__":
    main()
