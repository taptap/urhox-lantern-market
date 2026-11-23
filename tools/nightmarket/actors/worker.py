"""A night-shift street mechanic: garment pattern over a fully modelled articulated chassis."""

import numpy as np
from .mesh import (
    TAU,
    Part,
    box,
    cable,
    circular_band,
    curve,
    frame,
    loft,
    mix,
    path_tube,
    rect_ring,
    rgb,
    shell_grid,
    smooth,
    turn_x,
    turn_y,
    unit,
    write_actor,
)
from scipy.interpolate import PchipInterpolator

IRON = "464A49"
CAST = "646D69"
STEEL = "999B8D"
ALLOY = "AAA58E"
RED = "894F3E"
GOLD = "A28A63"
METAL = (0.51, 0.68)
BRUSH = (0.38, 0.77)
PAINT = (0.60, 0.31)
GUM = (0.81, 0.02)


def axis_shape(part, a, b, profile, color, finish, *, sides=16, flat=0.9):
    a, b = np.array(a), np.array(b)
    fs = np.array([p[0] for p in profile])
    radii = np.array([p[1] for p in profile])
    pp = mix(a, b, fs[:, None])
    path_tube(part, pp, np.column_stack((radii * flat, radii)), color, finish, sides)


def joint(part, c, width, radius, s):
    c = np.asarray(c)
    # Bearing cheeks, dust seal, screw boss, off-center socket recess.
    circular_band(
        part,
        c,
        (1, 0, 0),
        [
            (-width * 0.51, radius * 0.75),
            (-width * 0.47, radius),
            (-width * 0.32, radius),
            (-width * 0.30, radius * 0.78),
            (width * 0.30, radius * 0.78),
            (width * 0.32, radius),
            (width * 0.47, radius),
            (width * 0.51, radius * 0.75),
        ],
        IRON,
        METAL,
        sides=24,
    )
    for end in (-1, 1):
        c2 = c + (width * 0.50 * end, 0, 0)
        circular_band(
            part,
            c2,
            (end, 0, 0),
            [(-0.001, radius * 0.59), (0.002, radius * 0.67), (0.0045, radius * 0.60)],
            ALLOY if end == s else CAST,
            BRUSH,
            sides=18,
        )
        circular_band(
            part,
            c2 + (end * 0.004, 0, 0),
            (end, 0, 0),
            [(0, radius * 0.24), (0.0018, radius * 0.23)],
            "515655",
            METAL,
            sides=6,
        )


def anatomical_leg(part, s):
    shift = 0.022 if s < 0 else -0.018
    hip = np.array((s * 0.075, 0.862, -0.019 + shift * 0.45))
    knee = np.array((s * 0.091, 0.430 + (s + 1) * 0.004, 0.038 + shift))
    ankle = np.array((s * (0.108 if s < 0 else 0.121), 0.088, -0.025 + shift))
    axis_shape(
        part,
        knee,
        hip,
        [
            (0.04, 0.025),
            (0.1, 0.030),
            (0.18, 0.031),
            (0.22, 0.039),
            (0.29, 0.038),
            (0.76, 0.038),
            (0.87, 0.035),
            (0.96, 0.025),
        ],
        IRON,
        METAL,
        sides=16,
        flat=0.74,
    )
    # A folded enamel U-channel protects the thigh, with the telescoping rod exposed on its back.
    axis = unit(hip - knee)
    across = frame(axis)[:, 0]
    forward = unit(np.cross(across, axis))
    th = np.linspace(-2.25, 2.25, 30)[None, :]
    t = np.array([0.16, 0.17, 0.20, 0.25, 0.71, 0.84, 0.85])[:, None]
    r = np.array([0.034, 0.040, 0.044, 0.050, 0.052, 0.047, 0.044])[:, None]
    c = mix(knee, hip, (t + 0.032 * np.cos(th))[:, :, None])
    radial = np.sin(th)[..., None] * across * 0.81 + np.cos(th)[..., None] * forward
    shell_grid(
        part, (c + r[..., None] * radial, c + (r - 0.004)[..., None] * radial), RED if s < 0 else "898B7D", PAINT
    )
    axis_shape(
        part,
        mix(knee, hip, 0.20) - 0.036 * forward,
        mix(knee, hip, 0.90) - 0.037 * forward,
        [(0, 0.008), (0.03, 0.010), (0.34, 0.009), (0.36, 0.006), (0.83, 0.006), (0.85, 0.010), (1, 0.009)],
        STEEL,
        BRUSH,
        sides=12,
    )
    for t in (0.28, 0.73):
        tip = mix(knee, hip, t) + s * 0.0395 * across + 0.002 * forward
        circular_band(
            part,
            tip,
            s * across,
            [(-0.002, 0.0042), (0.001, 0.0050), (0.0017, 0.0042)],
            "8C8B78",
            BRUSH,
            sides=10,
        )
    # Fork visible on each side of the knee pin.
    for e in (-1, 1):
        i = np.array((e * 0.027, 0, 0))
        mid = mix(knee, hip, 0.22)
        axis_shape(
            part,
            knee + i,
            mid + i,
            [(0, 0.022), (0.24, 0.023), (0.79, 0.018), (1, 0.016)],
            CAST,
            METAL,
            sides=12,
            flat=0.32,
        )
    joint(part, knee, 0.083, 0.039, s)
    axis_shape(
        part,
        ankle,
        knee,
        [
            (0.07, 0.022),
            (0.15, 0.028),
            (0.22, 0.027),
            (0.34, 0.030),
            (0.66, 0.033),
            (0.74, 0.037),
            (0.81, 0.036),
            (0.91, 0.025),
            (0.97, 0.020),
        ],
        CAST if s < 0 else "6F6B5B",
        METAL,
        sides=16,
        flat=0.75,
    )
    for side in (-1, 1):
        d = np.array((side * 0.021, 0, -0.012))
        axis_shape(
            part,
            mix(ankle, knee, 0.17) + d,
            mix(ankle, knee, 0.76) + d,
            [(0, 0.007), (0.08, 0.009), (0.14, 0.009), (0.16, 0.006), (0.72, 0.006), (0.74, 0.009), (1, 0.010)],
            STEEL,
            BRUSH,
            sides=12,
        )
    # Separate shin enamel shields, and a cable following the flexion side of the joint.
    axis_shape(
        part,
        mix(ankle, knee, 0.24) + (0, 0, 0.022),
        mix(ankle, knee, 0.74) + (0, 0, 0.021),
        [(0, 0.013), (0.07, 0.024), (0.17, 0.025), (0.83, 0.027), (0.96, 0.022), (1, 0.014)],
        RED if s > 0 else "8C8170",
        PAINT,
        sides=16,
        flat=0.67,
    )
    cable(
        part,
        [
            mix(ankle, knee, 0.24) + (s * 0.013, 0, -0.024),
            mix(ankle, knee, 0.68) + (s * 0.020, 0, -0.025),
            knee + (s * 0.019, -0.020, -0.047),
            knee + (s * 0.020, 0.034, -0.044),
            mix(knee, hip, 0.47) + (s * 0.018, 0, -0.039),
        ],
        0.0048,
        "47443C",
        sides=8,
    )
    joint(part, ankle, 0.053, 0.025, s)
    # Flat contact tread, bevelled rubber welt and shaped steel toe with real instep/heel volume.
    toeR = turn_y(9 * s + (3 if s < 0 else 0))
    origin = np.array((ankle[0], 0, ankle[2]))

    def foot(p):
        return p @ toeR.T + origin

    for z, depth, x, y, col in [(0.018, 0.199, 0.091, 0.015, GUM), (0.025, 0.189, 0.095, 0.022, PAINT)]:
        bottom = 0 if col == GUM else 0.014
        box(
            part,
            (0, bottom + y / 2, z),
            (x, y, depth),
            "373A37" if col == GUM else "514D43",
            0.005,
            col,
            corner=0.024,
            steps=5,
            transform=foot,
        )
    # Sections perpendicular to the toe, varying in both width and instep height.
    rim = []
    for z, x, h in [
        (-0.070, 0.030, 0.040),
        (-0.060, 0.039, 0.062),
        (-0.037, 0.041, 0.079),
        (-0.018, 0.039, 0.089),
        (0.004, 0.038, 0.091),
        (0.029, 0.044, 0.071),
        (0.060, 0.046, 0.059),
        (0.094, 0.043, 0.049),
        (0.113, 0.028, 0.041),
    ]:
        t = np.arange(32) * TAU / 32
        xx = x * np.sign(np.cos(t)) * np.abs(np.cos(t)) ** 0.78
        yy = 0.027 + (h - 0.027) * (0.5 + 0.5 * np.sign(np.sin(t)) * np.abs(np.sin(t)) ** 0.79)
        rim.append(np.column_stack((xx, yy, z + t * 0)))
    loft(part, rim, "77776A", PAINT, transform=foot)
    for z in (0.053, 0.063, 0.073):
        cable(
            part,
            foot([[-0.041, 0.044, z], [0, 0.062 - (z - 0.053) * 0.27, z + 0.002], [0.041, 0.044, z]]),
            0.0019,
            IRON,
            METAL,
            count=11,
            sides=7,
        )
    box(part, (0, 0.044, -0.058), (0.067, 0.040, 0.022), CAST, 0.006, METAL, corner=0.006, transform=foot)


def arm(part, hands, s):
    shoulder = np.array((s * 0.153, 1.327, 0.012))
    elbow = np.array((s * 0.224, 1.099, -0.021 + s * 0.012))
    wrist = np.array((s * 0.239, 0.866, 0.012 + 0.021 * s))
    wrist[0] += s * 0.006 if s < 0 else 0
    joint(part, shoulder, 0.054, 0.029, s)
    axis_shape(
        part,
        elbow,
        shoulder,
        [(0, 0.025), (0.09, 0.034), (0.22, 0.034), (0.29, 0.040), (0.85, 0.041), (1, 0.030)],
        CAST,
        PAINT,
        flat=0.76,
    )
    joint(part, elbow, 0.055, 0.026, s)
    # A four-bar wrist actuator. Deliberately thinner below the rolled jacket sleeve.
    axis_shape(
        part,
        wrist,
        elbow,
        [
            (0, 0.019),
            (0.04, 0.024),
            (0.1, 0.021),
            (0.32, 0.020),
            (0.48, 0.029),
            (0.72, 0.034),
            (0.85, 0.030),
            (1, 0.018),
        ],
        "868A7A" if s > 0 else "806F5D",
        PAINT,
        sides=18,
        flat=0.71,
    )
    for u in (-1, 1):
        off = np.array((u * 0.014, 0, -0.011))
        axis_shape(
            part,
            mix(wrist, elbow, 0.09) + off,
            mix(wrist, elbow, 0.75) + off,
            [(0, 0.006), (0.13, 0.007), (0.18, 0.0047), (0.58, 0.0047), (0.60, 0.0075), (1, 0.008)],
            STEEL,
            BRUSH,
            sides=10,
        )
    cable(
        part,
        [
            wrist + (s * 0.009, 0, 0.013),
            mix(wrist, elbow, 0.45) + (s * 0.019, 0, 0.020),
            elbow + (s * 0.017, -0.020, 0.017),
            elbow + (s * 0.016, 0.032, 0.017),
        ],
        0.0046,
        "544C3E",
        count=15,
        sides=8,
    )
    joint(part, wrist, 0.042, 0.020, s)
    # Hands turned slightly inward, four separately articulated fingers and an opposed thumb.
    angle = turn_y(s * 13)

    def hand(p):
        return np.asarray(p) @ angle.T + wrist

    # Palm normals point generally into the body; X is palm thickness, Z its width.
    box(hands, (0, -0.027, 0), (0.041, 0.063, 0.065), IRON, 0.008, METAL, corner=0.014, transform=hand)
    box(
        hands,
        (s * 0.016, -0.026, -0.002),
        (0.016, 0.049, 0.060),
        "A09C88",
        0.005,
        PAINT,
        corner=0.008,
        transform=hand,
    )
    for i, z in enumerate((-0.022, -0.007, 0.009, 0.025)):
        length = (0.060, 0.078, 0.081, 0.067)[i]
        base = np.array((0, -0.053, z))
        hinge = base + (s * 0.0008, -length * 0.44, 0.001)
        distal = hinge + (-s * 0.010, -length * 0.32, 0.003)
        tip = distal + (-s * 0.010, -length * 0.16, 0.004)
        for n, (a, b, w) in enumerate(((base, hinge, 0.0077), (hinge, distal, 0.0068), (distal, tip, 0.0060))):
            axis_shape(
                hands,
                hand(a),
                hand(b),
                [(0, w * 0.85), (0.16, w), (0.80, w * 0.93), (1, w * 0.60)],
                "979A89" if n < 2 else "62665C",
                PAINT,
                sides=10,
                flat=0.90,
            )
        for p in (base, hinge):
            circular_band(
                hands, hand(p), angle[:, 2], [(-0.0047, 0.0062), (0.0047, 0.0062)], IRON, METAL, sides=10
            )
    thumb = [
        (-s * 0.007, -0.014, 0.027),
        (-s * 0.020, -0.032, 0.046),
        (-s * 0.021, -0.056, 0.047),
        (-s * 0.016, -0.067, 0.039),
    ]
    path_tube(hands, hand(thumb), [0.011, 0.011, 0.008, 0.005], "8F9281", PAINT, 12)
    return shoulder, elbow, wrist


# Tailor's sections: (height, half-width, half-depth, centre fore/aft).
JSECTIONS = np.array(
    [
        (0.827, 0.120, 0.080, -0.004),
        (0.840, 0.139, 0.094, -0.005),
        (0.860, 0.145, 0.100, -0.005),
        (0.905, 0.147, 0.108, -0.003),
        (0.980, 0.140, 0.102, -0.003),
        (1.060, 0.135, 0.097, 0),
        (1.122, 0.142, 0.103, 0.003),
        (1.199, 0.158, 0.114, 0.008),
        (1.272, 0.176, 0.117, 0.012),
        (1.312, 0.175, 0.111, 0.014),
        (1.345, 0.156, 0.099, 0.015),
        (1.374, 0.111, 0.081, 0.016),
        (1.390, 0.071, 0.060, 0.017),
        (1.397, 0.057, 0.050, 0.018),
    ]
)
JSPLINE = PchipInterpolator(JSECTIONS[:, 0], JSECTIONS[:, 1:], axis=0)


def jacket_pt(a, y, off=0):
    a, y = np.broadcast_arrays(a, y)
    x, z, cz = np.moveaxis(JSPLINE(np.clip(y, 0.827, 1.397)), -1, 0)
    lo = 1 - smooth(0.93, 1.30, y)
    ripple = (0.003 + 0.0045 * lo) * np.sin(8 * a + 3 * (y - 1) + 0.7 * np.sin(2 * a + y * 8))
    ripple += 0.0038 * np.sin(3 * a + 0.3) * np.sin(13 * y + 1.3 * a)
    for yy, amplitude, phase in [
        (0.887, 0.008, 0.3),
        (0.994, 0.006, 1.4),
        (1.088, 0.008, 0.6),
        (1.18, 0.007, -0.8),
        (1.294, 0.005, 2.4),
    ]:
        crest = yy + 0.025 * np.sin(a * 2 + phase) + 0.010 * np.cos(3 * a + yy)
        ripple -= amplitude * np.exp(-(((y - crest) / 0.010) ** 2)) * (0.67 + 0.33 * np.cos(3 * a + phase))
    ripple += lo * 0.006 * np.cos(18 * a + 1.5) * np.exp(-(((a - np.pi) % (TAU) - np.pi) ** 2) / 0.34)
    sa, ca = np.sin(a), np.cos(a)
    hem = (1 - smooth(0.827, 0.949, y)) * (
        -0.010 * ca - 0.009 * np.cos(3 * a + 1.3) + 0.004 * np.sin(8 * a - 0.5)
    )
    return np.stack(
        (
            np.sign(sa) * np.abs(sa) ** 0.86 * (x + ripple + off),
            y + hem,
            cz + np.sign(ca) * np.abs(ca) ** 0.87 * (z + ripple + off),
        ),
        -1,
    )


def garment_panel(part, a0, a1, y0, y1, color, offset=0.004, tilt=0, pouch=0):
    u = np.linspace(0, 1, 15)[None, :]
    v = np.linspace(0, 1, 9)[:, None]
    a = mix(a0, a1, u) + v * 0
    yy = mix(y0, y1, v) + (u - 0.5) * tilt
    # Clipped bottom corners and rounded bellows, not flat badges floating in front.
    a = a + (np.maximum(0, 0.14 - v) * 0.13) * (1 - 2 * u)
    bump = pouch * (np.sin(u * np.pi) * np.sin(v * np.pi)) ** 0.64
    top = jacket_pt(a, yy, offset + bump)
    shell_grid(part, (top, jacket_pt(a, yy, offset - 0.003)), color, (0.84, 0.01), "Canvas")
    return top


def make_jacket(part, arms):
    theta = np.arange(88) * TAU / 88
    ys = np.unique(np.r_[np.linspace(0.827, 1.397, 73), JSECTIONS[:, 0]])
    rings = [jacket_pt(theta, y) for y in ys]

    def pigment(p):
        x, y, z = p.T
        wear = (0.5 + 0.5 * np.sin(23 * x + 7 * z) * np.sin(y * 21 + x * 3)) * 0.20
        return mix(rgb("806545"), rgb("AA8B60"), wear[:, None])

    loft(part, rings, pigment, (0.88, 0), "Canvas")
    hem = np.stack(
        [jacket_pt(theta, y, 0.0018 + 0.001 * np.sin(38 * theta)) for y in [0.828, 0.831, 0.842, 0.847, 0.850]]
    )
    loft(part, hem, "675A43", (0.91, 0), "Canvas")
    # Broad shoulder yoke with a curved lower seam on the back; fold runs down centre back.
    a = np.linspace(np.pi * 0.48, np.pi * 1.52, 73)[None, :]
    v = np.linspace(0, 1, 10)[:, None]
    low = 1.246 + 0.039 * np.cos(a - np.pi) ** 2 - 0.018 * np.sin(2 * (a - np.pi)) ** 2
    y = mix(low, 1.37, v) + a * 0
    shell_grid(part, (jacket_pt(a, y, 0.0035), jacket_pt(a, y, 0.0003)), "89704D", (0.86, 0), "Canvas")
    path_tube(part, jacket_pt(a[0], low[0], 0.0036), 0.0020, "B49768", (0.85, 0), 7)
    for da in (-0.067, 0.067):
        y = np.linspace(0.865, 1.265, 40)
        a = np.pi + da + 0.022 * np.sin(y * 15.0)
        path_tube(part, jacket_pt(a, y, 0.0021), 0.0023, "756048", (0.91, 0), 7)
    # A storm placket covering the metal zip, three snaps, four working pockets.
    garment_panel(part, -0.067, 0.072, 0.852, 1.375, "6C5942", 0.0022)
    y = np.linspace(0.859, 1.371, 40)
    path_tube(part, jacket_pt(np.full(len(y), 0.060), y, 0.004), 0.0018, "A08A66", (0.79, 0.06), 7)
    for y in (0.927, 1.074, 1.206, 1.329):
        p = jacket_pt(np.array([0.012]), np.array([y]), 0.006)[0]
        circular_band(
            part, p, (0, 0, 1), [(-0.002, 0.0052), (0.001, 0.0057), (0.002, 0.0047)], GOLD, BRUSH, sides=12
        )
    for s in (-1, 1):
        a0, a1 = sorted((s * 0.23, s * 1.11))
        tilt = s * 0.018
        tab = garment_panel(part, a0, a1, 0.881, 1.004, "826747", 0.007, tilt, 0.010)
        for e in (0, -1):
            path_tube(part, tab[:, e], 0.00155, "A38A65", (0.88, 0), 7)
        garment_panel(part, a0 - 0.014, a1 + 0.014, 0.975, 1.017, "8C724F", 0.013, tilt, 0.0025)
    garment_panel(part, -0.91, -0.20, 1.146, 1.237, "877254", 0.005, 0.009, 0.004)
    garment_panel(part, -0.92, -0.19, 1.218, 1.247, "98805B", 0.009, 0.009, 0.002)
    garment_panel(part, 0.28, 0.76, 1.212, 1.236, "B7A87C", 0.004, 0.004)
    for i, h in enumerate((0.010, 0.006, 0.009, 0.014, 0.006, 0.009)):
        a = 0.37 + i * 0.053
        garment_panel(part, a, a + 0.019, 1.217, 1.217 + h, "646552", 0.006, 0.001)
    # Raised/worn stand collar with darker lining behind the service head.
    th = np.arange(60) * TAU / 60
    rims = []
    cs = []
    for x, z, y, co in [
        (0.080, 0.062, 1.372, "766447"),
        (0.086, 0.068, 1.383, "8A7454"),
        (0.074, 0.060, 1.418, "967F5B"),
        (0.070, 0.055, 1.424, "A38B66"),
        (0.062, 0.048, 1.419, "655B48"),
        (0.060, 0.048, 1.378, "544F40"),
    ]:
        rims.append(
            np.stack(
                (
                    x * np.sin(th),
                    y - 0.025 * np.maximum(np.cos(th), 0) ** 2 + 0.004 * np.sin(2 * th),
                    0.018 + z * np.cos(th),
                ),
                1,
            )
        )
        cs.append(rgb(co))
    loft(part, rims, None, (0.88, 0), "Canvas", ring_colors=np.array(cs)[:, None, :])
    sleeve_angle = np.arange(40) * TAU / 40

    def sleeve(tangent, cen, rad, tt, raise_by=0):
        f = frame(tangent, (0, 0, 1))
        ripple = (0.0026 + 0.0018 * np.sin(np.pi * tt)) * np.sin(5 * sleeve_angle + tt * 2.7)
        ripple -= 0.0054 * np.exp(-(((tt - (0.62 + 0.05 * np.cos(sleeve_angle))) / 0.056) ** 2))
        rad = rad + ripple + raise_by
        return (
            cen
            + np.outer(rad * np.cos(sleeve_angle), f[:, 0])
            + np.outer(rad * np.sin(sleeve_angle) * 0.91, f[:, 1])
        )

    for s, (shoulder, elbow, wrist) in zip((-1, 1), arms):
        bottom = mix(wrist, elbow, 0.57 if s > 0 else 0.46)
        centre = curve(
            [
                shoulder + (s * -0.015, 0.012, 0.002),
                mix(shoulder, elbow, 0.48) + (s * 0.010, 0, 0.004),
                elbow,
                bottom,
            ],
            46,
        )
        t = np.linspace(0, 1, len(centre))
        sizes = PchipInterpolator(
            [0, 0.05, 0.18, 0.31, 0.53, 0.65, 0.79, 0.94, 1],
            [0.040, 0.062, 0.069, 0.064, 0.051, 0.054, 0.046, 0.046, 0.040],
        )(t)
        tangents = unit(np.gradient(centre, axis=0))
        sleeve_rings = [sleeve(d, c, r, tt) for d, c, r, tt in zip(tangents, centre, sizes, t)]
        loft(part, sleeve_rings, "836A49", (0.87, 0), "Canvas")
        for t0, t1, col, raise_by in [
            (0.39, 0.45, "A48D67" if s < 0 else "81694D", 0.0018),
            (0.90, 0.99, "70614B", 0.004),
            (0.91, 0.935, "8B785B", 0.0055),
        ]:
            ix = np.where((t >= t0) & (t <= t1))[0]
            if len(ix) < 2:
                ix = np.arange(max(0, np.searchsorted(t, t0) - 1), min(len(t), np.searchsorted(t, t1) + 1))
            rings = [sleeve(tangents[i], centre[i], sizes[i], t[i], raise_by) for i in ix]
            loft(part, rings, col, (0.86, 0), "Canvas")
        path_tube(part, np.asarray(sleeve_rings)[1:-1, 6], 0.0015, "A18A61", (0.85, 0), 7)


def monitor(part):
    # A compact service CRT: deep tapered flyback housing, screwed chassis, gasket, curved glass.
    rot = turn_y(-7) @ turn_x(5)
    pos = np.array((-0.008, 1.565, 0.025))

    def head(p):
        return np.asarray(p) @ rot.T + pos

    def bezel(profile, color, finish):
        rings = []
        for z, x, y, r, dy in profile:
            q = rect_ring(x, y, r, 6)
            rings.append(np.column_stack((q[:, 0], q[:, 1] + dy, q[:, 0] * 0 + z)))
        loft(part, rings, color, finish, transform=head)

    bezel(
        [
            (-0.121, 0.076, 0.067, 0.017, 0.003),
            (-0.117, 0.087, 0.076, 0.020, 0.005),
            (-0.085, 0.102, 0.085, 0.022, 0.011),
            (-0.043, 0.116, 0.096, 0.023, 0.013),
            (0.065, 0.126, 0.104, 0.020, 0.013),
            (0.074, 0.124, 0.103, 0.019, 0.013),
        ],
        "8A8371",
        PAINT,
    )
    bezel(
        [
            (0.066, 0.126, 0.102, 0.018, 0.013),
            (0.071, 0.127, 0.105, 0.020, 0.013),
            (0.080, 0.126, 0.105, 0.020, 0.013),
        ],
        "494C43",
        (0.67, 0.22),
    )
    bezel(
        [
            (0.077, 0.125, 0.104, 0.019, 0.013),
            (0.084, 0.128, 0.106, 0.019, 0.013),
            (0.099, 0.126, 0.105, 0.021, 0.012),
            (0.106, 0.121, 0.100, 0.021, 0.012),
        ],
        "888572",
        (0.62, 0.25),
    )
    bezel(
        [
            (0.105, 0.112, 0.087, 0.019, 0.018),
            (0.112, 0.113, 0.087, 0.021, 0.018),
            (0.117, 0.108, 0.082, 0.019, 0.018),
            (0.119, 0.100, 0.074, 0.017, 0.018),
        ],
        "363D3D",
        (0.60, 0.18),
    )
    bezel(
        [
            (0.117, 0.101, 0.074, 0.019, 0.018),
            (0.121, 0.098, 0.071, 0.019, 0.018),
            (0.124, 0.091, 0.065, 0.019, 0.018),
            (0.127, 0.071, 0.047, 0.019, 0.018),
            (0.128, 0.036, 0.019, 0.014, 0.018),
        ],
        "3D5958",
        (0.30, 0.12),
    )
    # A modest true phosphor readout, recessed under the brow, not a painted face on a card.
    for s in (-1, 1):

        def eye(p, side=s):
            q = p.copy()
            q[:, 2] += 0.1301 - 0.025 * np.abs(q[:, 0])
            q[:, 1] += 0.031 + 0.028 * side * q[:, 0]
            return head(q)

        box(
            part,
            (s * 0.039, 0, 0),
            (0.034, 0.008, 0.0037),
            "AAC7A5",
            0.002,
            (0.28, 0.02),
            corner=0.003,
            transform=eye,
            surface="Phosphor",
        )
    box(
        part,
        (0, -0.013, 0.129),
        (0.020, 0.003, 0.0023),
        "8BAF98",
        0.001,
        (0.27, 0.02),
        transform=head,
        surface="Phosphor",
    )
    for i in range(4):
        box(
            part,
            (-0.065 + i * 0.022, -0.078, 0.108),
            (0.011, 0.004, 0.0026),
            "A8A18A",
            0.001,
            (0.53, 0.27),
            transform=head,
        )
    box(part, (0.078, -0.077, 0.109), (0.009, 0.003, 0.002), "B79871", 0.0008, (0.40, 0.14), transform=head)
    # Stepped rear service door, six projecting vent louvers and inset screws.
    bezel([(-0.122, 0.068, 0.056, 0.008, 0.008), (-0.128, 0.067, 0.055, 0.008, 0.008)], "696C61", (0.60, 0.45))
    for i in range(6):
        box(
            part,
            (0.004, 0.009 + (i - 2.5) * 0.011, -0.129),
            (0.081, 0.005, 0.006),
            "464C47",
            0.0016,
            (0.67, 0.33),
            transform=head,
        )
    for s in (-1, 1):
        for yy in (-0.034, 0.047):
            circular_band(
                part,
                (s * 0.054, yy, -0.129),
                (0, 0, -1),
                [(-0.001, 0.0038), (0.0013, 0.004), (0.002, 0.003)],
                STEEL,
                BRUSH,
                sides=9,
                transform=head,
            )
        for k in range(4):
            # Vents follow the slope of the cheek casting.
            zz = -0.032 + k * 0.018
            box(
                part,
                (s * (0.117 + (zz + 0.043) * 0.088), 0.031, zz),
                (0.003, 0.060, 0.008),
                "55594E",
                0.0013,
                (0.68, 0.33),
                transform=head,
            )
    box(part, (0, 0.116, -0.006), (0.125, 0.005, 0.072), "9B947E", 0.0018, PAINT, corner=0.007, transform=head)
    # Visible swivelling neck and braided return lead exit at the lower rear of the monitor.
    circular_band(
        part,
        (0, 1.448, 0.016),
        (0, 1, 0),
        [
            (-0.075, 0.034),
            (-0.056, 0.041),
            (-0.045, 0.036),
            (-0.035, 0.033),
            (-0.029, 0.041),
            (-0.022, 0.039),
            (-0.017, 0.031),
            (0.001, 0.031),
            (0.006, 0.041),
            (0.016, 0.042),
            (0.021, 0.031),
            (0.038, 0.033),
        ],
        CAST,
        METAL,
        sides=24,
    )
    for yy in (1.418, 1.433, 1.454):
        circular_band(part, (0, yy, 0.016), (0, 1, 0), [(-0.003, 0.038), (0.003, 0.038)], IRON, GUM, sides=20)
    cable(
        part,
        [
            head((-0.042, -0.058, -0.103)),
            (-0.052, 1.463, -0.074),
            (-0.043, 1.432, -0.061),
            (-0.025, 1.387, -0.027),
        ],
        0.008,
        "514E44",
        count=20,
        sides=10,
    )


def build():
    chassis, hands, jacket, crt = [
        Part(n) for n in ("WorkerChassis", "WorkerHands", "WorkerJacket", "WorkerMonitor")
    ]
    box(chassis, (0, 0.857, -0.004), (0.214, 0.113, 0.126), IRON, 0.024, METAL, corner=0.035)
    for s in (-1, 1):
        anatomical_leg(chassis, s)
    arms = [arm(chassis, hands, s) for s in (-1, 1)]
    make_jacket(jacket, arms)
    monitor(crt)
    write_actor("Worker", [chassis, jacket, hands, crt])
