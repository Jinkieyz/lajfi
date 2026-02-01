# plant.py
# Plants. Simple green spheres. Respawn when eaten.
# Without plants, everyone starves.

import bpy
import random

from .config import WORLD_SIZE, PLANT_ENERGY


class Plant:
    """
    Food source. Has position, energy, and mesh.

    Plants are simple icospheres that provide energy when eaten.
    They slowly gain more energy as they age.
    """

    __slots__ = ['position', 'energy', 'obj', 'age']  # Save memory

    def __init__(self, position=None):
        """
        Create plant at random position if none specified.

        Args:
            position: Optional [x, y, z] coordinates
        """
        self.position = position or [
            random.uniform(-WORLD_SIZE/2 + 2, WORLD_SIZE/2 - 2),
            random.uniform(-WORLD_SIZE/2 + 2, WORLD_SIZE/2 - 2),
            0.3  # Just above floor
        ]
        self.energy = PLANT_ENERGY
        self.obj = None
        self.age = 0

    def build_mesh(self):
        """Create simple sphere mesh."""
        bpy.ops.mesh.primitive_ico_sphere_add(
            subdivisions=2,
            radius=0.3,
            location=self.position
        )
        self.obj = bpy.context.active_object
        self.obj.name = "Plant"

    def update(self):
        """Tick. Age and grow slightly."""
        self.age += 1
        if self.age % 30 == 0 and self.energy < PLANT_ENERGY * 1.5:
            self.energy += 3  # Older plants give more

    def destroy(self):
        """Remove from scene."""
        if self.obj:
            bpy.data.objects.remove(self.obj, do_unlink=True)
            self.obj = None
