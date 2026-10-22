"""Pic module"""

import os
import tempfile

from PIL import Image
from rich import print as rprint

from pictl.config import Config
from pictl.utils import get_name


def compress(fi: str, fo: str = None, quiet: bool = False):
    """Compress any image into `webp` image.

    FI is the name of the input file.
    FO is the name of the output file.
    """
    try:
        settings = Config().read()
        optimize = settings["basic"].get("optimize", True)
        quality = settings["basic"].get("quality", 75)
    except FileNotFoundError:
        optimize = True
        quality = 75

    try:
        imgfile = Image.open(fi)
        has_alpha = imgfile.mode in ("RGBA", "LA") or (
            imgfile.mode == "P" and "transparency" in imgfile.info
        )
        imgfile = imgfile.convert("RGBA" if has_alpha else "RGB")
        if fo:
            filename = f"{fo}.webp"
        else:
            # Write to the system temp dir, not the CWD: callers like
            # Typora invoke this with a CWD that can be on a read-only
            # volume, so a bare relative filename fails to save.
            filename = os.path.join(tempfile.gettempdir(), f"{get_name(fi)}.webp")
        imgfile.save(filename, "webp", optimize=optimize, quality=quality)
        if not quiet:
            rprint(f"The output file is {filename}")
        return filename
    except FileNotFoundError:
        if not quiet:
            rprint(f"{fi} doesn't exsit. Please check it again.")
        return None
