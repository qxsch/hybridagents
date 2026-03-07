"""
Tool: calculator – evaluate simple math expressions safely.
"""

import ast
import operator
from hybridagents.core.tool_registry import tool

# Allowed operators for safe eval
_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.FloorDiv: operator.floordiv,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _safe_eval(node: ast.AST) -> float:
    if isinstance(node, ast.Expression):
        return _safe_eval(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        left = _safe_eval(node.left)
        right = _safe_eval(node.right)
        return _OPS[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_safe_eval(node.operand))
    raise ValueError(f"Unsupported expression node: {ast.dump(node)}")


@tool(
    name="calculator",
    description="Evaluate a mathematical expression. Supports +, -, *, /, **, %, // and parentheses for grouping. Examples: '2 + 3 * 4', '(2 + 3) * 6', '((1 + 2) ** 3) / 9'.",
    parameters={
        "expression": {"type": "string", "description": "Math expression to evaluate, may include parentheses for grouping"},
    },
)
def calculator(expression: str) -> str:
    try:
        tree = ast.parse(expression, mode="eval")
        result = _safe_eval(tree)
        return str(result)
    except Exception as exc:
        return f"Error: {exc}"
