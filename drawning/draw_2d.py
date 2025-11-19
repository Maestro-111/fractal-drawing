import os
from collections import defaultdict
from dataclasses import dataclass
from typing import List
from xml.etree.ElementTree import Element, ElementTree, SubElement

import numpy as np

from utils.fractal_regex import extract_symbol, parse_params


class SVGDrawer2D:

    """Fast, no color, SVG drawer - infinite zoom, small file size, fast rendering"""

    def __init__(self, logger, base_width=1.0, base_length=10.0, base_angle=25.0):
        self.base_width = base_width
        self.base_length = base_length
        self.base_angle = np.deg2rad(base_angle)
        self.logger = logger

        self.drawing_symbols = {"F"}
        self.axiom_symbols = {"A"}

        self.log_class_name()

    def log_class_name(self):
        self.logger.info(f"Drawer init {self.__class__.__name__}")

    # def _parse_params(self, token: str):
    #     m = re.search(r"\(([^)]*)\)", token) # search since params might be at any pos in token
    #     if not m:
    #         return []
    #     params = []
    #     for p in m.group(1).split(","):
    #         p = p.strip()
    #         if not p:
    #             continue
    #         try:
    #             params.append(float(p))
    #         except Exception:
    #             params.append(0.0)
    #     return params

    # def _extract_symbol(self, token: str) -> str:
    #     """
    #     Extract the base symbol from a token.
    #     Examples:
    #         "F(1.5,2.0)" → "F"
    #         "+(15)" → "+"
    #         "-(-3.5)" → "-"
    #         "A" → "A"
    #         "[" → "["
    #     """
    #     # First check for single-character special symbols
    #     if token[0] in {'+', '-', '[', ']'}:
    #         return token[0]
    #
    #     # Then check for alphanumeric symbols
    #     match = re.match(r"([A-Za-z0-9]+)", token)
    #     return match.group(1) if match else token

    def _get_color(self, symbol: str, params: list, depth: int) -> str:
        """Override this in subclasses for custom coloring"""
        return "rgb(50, 50, 50)"  # Default gray

    def draw(self, tokens: List[str], save_file: str, save_folder="fractals"):
        """

        Mutual 2d draw method for all classes

        :param tokens:
        :param save_file:
        :param save_folder:
        :return:
        """

        os.makedirs(save_folder, exist_ok=True)
        save_path = os.path.join(save_folder, save_file.replace(".png", ".svg"))

        segments = []
        stack = []
        depth = 0
        x, y, angle = 0.0, 0.0, np.pi / 2
        min_x, max_x, min_y, max_y = 0, 0, 0, 0

        max_depth = 0

        segments_by_color = defaultdict(list)

        for token in tokens:
            symbol = extract_symbol(token)
            params = parse_params(token)

            if symbol in self.drawing_symbols:
                length_mul = params[0] if len(params) >= 1 else 1.0
                width_mul = params[1] if len(params) >= 2 else 1.0
                length = self.base_length * length_mul
                width = self.base_width * width_mul

                new_x = x + length * np.cos(angle)
                new_y = y + length * np.sin(angle)

                color = self._get_color(symbol, params, depth)
                segments_by_color[color].append((x, y, new_x, new_y, width))

                segments.append((x, y, new_x, new_y, width))

                min_x = min(min_x, x, new_x)
                max_x = max(max_x, x, new_x)
                min_y = min(min_y, y, new_y)
                max_y = max(max_y, y, new_y)

                x, y = new_x, new_y

            elif symbol == "+":
                turn = np.deg2rad(params[0]) if params else self.base_angle
                angle += turn
            elif symbol == "-":
                turn = np.deg2rad(params[0]) if params else self.base_angle
                angle -= turn
            elif symbol == "[":
                stack.append((x, y, angle))
                depth += 1
            elif symbol == "]":
                if stack:
                    x, y, angle = stack.pop()
                    max_depth = max(max_depth, depth)
                    depth -= 1
            elif symbol in self.axiom_symbols:
                pass
            else:
                self.logger.warning(f"Unknown symbol {symbol}, skipping")

        padding = max(10, (max_x - min_x) * 0.05)
        width = max_x - min_x + 2 * padding
        height = max_y - min_y + 2 * padding

        svg = Element("svg", xmlns="http://www.w3.org/2000/svg")
        # Flip Y-axis by using negative height in viewBox
        svg.set("viewBox", f"{min_x - padding} {-(max_y + padding)} {width} {height}")
        svg.set("width", "1000")
        svg.set("height", "1000")

        # White background (adjust for flipped coordinates)
        bg = SubElement(svg, "rect")
        bg.set("x", str(min_x - padding))
        bg.set("y", str(-(max_y + padding)))
        bg.set("width", str(width))
        bg.set("height", str(height))
        bg.set("fill", "white")

        # Draw segments grouped by color
        for color, segments in segments_by_color.items():
            g = SubElement(svg, "g")
            g.set("stroke", color)
            g.set("stroke-linecap", "round")
            g.set("transform", "scale(1, -1)")

            for x1, y1, x2, y2, w in segments:
                line = SubElement(g, "line")
                line.set("x1", str(x1))
                line.set("y1", str(y1))
                line.set("x2", str(x2))
                line.set("y2", str(y2))
                line.set("stroke-width", str(w))

        tree = ElementTree(svg)
        tree.write(save_path, encoding="unicode", xml_declaration=True)

        self.logger.info(f"Saved SVG to {save_path}")
        self.logger.info(f" max depth recorded {max_depth}")


class TreeDrawer(SVGDrawer2D):
    """For more tree-like structures with pronounced trunk"""

    def __init__(self, logger, base_width=1.0, base_length=10.0, base_angle=25.0):
        super().__init__(logger, base_width, base_length, base_angle)
        self.drawing_symbols = {"F"}

    def _get_color(self, symbol: str, params: list, depth: int) -> str:
        width_mul = params[1] if len(params) >= 2 else 1.0

        # Trees: use depth AND width for more realistic coloring
        if depth <= 1 or width_mul > 2.0:
            # Main trunk - dark brown
            return "rgb(92, 51, 23)"
        elif depth <= 2 or width_mul > 1.0:
            # Major branches - medium brown
            return "rgb(120, 80, 35)"
        elif depth <= 3 or width_mul > 0.5:
            # Minor branches - light brown with green tint
            return "rgb(100, 100, 30)"
        else:
            # Leaves - green with variation
            green_variation = min(139, 100 + depth * 5)
            return f"rgb(34, {green_variation}, 34)"


class GeometricDrawer(SVGDrawer2D):
    """For geometric fractals like Koch, Hilbert, Levy"""

    def __init__(self, logger, base_width=1.0, base_length=10.0, base_angle=25.0):
        super().__init__(logger, base_width, base_length, base_angle)
        self.drawing_symbols = {"F"}

    def _get_color(self, symbol: str, params: list, depth: int) -> str:
        # Cool blue color for geometric patterns
        return "rgb(30, 144, 255)"


class SierpinskiDrawer(SVGDrawer2D):
    """For Sierpinski fractals that use multiple drawing symbols"""

    def __init__(self, logger, base_width=1.0, base_length=10.0, base_angle=25.0):
        super().__init__(logger, base_width, base_length, base_angle)
        self.drawing_symbols = {"F", "G", "A", "B"}

    def _get_color(self, symbol: str, params: list, depth: int) -> str:
        # Gradient from purple to pink based on depth
        if symbol in {"F", "A"}:
            # Purple tones
            red = min(180, 138 + depth * 8)
            return f"rgb({red}, 43, 226)"
        else:  # G, B
            # Pink tones
            red = min(255, 255 - depth * 10)
            return f"rgb({red}, 105, 180)"


class DragonDrawer(SVGDrawer2D):
    """For dragon curve - fire colors"""

    def __init__(self, logger, base_width=1.0, base_length=10.0, base_angle=25.0):
        super().__init__(logger, base_width, base_length, base_angle)
        self.drawing_symbols = {"F", "G"}

    def _get_color(self, symbol: str, params: list, depth: int) -> str:
        # Fire gradient: yellow -> orange -> red
        if symbol == "F":
            # Yellow to orange
            green = max(69, 165 - depth * 10)
            return f"rgb(255, {green}, 0)"
        else:  # G
            # Orange to red
            green = max(0, 69 - depth * 7)
            return f"rgb(255, {green}, 0)"


class PlantDrawer(SVGDrawer2D):

    """For fractal plants and ferns"""

    def __init__(self, logger, base_width=1.0, base_length=10.0, base_angle=25.0):
        super().__init__(logger, base_width, base_length, base_angle)
        self.drawing_symbols = {"F"}
        self.axiom_symbols = {"X"}

    def _get_color(self, symbol: str, params: list, depth: int) -> str:
        width_mul = params[1] if len(params) >= 2 else 1.0

        # Brown trunk/stem transitions to green leaves
        if depth <= 1 or width_mul > 1.5:
            # Thick base - brown
            return "rgb(101, 67, 33)"
        elif depth <= 3 or width_mul > 0.8:
            # Medium branches - olive
            return "rgb(85, 107, 47)"
        else:
            # Thin branches and leaves - green
            greenness = min(180, 100 + depth * 8)
            return f"rgb(34, {greenness}, 34)"


@dataclass
class DrawersPile:

    """
    data holder to extract appropriate holder by name
    """

    __drawers = {
        "general": SVGDrawer2D,
        "geometric": GeometricDrawer,
        "sierpinski": SierpinskiDrawer,
        "dragon": DragonDrawer,
        "plant": PlantDrawer,
        "tree": TreeDrawer,
    }

    def get_drawer(self, object_name):
        if object_name not in self.__drawers:
            raise Exception(f"Unknown drawer {object_name}")
        return self.__drawers[object_name]
