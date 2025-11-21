"""Test with class definition (like VHE)."""

from pyshort.core.tokenizer import Tokenizer
from pyshort.core.parser import Parser
import sys

source = """# [M:Test]

[C:TestClass]
  x ∈ f32[N]@GPU
  y ∈ f32[N]@GPU
"""

tokenizer = Tokenizer(source)
tokens = tokenizer.tokenize()

print("Tokens:")
for i, tok in enumerate(tokens[:30]):
    print(f"  {i}: {tok.type.name:15s} = {tok.value!r}")

print("\nParsing with loop detection...")

parser = Parser(tokens)

# Track calls
call_count = [0]
original_parse = Parser.parse

def traced_parse(self):
    call_count[0] += 1
    if call_count[0] > 1:
        # Only one call to parse() should happen
        print(f"Multiple parse() calls: {call_count[0]}")

    # Add timeout to the parse method itself
    position_visits = {}
    original_skip_whitespace = self.skip_whitespace

    def safe_skip_whitespace():
        pos = self.pos
        position_visits[pos] = position_visits.get(pos, 0) + 1
        if position_visits[pos] > 20:
            print(f"\n!!! LOOP in skip_whitespace at pos {pos} !!!")
            print(f"Token: {self.current_token}")
            sys.exit(1)
        return original_skip_whitespace()

    self.skip_whitespace = safe_skip_whitespace

    return original_parse(self)

Parser.parse = traced_parse

try:
    ast = parser.parse()
    print("SUCCESS!")
    print(f"Entities: {len(ast.entities)}")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
