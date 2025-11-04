import re
from typing import List, Tuple


def modify_axioms_with_base(
    axioms: List[Tuple[str, str, float]], base_angle=25, base_length=1, base_width=1
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
