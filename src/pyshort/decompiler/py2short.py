"""Python AST to PyShorthand decompiler implementation."""

import ast
from typing import List, Dict, Optional, Set
from pathlib import Path


class PyShorthandGenerator:
    """Generate PyShorthand from Python AST."""

    def __init__(self, aggressive: bool = False):
        """Initialize generator.

        Args:
            aggressive: If True, use aggressive type inference
        """
        self.aggressive = aggressive
        self.imports: Set[str] = set()
        self.dependencies: List[str] = []

    def generate(self, tree: ast.Module, source_file: Optional[str] = None) -> str:
        """Generate PyShorthand from Python AST.

        Args:
            tree: Python AST module
            source_file: Original source file path (for metadata)

        Returns:
            PyShorthand source code
        """
        lines = []

        # Generate metadata header
        module_name = self._extract_module_name(tree, source_file)
        lines.append(f"# [M:{module_name}] [Role:Core]")
        lines.append("")

        # Extract classes
        classes = [node for node in tree.body if isinstance(node, ast.ClassDef)]

        for cls in classes:
            entity_lines = self._generate_entity(cls)
            lines.extend(entity_lines)
            lines.append("")

        # Extract module-level functions
        functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)]

        if functions:
            lines.append("# Module-level functions")
            for func in functions:
                func_line = self._generate_function_signature(func)
                lines.append(f"{func_line}")
            lines.append("")

        return "\n".join(lines)

    def _extract_module_name(self, tree: ast.Module, source_file: Optional[str]) -> str:
        """Extract module name from AST or file path."""
        # Try to find module name from docstring or file path
        if tree.body and isinstance(tree.body[0], ast.Expr):
            if isinstance(tree.body[0].value, ast.Constant):
                docstring = tree.body[0].value.value
                if isinstance(docstring, str):
                    # Extract first line of docstring as module name
                    first_line = docstring.strip().split('\n')[0]
                    # Clean up common patterns
                    if '.' in first_line:
                        return first_line.split('.')[0]
                    return first_line[:50]  # Limit length

        # Fallback to file name
        if source_file:
            return Path(source_file).stem

        return "UnnamedModule"

    def _generate_entity(self, cls: ast.ClassDef) -> List[str]:
        """Generate PyShorthand entity from Python class.

        Args:
            cls: Python ClassDef node

        Returns:
            Lines of PyShorthand code
        """
        lines = []

        # Entity header
        lines.append(f"[C:{cls.name}]")

        # Extract class attributes with type hints
        state_vars = self._extract_state_variables(cls)

        if state_vars:
            for var in state_vars:
                lines.append(f"  {var}")
        else:
            lines.append("  # No typed attributes found")

        # Extract methods as comments (parser doesn't support F:name syntax in entities yet)
        methods = [node for node in cls.body if isinstance(node, ast.FunctionDef)]

        if methods:
            lines.append("")
            lines.append("  # Methods:")
            for method in methods:
                if method.name.startswith('_') and method.name != '__init__':
                    continue  # Skip private methods except __init__

                sig = self._generate_function_signature(method, indent="  # ")
                lines.append(sig)

        return lines

    def _extract_state_variables(self, cls: ast.ClassDef) -> List[str]:
        """Extract state variables from class.

        Looks for:
        1. Class-level annotated assignments
        2. Instance attributes in __init__
        """
        state_vars = []

        # 1. Class-level annotations
        for node in cls.body:
            if isinstance(node, ast.AnnAssign):
                var_name = self._get_name(node.target)
                type_spec = self._convert_type_annotation(node.annotation)
                state_vars.append(f"{var_name} ∈ {type_spec}")

        # 2. Instance attributes in __init__
        init_method = None
        for node in cls.body:
            if isinstance(node, ast.FunctionDef) and node.name == '__init__':
                init_method = node
                break

        if init_method:
            for node in ast.walk(init_method):
                # Look for self.attr = ...
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Attribute):
                            if isinstance(target.value, ast.Name) and target.value.id == 'self':
                                attr_name = target.attr

                                # Try to infer type from assignment
                                type_spec = self._infer_type(node.value)

                                # Check if we already have this from annotations
                                if not any(attr_name in sv for sv in state_vars):
                                    state_vars.append(f"{attr_name} ∈ {type_spec}")

                # Also handle annotated assignments in __init__
                elif isinstance(node, ast.AnnAssign):
                    if isinstance(node.target, ast.Attribute):
                        if isinstance(node.target.value, ast.Name) and node.target.value.id == 'self':
                            attr_name = node.target.attr
                            type_spec = self._convert_type_annotation(node.annotation)

                            if not any(attr_name in sv for sv in state_vars):
                                state_vars.append(f"{attr_name} ∈ {type_spec}")

        return state_vars

    def _generate_function_signature(self, func: ast.FunctionDef, indent: str = "") -> str:
        """Generate function signature in PyShorthand format.

        Args:
            func: Function definition node
            indent: Indentation prefix

        Returns:
            Function signature string
        """
        # Extract parameters
        params = []
        for arg in func.args.args:
            if arg.arg == 'self':
                continue

            param_str = arg.arg
            if arg.annotation:
                type_str = self._convert_type_annotation(arg.annotation)
                param_str = f"{arg.arg}: {type_str}"

            params.append(param_str)

        params_str = ", ".join(params)

        # Extract return type
        return_type = "Unknown"
        if func.returns:
            return_type = self._convert_type_annotation(func.returns)

        return f"{indent}F:{func.name}({params_str}) → {return_type}"

    def _convert_type_annotation(self, annotation: ast.expr) -> str:
        """Convert Python type annotation to PyShorthand type spec.

        Args:
            annotation: Python AST annotation node

        Returns:
            PyShorthand type specification
        """
        # Handle simple names: int, float, str, etc.
        if isinstance(annotation, ast.Name):
            python_type = annotation.id
            return self._map_python_type(python_type)

        # Handle subscripted types: List[int], Dict[str, int], etc.
        if isinstance(annotation, ast.Subscript):
            base = self._get_name(annotation.value)

            # Handle List, Tuple, etc.
            if base in ('List', 'list'):
                # Try to get element type
                if isinstance(annotation.slice, ast.Name):
                    elem_type = self._map_python_type(annotation.slice.id)
                    return f"list"  # Just use list type without shape
                return "list"

            # Handle Tensor, torch.Tensor, etc.
            if 'Tensor' in base or 'tensor' in base.lower():
                return "f32[N]@GPU"  # Default to GPU tensor with unknown shape N

        # Handle attribute access: torch.Tensor, np.ndarray
        if isinstance(annotation, ast.Attribute):
            full_name = self._get_attribute_name(annotation)
            if 'Tensor' in full_name:
                return "f32[N]@GPU"
            if 'ndarray' in full_name:
                return "f32[N]@CPU"

        # Fallback
        return "Unknown"  # Use 'Unknown' as valid identifier instead of '?'

    def _map_python_type(self, python_type: str) -> str:
        """Map Python type to PyShorthand type.

        Args:
            python_type: Python type name

        Returns:
            PyShorthand type name
        """
        type_map = {
            'int': 'i32',
            'float': 'f32',
            'str': 'str',
            'bool': 'bool',
            'list': 'list',
            'dict': 'dict',
            'tuple': 'tuple',
        }
        return type_map.get(python_type, python_type)

    def _infer_type(self, node: ast.expr) -> str:
        """Infer type from assignment value.

        Args:
            node: Python AST expression node

        Returns:
            Inferred PyShorthand type
        """
        # Number literals
        if isinstance(node, ast.Constant):
            if isinstance(node.value, int):
                return "i32"
            elif isinstance(node.value, float):
                return "f32"
            elif isinstance(node.value, str):
                return "str"
            elif isinstance(node.value, bool):
                return "bool"

        # List literal
        if isinstance(node, ast.List):
            return "list"

        # Dict literal
        if isinstance(node, ast.Dict):
            return "dict"

        # Function calls
        if isinstance(node, ast.Call):
            func_name = self._get_name(node.func)

            # torch.zeros, torch.ones, etc.
            if 'zeros' in func_name or 'ones' in func_name or 'randn' in func_name:
                return "f32[N]@GPU"

            # numpy arrays
            if 'array' in func_name:
                return "f32[N]@CPU"

            # PyTorch nn.Module components
            if 'Linear' in func_name:
                return "Linear"  # nn.Linear
            if 'Conv' in func_name:
                return "Conv"  # nn.Conv2d, etc.
            if 'LayerNorm' in func_name or 'BatchNorm' in func_name:
                return "Norm"  # Normalization layers
            if 'ModuleList' in func_name:
                return "ModuleList"
            if 'Embedding' in func_name:
                return "Embedding"
            if 'Dropout' in func_name:
                return "Dropout"
            if 'Attention' in func_name:
                return "Attention"

        return "Unknown"  # Use 'Unknown' as valid identifier instead of '?'

    def _get_name(self, node: ast.expr) -> str:
        """Extract name from AST node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return self._get_attribute_name(node)
        return "Unknown"  # Use 'Unknown' as valid identifier instead of '?'

    def _get_attribute_name(self, node: ast.Attribute) -> str:
        """Get full attribute name like 'torch.Tensor'."""
        parts = [node.attr]
        current = node.value
        while isinstance(current, ast.Attribute):
            parts.insert(0, current.attr)
            current = current.value
        if isinstance(current, ast.Name):
            parts.insert(0, current.id)
        return ".".join(parts)


def decompile(source: str, aggressive: bool = False) -> str:
    """Decompile Python source code to PyShorthand.

    Args:
        source: Python source code string
        aggressive: If True, use aggressive type inference

    Returns:
        PyShorthand code
    """
    tree = ast.parse(source)
    generator = PyShorthandGenerator(aggressive=aggressive)
    return generator.generate(tree)


def decompile_file(input_path: str, output_path: Optional[str] = None, aggressive: bool = False) -> str:
    """Decompile Python file to PyShorthand.

    Args:
        input_path: Path to Python source file
        output_path: Path to output .pys file (optional)
        aggressive: If True, use aggressive type inference

    Returns:
        PyShorthand code
    """
    with open(input_path, 'r') as f:
        source = f.read()

    tree = ast.parse(source, filename=input_path)
    generator = PyShorthandGenerator(aggressive=aggressive)
    result = generator.generate(tree, source_file=input_path)

    if output_path:
        with open(output_path, 'w') as f:
            f.write(result)

    return result
