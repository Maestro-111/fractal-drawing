class LSystemLexer:
    """
    Proper lexer for L-system strings.
    """

    def __init__(self, sequence: str):
        self.sequence = sequence
        self.pos = 0
        self.current_char = self.sequence[0] if sequence else None

    def advance(self):
        """Move to next character."""
        self.pos += 1
        if self.pos >= len(self.sequence):
            self.current_char = None
        else:
            self.current_char = self.sequence[self.pos]

    def peek(self):
        """Look at next character without advancing."""
        peek_pos = self.pos + 1
        if peek_pos >= len(self.sequence):
            return None
        return self.sequence[peek_pos]

    def skip_whitespace(self):
        """Skip any whitespace."""
        while self.current_char is not None and self.current_char.isspace():
            self.advance()

    def read_params(self):
        """Read parameter list like (1.5, 2.0, 3)."""

        if self.current_char != "(":
            return []

        self.advance()  # Skip '('

        params = []
        current_param = ""
        paren_depth = 1

        while self.current_char is not None and paren_depth > 0:
            if self.current_char == "(":
                paren_depth += 1
                current_param += self.current_char
            elif self.current_char == ")":
                paren_depth -= 1
                if paren_depth == 0:
                    # End of parameters
                    if current_param.strip():
                        try:
                            params.append((current_param.strip()))
                        except ValueError:
                            params.append("0.0")
                else:
                    current_param += self.current_char
            elif self.current_char == "," and paren_depth == 1:
                # Parameter separator
                if current_param.strip():
                    try:
                        params.append((current_param.strip()))
                    except ValueError:
                        params.append("0.0")
                current_param = ""
            else:
                current_param += self.current_char
            self.advance()

        return params

    def tokenize(self):
        """Return list of tokens."""
        tokens = []

        while self.current_char is not None:
            self.skip_whitespace()

            if self.current_char is None:
                break

            # Brackets
            if self.current_char == "[":
                tokens.append("[")
                self.advance()
            elif self.current_char == "]":
                tokens.append("]")
                self.advance()

            # Plus
            elif self.current_char == "+":
                symbol = self.current_char
                self.advance()
                params = self.read_params()
                if params:
                    tokens.append(f"{symbol}({", ".join(params)})")
                else:
                    tokens.append(symbol)

            # Minus
            elif self.current_char == "-":
                symbol = self.current_char
                self.advance()
                params = self.read_params()
                if params:
                    tokens.append(f"{symbol}({", ".join(params)})")
                else:
                    tokens.append(symbol)

            # Symbols (alphanumeric)
            elif self.current_char.isalnum():
                symbol = self.current_char
                self.advance()
                params = self.read_params()
                if params:
                    tokens.append(f"{symbol}({", ".join(params)})")
                else:
                    tokens.append(symbol)
            else:
                self.advance()

        return tokens
