"""Rebuild original Night Market character prefabs using only numeric anatomy and swatches.

    python -m tools.nightmarket.actors.build

No Blender installation, source pictures, scene camera or scene lighting required.
"""

import argparse
import xml.etree.ElementTree as ET

import numpy as np
from .mesh import OUT, PREFIX, TAU
from PIL import Image
from scipy.ndimage import gaussian_filter, map_coordinates


def materials():
    tex = OUT / "Materials"
    tex.mkdir(exist_ok=True, parents=True)
    rng = np.random.default_rng(14722)
    y, x = np.mgrid[:256, :256]
    noise = rng.normal(0, 1, (256, 256))
    filaments = gaussian_filter(noise, (6, 0.60), mode="wrap")
    warp = gaussian_filter(rng.normal(0, 1, (256, 256)), 7, mode="wrap")
    filaments = map_coordinates(
        filaments, (y, x + 33 * warp + 1.6 * np.sin(y * TAU / 64)), order=1, mode="grid-wrap"
    )
    coat = 128 + 37 * filaments / filaments.std() + 10 * noise
    weave = (
        126
        + 22 * np.cos(x * TAU / 8) * np.cos(y * TAU / 16)
        + 19 * np.cos(y * TAU / 8 + np.pi / 3) * np.sin(x * TAU / 16 + 0.6)
        + 8 * noise
    )
    for name, img in [("GuardHair", coat), ("DuckCloth", weave)]:
        Image.fromarray(np.uint8(np.clip(img, 0, 255))).convert("RGB").save(tex / f"{name}.png")
    for name in ["Finish", "Coat", "Canvas", "Phosphor"]:
        m = ET.Element("material")
        textile = name in ("Coat", "Canvas")
        shader = "Fibre" if textile else "Finish"
        ET.SubElement(m, "surfaceshader", name=f"{PREFIX}/Materials/{shader}.shader")
        if textile:
            tile = "GuardHair" if name == "Coat" else "DuckCloth"
            ET.SubElement(m, "surfacetexture", name="yarn", texture=f"{PREFIX}/Materials/{tile}.png")
            ET.SubElement(m, "parameter", name="coat", value="1" if name == "Coat" else "0")
        elif name == "Phosphor":
            ET.SubElement(m, "parameter", name="phosphor", value="0.90")
        ET.indent(m, space="  ")
        ET.ElementTree(m).write(tex / f"{name}.xml", encoding="utf-8", xml_declaration=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("actor", choices=["all", "cat", "worker"], nargs="?", default="all")
    actor = parser.parse_args().actor
    materials()
    if actor in ("all", "cat"):
        from . import cat

        cat.build()
    if actor in ("all", "worker"):
        from . import worker

        worker.build()
