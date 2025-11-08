import ast
import operator
import random
import re
from typing import Any, Callable


class SafeLambdaParser:
    """Safely parse and execute lambda-like expressions from strings"""

    SAFE_OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }

    SAFE_FUNCTIONS = {
        "abs": abs,
        "min": min,
        "max": max,
        "round": round,
        "int": int,
        "float": float,
        "random": random.random,
        "uniform": random.uniform,
        "triangular": random.triangular,
        "randint": random.randint,
        "gauss": random.gauss,
    }

    def parse_lambda_string(self, lambda_str: str) -> Callable:
        """
        Parse strings like:
        - "FT({x*0.9},{y*0.8})"
        - "+({x + random.triangular(-5, 5)})"
        - "+({{x + random.triangular(-5, 5)}})"  # Handle double braces

        Returns a callable function
        """
        # Normalize: convert {{ }} to { } for processing
        template = lambda_str.replace("{{", "{").replace("}}", "}")
        param_names = self._extract_params(template)
        expected_arg_count = len(param_names)

        # Create the lambda function
        def dynamic_lambda(*args):
            if len(args) < expected_arg_count:
                return ""  # fallback

            bindings = dict(zip(param_names, args))

            # Find all expressions in curly braces (non-greedy)
            def replace_expr(match):
                expr = match.group(1)
                try:
                    result = self._eval_expr(expr, bindings)
                    return str(result)
                except Exception as e:
                    raise ValueError(f"Failed to evaluate '{expr}': {e}")

            # Replace all {expr} with evaluated values
            result = re.sub(r"\{([^}]+)\}", replace_expr, template)
            return result

        return dynamic_lambda

    def _extract_params(self, template: str) -> list:
        """
        Extract parameter names from expressions in curly braces.
        E.g., "FT({x*0.9},{y*0.8})" -> ['x', 'y']
        """
        expressions = re.findall(r"\{([^}]+)\}", template)
        param_names = set()

        for expr in expressions:
            # Find all identifiers (variable names)
            for token in re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]*\b", expr):
                # Skip function names and common modules
                if token not in self.SAFE_FUNCTIONS and token not in {"random"}:
                    param_names.add(token)

        # Return in consistent order (alphabetical)
        return sorted(param_names)

    def _eval_expr(self, expr: str, bindings: dict) -> Any:
        """
        Safely evaluate an expression with given variable bindings.
        Uses AST to parse and whitelist operations.
        """
        try:
            tree = ast.parse(expr, mode="eval")
            return self._eval_node(tree.body, bindings)
        except SyntaxError as e:
            raise ValueError(f"Invalid syntax in expression '{expr}': {e}")

    def _eval_node(self, node, bindings: dict) -> Any:
        """Recursively evaluate AST nodes"""

        # Python 3.8+: ast.Constant replaces ast.Num, ast.Str, etc.
        if isinstance(node, ast.Constant):
            return node.value

        # Python 3.7 compatibility
        elif isinstance(node, ast.Num):
            return node.n

        elif isinstance(node, ast.Name):
            # Variable lookup
            if node.id in bindings:
                return bindings[node.id]
            else:
                raise NameError(f"Variable '{node.id}' not found in {bindings.keys()}")

        elif isinstance(node, ast.BinOp):
            # Binary operation (e.g., x * 0.9)
            left = self._eval_node(node.left, bindings)
            right = self._eval_node(node.right, bindings)
            op_type = type(node.op)
            if op_type in self.SAFE_OPERATORS:
                return self.SAFE_OPERATORS[op_type](left, right)  # type: ignore
            else:
                raise ValueError(f"Unsupported operation: {op_type}")

        elif isinstance(node, ast.UnaryOp):
            # Unary operation (e.g., -x)
            operand = self._eval_node(node.operand, bindings)
            op_type = type(node.op)  # type: ignore
            if op_type in self.SAFE_OPERATORS:
                return self.SAFE_OPERATORS[op_type](operand)  # type: ignore
            else:
                raise ValueError(f"Unsupported unary operation: {op_type}")

        elif isinstance(node, ast.Call):
            # Function call (e.g., random.triangular(-5, 5))
            func_name = self._get_func_name(node.func, bindings)

            if func_name not in self.SAFE_FUNCTIONS:
                raise ValueError(
                    f"Function '{func_name}' not allowed. Available: {list(self.SAFE_FUNCTIONS.keys())}"
                )

            # Evaluate arguments
            args = [self._eval_node(arg, bindings) for arg in node.args]
            kwargs = {
                kw.arg: self._eval_node(kw.value, bindings) for kw in node.keywords
            }

            return self.SAFE_FUNCTIONS[func_name](*args, **kwargs)  # type: ignore

        else:
            raise ValueError(f"Unsupported AST node type: {type(node).__name__}")

    def _get_func_name(self, node, bindings: dict) -> str:
        """Extract function name from Call node"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            # Handle module.function (e.g., random.triangular)
            if isinstance(node.value, ast.Name) and node.value.id == "random":
                return node.attr  # Return just 'triangular', 'uniform', etc.
            return node.attr
        else:
            raise ValueError(f"Unsupported function call type: {type(node)}")


def create_parametric_lambda(replacement: str) -> Callable:
    """
    Convert string like "FT({x*0.9},{y*0.8})" to actual lambda function.
    Automatically detects parameter count and names.
    """
    parser = SafeLambdaParser()
    return parser.parse_lambda_string(replacement)


# Test function
def test_lambda_parser():
    """Test the parser with various inputs"""

    print("Testing lambda parser...")

    # Test 1: Simple parameters
    func1 = create_parametric_lambda("FT({x*0.9},{y*0.8})")
    result1 = func1(10, 5)
    print(f"Test 1: {result1}")
    assert result1 == "FT(9.0,4.0)", f"Expected 'FT(9.0,4.0)', got '{result1}'"

    # Test 2: Single brace (your case)
    func2 = create_parametric_lambda("+({x + random.triangular(-5, 5)})")
    result2 = func2(10)
    print(f"Test 2: {result2}")
    # Result should be between +(5) and +(15)

    # Test 3: Double braces (escaped)
    func3 = create_parametric_lambda("+({{x + random.triangular(-5, 5)}})")
    result3 = func3(10)
    print(f"Test 3: {result3}")

    # Test 4: Complex
    func4 = create_parametric_lambda("FB({x*0.8},{y*0.6})[+(15)FL({x*0.6},{y*0.6})]")
    result4 = func4(10, 8)
    print(f"Test 4: {result4}")
    assert "FB(8.0,4.8)" in result4

    # Test 5: Edge case - nested function calls
    func5 = create_parametric_lambda("F({max(x, y)})")
    result5 = func5(3, 7)
    print(f"Test 5: {result5}")
    assert result5 == "F(7)", f"Expected 'F(7)', got '{result5}'"

    print("All tests passed! ✓")


if __name__ == "__main__":
    test_lambda_parser()
