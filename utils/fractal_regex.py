import re
from typing import List


def parse_params(token: str) -> List[float]:
    """

    extract float param from token, e.g.
    F(1,2) -> [1,2]
    F -> []

    :param token:
    :return:
    """

    m = re.search(
        r"\(([^)]*)\)", token
    )  # search since params might be at any pos in token

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


def make_regex(key: str):
    """
    Create regex pattern for L-system rule matching.
    If key has parameters (e.g., "F(x,y)"), require them in the match.
    If key has no parameters (e.g., "F"), match just the symbol.
    """

    if "(" not in key:
        if key in {"+", "-"}:
            # Avoid matching +/- inside numbers
            return rf"(?<![\d.])\{key}"
        return re.escape(key)

    # Handle parameterized patterns - REQUIRE parentheses
    base = key.split("(")[0]
    param_pattern = r"\(([^)]*)\)"  # Required, not optional

    if base in {"+", "-"}:
        return rf"(?<![\d.])\{base}{param_pattern}"
    return re.escape(base) + param_pattern


def extract_symbol(token: str) -> str:
    """
    Extract the base symbol from a token.
    Examples:
        "F(1.5,2.0)" → "F"
        "+(15)" → "+"
        "-(-3.5)" → "-"
        "A" → "A"
        "[" → "["
    """

    # First check for single-character special symbols
    if token[0] in {"+", "-", "[", "]"}:
        return token[0]

    # check for alphanumeric symbols
    match = re.match(r"([A-Za-z0-9]+)", token)
    return match.group(1) if match else token
