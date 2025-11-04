import json
import re
from typing import List, Tuple

from .lambda_parser import SafeLambdaParser

# make a class!


def load_templates(templates_path="templates.json"):
    """Load all templates from JSON file"""
    with open(templates_path, "r") as f:
        return json.load(f)


def create_parametric_lambda(replacement: str):
    """
    Convert string like "FT({x*0.9},{y*0.8})"
    to actual lambda function
    """

    parser = SafeLambdaParser()  # how it works?
    return parser.parse_lambda_string(replacement)


def parse_rule(rule_dict):
    """Convert JSON rule dict to tuple format"""

    pattern = rule_dict["pattern"]
    probability = float(rule_dict.get("probability", 1.0))
    axiom = rule_dict.get("axiom", False)

    if rule_dict.get("is_parametric"):
        replacement = create_parametric_lambda(rule_dict["replacement"])
    else:
        replacement = rule_dict["replacement"]

    return (pattern, replacement, axiom, probability)


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
    object_name: str, templates_path
) -> Tuple[List, float, float, float, int, str]:
    """
    Load initial parameters for given object.
    Returns: (rules, length, angle, width)
    """
    templates = load_templates(templates_path)

    # Get template or fallback to placeholder
    if object_name not in templates:
        print(f"Warning: '{object_name}' not found in templates. Using placeholder.")
        template = templates["placeholder"]
    else:
        template = templates[object_name]

    axioms = []
    rules = []

    for rule in template["rules"]:
        pattern, replacement, axiom, probability = parse_rule(rule)

        if axiom:
            axioms.append((pattern, replacement, probability))
        else:
            rules.append((pattern, replacement, probability))

    params = template["params"]
    length = params["length"]
    width = params["width"]
    angle = params["angle"]
    iter = params["iterations"]
    base_axiom = template["base_axiom"]

    modified_axiom_rules = modify_axioms_with_base(axioms, angle, length, width)
    all_rules = modified_axiom_rules + rules

    return all_rules, length, angle, width, iter, base_axiom


def get_drawer(object_name: str, templates_path: str):
    """Return appropriate drawer based on color flag and object type"""
    templates = load_templates(templates_path)

    template = templates.get(object_name, templates["placeholder"])
    requires_color = template.get("supports_color", False)

    # if requires_color:
    #     raise ValueError(f"Object '{object_name}' does not support colored rendering. Set --color=False")

    from drawning.draw_2d import LSystemDrawer2D, TreeDrawer2D

    if requires_color:
        return TreeDrawer2D
    else:
        return LSystemDrawer2D
