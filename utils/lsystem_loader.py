import json
import re
from typing import List, Tuple

from .lambda_parser import SafeLambdaParser


class Loader:
    def __init__(self, object_name: str, logger, templates_path: str):
        self.object_name = object_name
        self.logger = logger

        self.templates_path = templates_path
        self.lambda_parser = SafeLambdaParser()

    def fetch_initial_template(self):
        """Load all templates from JSON file"""

        with open(self.templates_path, "r") as f:
            templates = json.load(f)
            template = templates.get(self.object_name, templates["placeholder"])

            base_axiom = template["base_axiom"]

            allowed_symbols = set()
            allowed_symbols.update(base_axiom)

            for rule in template["rules"]:
                symbols = [symbol for symbol in rule["pattern"]]
                allowed_symbols.update(symbols)

            return template, allowed_symbols

    def parse_rule(self, rule_dict):
        """Convert JSON rule dict to tuple format"""

        pattern = rule_dict["pattern"]

        probability = float(rule_dict.get("probability", 1.0))
        axiom = rule_dict.get("axiom", False)

        if rule_dict.get("is_parametric"):
            replacement = self.lambda_parser.parse_lambda_string(
                rule_dict["replacement"]
            )
        else:
            replacement = rule_dict["replacement"]

        return pattern, replacement, axiom, probability

    @staticmethod
    def modify_axioms_with_base(
        axioms: List[Tuple[str, str, float]], base_angle, base_length, base_width
    ):
        modified_axioms = []

        for key, rule, prob in axioms:
            # Replace "angle" as full word (not inside parentheses of +, etc.)
            rule = re.sub(r"\bangle\b", str(base_angle), rule)
            # Replace standalone "L" but not "FL", "AL", etc.
            rule = re.sub(r"(?<![A-Za-z])L(?![A-Za-z])", str(base_length), rule)
            # Replace standalone "W" but not "FW", "AW", etc.
            rule = re.sub(r"(?<![A-Za-z])W(?![A-Za-z])", str(base_width), rule)

            modified_axioms.append((key, rule, prob))

        return modified_axioms

    def get_init_params(
        self, template: dict
    ) -> Tuple[List, float, float, float, int, str]:
        """
        Load initial parameters for given object.
        Returns: (rules, length, angle, width)
        """

        self.logger.info(f"Loaded template for: {self.object_name}")

        axioms = []
        rules = []

        for rule in template["rules"]:
            pattern, replacement, axiom, probability = self.parse_rule(rule)

            if axiom:
                axioms.append((pattern, replacement, probability))
            else:
                rules.append((pattern, replacement, probability))

        base_axiom = template["base_axiom"]
        params = template["params"]
        length = params["length"]
        width = params["width"]
        angle = params["angle"]
        iterations = params["iterations"]

        modified_axiom_rules = self.modify_axioms_with_base(
            axioms, angle, length, width
        )
        self.logger.info(f"Parameters: length={length}, angle={angle}, width={width}")

        all_rules = modified_axiom_rules + rules

        self.logger.info(f"Rules: {len(all_rules)}")

        return all_rules, length, angle, width, iterations, base_axiom

    def get_drawer(self, template):
        """Return appropriate drawer based on drawer type and object type"""

        drawer_name = template.get("drawer_name", "general")

        self.logger.info(f"{self.object_name} requires drawer {drawer_name}")

        from drawning.draw_2d import DrawersPile

        pile = DrawersPile()
        return pile.get_drawer(drawer_name)
