"""Procedural modular miniature tree for D&D terrain (28 mm scale).

Generates two printable STLs:
  tree_bottom.stl  - stand, roots and trunk, cut at the top; pin socket
                     + 2 pockets for 5x2 mm magnets
  tree_crown.stl   - bare branching crown with matching pin and magnet
                     pockets (printed upside down)

Geometry is mm; assembled height ~87 mm.
"""

import math
import random

import numpy as np
import trimesh

rng = random.Random(7)
nprng = np.random.default_rng(7)

SEG = 20  # radial segments per tube ring

# ------------------------------------------------------------------ parameters
BASE_R     = 18.0   # stand radius
BASE_T     = 3.0    # stand thickness
TOP_H      = 32.0   # cut plane of the lower half

SHOULDER_R = 10.5   # radius of the sawn top
PIN_R      = 2.00   # printed pin radius
PIN_HOLE_R = 2.15   # socket -> 0.15 mm/side clearance
PIN_LEN    = 6.5    # pin protrusion
PIN_DEPTH  = 8.0    # socket depth
UNDER_T    = 3.0    # crown base slab thickness
CROWN_H    = 50.0   # crown height above the cut plane

MAG_R      = 5.75   # magnet pocket centre radius
MAG_HOLE_R = 2.70   # for 5x2 mm magnets
MAG_DEPTH  = 2.2    # for 2 mm magnets

# --------------------------------------------------------------------- helpers

def frame_chain(pts):
    n = len(pts)
    tang = np.zeros((n, 3))
    for i in range(n):
        d = pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]
        L = np.linalg.norm(d)
        tang[i] = d / L if L > 1e-9 else np.array([0.0, 0.0, 1.0])
    u = np.zeros((n, 3))
    ref = np.array([1.0, 0.0, 0.0])
    if abs(tang[0].dot(ref)) > 0.9:
        ref = np.array([0.0, 1.0, 0.0])
    u[0] = ref - tang[0] * ref.dot(tang[0])
    u[0] /= np.linalg.norm(u[0])
    for i in range(1, n):
        u[i] = u[i - 1] - tang[i] * u[i - 1].dot(tang[i])
        L = np.linalg.norm(u[i])
        u[i] = u[i] / L if L > 1e-9 else u[i - 1]
    v = np.array([np.cross(tang[i], u[i]) for i in range(n)])
    return tang, u, v


def tube(pts, radii, ridge=0.07, ridges=7, seed=0):
    """Bark-textured capped tube through pts with per-point radius."""
    pts = np.asarray(pts, float)
    radii = np.asarray(radii, float)
    n = len(pts)
    tang, u, v = frame_chain(pts)
    phase = (seed * 1.7) % (2 * math.pi)
    ang = np.linspace(0, 2 * math.pi, SEG, endpoint=False)

    rings = []
    for i in range(n):
        wob = 1.0 + 0.03 * math.sin(2 * math.pi * i / 3.7 + seed * 0.3)
        rr = radii[i] * wob * (
            1.0 + ridge * np.sin(ang * ridges + phase + i * 0.15)
            + 0.5 * ridge * np.sin(ang * 3 + phase * 1.7)
        )
        ring = (pts[i] + np.outer(rr * np.cos(ang), u[i])
                + np.outer(rr * np.sin(ang), v[i]))
        rings.append(ring)
    verts = np.stack(rings).reshape(-1, 3)
    c_start = len(verts)
    c_end = len(verts) + 1
    verts = np.vstack([verts, pts[0], pts[-1]])

    faces = []
    for i in range(n - 1):
        for j in range(SEG):
            a = SEG * i + j
            b = SEG * i + (j + 1) % SEG
            c = SEG * (i + 1) + j
            d = SEG * (i + 1) + (j + 1) % SEG
            faces.append((a, b, d))
            faces.append((a, d, c))
    for j in range(SEG):
        faces.append((j, c_start, (j + 1) % SEG))
        j2 = SEG * (n - 1) + j
        faces.append((j2, SEG * (n - 1) + (j + 1) % SEG, c_end))
    mesh = trimesh.Trimesh(vertices=verts, faces=faces, process=True)
    if mesh.volume < 0:
        mesh.invert()
    return mesh


def cylinder(r, z0, z1, cx=0.0, cy=0.0, seg=48):
    return trimesh.creation.cylinder(
        radius=r, height=abs(z1 - z0), sections=seg,
        transform=trimesh.transformations.translation_matrix([cx, cy, (z0 + z1) / 2.0]))

# ------------------------------------------------------------- branch growth

def grow_branch(p0, direction, length, r0, r1, segs=8, curve=0.15, grav=-0.02):
    d = np.asarray(direction, float)
    d = d / np.linalg.norm(d)
    pts = [np.asarray(p0, float)]
    step = length / segs
    for _ in range(segs):
        d = d + np.array([rng.uniform(-curve, curve),
                          rng.uniform(-curve, curve),
                          grav / segs])
        L = np.linalg.norm(d)
        d = d / L
        p = pts[-1] + d * step
        p[2] = max(p[2], 0.8)
        pts.append(p)
    return np.array(pts), np.linspace(r0, r1, segs + 1)


def grow_twig(p0, d, length, r0, r1, depth=0):
    out = []
    pts, radii = grow_branch(p0, d, length, r0, r1,
                             segs=max(4, int(length / 4)), curve=0.19, grav=-0.008)
    out.append(tube(pts, radii, seed=depth * 13 + rng.randint(0, 999)))
    n_kids = 2 if depth < 2 else 1
    for _ in range(n_kids):
        if rng.random() < 0.85:
            i = int(rng.uniform(0.3, 0.72) * (len(pts) - 2)) + 1
            nd = pts[i] - pts[i - 2]
            nd = nd + np.array([rng.uniform(-0.9, 0.9), rng.uniform(-0.9, 0.9),
                                rng.uniform(0.6, 1.4)])
            L = length * rng.uniform(0.38, 0.6) * (0.85 ** depth)
            r = radii[i] * 0.7
            if L > 3.5 and r > 0.95:
                out += grow_twig(pts[i], nd, L, r, max(0.95, r * 0.45), depth + 1)
    return out

# --------------------------------------------------------------- bottom half

def build_bottom():
    meshes = [cylinder(BASE_R, 0.0, BASE_T, seg=72)]

    zs = np.linspace(0.0, 26.5, 22)
    pts = []
    rad = []
    for z in zs:
        t = z / 26.5
        r = (6.3 + 0.9 * math.exp(-(z / 4.0) ** 2)) * (1 - 0.12 * t)
        r *= 1.0 + 0.05 * math.sin(z / 6.5)
        rad.append(max(4.0, r))
        pts.append([0.35 * math.sin(z / 14.0), 0.3 * math.sin(z / 11.0 + 1.2), z])
    meshes.append(tube(np.array(pts), rad, ridge=0.09, ridges=8, seed=3))

    cz = np.linspace(23.5, TOP_H, 18)
    cr = []
    for z in cz:
        t = (z - 23.5) / (TOP_H - 23.5)
        cr.append(6.3 + (SHOULDER_R - 6.3) * min(1.0, (t / 0.62) ** 1.6))
    cpts = [[0.3 * math.sin(z / 14.0), 0.26 * math.sin(z / 11.0 + 1.2), z] for z in cz]
    meshes.append(tube(np.array(cpts), cr, ridge=0.04, ridges=9, seed=5))

    for k in range(6):
        a = k * math.pi / 3 + rng.uniform(-0.3, 0.3)
        z0 = rng.uniform(4, 11)
        L = rng.uniform(9, 13)
        d = np.array([math.cos(a), math.sin(a), -0.75])
        d /= np.linalg.norm(d)
        meshes += grow_twig([d[0] * 4.5, d[1] * 4.5, z0], d, L, 3.0, 1.2, depth=1)

    solid = trimesh.boolean.union(meshes, engine='manifold')
    cuts = [cylinder(PIN_HOLE_R, TOP_H - PIN_DEPTH, TOP_H + 2)]
    for ang in (math.pi / 2, 3 * math.pi / 2):
        cx, cy = math.cos(ang) * MAG_R, math.sin(ang) * MAG_R
        cuts.append(cylinder(MAG_HOLE_R, TOP_H - MAG_DEPTH, TOP_H + 2, cx, cy))
    return trimesh.boolean.difference([solid] + cuts, engine='manifold')

# ---------------------------------------------------------------- crown half

def build_crown():
    meshes = [cylinder(SHOULDER_R, 0.0, UNDER_T, seg=72),
              cylinder(PIN_R, -PIN_LEN, 0.6)]

    n = 12
    zs = np.linspace(UNDER_T - 0.5, CROWN_H, n)
    pts = []
    for i, z in enumerate(zs):
        t = i / (n - 1.0)
        pts.append([0.9 * math.sin(t * 2.1), 0.7 * math.cos(t * 1.6), z])
    pts = np.array(pts)
    radii = np.linspace(4.6, 2.3, n)
    meshes.append(tube(pts, radii, ridge=0.08, ridges=7, seed=11))

    specs = [(0.08, 68, 120, 28, 2.5, 1.0), (0.20, 205, 118, 27, 2.5, 1.0),
             (0.32, 335, 62, 25, 2.4, 1.0), (0.44, 95, 55, 23, 2.3, 0.95),
             (0.56, 250, 48, 20, 2.2, 0.95), (0.68, 30, 40, 17, 2.0, 0.9),
             (0.80, 160, 32, 13, 1.8, 0.9), (0.92, 285, 24, 10, 1.6, 0.9)]
    for f, az_deg, polar_deg, L, r0, r1 in specs:
        i = int(f * (len(pts) - 2)) + 1
        az = math.radians(az_deg + rng.uniform(-18, 18))
        polar = math.radians(max(12, polar_deg + rng.uniform(-10, 8)))
        d = np.array([math.sin(polar) * math.cos(az),
                      math.sin(polar) * math.sin(az),
                      math.cos(polar)])
        meshes += grow_twig(pts[i], d, L, r0, r1, depth=0)

    meshes += grow_twig(pts[-1], np.array([0.25, -0.3, 1.0]), 14, 2.0, 0.95, depth=0)

    solid = trimesh.boolean.union(meshes, engine='manifold')
    cuts = []
    for ang in (math.pi / 2, 3 * math.pi / 2):
        cx, cy = math.cos(ang) * MAG_R, -math.sin(ang) * MAG_R  # mirrored
        cuts.append(cylinder(MAG_HOLE_R, -0.5, MAG_DEPTH, cx, cy))
    return trimesh.boolean.difference([solid] + cuts, engine='manifold')

# ------------------------------------------------------------------- output

if __name__ == '__main__':
    parts = {'bottom': build_bottom(), 'crown': build_crown()}
    for name, m in parts.items():
        m.merge_vertices()
        m.fix_normals()
        print(f'{name}: volume {m.volume / 1000:.1f} cm3, watertight={m.is_watertight}, '
              f'extents={np.round(m.extents, 1)}')
        m.export(f'/workspace/tree/tree_{name}.stl')

    crown2 = parts['crown'].copy()
    crown2.apply_translation([0, 0, TOP_H])
    asm = trimesh.boolean.union([parts['bottom'], crown2], engine='manifold')
    print('assembled watertight:', asm.is_watertight,
          'bbox:', np.round(asm.extents, 1), 'zmax:', round(asm.bounds[1][2], 1))
