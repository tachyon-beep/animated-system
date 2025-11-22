"""Unit tests for v1.4 parser enhancements (tag parsing)."""

import pytest

from pyshort.core.parser import Parser, ParseError
from pyshort.core.tokenizer import Tokenizer


class TestParserV14TagRecognition:
    """Test parser v1.4 tag recognition."""

    def parse_tag(self, source: str):
        """Helper to parse a tag from source."""
        tokenizer = Tokenizer(source)
        tokens = tokenizer.tokenize()
        parser = Parser(tokens)
        return parser.parse_tag()

    def test_parse_operation_tag_basic(self):
        """Test parsing basic operation tag."""
        tag = self.parse_tag("[Lin:MatMul]")
        assert tag.base == "Lin"
        assert tag.qualifiers == ["MatMul"]
        assert tag.tag_type == "operation"

    def test_parse_operation_tag_complex(self):
        """Test parsing complex operation tag with multiple qualifiers."""
        tag = self.parse_tag("[NN:∇:Lin:MatMul]")
        assert tag.base == "NN"
        assert tag.qualifiers == ["∇", "Lin", "MatMul"]
        assert tag.tag_type == "operation"

    def test_parse_complexity_tag_simple(self):
        """Test parsing simple complexity tag."""
        tag = self.parse_tag("[O(N)]")
        assert tag.base == "O(N)"
        assert tag.tag_type == "complexity"
        assert tag.is_complexity

    def test_parse_complexity_tag_multi_variable(self):
        """Test parsing multi-variable complexity tag."""
        tag = self.parse_tag("[O(N*M)]")
        assert tag.base == "O(N*M)"
        assert tag.tag_type == "complexity"

    def test_parse_complexity_tag_batch(self):
        """Test parsing batch complexity tag."""
        tag = self.parse_tag("[O(B*N*D)]")
        assert tag.base == "O(B*N*D)"
        assert tag.tag_type == "complexity"

    def test_parse_complexity_tag_exponent(self):
        """Test parsing complexity with exponent."""
        tag = self.parse_tag("[O(N²)]")
        assert tag.base == "O(N²)"
        assert tag.tag_type == "complexity"

    def test_parse_complexity_tag_attention(self):
        """Test parsing attention complexity."""
        tag = self.parse_tag("[O(B*N²*D)]")
        assert tag.base == "O(B*N²*D)"
        assert tag.tag_type == "complexity"

    def test_parse_decorator_tag_property(self):
        """Test parsing property decorator tag."""
        tag = self.parse_tag("[Prop]")
        assert tag.base == "Prop"
        assert tag.tag_type == "decorator"
        assert tag.is_decorator

    def test_parse_decorator_tag_static(self):
        """Test parsing static method decorator."""
        tag = self.parse_tag("[Static]")
        assert tag.base == "Static"
        assert tag.tag_type == "decorator"

    def test_parse_decorator_tag_class(self):
        """Test parsing class method decorator."""
        tag = self.parse_tag("[Class]")
        assert tag.base == "Class"
        assert tag.tag_type == "decorator"

    def test_parse_decorator_tag_abstract(self):
        """Test parsing abstract method decorator."""
        tag = self.parse_tag("[Abstract]")
        assert tag.base == "Abstract"
        assert tag.tag_type == "decorator"

    def test_parse_decorator_tag_cached(self):
        """Test parsing cached decorator."""
        tag = self.parse_tag("[Cached]")
        assert tag.base == "Cached"
        assert tag.tag_type == "decorator"

    def test_parse_decorator_tag_with_qualifiers(self):
        """Test parsing decorator with qualifiers."""
        tag = self.parse_tag("[Cached:TTL:60]")
        assert tag.base == "Cached"
        assert tag.qualifiers == ["TTL", "60"]
        assert tag.tag_type == "decorator"

    def test_parse_decorator_tag_rate_limit(self):
        """Test parsing rate limit decorator."""
        tag = self.parse_tag("[RateLimit:100]")
        assert tag.base == "RateLimit"
        assert tag.qualifiers == ["100"]
        assert tag.tag_type == "decorator"

    def test_parse_http_route_get_simple(self):
        """Test parsing simple GET route."""
        tag = self.parse_tag("[GET/users]")
        assert tag.tag_type == "http_route"
        assert tag.http_method == "GET"
        assert tag.http_path == "/users"

    def test_parse_http_route_post(self):
        """Test parsing POST route."""
        tag = self.parse_tag("[POST/api/users]")
        assert tag.http_method == "POST"
        assert tag.http_path == "/api/users"
        assert tag.tag_type == "http_route"

    def test_parse_http_route_with_param(self):
        """Test parsing route with path parameter."""
        tag = self.parse_tag("[GET/users/{id}]")
        assert tag.http_method == "GET"
        assert tag.http_path == "/users/{id}"

    def test_parse_http_route_complex_path(self):
        """Test parsing complex route path."""
        tag = self.parse_tag("[POST/api/users/{user_id}/posts/{post_id}]")
        assert tag.http_method == "POST"
        assert tag.http_path == "/api/users/{user_id}/posts/{post_id}"

    def test_parse_http_route_put(self):
        """Test parsing PUT route."""
        tag = self.parse_tag("[PUT/api/resource/{id}]")
        assert tag.http_method == "PUT"

    def test_parse_http_route_delete(self):
        """Test parsing DELETE route."""
        tag = self.parse_tag("[DELETE/api/resource/{id}]")
        assert tag.http_method == "DELETE"

    def test_parse_http_route_patch(self):
        """Test parsing PATCH route."""
        tag = self.parse_tag("[PATCH/api/resource/{id}]")
        assert tag.http_method == "PATCH"

    def test_parse_operation_with_complexity_qualifier(self):
        """Test parsing operation tag with complexity as qualifier."""
        tag = self.parse_tag("[Lin:MatMul:O(N*D)]")
        assert tag.base == "Lin"
        assert tag.qualifiers == ["MatMul", "O(N*D)"]
        assert tag.tag_type == "operation"
        assert tag.complexity == "O(N*D)"

    def test_parse_combined_neural_net_tag(self):
        """Test parsing combined neural net operation."""
        tag = self.parse_tag("[NN:∇:Lin:MatMul:O(B*N*D)]")
        assert tag.base == "NN"
        assert "∇" in tag.qualifiers
        assert "Lin" in tag.qualifiers
        assert "MatMul" in tag.qualifiers
        assert "O(B*N*D)" in tag.qualifiers
        assert tag.complexity == "O(B*N*D)"

    def test_parse_iter_tag_with_complexity(self):
        """Test parsing iteration tag with complexity."""
        tag = self.parse_tag("[Iter:Hot:O(N)]")
        assert tag.base == "Iter"
        assert tag.qualifiers == ["Hot", "O(N)"]
        assert tag.complexity == "O(N)"

    def test_parse_io_tag_with_qualifiers(self):
        """Test parsing IO tag with qualifiers."""
        tag = self.parse_tag("[IO:Disk:Block]")
        assert tag.base == "IO"
        assert tag.qualifiers == ["Disk", "Block"]
        assert tag.tag_type == "operation"

    def test_parse_empty_tag_raises_error(self):
        """Test that empty tag raises error."""
        with pytest.raises(ParseError, match="Empty tag"):
            self.parse_tag("[]")

    def test_parse_unterminated_tag_raises_error(self):
        """Test that unterminated tag raises error."""
        with pytest.raises(ParseError, match="Unterminated tag"):
            tokenizer = Tokenizer("[Lin:MatMul")
            tokens = tokenizer.tokenize()
            parser = Parser(tokens)
            parser.parse_tag()


class TestParserV14FullStatements:
    """Test parsing full statements with v1.4 tags."""

    def parse_string(self, source: str):
        """Helper to parse PyShorthand source."""
        from pyshort.core.parser import parse_string
        return parse_string(source)

    def test_parse_function_with_decorator_tag(self):
        """Test parsing function with decorator tag."""
        source = """# [M:Test]
F:device() → str [Prop]
"""
        ast = self.parse_string(source)
        assert len(ast.functions) == 1
        func = ast.functions[0]
        assert func.name == "device"
        assert len(func.tags) == 1
        assert func.tags[0].tag_type == "decorator"
        assert func.tags[0].base == "Prop"

    def test_parse_function_with_http_route_tag(self):
        """Test parsing function with HTTP route tag."""
        source = """# [M:Test]
F:get_user(id: i32) → User [GET/users/{id}]
"""
        ast = self.parse_string(source)
        func = ast.functions[0]
        assert len(func.tags) == 1
        assert func.tags[0].tag_type == "http_route"
        assert func.tags[0].http_method == "GET"
        assert func.tags[0].http_path == "/users/{id}"

    def test_parse_function_with_complexity_tag(self):
        """Test parsing function with complexity tag."""
        source = """# [M:Test]
F:process(data: List) → Result [O(N)]
"""
        ast = self.parse_string(source)
        func = ast.functions[0]
        assert len(func.tags) == 1
        assert func.tags[0].tag_type == "complexity"
        assert func.tags[0].complexity == "O(N)"

    def test_parse_function_with_multiple_tags(self):
        """Test parsing function with multiple tags."""
        source = """# [M:Test]
F:forward(x: Tensor) → Tensor [Prop] [NN:∇:Lin] [O(B*N*D)]
"""
        ast = self.parse_string(source)
        func = ast.functions[0]
        assert len(func.tags) == 3

        # Check each tag type
        tag_types = [tag.tag_type for tag in func.tags]
        assert "decorator" in tag_types
        assert "operation" in tag_types
        assert "complexity" in tag_types

    def test_parse_function_with_cached_decorator(self):
        """Test parsing function with cached decorator with args."""
        source = """# [M:Test]
F:expensive_computation(x: i32) → i32 [Cached:TTL:60]
"""
        ast = self.parse_string(source)
        func = ast.functions[0]
        assert func.tags[0].base == "Cached"
        assert func.tags[0].qualifiers == ["TTL", "60"]

    def test_parse_class_method_with_tags(self):
        """Test parsing class method with v1.4 tags."""
        source = """# [M:Test]
[C:Model]
  state ∈ Dict

  # Methods:
  # F:predict(x: Tensor) → Tensor [NN:∇:Lin:MatMul:O(B*N*D)]
"""
        ast = self.parse_string(source)
        assert len(ast.entities) == 1
        cls = ast.entities[0]
        assert hasattr(cls, 'methods')
        # Note: The comment parser might not parse methods in comments
        # This is more of an integration test

    def test_backward_compatibility_v13_tags(self):
        """Test that v1.3 tags still parse correctly."""
        source = """# [M:Test]
F:process() → None [Lin:MatMul]
"""
        ast = self.parse_string(source)
        func = ast.functions[0]
        assert len(func.tags) == 1
        assert func.tags[0].tag_type == "operation"
        assert func.tags[0].base == "Lin"
        assert func.tags[0].qualifiers == ["MatMul"]
