"""Standing mackerel tabby. The continuous skin is sculpted as a 3-D implicit field."""

import numpy as np
from .mesh import (
    TAU,
    Part,
    box,
    cable,
    circular_band,
    curve,
    ellipsoid,
    frame,
    loft,
    mix,
    path_tube,
    rect_ring,
    rgb,
    shell_grid,
    smooth,
    turn_y,
    unit,
    write_actor,
)
from scipy.ndimage import map_coordinates
from scipy.spatial import cKDTree
from skimage.measure import marching_cubes

HEAD = np.array((-0.003, 0.292, 0.183))
R = turn_y(-20)
TAIL = curve(
    [
        (0, 0.221, -0.200),
        (0.004, 0.203, -0.240),
        (0.009, 0.163, -0.253),
        (0.012, 0.116, -0.257),
        (0.014, 0.075, -0.263),
        (0.016, 0.043, -0.275),
        (0.021, 0.022, -0.298),
        (0.025, 0.014, -0.329),
        (0.024, 0.014, -0.351),
        (0.019, 0.017, -0.362),
    ],
    27,
)
TAIL_T = np.r_[0, np.cumsum(np.linalg.norm(np.diff(TAIL, axis=0), axis=1))]
TAIL_R = np.interp(
    TAIL_T / TAIL_T[-1], [0, 0.16, 0.43, 0.68, 0.86, 0.98, 1], [0.024, 0.022, 0.018, 0.015, 0.012, 0.009, 0.005]
)


def hworld(p):
    return np.asarray(p) @ R.T + HEAD


def union(a, b, k):
    return np.minimum(a, b) - np.maximum(k - np.abs(a - b), 0) ** 2 / (4 * k)


def egg(p, c, scale):
    d = (p - c) / scale
    k0 = np.sqrt((d * d).sum(-1))
    k1 = np.linalg.norm(d / scale, axis=-1)
    return np.where(k1 > 1e-9, k0 * (k0 - 1) / np.maximum(1e-12, k1), -min(scale))


def limb(p, a, b, r1, r2, width=1):
    a, b = np.asarray(a), np.asarray(b)
    ab = b - a
    t = np.clip(((p - a) * ab).sum(-1) / (ab * ab).sum(), 0, 1)
    d = p - (a + t[..., None] * ab)
    n = np.sqrt((d[..., 0] / width) ** 2 + d[..., 1] ** 2 + d[..., 2] ** 2)
    return n - mix(r1, r2, t)


def trunk(p):
    d = egg(p, (0, 0.202, -0.136), (0.073, 0.085, 0.099))
    d = union(d, egg(p, (0, 0.201, -0.041), (0.0665, 0.072, 0.129)), 0.021)
    d = union(d, egg(p, (0, 0.204, 0.051), (0.070, 0.082, 0.099)), 0.027)
    d = union(d, egg(p, (0, 0.214, 0.110), (0.058, 0.068, 0.065)), 0.022)
    return union(d, limb(p, (0, 0.234, 0.105), (-0.002, 0.282, 0.170), 0.050, 0.040, 0.95), 0.026)


def head_field(q):
    d = egg(q, (0, 0.006, 0), (0.051, 0.046, 0.054))
    d = union(d, egg(q, (0, -0.024, 0.034), (0.031, 0.021, 0.041)), 0.008)
    d = union(d, egg(q, (0, 0.000, 0.041), (0.019, 0.022, 0.036)), 0.007)
    ax = np.abs(q[..., 0])
    side = np.stack((ax, q[..., 1], q[..., 2]), -1)
    d = union(d, egg(side, (0.031, -0.007, 0.011), (0.027, 0.030, 0.037)), 0.009)
    d = union(d, egg(side, (0.029, 0.020, 0.024), (0.019, 0.015, 0.029)), 0.006)
    d = union(d, egg(side, (0.034, 0.026, -0.015), (0.022, 0.020, 0.022)), 0.008)
    d = union(d, egg(side, (0.017, -0.015, 0.049), (0.022, 0.020, 0.033)), 0.007)
    return d


def legs(p, s):
    # One rear leg carries the weight while the opposite forefoot is slightly farther forward.
    j = 0.013 * s
    hip, knee = (0.045 * s, 0.204, -0.151 + j), (0.050 * s, 0.131, -0.116 + j)
    hock, ankle = (0.056 * s, 0.073, -0.194 + j), (0.053 * s, 0.022, -0.183 + j)
    d = egg(p, (0.047 * s, 0.185, -0.151 + j), (0.039, 0.066, 0.064))
    d = union(d, limb(p, hip, knee, 0.052, 0.031, 0.70), 0.016)
    d = union(d, limb(p, knee, hock, 0.029, 0.0145, 0.77), 0.014)
    d = union(d, limb(p, hock, ankle, 0.0145, 0.0125, 0.82), 0.006)
    j = -0.013 * s
    scapula, shoulder = (0.039 * s, 0.248, 0.063 + j), (0.051 * s, 0.188, 0.106 + j)
    elbow, wrist = (0.046 * s, 0.126, 0.079 + j), (0.044 * s, 0.023, 0.108 + j)
    fore = limb(p, scapula, shoulder, 0.035, 0.030, 0.67)
    fore = union(fore, limb(p, shoulder, elbow, 0.028, 0.016, 0.83), 0.013)
    fore = union(fore, limb(p, elbow, wrist, 0.018, 0.0115, 0.80), 0.008)
    d = np.minimum(d, fore)
    for x, z, w in [(ankle[0], ankle[2], 1.03), (wrist[0], wrist[2], 0.92)]:
        paw = egg(p, (x, 0.014, z + 0.008), (0.018 * w, 0.0142, 0.025 * w))
        for i, fac in enumerate([0.83, 1, 0.98, 0.80]):
            tx = x + (i - 1.5) * 0.0084 * w
            paw = union(
                paw,
                egg(p, (tx, 0.0088, z + 0.018 + 0.012 * fac), (0.0068 * w, 0.0102 * fac, 0.014 * fac)),
                0.0020,
            )
        d = union(d, paw, 0.007)
    return d


def skin_field(p):
    d = trunk(p)
    sel = p[:, 2] > 0.105
    d[sel] = union(d[sel], head_field((p[sel] - HEAD) @ R), 0.014)
    for s in (-1, 1):
        sel = (p[:, 0] * s > -0.028) & (p[:, 2] < 0.195) & (p[:, 2] > -0.253)
        d[sel] = union(d[sel], legs(p[sel], s), 0.017)
    sel = p[:, 2] < -0.154
    pp = p[sel]
    tail = np.full(len(pp), 1.0)
    for i in range(len(TAIL) - 1):
        tail = np.minimum(tail, limb(pp, TAIL[i], TAIL[i + 1], TAIL_R[i], TAIL_R[i + 1]))
    d[sel] = union(d[sel], tail, 0.016)
    return np.maximum(d, -p[:, 1])


def pigment(p):
    """Pigment only, in anatomical space: no AO, highlights, lights, or viewing direction."""
    x, y, z = p.T
    ax = np.abs(x)
    noise = np.random.default_rng(233).normal(0, 1, (37, 37, 37))

    def fleck(freq, offset):
        return map_coordinates(noise, (p * freq + offset).T, order=3, mode="grid-wrap")

    drift = fleck((42, 38, 40), 8)
    tick = fleck((280, 265, 115), 3)
    guard = fleck((110, 102, 64), 12)
    base = np.broadcast_to(rgb("A76C43"), p.shape).copy()
    chest = np.exp(-(((z - 0.115) / 0.096) ** 2)) * (1 - smooth(0.176, 0.253, y))
    ventral = (1 - smooth(0.141, 0.202, y)) * (1 - smooth(0.055, 0.078, ax))
    base = mix(base, rgb("CDA37B"), (0.38 * chest + 0.43 * ventral).clip(0, 0.86)[:, None])
    # Irregular mackerel bars wrap around either flank, forking over the hip.
    phase = (
        z * TAU / 0.040
        + 1.65 * np.sin(y * 26 + 0.72 * np.sin(z * 36))
        + 0.7 * np.sin(z * 53 + x * 23)
        + 0.42 * np.sin(y * 89 + z * 34)
        + 0.48 * drift
        + 0.11 * tick
    )
    side = smooth(0.00, 0.94, np.cos(phase)) * smooth(0.135, 0.209, y)
    side *= (0.52 + 0.27 * smooth(0.038, 0.066, ax)) * (0.79 + 0.21 * smooth(-0.85, 0.55, guard))
    fork = (
        smooth(0.71, 0.99, np.cos(phase * 0.92 + 1.9 + 1.7 * np.sin(y * 42 + z * 14)))
        * smooth(0.115, 0.237, -z)
        * 0.45
    )
    spine = (1 - smooth(0.006, 0.017, ax)) * smooth(0.237, 0.274, y)
    stripes = np.maximum.reduce([side, fork, spine * 0.84])
    ring = smooth(0.28, 0.94, np.cos(y * TAU / 0.031 + 1.1 * np.sin(z * 38) + x * 52 + 0.37 * drift))
    stripes = np.maximum(stripes, ring * (1 - smooth(0.11, 0.183, y)) * smooth(0.016, 0.051, y) * 0.61)
    base = mix(base, rgb("775237"), stripes[:, None])
    # A slightly paler foot, without white socks.
    base = mix(base, rgb("BD936C"), ((1 - smooth(0.014, 0.049, y)) * 0.52)[:, None])
    sel = z < -0.222
    if sel.any():
        spine_samples = curve(TAIL, 150)
        cp, idx = cKDTree(spine_samples).query(p[sel])
        t = idx / (len(spine_samples) - 1)
        tr = 0.67 * smooth(0.33, 0.86, np.cos(t * TAU * 7.3 - 0.3)) + 0.3 * smooth(0.85, 0.98, t)
        tc = mix(rgb("AC784E"), rgb("755139"), tr.clip(0, 1)[:, None])
        base[sel] = mix(base[sel], tc, (1 - smooth(0.023, 0.040, cp))[:, None])
    # Forehead M, cheek streaks, pale whisker pads and chin follow the turned skull.
    q = (p - HEAD) @ R
    qx, qy, qz = np.abs(q[:, 0]), q[:, 1], q[:, 2]
    headmask = smooth(0.133, 0.179, z) * smooth(0.231, 0.268, y)
    headbase = np.broadcast_to(rgb("B57B4F"), p.shape).copy()
    jaw = (1 - smooth(-0.027, 0.003, qy)) * smooth(0.006, 0.047, qz)
    headbase = mix(headbase, rgb("E2BE90"), jaw[:, None])
    brow = smooth(0.016, 0.038, qy)
    mline = np.exp(-(((qx - (0.0065 + 0.007 * (1 + np.cos(qz * 84)) * 0.5)) / 0.0032) ** 2))
    mline += np.exp(-(((qx - (0.022 + 0.003 * np.sin(qz * 83))) / 0.0035) ** 2)) * 0.74
    a = np.exp(-(((qy - (-0.001 + 0.22 * qz + 0.005 * np.sin(qz * 70))) / 0.0035) ** 2))
    b = np.exp(-(((qy - (-0.017 + 0.19 * qz + 0.004 * np.sin(qz * 66))) / 0.0045) ** 2))
    cheek = (a * 0.65 + b * 0.51) * smooth(0.029, 0.045, qx) * (1 - smooth(0.033, 0.057, qz))
    headbase = mix(headbase, rgb("70513A"), np.clip(0.77 * mline * brow + cheek, 0, 0.86)[:, None])
    tint = 0.99 + 0.037 * guard + 0.028 * tick + 0.016 * drift
    return mix(base, headbase, headmask[:, None]) * tint[:, None]


def body(part):
    step = 0.0034
    xyz = [
        np.arange(lo, hi, step, dtype=np.float32)
        for lo, hi in [(-0.1081, 0.127), (-0.0093, 0.36), (-0.4581, 0.293)]
    ]
    vol = np.empty(tuple(map(len, xyz)), dtype=np.float32)
    for i in range(0, len(xyz[0]), 5):
        p = np.stack(np.meshgrid(xyz[0][i : i + 5], *xyz[1:], indexing="ij"), -1)
        vol[i : i + 5] = skin_field(p.reshape(-1, 3)).reshape(p.shape[:-1])
    v, f, _, _ = marching_cubes(vol, 0.0, allow_degenerate=False)
    n = unit(np.stack([map_coordinates(d, v.T, order=1) for d in np.gradient(vol)], 1))
    v = v * step + np.array([a[0] for a in xyz])
    v[:, 1] = np.maximum(v[:, 1], 0)
    part.add(v, f, pigment(v), (0.86, 0), "Coat", normals=n)

    # Closed, tapered guard-hair clumps follow the coat grain. They break the
    # silhouette in profile and respond to the same lights as the underlying fur.
    rng = np.random.default_rng(291)
    area = np.linalg.norm(np.cross(v[f[:, 1]] - v[f[:, 0]], v[f[:, 2]] - v[f[:, 0]]), axis=1)
    triangles = f[rng.choice(len(f), 26000, p=area / area.sum())]
    r, s = rng.random((2, len(triangles))); r = np.sqrt(r)
    bary = np.stack((1-r, r*(1-s), r*s), 1)[:, :, None]
    roots = (v[triangles] * bary).sum(1); ns = unit((n[triangles] * bary).sum(1))
    x, y, z = roots.T
    keep = (y > .015) & (z < .195) & ~((z > -.067) & (z < .132) & (y > .194))
    roots, ns = roots[keep], ns[keep]; x, y, z = roots.T
    leg = 1-smooth(.09, .185, y)
    flow = np.stack((.16*np.sign(x), -.43-.94*leg, -1+.86*leg), 1) + rng.normal(0,.16,roots.shape)
    flow = unit(flow-ns*(ns*flow).sum(1)[:, None]); crossflow = unit(np.cross(ns, flow))
    length = (rng.uniform(.004,.009,len(roots))*(1-.44*leg))[:,None]
    half = rng.uniform(.00034,.00084,(len(roots),1)); foot = roots-.00035*ns
    points = np.stack((foot-half*crossflow,foot+half*crossflow,foot-.0013*flow,foot+length*(flow+.37*ns)),1)
    facets = np.array([(0,1,2),(0,3,1),(1,3,2),(2,3,0)]) + 4*np.arange(len(roots))[:,None,None]
    color = pigment(roots)*rng.uniform(.88,1.12,(len(roots),1))
    colors = color[:,None,:]*np.array([.93,.99,.96,1.13])[None,:,None]
    normals = unit(np.stack((ns-.18*crossflow,ns+.18*crossflow,ns,ns-.1*flow),1))
    part.add(points.reshape(-1,3), facets.reshape(-1,3), colors.reshape(-1,3), (.91,0), "Coat", normals=normals.reshape(-1,3))


def pinna(part, s):
    # A cupped ear with a thick free rim, recessed concha, and convex furred back.
    boundary = np.array(
        [
            [-0.82, 0.04],
            [-0.55, -0.08],
            [0.10, -0.12],
            [0.72, -0.02],
            [0.91, 0.19],
            [0.89, 0.36],
            [0.72, 0.60],
            [0.49, 0.89],
            [0.35, 0.99],
            [0.25, 1.0],
            [0.15, 0.94],
            [-0.10, 0.67],
            [-0.39, 0.44],
            [-0.68, 0.25],
            [-0.81, 0.13],
        ]
    )
    b = np.repeat(boundary, 2, axis=0)
    b[::2] = 0.75 * boundary + 0.25 * np.roll(boundary, 1, axis=0)
    b[1::2] = 0.75 * boundary + 0.25 * np.roll(boundary, -1, axis=0)
    rings, cols = [], []
    for scale, depth, color in [
        (0.16, -0.017, "AD7649"),
        (0.55, -0.015, "A56C3E"),
        (0.91, -0.010, "8E5B38"),
        (1, -0.002, "80583A"),
        (1, 0.002, "9C6A47"),
        (0.92, 0.005, "BF946E"),
        (0.79, 0.0043, "C39977"),
        (0.58, -0.0007, "AE8578"),
        (0.26, -0.0038, "966F64"),
    ]:
        u, v = mix((0.03, 0.34), b, scale).T
        x = s * (0.034 + 0.029 * u + 0.008 * v)
        y = 0.028 + 0.058 * v - 0.001 * u
        z = -0.004 - 0.017 * v - 0.010 * u + depth * (1 - 0.47 * np.clip(v, 0, 1)) + 0.004 * u * u
        rings.append(hworld(np.column_stack((x, y, z))))
        c = np.broadcast_to(rgb(color), (len(u), 3)).copy()
        c = mix(c, rgb("684832"), (0.25 * smooth(0.51, 0.96, v))[:, None])
        cols.append(c)
    loft(part, rings, None, (0.84, 0), "Coat", ring_colors=cols)


def ray_hit(origin, direction, field):
    origin, direction = np.asarray(origin), unit(direction)
    lo = np.zeros(origin.shape[:-1])
    hi = lo + 0.19
    for _ in range(25):
        m = (lo + hi) * 0.5
        d = field(origin + m[..., None] * direction)
        lo, hi = np.where(d < 0, m, lo), np.where(d < 0, hi, m)
    return origin + direction * ((lo + hi) * 0.5)[..., None]


def cat_eye(part, s):
    u, v, n = frame((s * 0.49, 0.055, 0.87)).T
    u, v = unit(u + s * 0.12 * v), unit(v - s * 0.12 * u)
    origin = np.array((s * 0.015, 0.012, 0.019))
    th = np.arange(48) * TAU / 48
    shape_x = np.cos(th)
    shape_y = np.sin(th) * (1 - 0.47 * np.cos(th) ** 2)
    radii = np.r_[0.19, 0.91, 1, np.linspace(0.975, 0.03, 21)]
    dx, dy = radii[:, None] * shape_x, radii[:, None] * shape_y
    start = origin + dx[..., None] * 0.0128 * u + dy[..., None] * 0.0075 * v
    skull = ray_hit(start, n, head_field)
    off = 0.0004 + 0.0021 * (1 - radii * radii)
    off[:2] = -0.002
    rings = hworld(skull + off[:, None, None] * n)
    iris = (
        mix(rgb("A89A69"), rgb("CDC193"), (0.23 + 0.18 * np.sin(th * 19 + np.sin(th * 11)))[None, :, None])
        + dx[..., None] * 0
    )
    iris = mix(iris, rgb("6C614D"), smooth(0.79, 1, radii)[:, None, None])
    aperture = (dx / 0.22) ** 2 + (dy / 0.94) ** 2
    iris = mix(rgb("272A25"), iris, smooth(0.84, 1.24, aperture)[..., None])
    loft(part, rings, None, (0.23, 0), ring_colors=iris)
    for top in (False, True):
        t = np.linspace(-1, 1, 20)
        yy = np.sqrt(1 - t * t) * (1 - 0.47 * t * t) * (0.0076 if top else -0.0074)
        rim = ray_hit(origin + t[:, None] * 0.0128 * u + yy[:, None] * v, n, head_field) + 0.00055 * n
        path_tube(part, hworld(rim), 0.00030 + 0.0010 * (1 - t * t), "74563B" if top else "BD9569", (0.76, 0), 8)


def cat_face(part):
    for s in (-1, 1):
        pinna(part, s)
        cat_eye(part, s)
        # Tactile whiskers on three staggered rows, fine enough not to read as wire antennas.
        for i in range(7):
            row, col = divmod(i, 3)
            o = ray_hit(
                (s * 0.016, -0.018 + 0.005 * row, 0.048 + 0.005 * col), (s * 0.90, -0.04, 0.40), head_field
            )
            o = o + np.array((s * 0.00035, 0, 0))
            ellipsoid(part, hworld(o), (0.00085, 0.00060, 0.00086), "79543A", segments=9, bands=6)
            span = 0.042 + 0.005 * col + 0.002 * row
            tip = o + (s * span, -0.015 + 0.012 * row + 0.002 * col, -0.017 + 0.013 * col + 0.003 * row)
            pp = curve([o, o + (s * 0.016, 0.003 * row, 0.002 + 0.005 * col), tip], 12)
            path_tube(part, hworld(pp), np.linspace(0.00045, 0.00011, 12), "D1B89B", (0.76, 0), 6)

    # Nose leather is widest at its top; the philtrum parts the two whisker pads.
    def nose(q):
        q[:, 0] *= 0.68 + 0.33 * q[:, 1]
        return q

    snout = np.array((0, -0.0065, 0.0777))
    ellipsoid(
        part, hworld(snout), (0.014, 0.0084, 0.0055), "A47469", (0.55, 0), orientation=R, segments=26, deform=nose
    )
    for s in (-1, 1):
        ellipsoid(
            part,
            hworld(snout + (s * 0.0057, 0.0018, 0.0040)),
            (0.0022, 0.0012, 0.0009),
            "684A45",
            (0.61, 0),
            orientation=R,
            segments=14,
            bands=9,
        )
        cable(
            part,
            hworld(
                [(0, -0.0135, 0.079), (0, -0.021, 0.078), (s * 0.009, -0.027, 0.075), (s * 0.021, -0.026, 0.074)]
            ),
            0.00070,
            "805C49",
            count=14,
            sides=7,
        )


def cat_pack(vest, pack):
    # Fitted saddle and webbing: sample the 3-D chest radially, never a camera projection.
    # Angle is zero at the spine, pi below the breastbone.
    def shoulder_skin(p):
        d = trunk(p)
        for s in (-1, 1):
            j = -0.013 * s
            q = limb(p, (0.039 * s, 0.248, 0.063 + j), (0.051 * s, 0.188, 0.106 + j), 0.035, 0.030, 0.67)
            q = union(
                q,
                limb(p, (0.051 * s, 0.188, 0.106 + j), (0.046 * s, 0.126, 0.079 + j), 0.028, 0.016, 0.83),
                0.013,
            )
            d = union(d, q, 0.017)
        return d

    def fitted(angle, z, off, neck=False):
        angle, z = np.broadcast_arrays(angle, z)
        if neck:
            axis = unit((0, 0.58, 0.815))
            up = np.array((0, axis[2], -axis[1]))
            origin = np.array((0, 0.246, 0.129)) + z[..., None] * axis
            d = np.sin(angle)[..., None] * np.array((1, 0, 0)) + np.cos(angle)[..., None] * up
        else:
            origin = np.stack((z * 0, z * 0 + 0.201, z), -1)
            d = np.stack((np.sin(angle), np.cos(angle), z * 0), -1)
        return ray_hit(origin, d, shoulder_skin) + d * off

    t = np.linspace(0, 1, 14)[:, None]
    u = np.linspace(-1, 1, 49)[None, :]
    a = (1.31 + 0.20 * np.cos(t * np.pi) ** 2 - 0.08 * np.sin(t * np.pi)) * u
    za = -0.061 + 0.013 * np.sin(a) ** 2
    zb = 0.113 - 0.038 * np.sin(a) ** 2
    z = mix(za, zb, t)
    shell_grid(vest, (fitted(a, z, 0.0033), fitted(a, z, 0.0002)), "4C5548", (0.86, 0), "Canvas")
    for row in (0, -1):
        path_tube(vest, fitted(a[row], z[row], 0.0036), 0.00135, "777D66", (0.86, 0), 8)
    for col in (0, -1):
        path_tube(vest, fitted(a[:, col], z[:, col], 0.0037), 0.00135, "777D66", (0.85, 0), 8)
    th = np.arange(72) * TAU / 72
    for front in (False, True):

        def center(a, neck=front):
            return np.zeros_like(a) if neck else -0.052 + 0.008 * np.cos(a)

        zz = center(th) + np.array([-0.010, -0.009, 0.009, 0.010])[:, None]
        shell_grid(
            vest,
            (fitted(th, zz, 0.0047, front), fitted(th, zz, 0.001, front)),
            "747A56" if not front else "747D59",
            (0.83, 0),
            "Canvas",
            True,
        )
        for seam in (-0.0074, 0.0074):
            st = th[::2, None] + np.array([0.008, 0.87 * TAU / 72])
            runs = fitted(st, center(st) + seam, 0.0049, front)
            for stitch in runs:
                path_tube(vest, stitch, 0.00042, "969575", (0.84, 0), 6)
        for s in (-1, 1):
            angle = s * (1.48 if front else 1.58)
            x, y, zp = fitted(angle, center(angle), 0.0055, front)
            box(vest, (x, y, zp), (0.0048, 0.016, 0.022), "696855", 0.0018, (0.49, 0.53), corner=0.0027)
            box(vest, (x + s * 0.0025, y, zp), (0.0013, 0.009, 0.015), "333934", 0.0006, (0.71, 0.1))

    # Raised rectangular field pack with an inclined top, gasket, side catches and small recessed display.
    def rack(p):
        p = p.copy()
        p[:, 1] += 0.070 * p[:, 2]
        return p + np.array((0, 0.280, 0.027))

    profiles = [
        (-0.011, 0.043, 0.060, 0.013),
        (-0.008, 0.052, 0.070, 0.015),
        (0.001, 0.055, 0.072, 0.015),
        (0.024, 0.052, 0.068, 0.014),
        (0.034, 0.049, 0.065, 0.012),
        (0.036, 0.046, 0.062, 0.010),
    ]
    rings = []
    for y, x, z, r in profiles:
        r0 = rect_ring(x, z, r, 6)
        rings.append(np.column_stack((r0[:, 0], np.full(len(r0), y), r0[:, 1])))
    loft(pack, rings, "37393B", (0.76, 0.03), "Canvas", transform=rack)
    box(pack, (0, 0.028, 0), (0.107, 0.0036, 0.139), "252B2D", 0.0014, (0.72, 0.05), corner=0.014, transform=rack)
    box(
        pack, (0, 0.0367, 0), (0.096, 0.0068, 0.128), "434745", 0.0025, (0.64, 0.12), corner=0.011, transform=rack
    )
    box(
        pack,
        (0, 0.0391, 0.004),
        (0.084, 0.0047, 0.111),
        "30373C",
        0.0018,
        (0.60, 0.12),
        corner=0.008,
        transform=rack,
    )
    box(
        pack,
        (0, 0.0415, 0.011),
        (0.071, 0.0026, 0.080),
        "434D52",
        0.001,
        (0.61, 0.13),
        corner=0.006,
        transform=rack,
    )
    # Ribbed non-slip lid and a service bar set into the rear end.
    for i in range(5):
        box(
            pack,
            (0, 0.0430, 0.023 + (i - 2) * 0.007),
            (0.056 - 0.0017 * abs(i - 2), 0.0008, 0.00135),
            "657075",
            0.0003,
            (0.59, 0.12),
            corner=0.00065,
            transform=rack,
        )
    box(
        pack,
        (0, 0.0421, -0.039),
        (0.060, 0.0029, 0.011),
        "272C2C",
        0.001,
        (0.48, 0.16),
        corner=0.003,
        transform=rack,
    )
    for i, col in enumerate(("88B3A0", "828B74", "6D6B58")):
        box(
            pack,
            (-0.021 + i * 0.008, 0.0437, -0.039),
            (0.0045, 0.0008, 0.0023),
            col,
            0.0003,
            (0.35, 0.11),
            transform=rack,
        )
    for s in (-1, 1):
        for z0 in (-0.040, 0.038):
            box(
                pack,
                (s * 0.0528, 0.017, z0),
                (0.006, 0.023, 0.017),
                "5E6357",
                0.002,
                (0.51, 0.38),
                corner=0.003,
                transform=rack,
            )
            box(
                pack,
                (s * 0.0560, 0.019, z0),
                (0.0016, 0.010, 0.010),
                "353735",
                0.0006,
                (0.55, 0.21),
                transform=rack,
            )
        for z0 in (-0.049, 0.051):
            circular_band(
                pack,
                (s * 0.0375, 0.0405, z0),
                (0, 1, 0),
                [(-0.001, 0.0024), (0.0003, 0.0026), (0.001, 0.002)],
                "8D8D80",
                (0.45, 0.69),
                sides=10,
                transform=rack,
            )


def build():
    skin, face, vest, pack = [Part(n) for n in ("CatBody", "CatHeadDetails", "CatWebbing", "CatFieldPack")]
    body(skin)
    cat_face(face)
    cat_pack(vest, pack)
    write_actor("Cat", [skin, face, vest, pack])
