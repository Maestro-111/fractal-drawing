import ast
import inspect
import random
from typing import List

from utils.fractal_regex import extract_symbol, parse_params
from utils.tokenizer import LSystemLexer


class LSystemMixin:
    def __init__(self, axiom: List[str], logger):
        self.axiom = axiom
        self.state = axiom
        self.logger = logger
        self.rules = (  # type: ignore
            {}
        )  # { base_symbol: [(replacement, regex_pattern, probability), ...] }

    def add_rules(self, rules):
        """
        Add L-system rules.
        Each rule can be:
            (key, replacement)
            (key, replacement, probability)

        Example:
            ("A", "F(1,1)[+A][-A]", 0.5)
            ("F(x,y)", lambda x, y: f"F({1.2*x},{1.3*y})")
            ("+(angle)", lambda angle=15: f"+({angle + 10})")
        """

        for rule in rules:
            if len(rule) == 3:
                key, replacement, prob = rule
            else:
                key, replacement = rule
                prob = 1.0

            self.logger.info(f"Adding rule for : {key}")

            self.logger.info(
                f"following replacement: {replacement} and probability: {prob}"
            )

            base = extract_symbol(key)

            self.rules.setdefault(base, []).append((replacement, prob))

    @staticmethod
    def _pick_rule(rules):
        """Select a rule based on probabilities."""
        if len(rules) == 1:
            return rules[0]
        p = random.random()
        cumulative = 0
        for r in rules:
            cumulative += r[1]
            if p <= cumulative:
                return r
        return rules[-1]

    @staticmethod
    def _safe_eval_number(expr: str):
        """Return float value for simple expressions like '-(-4.3)' or '2*3'."""
        expr = expr.strip()
        if not expr:
            return 0.0
        try:
            val = ast.literal_eval(expr)
            if isinstance(val, (int, float)):
                return float(val)
        except Exception:
            pass
        try:
            val = eval(expr, {"__builtins__": {}})
            return float(val)
        except Exception:
            return 0.0

    def _apply_rule(self, rules, token_params):
        replacement, _ = self._pick_rule(rules)

        if isinstance(replacement, str):
            return replacement

        # adjust arg count to lambda’s signature
        sig = inspect.signature(replacement)
        n_expected = len(sig.parameters)

        if len(token_params) < n_expected:
            token_params += [1.0] * (n_expected - len(token_params))

        result = replacement(*token_params)
        return result

    def generate(self, n_iter: int = 1):
        """Apply all rules for n iterations."""

        for i in range(n_iter):
            self.logger.info(f"Generating layer for {i}th iteration")

            new_state = []

            for token in self.state:
                token_base = extract_symbol(token)
                token_params = parse_params(token)

                token_rules = self.rules.get(token_base, [])

                if not token_rules:
                    new_state.append(token_base)
                    continue

                new_raw_str = self._apply_rule(token_rules, token_params)
                tokenizer = LSystemLexer(new_raw_str)

                new_token = tokenizer.tokenize()
                new_state.extend(new_token)

            self.state = new_state

            self.logger.info(f"Finished generating layer for {i}th iteration")
            self.logger.info(
                f"length {len(self.state)}; {self.state[:50]}... new state"
            )

        return self.state
