"""Read a configuration from stdin and write a UTF-8 YAML file."""

import argparse
import sys
from pathlib import Path

import pyparsing as pp

from language import translate


def main():
    """Handle command-line arguments, translation and diagnostic messages."""
    parser = argparse.ArgumentParser(description="Перевод конфигурации в YAML")
    parser.add_argument("-o", "--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        source = sys.stdin.buffer.read().decode("utf-8")
        document = translate(source, sys.stderr)
        args.output.write_text(document, encoding="utf-8")
    except pp.ParseBaseException as error:
        print(
            f"Строка {error.lineno}, столбец {error.col}: {error.msg}",
            file=sys.stderr,
        )
        return 1
    except (OSError, UnicodeError) as error:
        print(f"Ошибка ввода или вывода: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
