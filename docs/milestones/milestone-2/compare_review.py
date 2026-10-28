"""Compare retained before/after pixels and make a human review contact sheet."""

import json
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw

ROOT = Path(__file__).resolve().parent
NAMES = sorted(path.stem for path in (ROOT / "before").glob("*.png"))


def main():
    comparisons = ROOT / "comparisons"
    comparisons.mkdir(exist_ok=True)
    sheet = Image.new("RGB", (1500, len(NAMES) * 280), "white")
    draw = ImageDraw.Draw(sheet)
    results = {}
    for row, name in enumerate(NAMES):
        before = Image.open(ROOT / "before" / f"{name}.png").convert("RGB")
        after = Image.open(ROOT / "after" / f"{name}.png").convert("RGB")
        difference = ImageChops.difference(before, after)
        difference.save(comparisons / f"{name}.diff.png")
        results[name] = {"size": list(after.size), "pixels_identical": difference.getbbox() is None}
        for col, (label, image) in enumerate(
            [("before", before), ("after", after), ("difference", difference)]
        ):
            preview = image.copy()
            preview.thumbnail((490, 240))
            sheet.paste(preview, (col * 500, row * 280 + 30))
            draw.text((col * 500 + 5, row * 280 + 8), f"{name}: {label}", fill="black")
    sheet.save(comparisons / "contact-sheet.png")
    (comparisons / "results.json").write_text(json.dumps(results, indent=2) + "\n")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
