import os
import re
from xml.etree.ElementTree import Element, ElementTree, SubElement

import numpy as np


class SVGDrawer2D:

    """Fast SVG drawer - infinite zoom, small file size, fast rendering"""

    def __init__(self, logger, base_width=1.0, base_length=10.0, base_angle=25.0):
        self.base_width = base_width
        self.base_length = base_length
        self.base_angle = np.deg2rad(base_angle)
        self.logger = logger
        self.drawing_symbols = {"F", "A", "B", "X", "Y", "G", "W", "Z", "0", "1"}

    def _parse_tokens(self, sequence: str):
        pattern = r"[A-Za-z0-9]+(?:\([^)]*\))?|\+|\-|\[|\]"
        return re.findall(pattern, sequence)

    def _parse_params(self, token: str):
        m = re.search(r"\(([^)]*)\)", token)
        if not m:
            return []
        params = []
        for p in m.group(1).split(","):
            p = p.strip()
            if not p:
                continue
            try:
                params.append(float(p))
            except Exception:
                params.append(0.0)
        return params

    def _extract_symbol(self, token: str) -> str:
        match = re.match(r"([A-Za-z0-9]+)", token)
        return match.group(1) if match else token

    def draw(self, sequence: str, save_file: str, save_folder="fractals"):
        os.makedirs(save_folder, exist_ok=True)
        save_path = os.path.join(save_folder, save_file.replace(".png", ".svg"))

        # First pass: collect all segments to determine bounds
        segments = []
        stack = []
        x, y, angle = 0.0, 0.0, np.pi / 2
        min_x, max_x, min_y, max_y = 0, 0, 0, 0

        tokens = self._parse_tokens(sequence)

        for token in tokens:
            symbol = self._extract_symbol(token)
            params = self._parse_params(token)

            if symbol in self.drawing_symbols:
                length_mul = params[0] if len(params) >= 1 else 1.0
                width_mul = params[1] if len(params) >= 2 else 1.0
                length = self.base_length * length_mul
                width = self.base_width * width_mul

                new_x = x + length * np.cos(angle)
                new_y = y + length * np.sin(angle)

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
            elif symbol == "]":
                if stack:
                    x, y, angle = stack.pop()
            else:
                self.logger.warning(f"Unknown symbol {symbol}, skipping")

        # Calculate viewBox with padding
        padding = max(10, (max_x - min_x) * 0.05)
        width = max_x - min_x + 2 * padding
        height = max_y - min_y + 2 * padding

        # Create SVG
        svg = Element("svg", xmlns="http://www.w3.org/2000/svg")
        svg.set("viewBox", f"{min_x - padding} {min_y - padding} {width} {height}")
        svg.set("width", "1000")  # Default display size
        svg.set("height", "1000")

        # White background
        bg = SubElement(svg, "rect")
        bg.set("x", str(min_x - padding))
        bg.set("y", str(min_y - padding))
        bg.set("width", str(width))
        bg.set("height", str(height))
        bg.set("fill", "white")

        # Create a group for all lines
        g = SubElement(svg, "g")
        g.set("stroke", "green")
        g.set("stroke-linecap", "round")

        # Draw all segments
        for x1, y1, x2, y2, w in segments:
            line = SubElement(g, "line")
            line.set("x1", str(x1))
            line.set("y1", str(y1))
            line.set("x2", str(x2))
            line.set("y2", str(y2))
            line.set("stroke-width", str(w))

        # Save
        tree = ElementTree(svg)
        tree.write(save_path, encoding="unicode", xml_declaration=True)
        self.logger.info(f"Saved SVG to {save_path}")


class ColoredTreeSVGDrawer2D(SVGDrawer2D):
    """Colored SVG drawer for trees"""

    def __init__(self, logger, base_width=1.0, base_length=10.0, base_angle=25.0):
        super().__init__(logger, base_width, base_length, base_angle)
        self.drawing_symbols = {"FT", "FB", "FL", "F", "A", "B", "X", "Y"}
        self.color_map = {
            "FT": "rgb(92, 51, 23)",  # Dark brown
            "FB": "rgb(140, 69, 18)",  # Light brown
            "FL": "rgb(0, 204, 0)",  # Green
            "F": "rgb(50, 50, 50)",
            "A": "rgb(100, 100, 100)",
            "B": "rgb(150, 150, 150)",
            "X": "rgb(80, 80, 80)",
            "Y": "rgb(180, 180, 180)",
        }

    def _extract_symbol(self, token: str) -> str:
        match = re.match(r"(F[TBL]|[A-Za-z0-9])", token)
        return match.group(1) if match else token

    def draw(self, sequence: str, save_file: str, save_folder="fractals"):
        os.makedirs(save_folder, exist_ok=True)
        save_path = os.path.join(save_folder, save_file.replace(".png", ".svg"))

        # Collect segments with colors
        segments_by_color = {}  # type: ignore
        stack = []
        x, y, angle = 0.0, 0.0, np.pi / 2
        min_x, max_x, min_y, max_y = 0, 0, 0, 0

        tokens = self._parse_tokens(sequence)

        for token in tokens:
            symbol = self._extract_symbol(token)
            params = self._parse_params(token)

            if symbol in self.drawing_symbols:
                length_mul = params[0] if len(params) >= 1 else 1.0
                width_mul = params[1] if len(params) >= 2 else 1.0
                length = self.base_length * length_mul
                width = self.base_width * width_mul * 2

                new_x = x + length * np.cos(angle)
                new_y = y + length * np.sin(angle)

                color = self.color_map.get(symbol, "rgb(50,50,50)")

                if color not in segments_by_color:
                    segments_by_color[color] = []
                segments_by_color[color].append((x, y, new_x, new_y, width))

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
            elif symbol == "]":
                if stack:
                    x, y, angle = stack.pop()

        # Calculate viewBox
        padding = max(10, (max_x - min_x) * 0.05)
        width = max_x - min_x + 2 * padding
        height = max_y - min_y + 2 * padding

        # Create SVG
        svg = Element("svg", xmlns="http://www.w3.org/2000/svg")
        # FIX: Flip Y-axis by using negative height in viewBox
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
            # FIX: Apply scale transform to flip Y
            g.set("transform", "scale(1, -1)")

            for x1, y1, x2, y2, w in segments:
                line = SubElement(g, "line")
                line.set("x1", str(x1))
                line.set("y1", str(y1))
                line.set("x2", str(x2))
                line.set("y2", str(y2))
                line.set("stroke-width", str(w))

        # Save
        tree = ElementTree(svg)
        tree.write(save_path, encoding="unicode", xml_declaration=True)
        self.logger.info(f"Saved colored SVG to {save_path}")
