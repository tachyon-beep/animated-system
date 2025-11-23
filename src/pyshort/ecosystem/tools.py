"""Core tools for PyShorthand ecosystem progressive disclosure."""

import ast
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass


@dataclass
class MethodImplementation:
    """Full implementation of a method."""

    class_name: str
    method_name: str
    source_code: str
    line_start: int
    line_end: int
    dependencies: List[str]  # Other methods called within this method


@dataclass
class ClassDetails:
    """Detailed class information."""

    name: str
    base_classes: List[str]
    attributes: Dict[str, str]  # name -> type annotation
    methods: Dict[str, str]  # name -> signature
    nested_structures: Dict[str, str]  # For ModuleDict, etc.


class CodebaseExplorer:
    """
    Progressive disclosure system for code understanding.

    Provides on-demand access to implementation details while maintaining
    a lightweight PyShorthand overview as the default context.
    """

    def __init__(self, codebase_path: Path):
        """Initialize explorer with path to Python codebase.

        Args:
            codebase_path: Path to the Python file or directory to explore
        """
        self.codebase_path = Path(codebase_path)
        self.cache: Dict[str, str] = {}
        self._ast_cache: Dict[Path, ast.Module] = {}

    def get_implementation(
        self, target: str, include_context: bool = True
    ) -> Optional[str]:
        """Retrieve full Python implementation of a specific method.

        Args:
            target: Format "ClassName.method_name" (e.g., "GPT.forward")
            include_context: Include related helper methods called within

        Returns:
            Full Python source code of the method, or None if not found

        Example:
            >>> explorer = CodebaseExplorer("model.py")
            >>> code = explorer.get_implementation("GPT.configure_optimizers")
            >>> print(code)
            def configure_optimizers(self, weight_decay, learning_rate, betas, device_type):
                param_dict = {pn: p for pn, p in self.named_parameters()}
                ...
        """
        cache_key = f"impl:{target}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        # Parse target
        if "." not in target:
            return None

        class_name, method_name = target.rsplit(".", 1)

        # Find implementation
        impl = self._extract_method_implementation(class_name, method_name)
        if impl is None:
            return None

        result = impl.source_code

        # Optionally include called methods
        if include_context and impl.dependencies:
            result += "\n\n# Called methods:\n"
            for dep in impl.dependencies:
                dep_impl = self._extract_method_implementation(class_name, dep)
                if dep_impl:
                    result += f"\n{dep_impl.source_code}\n"

        self.cache[cache_key] = result
        return result

    def get_class_details(
        self,
        class_name: str,
        include_methods: bool = False,
        expand_nested: bool = True,
    ) -> Optional[str]:
        """Retrieve detailed type information for a class.

        Args:
            class_name: Name of the class to inspect
            include_methods: Include full method implementations (expensive)
            expand_nested: Expand nested structures like ModuleDict

        Returns:
            Formatted string with class details, or None if not found

        Example:
            >>> explorer = CodebaseExplorer("model.py")
            >>> details = explorer.get_class_details("GPT", expand_nested=True)
            >>> print(details)
            class GPT(nn.Module):
                config: GPTConfig
                transformer: nn.ModuleDict = {
                    'wte': nn.Embedding(50304, 768),
                    ...
                }
        """
        cache_key = f"class:{class_name}:{include_methods}:{expand_nested}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        details = self._extract_class_details(class_name, expand_nested)
        if details is None:
            return None

        # Format output
        lines = []

        # Class declaration
        if details.base_classes:
            bases = ", ".join(details.base_classes)
            lines.append(f"class {details.name}({bases}):")
        else:
            lines.append(f"class {details.name}:")

        # Attributes with types
        if details.attributes:
            lines.append("    # State Variables:")
            for attr_name, attr_type in details.attributes.items():
                if attr_name in details.nested_structures and expand_nested:
                    # Show expanded structure
                    lines.append(f"    {attr_name}: {attr_type} = {{")
                    for key, val in self._parse_nested_structure(
                        details.nested_structures[attr_name]
                    ).items():
                        lines.append(f"        '{key}': {val},")
                    lines.append("    }")
                else:
                    lines.append(f"    {attr_name}: {attr_type}")

        # Method signatures
        if details.methods:
            lines.append("")
            lines.append("    # Methods:")
            for method_name, signature in details.methods.items():
                lines.append(f"    {signature}")

                # Optionally include full implementation
                if include_methods:
                    impl = self._extract_method_implementation(
                        class_name, method_name
                    )
                    if impl:
                        # Indent implementation
                        for line in impl.source_code.split("\n"):
                            lines.append(f"    {line}")

        result = "\n".join(lines)
        self.cache[cache_key] = result
        return result

    def search_usage(self, symbol: str) -> List[str]:
        """Find where a class/method is used in the codebase.

        Args:
            symbol: Class name, method name, or variable to search for

        Returns:
            List of usage locations (formatted strings)

        Example:
            >>> explorer = CodebaseExplorer("model.py")
            >>> usages = explorer.search_usage("LayerNorm")
            >>> for usage in usages:
            ...     print(usage)
            Block.ln_1 (state variable)
            Block.ln_2 (state variable)
            GPT.transformer.ln_f (nested in ModuleDict)
        """
        usages = []

        # Search through all classes
        for file_path in self._get_python_files():
            tree = self._get_ast(file_path)
            if tree is None:
                continue

            for node in ast.walk(tree):
                # Check class attribute assignments
                if isinstance(node, ast.ClassDef):
                    for item in node.body:
                        if isinstance(item, ast.Assign):
                            # Check if symbol appears in the value
                            if self._contains_symbol(item.value, symbol):
                                for target in item.targets:
                                    if isinstance(target, ast.Attribute):
                                        usages.append(
                                            f"{node.name}.{target.attr} (state variable)"
                                        )
                                    elif isinstance(target, ast.Name):
                                        usages.append(
                                            f"{node.name}.{target.id} (state variable)"
                                        )

                # Check method calls
                if isinstance(node, ast.Call):
                    if self._is_class_instantiation(node, symbol):
                        # Find containing class/method
                        parent = self._find_parent_context(tree, node)
                        if parent:
                            usages.append(f"{parent} (instantiation)")

        return usages

    # Private methods

    def _get_python_files(self) -> List[Path]:
        """Get all Python files in codebase path."""
        if self.codebase_path.is_file():
            return [self.codebase_path]
        return list(self.codebase_path.rglob("*.py"))

    def _get_ast(self, file_path: Path) -> Optional[ast.Module]:
        """Get AST for a Python file (with caching)."""
        if file_path in self._ast_cache:
            return self._ast_cache[file_path]

        try:
            with open(file_path) as f:
                tree = ast.parse(f.read(), filename=str(file_path))
            self._ast_cache[file_path] = tree
            return tree
        except Exception:
            return None

    def _extract_method_implementation(
        self, class_name: str, method_name: str
    ) -> Optional[MethodImplementation]:
        """Extract source code for a specific method."""
        for file_path in self._get_python_files():
            tree = self._get_ast(file_path)
            if tree is None:
                continue

            # Find the class
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and node.name == class_name:
                    # Find the method
                    for item in node.body:
                        if isinstance(
                            item, (ast.FunctionDef, ast.AsyncFunctionDef)
                        ) and item.name == method_name:
                            # Extract source code
                            source = ast.get_source_segment(
                                open(file_path).read(), item
                            )
                            if source is None:
                                continue

                            # Find dependencies (methods called within)
                            deps = self._find_method_calls(item)

                            return MethodImplementation(
                                class_name=class_name,
                                method_name=method_name,
                                source_code=source,
                                line_start=item.lineno,
                                line_end=item.end_lineno or item.lineno,
                                dependencies=deps,
                            )

        return None

    def _extract_class_details(
        self, class_name: str, expand_nested: bool
    ) -> Optional[ClassDetails]:
        """Extract detailed information about a class."""
        for file_path in self._get_python_files():
            tree = self._get_ast(file_path)
            if tree is None:
                continue

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and node.name == class_name:
                    # Extract base classes
                    base_classes = []
                    for base in node.bases:
                        base_classes.append(ast.unparse(base))

                    # Extract attributes (from __init__ typically)
                    attributes = {}
                    nested_structures = {}
                    init_method = None

                    for item in node.body:
                        if (
                            isinstance(item, ast.FunctionDef)
                            and item.name == "__init__"
                        ):
                            init_method = item
                            break

                    if init_method:
                        for stmt in init_method.body:
                            if isinstance(stmt, ast.Assign):
                                for target in stmt.targets:
                                    if isinstance(target, ast.Attribute):
                                        if isinstance(
                                            target.value, ast.Name
                                        ) and target.value.id == "self":
                                            attr_name = target.attr
                                            # Try to infer type
                                            attr_type = self._infer_type(
                                                stmt.value
                                            )
                                            attributes[attr_name] = attr_type

                                            # Check if it's a nested structure
                                            if expand_nested and isinstance(
                                                stmt.value, ast.Call
                                            ):
                                                if self._is_nested_structure(
                                                    stmt.value
                                                ):
                                                    nested_structures[
                                                        attr_name
                                                    ] = ast.unparse(stmt.value)

                    # Extract method signatures
                    methods = {}
                    for item in node.body:
                        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            # Build signature
                            sig = self._build_signature(item)
                            methods[item.name] = sig

                    return ClassDetails(
                        name=class_name,
                        base_classes=base_classes,
                        attributes=attributes,
                        methods=methods,
                        nested_structures=nested_structures,
                    )

        return None

    def _infer_type(self, node: ast.AST) -> str:
        """Infer type from AST node."""
        if isinstance(node, ast.Call):
            # Constructor call like nn.Linear(...)
            return ast.unparse(node.func)
        elif isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return ast.unparse(node)
        return "Unknown"

    def _is_nested_structure(self, node: ast.Call) -> bool:
        """Check if this is a nested structure like ModuleDict."""
        func_name = ast.unparse(node.func)
        return any(
            pattern in func_name
            for pattern in ["ModuleDict", "ModuleList", "Sequential", "ParameterDict"]
        )

    def _parse_nested_structure(self, source: str) -> Dict[str, str]:
        """Parse nested structure from source code."""
        # Simple implementation - could be enhanced
        try:
            tree = ast.parse(source, mode="eval")
            if isinstance(tree.body, ast.Call):
                # Extract dict argument for ModuleDict
                for arg in tree.body.args:
                    if isinstance(arg, ast.Dict):
                        result = {}
                        for key, value in zip(arg.keys, arg.values):
                            key_str = ast.unparse(key) if key else "?"
                            val_str = ast.unparse(value)
                            result[key_str.strip("'")] = val_str
                        return result
        except Exception:
            pass
        return {}

    def _build_signature(self, func_node: ast.FunctionDef) -> str:
        """Build method signature string from AST."""
        args = []
        for arg in func_node.args.args:
            arg_str = arg.arg
            if arg.annotation:
                arg_str += f": {ast.unparse(arg.annotation)}"
            args.append(arg_str)

        # Add defaults
        defaults = func_node.args.defaults
        if defaults:
            num_defaults = len(defaults)
            for i, default in enumerate(defaults):
                arg_idx = len(args) - num_defaults + i
                args[arg_idx] += f" = {ast.unparse(default)}"

        args_str = ", ".join(args)

        # Return type
        returns = ""
        if func_node.returns:
            returns = f" -> {ast.unparse(func_node.returns)}"

        return f"def {func_node.name}({args_str}){returns}"

    def _find_method_calls(self, func_node: ast.FunctionDef) -> List[str]:
        """Find all method calls within a function."""
        calls = set()
        for node in ast.walk(func_node):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    # self.method_name()
                    if isinstance(node.func.value, ast.Name):
                        if node.func.value.id == "self":
                            calls.add(node.func.attr)
        return list(calls)

    def _contains_symbol(self, node: ast.AST, symbol: str) -> bool:
        """Check if AST node contains a reference to symbol."""
        source = ast.unparse(node)
        return symbol in source

    def _is_class_instantiation(self, call_node: ast.Call, class_name: str) -> bool:
        """Check if this call instantiates the given class."""
        func_name = ast.unparse(call_node.func)
        return class_name in func_name

    def _find_parent_context(
        self, tree: ast.Module, target_node: ast.AST
    ) -> Optional[str]:
        """Find the class.method context containing a node."""
        # Walk tree to find parent
        # This is simplified - would need proper parent tracking
        return None  # TODO: Implement proper parent tracking
