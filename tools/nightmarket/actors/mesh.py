"""Closed surface primitives for the characters (metres, Y up)."""

import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.interpolate import make_interp_spline
from ..mdl import write_model

ROOT = Path(__file__).resolve().parents[3]
PREFIX = "NightMarket/Actors"
OUT = ROOT / "assets" / PREFIX
TAU = np.pi * 2


def unit(v):
    v = np.asarray(v, dtype=float)
    return v / np.maximum(np.linalg.norm(v, axis=-1, keepdims=True), 1e-15)


def rgb(hexcode):
    return np.array(list(bytes.fromhex(hexcode)), dtype=float)


def mix(a, b, t):
    return np.asarray(a) + (np.asarray(b) - np.asarray(a)) * np.asarray(t)


def smooth(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def turn_y(degrees):
    s, c = np.sin(np.radians(degrees)), np.cos(np.radians(degrees))
    return np.array(((c, 0, s), (0, 1, 0), (-s, 0, c)))


def turn_x(degrees):
    s, c = np.sin(np.radians(degrees)), np.cos(np.radians(degrees))
    return np.array(((1, 0, 0), (0, c, -s), (0, s, c)))


def frame(direction, across=(1, 0, 0)):
    """Columns are local cross-section X, Y, and axial Z."""
    n = unit(direction)
    if abs(np.dot(n, unit(across))) > 0.994:
        across = (0, 0, 1) if abs(n[2]) < 0.96 else (0, 1, 0)
    x = unit(np.asarray(across) - n * np.dot(n, across))
    return np.column_stack((x, np.cross(n, x), n))


def curve(points, count):
    points = np.asarray(points, dtype=float)
    t = np.r_[0, np.cumsum(np.linalg.norm(np.diff(points, axis=0), axis=1))]
    return make_interp_spline(t / t[-1], points, k=min(3, len(points) - 1))(np.linspace(0, 1, count))


def normals_for(p, f):
    a, b, c = p[f].transpose(1, 0, 2)
    fn = unit(np.cross(b - a, c - a))
    out = np.zeros_like(p)
    for n, (v, w, q) in enumerate(((a, b, c), (b, c, a), (c, a, b))):
        ang = np.arccos(np.clip((unit(w - v) * unit(q - v)).sum(1), -1, 1))
        np.add.at(out, f[:, n], fn * ang[:, None])
    return unit(out)


class Part:
    def __init__(self, name):
        self.name = name
        self.surfaces = defaultdict(list)
        self.solids = 0

    def add(self, points, faces, color, finish=(0.74, 0), surface="Finish", normals=None):
        p, f = np.asarray(points, dtype=float), np.asarray(faces, dtype=np.int32)
        a, b, c = p[f].transpose(1, 0, 2)
        volume6 = ((a - p.mean(0)) * np.cross(b - a, c - a)).sum()
        if abs(volume6) < 1e-15:
            raise ValueError(f"{self.name}: degenerate solid")
        if volume6 < 0:
            f = f[:, ::-1]
        # Validate the authored topology before joining disconnected solid pieces for a draw.
        edges = np.concatenate((f[:, :2], f[:, 1:], f[:, [2, 0]]))
        codes = edges.min(1).astype("int64") * len(p) + edges.max(1)
        _, groups, uses = np.unique(codes, return_inverse=True, return_counts=True)
        winding = np.bincount(groups, weights=np.sign(edges[:, 0] - edges[:, 1]))
        if not np.all(uses == 2) or np.any(winding):
            raise ValueError(f"{self.name}: open, non-manifold, or inconsistently wound surface")
        if normals is None:
            normals = normals_for(p, f)
        if callable(color):
            color = color(p)
        if isinstance(color, str):
            color = rgb(color)
        colors = np.round(np.clip(np.broadcast_to(color, p.shape), 0, 255)).astype("uint8")
        uv = np.broadcast_to(finish, (len(p), 2))
        self.surfaces[surface].append((p, f, normals, colors, uv))
        self.solids += 1

    def write(self, root):
        verts, inds, geoms = [], [], []
        mats = []
        positions = []
        for name, chunks in self.surfaces.items():
            start, first = len(inds), len(verts)
            for p, f, n, color, uv in chunks:
                positions.append(p)
                inds.extend((f + len(verts)).ravel().tolist())
                verts.extend(
                    (*v, *normal, *col, 255, *st)
                    for v, normal, col, st in zip(p, n, color, uv)
                )
            sub = np.array([v[:3] for v in verts[first:]])
            geoms.append((start, len(inds) - start, (sub.min(0) + sub.max(0)) / 2))
            mats.append(f"{PREFIX}/Materials/{name}.xml")
        write_model(OUT / "Meshes" / (self.name + ".mdl"), verts, inds, geoms, colored=True)
        node = ET.SubElement(root, "node")
        attr(node, "Name", self.name)
        sm = ET.SubElement(node, "component", type="StaticModel")
        attr(sm, "Model", f"Model;{PREFIX}/Meshes/{self.name}.mdl")
        attr(sm, "Material", "Material;" + ";".join(mats))
        attr(sm, "Cast Shadows", "true")
        print(
            f"  {self.name:22} {len(verts):6} vertices  {len(inds) // 3:6} triangles  {self.solids:3} closed solids"
        )
        return np.concatenate(positions)


def attr(parent, key, value):
    ET.SubElement(parent, "attribute", name=key, value=value)


def write_actor(name, parts):
    root = ET.Element("node")
    attr(root, "Name", name)
    print(name)
    positions = np.concatenate([p.write(root) for p in parts])
    ET.indent(root, space="  ")
    ET.ElementTree(root).write(OUT / f"{name}.xml", encoding="utf-8", xml_declaration=True)
    print("  local bounds (m):", positions.min(0).round(5), positions.max(0).round(5))


def loft(part, rings, color, finish=(0.74, 0), surface="Finish", transform=None, ring_colors=None):
    """Closed caps, shared edges, and no duplicate vertices at the radial seam."""
    rings = np.asarray(rings)
    m, n, _ = rings.shape
    p = np.concatenate((rings.reshape(-1, 3), [rings[0].mean(0), rings[-1].mean(0)]))
    if transform is not None:
        p = transform(p)
    ids = np.arange(m * n).reshape(m, n)
    a, b = ids[:-1].ravel(), np.roll(ids[:-1], -1, axis=1).ravel()
    c, d = b + n, a + n
    f = np.concatenate(
        (
            np.stack((a, b, c), 1),
            np.stack((a, c, d), 1),
            np.stack((ids[0], np.full(n, m * n), np.roll(ids[0], -1)), 1),
            np.stack((ids[-1], np.roll(ids[-1], -1), np.full(n, m * n + 1)), 1),
        )
    )
    if ring_colors is not None:
        cs = np.broadcast_to(ring_colors, rings.shape)
        color = np.concatenate((cs.reshape(-1, 3), [cs[0].mean(0), cs[-1].mean(0)]))
    part.add(p, f, color, finish, surface)


def shell_grid(part, samples, color, finish, surface="Finish", loop=False):
    """A fitted panel with solid thickness, or a belt closed around its circumference."""
    top, bottom = samples
    m, n, _ = top.shape
    pos = np.concatenate((top.reshape(-1, 3), bottom.reshape(-1, 3)))
    ids = np.arange(m * n).reshape(m, n)
    end = m * n
    faces = []

    def quad(a, b, c, d):
        faces.extend([[a, b, c], [a, c, d]])

    for i in range(m - 1):
        for j in range(n if loop else n - 1):
            k = (j + 1) % n
            a, b, c, d = ids[i, j], ids[i, k], ids[i + 1, k], ids[i + 1, j]
            quad(a, b, c, d)
            quad(d + end, c + end, b + end, a + end)
    for i in [0, m - 1]:
        for j in range(n if loop else n - 1):
            a, b = ids[i, j], ids[i, (j + 1) % n]
            if i == 0:
                a, b = b, a
            quad(a, b, b + end, a + end)
    if not loop:
        for j in [0, n - 1]:
            for i in range(m - 1):
                a, b = ids[i, j], ids[i + 1, j]
                if j == n - 1:
                    a, b = b, a
                quad(a, b, b + end, a + end)
    part.add(pos, faces, color, finish, surface)


def path_tube(
    part,
    path,
    radii,
    color,
    finish=(0.74, 0),
    sides=12,
    *,
    across=(1, 0, 0),
    surface="Finish",
    transform=None,
    ring_colors=None,
):
    path = np.asarray(path, dtype=float)
    radii = np.asarray(radii)
    if radii.ndim == 1 and len(radii) == len(path):
        radii = radii[:, None]
    radii = np.broadcast_to(radii, (len(path), 2))
    dirs = unit(np.gradient(path, axis=0))
    phi = np.arange(sides) * TAU / sides
    rings = []
    for center, tangent, (rx, ry) in zip(path, dirs, radii):
        f = frame(tangent, across)
        # Parallel transport handles rods and bent wire without sudden rim flips.
        across = f[:, 0]
        rings.append(center + np.outer(np.cos(phi) * rx, f[:, 0]) + np.outer(np.sin(phi) * ry, f[:, 1]))
    loft(part, rings, color, finish, surface, transform=transform, ring_colors=ring_colors)


def cable(part, points, radius, color, finish=(0.7, 0.05), *, count=18, sides=9, **kw):
    path_tube(part, curve(points, count), radius, color, finish, sides, **kw)


def ellipsoid(
    part,
    center,
    size,
    color,
    finish=(0.74, 0),
    *,
    orientation=None,
    segments=24,
    bands=14,
    surface="Finish",
    deform=None,
):
    # The two poles are single vertices, not zero-radius rings.
    t, p = np.meshgrid(np.arange(segments) * TAU / segments, np.arange(1, bands) * np.pi / bands)
    q = np.concatenate(
        (
            np.stack((np.cos(t) * np.sin(p), np.cos(p), np.sin(t) * np.sin(p)), -1).reshape(-1, 3),
            [[0, 1, 0], [0, -1, 0]],
        )
    )
    n0, n1 = len(q) - 2, len(q) - 1
    ids = np.arange(n0).reshape(-1, segments)
    a, b = ids[:-1].ravel(), np.roll(ids[:-1], -1, axis=1).ravel()
    f = np.concatenate(
        (
            np.stack((a, b, b + segments), 1),
            np.stack((a, b + segments, a + segments), 1),
            np.stack((ids[0], np.full(segments, n0), np.roll(ids[0], -1)), 1),
            np.stack((ids[-1], np.roll(ids[-1], -1), np.full(segments, n1)), 1),
        )
    )
    q = q if deform is None else deform(q.copy())
    p = q * size
    if orientation is not None:
        p = p @ np.asarray(orientation).T
    part.add(p + center, f, color, finish, surface)


def rect_ring(rx, rz, r, steps):
    r = min(r, rx * 0.96, rz * 0.96)
    rim = []
    for (sx, sz), a in zip(((1, 1), (-1, 1), (-1, -1), (1, -1)), range(4)):
        th = (a + np.linspace(0, 1, steps)) * np.pi / 2
        rim.extend(np.stack((sx * (rx - r) + r * np.cos(th), sz * (rz - r) + r * np.sin(th)), 1))
    return np.asarray(rim)


def box(
    part,
    center,
    size,
    color,
    bevel=0.003,
    finish=(0.74, 0),
    *,
    corner=None,
    transform=None,
    surface="Finish",
    steps=4,
):
    x, y, z = np.asarray(size) / 2
    b = min(bevel, x * 0.83, y * 0.83, z * 0.83)
    r = min(corner if corner is not None else max(b * 1.75, 0.001), x * 0.85, z * 0.85)
    # Extra coplanar perimeter keeps large planar faces flat right up to their bevel.
    rings = []
    for h, inset in (
        (-y, b * 1.10),
        (-y, b),
        (-y + 0.293 * b, 0.293 * b),
        (-y + b, 0),
        (y - b, 0),
        (y - 0.293 * b, 0.293 * b),
        (y, b),
        (y, b * 1.10),
    ):
        ring = rect_ring(x - inset, z - inset, max(0.08 * r, r - inset), steps)
        rings.append(np.column_stack((ring[:, 0], np.full(len(ring), h), ring[:, 1])) + center)
    loft(part, rings, color, finish, surface, transform=transform)


def circular_band(part, center, axis, profile, color, finish, *, sides=20, across=(1, 0, 0), transform=None):
    """A closed stepped axle or lens barrel: profile is [(axial offset, radius), ...]."""
    f = frame(axis, across)
    angle = np.arange(sides) * TAU / sides
    rings = [
        np.asarray(center)
        + off * f[:, 2]
        + r * (np.outer(np.cos(angle), f[:, 0]) + np.outer(np.sin(angle), f[:, 1]))
        for off, r in profile
    ]
    loft(part, rings, color, finish, transform=transform)
