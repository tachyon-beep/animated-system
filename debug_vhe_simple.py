"""Debug VHE-like structure."""

from pyshort.core.tokenizer import Tokenizer
from pyshort.core.parser import Parser

source = """# [M:Test]

[C:VHE]
  ◊ [Ref:Substrate]

  // Comment
  pos ∈ f32[N]@GPU
"""

tokenizer = Tokenizer(source)
tokens = tokenizer.tokenize()

print("Tokens (first 30):")
for i, tok in enumerate(tokens[:30]):
    print(f"  {i:2d}: {tok.type.name:15s} {tok.value!r:25s} L{tok.line}")

parser = Parser(tokens)
try:
    ast = parser.parse()
    print(f"\n✓ Parse succeeded")
    if ast.entities:
        cls = ast.entities[0]
        print(f"Class: {cls.name}")
        print(f"  Dependencies: {len(cls.dependencies)}")
        print(f"  State vars: {len(cls.state)}")
        for sv in cls.state:
            print(f"    - {sv.name}")

    if ast.diagnostics:
        print(f"\nDiagnostics:")
        for d in ast.diagnostics:
            print(f"  [{d.severity.value}] L{d.line}: {d.message}")
except Exception as e:
    print(f"\n✗ ERROR: {e}")
    import traceback
    traceback.print_exc()
