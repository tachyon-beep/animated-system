"""Debug class parsing."""

from pyshort.core.tokenizer import Tokenizer
from pyshort.core.parser import Parser

source = """# [M:Test]

[C:VHE]
  pos ∈ f32[N]@GPU
  vel ∈ f32[N]@GPU
"""

tokenizer = Tokenizer(source)
tokens = tokenizer.tokenize()

print("Tokens:")
for i, tok in enumerate(tokens):
    print(f"  {i:2d}: {tok.type.name:15s} {tok.value!r:20s} L{tok.line}")

# Monkey patch to trace
Parser_parse_class = Parser.parse_class

def traced_parse_class(self, line):
    print(f"\n=== parse_class called at token {self.pos}: {self.current_token} ===")
    result = Parser_parse_class(self, line)
    print(f"=== parse_class done, state vars: {len(result.state)} ===")
    print(f"Current token after parse_class: {self.current_token}")
    return result

Parser.parse_class = traced_parse_class

parser = Parser(tokens)
try:
    ast = parser.parse()
    print(f"\n✓ SUCCESS")
    print(f"Entities: {len(ast.entities)}")
    if ast.entities:
        print(f"  State vars in class: {len(ast.entities[0].state)}")
        for sv in ast.entities[0].state:
            print(f"    - {sv.name}")
except Exception as e:
    print(f"\n✗ ERROR: {e}")
    import traceback
    traceback.print_exc()
