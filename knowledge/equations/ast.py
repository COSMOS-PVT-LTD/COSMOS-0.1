"""Source-faithful expression trees. Parse failure is explicit, never invented."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re

__all__ = ("ExprNode", "NodeKind", "parse_equation", "serialize_node")


class NodeKind(Enum):
    SYMBOL = "SYMBOL"
    NUMBER = "NUMBER"
    ADD = "ADD"
    SUB = "SUB"
    MUL = "MUL"
    DIV = "DIV"
    POW = "POW"
    NEG = "NEG"
    CALL = "CALL"
    EQ = "EQ"
    GROUP = "GROUP"


@dataclass(frozen=True, slots=True, kw_only=True)
class ExprNode:
    kind: NodeKind
    value: str | None = None
    children: tuple[ExprNode, ...] = ()


_NUMBER = re.compile(r"^[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?")
_IDENT = re.compile(r"^[A-Za-zΑ-Ωα-ωµμρνστωθγλδφψΔΣΩ][A-Za-z0-9_Α-Ωα-ωµμρνστωθγλδφψΔΣΩ]*")
_FUNCTIONS = frozenset({"sin", "cos", "tan", "log", "ln", "exp", "sqrt", "abs", "min", "max"})


def parse_equation(text: str) -> ExprNode | None:
    """Parse a source equation. Returns None when the text is not a parseable identity."""

    compact = text.strip()
    if not compact or "=" not in compact:
        return None
    tokens = _tokenize(compact)
    if not tokens or not any(token in {"*", "/", "+", "-", "**", "^", "("} for token in tokens):
        return None
    parser = _Parser(tokens)
    try:
        tree = parser.parse_equation()
        parser.expect_end()
    except _ParseError:
        return None
    return tree


def serialize_node(node: ExprNode) -> str:
    if node.kind is NodeKind.SYMBOL:
        return node.value or ""
    if node.kind is NodeKind.NUMBER:
        return node.value or ""
    if node.kind is NodeKind.NEG:
        return f"-{serialize_node(node.children[0])}"
    if node.kind is NodeKind.GROUP:
        return f"({serialize_node(node.children[0])})"
    if node.kind is NodeKind.CALL:
        args = ", ".join(serialize_node(child) for child in node.children)
        return f"{node.value}({args})"
    if node.kind is NodeKind.EQ:
        return f"{serialize_node(node.children[0])} = {serialize_node(node.children[1])}"
    op = {
        NodeKind.ADD: " + ",
        NodeKind.SUB: " - ",
        NodeKind.MUL: " * ",
        NodeKind.DIV: " / ",
        NodeKind.POW: " ** ",
    }[node.kind]
    return op.join(serialize_node(child) for child in node.children)


class _ParseError(ValueError):
    pass


class _Parser:
    def __init__(self, tokens: tuple[str, ...]) -> None:
        self.tokens = tokens
        self.index = 0

    def parse_equation(self) -> ExprNode:
        left = self.parse_expr()
        if self.peek() != "=":
            raise _ParseError("missing equals")
        self.advance()
        right = self.parse_expr()
        return ExprNode(kind=NodeKind.EQ, children=(left, right))

    def parse_expr(self) -> ExprNode:
        node = self.parse_term()
        while self.peek() in {"+", "-"}:
            op = self.advance()
            right = self.parse_term()
            kind = NodeKind.ADD if op == "+" else NodeKind.SUB
            node = ExprNode(kind=kind, children=(node, right))
        return node

    def parse_term(self) -> ExprNode:
        node = self.parse_unary()
        while True:
            nxt = self.peek()
            if nxt in {"*", "/"}:
                op = self.advance()
                right = self.parse_unary()
                kind = NodeKind.MUL if op == "*" else NodeKind.DIV
                node = ExprNode(kind=kind, children=(node, right))
                continue
            if nxt is not None and nxt not in {")", "+", "-", "=", ",", "**", "^"} and (
                _IDENT.match(nxt) or _NUMBER.match(nxt) or nxt == "("
            ):
                right = self.parse_unary()
                node = ExprNode(kind=NodeKind.MUL, children=(node, right))
                continue
            break
        return node

    def parse_unary(self) -> ExprNode:
        if self.peek() == "-":
            self.advance()
            return ExprNode(kind=NodeKind.NEG, children=(self.parse_unary(),))
        return self.parse_power()

    def parse_power(self) -> ExprNode:
        node = self.parse_primary()
        if self.peek() in {"^", "**"}:
            self.advance()
            return ExprNode(kind=NodeKind.POW, children=(node, self.parse_unary()))
        return node

    def parse_primary(self) -> ExprNode:
        token = self.peek()
        if token is None:
            raise _ParseError("unexpected end")
        if token == "(":
            self.advance()
            inner = self.parse_expr()
            if self.peek() != ")":
                raise _ParseError("missing closing parenthesis")
            self.advance()
            return ExprNode(kind=NodeKind.GROUP, children=(inner,))
        if _NUMBER.match(token):
            self.advance()
            return ExprNode(kind=NodeKind.NUMBER, value=token)
        if _IDENT.match(token):
            self.advance()
            if token in _FUNCTIONS and self.peek() == "(":
                self.advance()
                args = [self.parse_expr()]
                while self.peek() == ",":
                    self.advance()
                    args.append(self.parse_expr())
                if self.peek() != ")":
                    raise _ParseError("missing closing parenthesis")
                self.advance()
                return ExprNode(kind=NodeKind.CALL, value=token, children=tuple(args))
            return ExprNode(kind=NodeKind.SYMBOL, value=token)
        raise _ParseError(f"unexpected token {token}")

    def peek(self) -> str | None:
        if self.index >= len(self.tokens):
            return None
        return self.tokens[self.index]

    def advance(self) -> str:
        token = self.peek()
        if token is None:
            raise _ParseError("unexpected end")
        self.index += 1
        return token

    def expect_end(self) -> None:
        if self.peek() is not None:
            raise _ParseError("trailing tokens")


def _tokenize(text: str) -> tuple[str, ...]:
    index = 0
    tokens: list[str] = []
    while index < len(text):
        char = text[index]
        if char.isspace():
            index += 1
            continue
        if text.startswith("**", index):
            tokens.append("**")
            index += 2
            continue
        if char in {"+", "-", "*", "/", "=", "^", "(", ")", ","}:
            if char == "×" or char == "·":
                tokens.append("*")
            else:
                tokens.append(char)
            index += 1
            continue
        if char in {"×", "·"}:
            tokens.append("*")
            index += 1
            continue
        number = _NUMBER.match(text[index:])
        if number:
            tokens.append(number.group(0))
            index += number.end()
            continue
        ident = _IDENT.match(text[index:])
        if ident:
            tokens.append(ident.group(0))
            index += ident.end()
            continue
        return ()
    return tuple(tokens)
