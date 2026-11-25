"""Exercise the translator through its command-line interface."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml


def run_cli(source, destination):
    """Run the same entry point as run.sh with a controlled input stream."""
    script = Path(__file__).resolve().parents[1] / "src" / "main.py"
    return subprocess.run(
        [sys.executable, script, "-o", destination],
        input=source, text=True, encoding="utf-8", capture_output=True,
        check=False,
    )


def check_document(source, expected, messages=""):
    """Compare the emitted YAML value and the separate print stream."""
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "result.yaml"
        result = run_cli(source, path)
        assert result.returncode == 0, result.stderr
        assert result.stderr == messages, result.stderr
        assert result.stdout == ""
        assert yaml.safe_load(path.read_text(encoding="utf-8")) == expected


def check_invalid(source):
    """Check that a rejected document leaves an existing file intact."""
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "result.yaml"
        path.write_text("original", encoding="utf-8")
        result = run_cli(source, path)
        assert result.returncode != 0
        assert "Строка" in result.stderr and "столбец" in result.stderr
        assert path.read_text(encoding="utf-8") == "original"


def test_examples():
    """Verify all three domain configurations against independent values."""
    examples = Path(__file__).resolve().parents[1] / "examples"
    cases = [
        ("library", {"title": "Атлас мира", "copies": 27}, ""),
        ("greenhouse", {"zone": "Север", "sensor": {"limit": 19}}, ""),
        ("studio", {"project": "Запись", "session": {"channels": 8}}, "8\n"),
    ]
    for name, expected, messages in cases:
        source = (examples / f"{name}.conf").read_text(encoding="utf-8")
        check_document(source, expected, messages)


def test_values():
    """Cover scalar roots, nested dictionaries and chained declarations."""
    for source, expected in [
        ("0XfF", 255), ("{}", {}), ("[[]]", ""),
        ("[[ null:\n\t#текст ]]", " null:\n\t#текст "),
        ("set A = [[yes]]; {a = A, A = {},}", {"a": "yes", "A": {}}),
        ("set x = {a = 0xF}; set y = x; {z = y}", {"z": {"a": 15}}),
    ]:
        check_document(source, expected)
    check_document("|+ |print 2| |print |+ 1 0x3|||", 6, "2\n4\n")


def test_invalid():
    """Reject invalid syntax, arity, names, scope, types and trailing text."""
    for source in [
        "", "15", "0x", "0x1g", "[[open", "{a_b = 0x1}",
        "{a = 0x1 b = 0x2}", "{a = 0x1", "{a = 0x1, a = 0x2}",
        "set x = 0x1 x", "set x = y; set y = 0x1; x", "|+ 1|",
        "|+ 1 2 3|", "|print|", "|+ [[x]] 1|", "{} extra", "|- 2 1|",
    ]:
        check_invalid(source)


def load_tests(loader, tests, pattern):
    """Register function tests with standard unittest discovery."""
    for test in (test_examples, test_values, test_invalid):
        tests.addTest(unittest.FunctionTestCase(test))
    return tests
