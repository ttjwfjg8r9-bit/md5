import ast
from typing import Tuple


def validate_syntax(code: str) -> Tuple[bool, str]:
    try:
        ast.parse(code)
        return True, "ok"
    except SyntaxError as e:
        return False, str(e)


def validate_has_analyze(code: str) -> Tuple[bool, str]:
    try:
        tree = ast.parse(code)
        names = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
        if "analyze" not in names:
            return False, "missing analyze()"
        return True, "ok"
    except Exception as e:
        return False, str(e)
