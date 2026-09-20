import ast

from kaprekarevolve.interfaces.shape import CodeShape

#: Constants that describe the *structure* of a four-digit map rather than encoding an
#: answer: the digit count, the base, the domain modulus and the first few small
#: integers every rotation or slice needs.
STRUCTURAL_INTEGERS = frozenset({0, 1, 2, 3, 4, 10, 10000})

#: A branch is the cheapest way to bolt a special case onto a map, and special cases are
#: exactly what made the recorded winners unreadable, so they cost more than a node.
BRANCH_COST = 6

#: A constant outside STRUCTURAL_INTEGERS is usually a memorised answer.
MAGIC_COST = 8

#: An element of a list/dict/set/tuple literal is one entry of a lookup table.
TABLE_COST = 8


class AstShapeAnalyzer:
    """Measures a candidate's ``transform`` by walking its AST.

    The measure has to resist being gamed, because the score multiplies by it. Three
    routes were found to score a perfect 1.0 against a naive node count, and each is
    closed here:

    * ``int("6174")`` - a magic constant hidden inside a *string*. Numeric-looking
      strings are charged exactly like the integer they spell.
    * ``3 * 10 * 10 * 10`` - a magic constant synthesised from allowed ones. Charged by
      counting the arithmetic it takes, which is what ``node_count`` already does.
    * ``[1, 2, 3, ...][value % 20]`` - a lookup table, cheap per element. Charged per
      element instead.

    Format specifiers (the ``04d`` in ``f"{value:04d}"``), booleans and the empty string
    are structural punctuation, not answers, so they are free.
    """

    def analyze(self, source: str) -> CodeShape:
        function = self._transform_function(source)
        body = self._without_docstring(function)
        nodes = [node for statement in body for node in ast.walk(statement)]
        spec_constants = self._format_spec_constants(body)

        node_count = len(nodes)
        branch_count = sum(1 for node in nodes if isinstance(node, ast.If | ast.IfExp))
        magic_constant_count = sum(
            1
            for node in nodes
            if isinstance(node, ast.Constant)
            and id(node) not in spec_constants
            and not self._is_structural(node.value)
        )
        table_element_count = sum(self._table_size(node) for node in nodes)

        return CodeShape(
            node_count=node_count,
            branch_count=branch_count,
            magic_constant_count=magic_constant_count,
            table_element_count=table_element_count,
            cost=(
                node_count
                + BRANCH_COST * branch_count
                + MAGIC_COST * magic_constant_count
                + TABLE_COST * table_element_count
            ),
        )

    @staticmethod
    def _transform_function(source: str) -> ast.FunctionDef:
        for node in ast.walk(ast.parse(source)):
            if isinstance(node, ast.FunctionDef) and node.name == "transform":
                return node
        raise ValueError("source defines no transform function")

    @staticmethod
    def _without_docstring(function: ast.FunctionDef) -> list[ast.stmt]:
        body = function.body
        if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
            return body[1:]
        return body

    @staticmethod
    def _format_spec_constants(body: list[ast.stmt]) -> set[int]:
        """Identify constants that are format specifiers, which are free."""
        spec_constants: set[int] = set()
        for statement in body:
            for node in ast.walk(statement):
                if isinstance(node, ast.FormattedValue) and node.format_spec is not None:
                    spec_constants.update(
                        id(inner) for inner in ast.walk(node.format_spec)
                    )
        return spec_constants

    @staticmethod
    def _is_structural(value: object) -> bool:
        if isinstance(value, bool):
            return True
        if isinstance(value, int):
            return value in STRUCTURAL_INTEGERS
        if isinstance(value, str):
            # "" and "," join separators are punctuation; "6174" is a memorised answer.
            return not value.strip().isdigit()
        return False

    @staticmethod
    def _table_size(node: ast.AST) -> int:
        if isinstance(node, ast.List | ast.Set | ast.Tuple):
            return len(node.elts)
        if isinstance(node, ast.Dict):
            return len(node.keys)
        return 0
