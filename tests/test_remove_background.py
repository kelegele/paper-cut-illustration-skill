"""Behavioral checks for local chroma-key cutouts; run using uv and Pillow."""
import importlib.util
from pathlib import Path
import unittest

from PIL import Image, ImageDraw

MODULE_PATH = Path(__file__).resolve().parents[1] / "paper-cut-illustration" / "scripts" / "remove_background.py"
KEY = (0, 255, 0)


class CutoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location("remove_background", MODULE_PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        cls.cutout = staticmethod(module.cutout)

    def make_sticker(self):
        image = Image.new("RGB", (15, 15), KEY)
        draw = ImageDraw.Draw(image)
        draw.rectangle((3, 3, 11, 11), fill="white")
        draw.rectangle((5, 5, 9, 9), fill=(80, 40, 120))
        return image

    def test_background_transparent_and_white_border_preserved(self):
        image = self.make_sticker()
        result = self.cutout(image, KEY)
        self.assertEqual(result.mode, "RGBA")
        self.assertEqual(result.size, image.size)
        self.assertEqual(result.getpixel((0, 0))[3], 0)
        self.assertEqual(result.getpixel((3, 7)), (255, 255, 255, 255))
        self.assertEqual(result.getpixel((7, 7)), (80, 40, 120, 255))
        self.assertEqual(image.getpixel((0, 0)), KEY)

    def test_enclosed_matching_clothing_is_preserved(self):
        image = self.make_sticker()
        image.putpixel((7, 7), KEY)
        result = self.cutout(image, KEY)
        self.assertEqual(result.getpixel((7, 7)), (*KEY, 255))

    def test_seed_removes_only_selected_enclosed_hole(self):
        image = self.make_sticker()
        image.putpixel((6, 7), KEY)
        image.putpixel((8, 7), KEY)
        result = self.cutout(image, KEY, seeds=[(6, 7)])
        self.assertEqual(result.getpixel((6, 7))[3], 0)
        self.assertEqual(result.getpixel((8, 7)), (*KEY, 255))

    def test_existing_alpha_is_not_made_opaque(self):
        image = self.make_sticker().convert("RGBA")
        image.putpixel((7, 7), (80, 40, 120, 100))
        image.putpixel((8, 7), (80, 40, 120, 0))
        result = self.cutout(image, KEY)
        self.assertEqual(result.getpixel((7, 7)), (80, 40, 120, 100))
        self.assertEqual(result.getpixel((8, 7))[3], 0)

    def test_blended_white_edge_has_soft_alpha_without_green_spill(self):
        image = self.make_sticker()
        # This is a white edge composited at low opacity over green.
        image.putpixel((2, 7), (50, 255, 50))
        red, green, blue, alpha = self.cutout(image, KEY).getpixel((2, 7))
        self.assertGreater(alpha, 0)
        self.assertLess(alpha, 255)
        self.assertLessEqual(max(red, green, blue) - min(red, green, blue), 25)
        self.assertGreaterEqual(min(red, green, blue), 200)

    def test_unmatched_border_is_rejected(self):
        image = Image.new("RGB", (15, 15), "white")
        image.putpixel((7, 7), KEY)
        with self.assertRaises(ValueError):
            self.cutout(image, KEY)


if __name__ == "__main__":
    unittest.main()
