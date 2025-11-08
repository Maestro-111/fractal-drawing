import ast
import inspect
import random
import re


class LSystemMixin:
    def __init__(self, axiom: str, logger):
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

            pattern = self._make_regex(key)

            self.logger.info(
                f"Generated pattern {pattern} for : {key} with the "
                f"following replacement: {replacement} and probability: {prob}"
            )

            base = self._base_symbol(key)

            self.rules.setdefault(base, []).append((replacement, pattern, prob))

    def _make_regex(self, key: str):
        """
        Match both parameterized and non-parameterized versions.
        Avoid matching + or - inside numeric expressions.
        """
        if "(" not in key:
            if key in {"+", "-"}:
                return rf"(?<![\d.])\{key}(?:\(([^)]*)\))?"
            return re.escape(key)

        base = key.split("(")[0]
        # optional parentheses with any number of comma-separated params
        param_pattern = r"(?:\(([^)]*)\))?"
        # also guard against matches inside numbers for + or -
        if base in {"+", "-"}:
            return rf"(?<![\d.])\{base}{param_pattern}"
        return re.escape(base) + param_pattern

    def _base_symbol(self, key: str):
        """Return the symbol name before '(' if parameterized."""
        return key.split("(")[0]

    def _pick_rule(self, rules):
        """Select a rule based on probabilities."""
        if len(rules) == 1:
            return rules[0]
        p = random.random()
        cumulative = 0
        for r in rules:
            cumulative += r[2]
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

    def _apply_rule(self, pattern, rules, match):
        replacement, _, _ = self._pick_rule(rules)
        if isinstance(replacement, str):
            return replacement

        params = match.group(1)
        args = []
        if params:
            for p in params.split(","):
                val = self._safe_eval_number(p)
                args.append(val)

        # adjust arg count to lambda’s signature
        sig = inspect.signature(replacement)
        n_expected = len(sig.parameters)
        if len(args) < n_expected:
            args += [1.0] * (n_expected - len(args))

        # self.logger.info(
        #     f"Pattern: {pattern}, matched: {match.group(0)}, args={args}, replacement={replacement}"
        # )

        result = replacement(*args)
        return result

    def generate(self, n_iter: int = 1):
        """Apply all rules for n iterations."""
        for i in range(n_iter):
            self.logger.info(f"Generating layer for {i}th iteration")

            new_state = self.state
            for base, rules in self.rules.items():
                pattern = rules[0][1]  # same regex for all rules under this symbol
                new_state = re.sub(
                    pattern, lambda m: self._apply_rule(pattern, rules, m), new_state
                )
            self.state = new_state

            self.logger.info(f"Finished generating layer for {i}th iteration")
            self.logger.info(
                f"length {len(self.state)}; {self.state[:200]}... new state"
            )

        return self.state
