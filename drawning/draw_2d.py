import os
import re

import matplotlib.pyplot as plt
import numpy as np


class LSystemDrawer2D:
    def __init__(self, logger, base_width=1.0, base_length=10.0, base_angle=25.0):
        self.base_width = base_width
        self.base_length = base_length
        self.base_angle = np.deg2rad(base_angle)
        self.logger = logger

    def _parse_tokens(self, sequence: str):
        """Split into tokens like F(1,2), +(30), -, [, ], A"""
        pattern = r"[A-Za-z]+(?:\([^)]*\))?|\+|\-|\[|\]"
        return re.findall(pattern, sequence)

    def _parse_params(self, token: str):
        """Extract numeric params safely."""
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
            except ValueError:
                try:
                    params.append(eval(p, {"__builtins__": {}}))
                except Exception:
                    params.append(0.0)
        return params

    def draw(self, sequence: str, save_file: str, save_folder="fractals"):
        os.makedirs(save_folder, exist_ok=True)
        save_path = os.path.join(save_folder, save_file)

        stack = []
        x, y, angle = 0.0, 0.0, np.pi / 2
        segments = []

        tokens = self._parse_tokens(sequence)

        for token in tokens:
            base = re.match(r"[A-Za-z\+\-]", token)
            symbol = base.group(0) if base else token
            params = self._parse_params(token)

            if symbol == "F":
                length_mul = params[0] if len(params) >= 1 else 1.0
                width_mul = params[1] if len(params) >= 2 else 1.0

                length = self.base_length * length_mul
                width = self.base_width * width_mul

                new_x = x + length * np.cos(angle)
                new_y = y + length * np.sin(angle)

                segments.append(((x, y), (new_x, new_y), width))
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
                x, y, angle = stack.pop()

        # --- Plot ---
        fig, ax = plt.subplots(figsize=(20, 20))
        if segments:
            # Draw each segment with its width
            for (x1, y1), (x2, y2), w in segments:
                ax.plot([x1, x2], [y1, y2], color="green", linewidth=w)
            ax.autoscale()
        ax.axis("off")
        plt.tight_layout()
        plt.savefig(save_path, dpi=300)
        plt.close(fig)


class TreeDrawer2D(LSystemDrawer2D):
    def __init__(self, logger, base_width=1.0, base_length=10.0, base_angle=25.0):
        super().__init__(logger, base_width, base_length, base_angle)

    def go_colored_forward(self, x, y, params, angle):
        length_mul = params[0] if len(params) >= 1 else 1.0
        width_mul = params[1] if len(params) >= 2 else 1.0

        length = self.base_length * length_mul
        width = self.base_width * width_mul

        new_x = x + length * np.cos(angle)
        new_y = y + length * np.sin(angle)

        return new_x, new_y, width

    def draw(self, sequence: str, save_file: str, save_folder="fractals"):
        os.makedirs(save_folder, exist_ok=True)
        save_path = os.path.join(save_folder, save_file)

        stack = []
        x, y, angle = 0.0, 0.0, np.pi / 2

        tokens = self._parse_tokens(sequence)
        fig, ax = plt.subplots(figsize=(10, 10))

        for token in tokens:
            base = re.match(r"[A-Za-z]+|\+|\-|\[|\]", token)
            symbol = base.group(0) if base else token
            params = self._parse_params(token)

            if symbol == "FT":
                new_x, new_y, new_width = self.go_colored_forward(x, y, params, angle)

                color = (0.36, 0.20, 0.09)
                ax.plot([x, new_x], [y, new_y], color=color, linewidth=new_width * 2)

                x, y = new_x, new_y

            elif symbol == "FB":
                new_x, new_y, new_width = self.go_colored_forward(x, y, params, angle)

                color = (0.55, 0.27, 0.07)
                ax.plot([x, new_x], [y, new_y], color=color, linewidth=new_width * 2)

                x, y = new_x, new_y

            elif symbol == "FL":
                new_x, new_y, new_width = self.go_colored_forward(x, y, params, angle)

                color = (0.0, 0.8, 0.0)

                ax.plot([x, new_x], [y, new_y], color=color, linewidth=new_width * 2)
                ax.scatter(new_x, new_y, color=color, s=3, zorder=3)

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
                x, y, angle = stack.pop()

        ax.axis("off")
        plt.tight_layout()
        plt.savefig(save_path, dpi=300)
        plt.close(fig)
