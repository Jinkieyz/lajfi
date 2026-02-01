# gielis.py
# Johan Gielis' superformula. I discovered it in 2025. It describes almost all organic forms.
#
# The formula (polar coordinates):
#     r = (|cos(m*theta/4)|^n2 + |sin(m*theta/4)|^n3) ^ (-1/n1)
#
# Parameters:
#     m  = symmetry (number of lobes/arms)
#     n1 = overall roundness (low = angular, high = rounded)
#     n2 = curvature of cosine term
#     n3 = curvature of sine term
#
# Reference:
#     Gielis, J. (2003). A generic geometric transformation that unifies a wide
#     range of natural and abstract shapes. American Journal of Botany, 90(3), 333-338.

import bpy
import math


def gielis_r(angle, m, n1, n2, n3):
    """
    Calculate radius at a given angle using the Gielis superformula.

    Args:
        angle: The angle in radians
        m: Symmetry parameter (number of lobes)
        n1: Overall roundness
        n2: Cosine term curvature
        n3: Sine term curvature

    Returns:
        float: The radius at the given angle
    """
    if abs(n1) < 0.001:  # Avoid division by zero
        n1 = 0.001

    t = m * angle / 4.0  # Gielis transformation
    term1 = abs(math.cos(t)) ** n2  # Cosine component
    term2 = abs(math.sin(t)) ** n3  # Sine component
    denom = term1 + term2

    if denom < 0.0001:  # Avoid zero again
        return 1.0

    # Clamp to prevent explosion
    return max(0.1, min(5.0, denom ** (-1.0 / n1)))


def create_gielis_mesh(params, resolution=24, scale=1.0, location=(0, 0, 0)):
    """
    Build a 3D mesh from Gielis parameters using spherical product.

    Two superformulas are combined:
        - One for horizontal profile (theta: 0 to 2*pi)
        - One for vertical profile (phi: 0 to pi)

    Args:
        params: Dictionary with keys m1, m2, n1, n2, n3, n1b, n2b, n3b
        resolution: Mesh resolution (higher = smoother)
        scale: Size multiplier
        location: Position tuple (x, y, z)

    Returns:
        bpy.types.Object: The created Blender mesh object
    """
    verts = []
    faces = []

    # Extract parameters
    m1, m2 = params['m1'], params['m2']  # Horizontal/vertical symmetry
    n1, n2, n3 = params['n1'], params['n2'], params['n3']  # Horizontal curves
    n1b, n2b, n3b = params['n1b'], params['n2b'], params['n3b']  # Vertical curves

    theta_steps = resolution
    phi_steps = resolution // 2

    # Build all vertices
    for j in range(phi_steps + 1):
        phi = (j / phi_steps) * math.pi  # 0 to pi

        for i in range(theta_steps):
            theta = (i / theta_steps) * 2 * math.pi  # 0 to 2*pi

            r1 = gielis_r(theta, m1, n1, n2, n3)  # Horizontal radius
            r2 = gielis_r(phi, m2, n1b, n2b, n3b)  # Vertical radius
            r = r1 * r2 * scale  # Combined radius

            # Spherical to Cartesian conversion
            x = r * math.sin(phi) * math.cos(theta) + location[0]
            y = r * math.sin(phi) * math.sin(theta) + location[1]
            z = r * math.cos(phi) + location[2]

            verts.append((x, y, z))

    # Connect into quads
    for j in range(phi_steps):
        for i in range(theta_steps):
            next_i = (i + 1) % theta_steps  # Wrap around

            v1 = j * theta_steps + i
            v2 = j * theta_steps + next_i
            v3 = (j + 1) * theta_steps + next_i
            v4 = (j + 1) * theta_steps + i

            faces.append((v1, v2, v3, v4))

    # Create Blender mesh
    mesh = bpy.data.meshes.new("Gielis")
    mesh.from_pydata(verts, [], faces)
    mesh.update()

    # Create object and link to scene
    obj = bpy.data.objects.new("Gielis", mesh)
    bpy.context.collection.objects.link(obj)

    return obj
