"""Unit tests for v1.4 AST node enhancements (Tag class)."""

import pytest

from pyshort.core.ast_nodes import Tag


class TestTagV14:
    """Test Tag class v1.4 enhancements."""

    def test_operation_tag_basic(self):
        """Test basic operation tag (v1.3 compatibility)."""
        tag = Tag(base="Lin", qualifiers=["MatMul"], tag_type="operation")
        assert tag.base == "Lin"
        assert tag.qualifiers == ["MatMul"]
        assert tag.tag_type == "operation"
        assert tag.is_operation
        assert not tag.is_complexity
        assert not tag.is_decorator
        assert not tag.is_http_route
        assert str(tag) == "[Lin:MatMul]"

    def test_complexity_tag_simple(self):
        """Test simple complexity tag."""
        tag = Tag(base="O(N)", tag_type="complexity")
        assert tag.base == "O(N)"
        assert tag.tag_type == "complexity"
        assert tag.is_complexity
        assert tag.complexity == "O(N)"
        assert str(tag) == "[O(N)]"

    def test_complexity_tag_multi_variable(self):
        """Test multi-variable complexity tag."""
        tag = Tag(base="O(N*M*D)", tag_type="complexity")
        assert tag.base == "O(N*M*D)"
        assert tag.is_complexity
        assert tag.complexity == "O(N*M*D)"
        assert str(tag) == "[O(N*M*D)]"

    def test_complexity_tag_exponent(self):
        """Test complexity tag with exponent."""
        tag = Tag(base="O(N²)", tag_type="complexity")
        assert tag.is_complexity
        assert tag.complexity == "O(N²)"

    def test_decorator_tag_property(self):
        """Test property decorator tag."""
        tag = Tag(base="Prop", tag_type="decorator")
        assert tag.base == "Prop"
        assert tag.tag_type == "decorator"
        assert tag.is_decorator
        assert str(tag) == "[Prop]"

    def test_decorator_tag_static(self):
        """Test static method decorator tag."""
        tag = Tag(base="Static", tag_type="decorator")
        assert tag.base == "Static"
        assert tag.is_decorator
        assert str(tag) == "[Static]"

    def test_decorator_tag_with_qualifiers(self):
        """Test decorator tag with qualifiers."""
        tag = Tag(base="Cached", qualifiers=["TTL", "60"], tag_type="decorator")
        assert tag.base == "Cached"
        assert tag.qualifiers == ["TTL", "60"]
        assert tag.is_decorator
        assert str(tag) == "[Cached:TTL:60]"

    def test_decorator_tag_rate_limit(self):
        """Test rate limit decorator tag."""
        tag = Tag(base="RateLimit", qualifiers=["100"], tag_type="decorator")
        assert tag.base == "RateLimit"
        assert tag.qualifiers == ["100"]
        assert str(tag) == "[RateLimit:100]"

    def test_http_route_get(self):
        """Test GET HTTP route tag."""
        tag = Tag(
            base="GET /users",
            tag_type="http_route",
            http_method="GET",
            http_path="/users"
        )
        assert tag.tag_type == "http_route"
        assert tag.http_method == "GET"
        assert tag.http_path == "/users"
        assert tag.is_http_route
        assert str(tag) == "[GET /users]"

    def test_http_route_post_with_params(self):
        """Test POST HTTP route with path parameters."""
        tag = Tag(
            base="POST /api/users/{id}",
            tag_type="http_route",
            http_method="POST",
            http_path="/api/users/{id}"
        )
        assert tag.http_method == "POST"
        assert tag.http_path == "/api/users/{id}"
        assert str(tag) == "[POST /api/users/{id}]"

    def test_http_route_complex_path(self):
        """Test HTTP route with complex path."""
        tag = Tag(
            base="GET /api/v1/resources/{resource_id}/items/{item_id}",
            tag_type="http_route",
            http_method="GET",
            http_path="/api/v1/resources/{resource_id}/items/{item_id}"
        )
        assert tag.http_path == "/api/v1/resources/{resource_id}/items/{item_id}"

    def test_operation_tag_with_complexity_qualifier(self):
        """Test operation tag that includes complexity as qualifier."""
        tag = Tag(base="Lin", qualifiers=["MatMul", "O(N*D)"], tag_type="operation")
        assert tag.is_operation
        assert tag.complexity == "O(N*D)"
        assert str(tag) == "[Lin:MatMul:O(N*D)]"

    def test_combined_operation_tag(self):
        """Test complex combined operation tag."""
        tag = Tag(base="NN", qualifiers=["∇", "Lin", "MatMul", "O(B*N*D)"], tag_type="operation")
        assert tag.base == "NN"
        assert "∇" in tag.qualifiers
        assert "Lin" in tag.qualifiers
        assert tag.complexity == "O(B*N*D)"
        assert str(tag) == "[NN:∇:Lin:MatMul:O(B*N*D)]"

    def test_custom_tag_type(self):
        """Test custom tag type."""
        tag = Tag(base="CustomTag", qualifiers=["Arg1"], tag_type="custom")
        assert tag.tag_type == "custom"
        assert str(tag) == "[CustomTag:Arg1]"

    def test_invalid_complexity_notation_raises_error(self):
        """Test that invalid complexity notation raises ValueError."""
        with pytest.raises(ValueError, match="Invalid complexity notation"):
            Tag(base="O(", tag_type="complexity")

    def test_invalid_http_route_missing_path_raises_error(self):
        """Test that HTTP route without path raises ValueError."""
        with pytest.raises(ValueError, match="must have both http_method and http_path"):
            Tag(base="GET", tag_type="http_route", http_method="GET", http_path=None)

    def test_invalid_http_method_raises_error(self):
        """Test that invalid HTTP method raises ValueError."""
        with pytest.raises(ValueError, match="Invalid HTTP method"):
            Tag(base="INVALID", tag_type="http_route", http_method="INVALID", http_path="/path")

    def test_http_route_path_must_start_with_slash(self):
        """Test that HTTP path must start with /."""
        with pytest.raises(ValueError, match="must start with '/'"):
            Tag(base="GET users", tag_type="http_route", http_method="GET", http_path="users")

    def test_unknown_decorator_becomes_custom(self):
        """Test that unknown decorator tags become custom type."""
        tag = Tag(base="UnknownDecorator", tag_type="decorator")
        # Should automatically convert to custom
        assert tag.tag_type == "custom"

    def test_tag_equality(self):
        """Test tag equality (frozen dataclass)."""
        tag1 = Tag(base="Lin", qualifiers=["MatMul"], tag_type="operation")
        tag2 = Tag(base="Lin", qualifiers=["MatMul"], tag_type="operation")
        tag3 = Tag(base="Lin", qualifiers=["Reduce"], tag_type="operation")
        assert tag1 == tag2
        assert tag1 != tag3

    def test_tag_immutability(self):
        """Test that tags are immutable (frozen)."""
        tag = Tag(base="Lin", tag_type="operation")
        with pytest.raises(Exception):  # FrozenInstanceError
            tag.base = "Modified"  # type: ignore

    def test_complexity_extraction_from_qualifiers(self):
        """Test complexity extraction from qualifiers list."""
        tag = Tag(base="Iter", qualifiers=["Hot", "O(N)", "Scan"], tag_type="operation")
        assert tag.complexity == "O(N)"

    def test_no_complexity_returns_none(self):
        """Test that tags without complexity return None."""
        tag = Tag(base="Lin", qualifiers=["MatMul"], tag_type="operation")
        assert tag.complexity is None

    def test_is_io_property(self):
        """Test is_io property."""
        tag = Tag(base="IO", qualifiers=["Disk"], tag_type="operation")
        assert tag.is_io

        tag2 = Tag(base="Lin", tag_type="operation")
        assert not tag2.is_io

    def test_is_sync_property(self):
        """Test is_sync property."""
        tag = Tag(base="Sync", qualifiers=["Lock"], tag_type="operation")
        assert tag.is_sync

        tag2 = Tag(base="Lin", tag_type="operation")
        assert not tag2.is_sync
