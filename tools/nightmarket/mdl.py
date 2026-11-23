"""Write the two static UMD2 vertex layouts used by Lantern Market."""
from struct import pack, Struct


def write_model(path, vertices, indices, groups, *, colored=False):
    # Position, normal, then either RGBA8 + UV (actors) or UV + tangent (street).
    layout = (3, 0x103, 0x506, 0x402) if colored else (3, 0x103, 0x402, 0x304)
    vertex = Struct('<6f4B2f' if colored else '<12f')
    bounds = [fn(v[i] for v in vertices) for fn in (min, max) for i in range(3)]
    short = len(vertices) <= 65535
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('wb') as f:
        f.write(pack('<4s9I', b'UMD2', 1, len(vertices), len(layout), *layout, 0, 0))
        f.writelines(vertex.pack(*v) for v in vertices)
        f.write(pack('<3I', 1, len(indices), 2 if short else 4))
        f.write(pack(f'<{len(indices)}' + ('H' if short else 'I'), *indices))
        f.write(pack('<I', len(groups)))
        for start, count, _ in groups:
            # One triangle-list LOD, no bones, both buffers at index zero.
            f.write(pack('<IIf5I', 0, 1, 0., 0, 0, 0, start, count))
        f.write(pack('<2I6f', 0, 0, *bounds))  # No morphs or skeleton.
        f.writelines(pack('<3f', *center) for _, _, center in groups)
        f.write(bytes(10))  # No secondary UVs, stroke normals or convex hulls.
