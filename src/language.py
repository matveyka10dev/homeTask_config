"""Parse and evaluate the configuration language of variant 17."""

import pyparsing as pp
import yaml


def build_grammar():
    """Build a grammar whose actions produce located expression nodes."""
    value = pp.Forward()
    expression = pp.Forward()
    name = pp.Regex(r"[a-zA-Z]+")
    number = pp.Regex(r"0[xX][0-9a-fA-F]+")
    number.set_parse_action(lambda t: int(t[0], 16))
    decimal = pp.Word(pp.nums).set_parse_action(lambda t: int(t[0]))
    string = pp.Regex(r"\[\[[\s\S]*?\]\]").set_parse_action(
        lambda t: t[0][2:-2]
    )
    reference = name.copy().set_parse_action(
        lambda s, loc, t: [("ref", loc, t[0])]
    )
    pair = pp.Group(name + pp.Suppress("=") + value)
    members = pp.Optional(pp.DelimitedList(pair, allow_trailing_delim=True))
    mapping = pp.Suppress("{") + members + pp.Suppress("}")
    mapping.set_parse_action(lambda s, loc, t: [("map", loc, list(t))])
    operand = number | decimal | string | mapping | expression | reference
    addition = pp.Literal("+") + operand + operand
    printing = pp.Keyword("print") + operand
    expression <<= pp.Suppress("|") + (addition | printing) + pp.Suppress("|")
    expression.set_parse_action(lambda s, loc, t: [(t[0], loc, *t[1:])])
    value <<= number | string | mapping | expression | reference
    binding = pp.Group(
        pp.Keyword("set").suppress() + name + pp.Suppress("=")
        + value + pp.Suppress(";")
    )
    return (pp.ZeroOrMore(binding) + value).parse_with_tabs()


def evaluate_mapping(pairs, source, location, constants, output):
    """Evaluate dictionary entries in order and reject duplicate keys."""
    result = {}
    for key, item in pairs:
        if key in result:
            raise pp.ParseFatalException(
                source, location, f"Повтор ключа {key}"
            )
        result[key] = evaluate(item, source, constants, output)
    return result


def evaluate(node, source, constants, output):
    """Evaluate a syntax node, resolving names in declaration order."""
    if not isinstance(node, tuple):
        return node
    kind, location, *args = node
    if kind == "ref":
        name = args[0]
        if name not in constants:
            raise pp.ParseFatalException(
                source, location, f"Неизвестная константа {name}"
            )
        return constants[name]
    if kind == "map":
        return evaluate_mapping(args[0], source, location, constants, output)
    values = [evaluate(item, source, constants, output) for item in args]
    if kind == "print":
        print(values[0], file=output)
        return values[0]
    if not all(isinstance(item, int) for item in values):
        raise pp.ParseFatalException(source, location, "Для + нужны числа")
    return sum(values)


def translate(source, output):
    """Translate one document to YAML and send print output to a stream."""
    *bindings, root = build_grammar().parse_string(source, parse_all=True)
    constants = {}
    for name, node in bindings:
        constants[name] = evaluate(node, source, constants, output)
    result = evaluate(root, source, constants, output)
    return yaml.safe_dump(result, allow_unicode=True, sort_keys=False)
