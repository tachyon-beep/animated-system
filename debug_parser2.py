"""Minimal debug to find infinite loop."""

from pyshort.core.tokenizer import Tokenizer
from pyshort.core.parser import Parser

source = """# [M:Test]
x ∈ f32
"""

tokenizer = Tokenizer(source)
tokens = tokenizer.tokenize()

print("Tokens:")
for i, tok in enumerate(tokens):
    print(f"  {i}: {tok.type.name} = {tok.value!r}")

print("\nParsing with loop detection...")

parser = Parser(tokens)

# Track positions to detect loops
position_history = []
max_same_position = 5

original_parse_statement = Parser.parse_statement

def traced_parse_statement(self, line):
    pos = self.pos
    position_history.append(pos)

    # Check for loop
    if len(position_history) > max_same_position:
        last_n = position_history[-max_same_position:]
        if len(set(last_n)) == 1:  # Same position 5 times
            print(f"\n!!! INFINITE LOOP at position {pos} !!!")
            print(f"Current token: {self.current_token}")
            print(f"Last {max_same_position} positions: {last_n}")
            import sys
            sys.exit(1)

    return original_parse_statement(self, line)

Parser.parse_statement = traced_parse_statement

try:
    ast = parser.parse()
    print("SUCCESS!")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
