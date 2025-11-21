"""Debug script to trace parser execution."""

import sys
from pyshort.core.tokenizer import Tokenizer
from pyshort.core.parser import Parser

# Simple test case
source = """# [M:Test] [Role:Core]

pos ∈ f32[N]@GPU
"""

print("=== TOKENIZING ===")
tokenizer = Tokenizer(source)
tokens = tokenizer.tokenize()

for i, tok in enumerate(tokens[:20]):  # First 20 tokens
    print(f"{i:3d}: {tok.type.name:15s} {tok.value!r:20s} L{tok.line}:{tok.column}")

print("\n=== PARSING (with trace) ===")

# Monkey-patch Parser to add trace
original_advance = Parser.advance
call_count = [0]

def traced_advance(self):
    call_count[0] += 1
    if call_count[0] > 100:
        print(f"\n!!! INFINITE LOOP DETECTED (100+ advances) !!!")
        print(f"Current token: {self.current_token}")
        print(f"Position: {self.pos}")
        sys.exit(1)
    result = original_advance(self)
    print(f"  advance() -> {self.current_token.type.name:15s} {self.current_token.value!r:20s} (pos={self.pos})")
    return result

Parser.advance = traced_advance

parser = Parser(tokens)
try:
    ast = parser.parse()
    print(f"\n=== SUCCESS ===")
    print(f"Metadata: {ast.metadata.module_name}")
    print(f"Total advances: {call_count[0]}")
except Exception as e:
    print(f"\n=== ERROR ===")
    print(f"Exception: {e}")
    print(f"Total advances before crash: {call_count[0]}")
    import traceback
    traceback.print_exc()
