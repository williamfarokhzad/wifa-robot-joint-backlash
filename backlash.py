"""Replay ideal angular play at one robot joint. No hardware interfaces."""

import argparse
import csv
import re
from decimal import Decimal
from pathlib import Path
import sys

ANGLE = re.compile(r"-?[0-9]{1,7}(?:\.[0-9]{1,6})?")
LIMIT = Decimal("1000000")


def angle(text: str) -> Decimal:
    """Use exact decimal degrees at the contact boundaries."""
    if not ANGLE.fullmatch(text.strip()):
        raise ValueError(f"invalid angle {text!r}; use a decimal with up to six places")
    value = Decimal(text.strip())
    if abs(value) > LIMIT:
        raise ValueError("angle magnitude exceeds 1000000 degrees")
    return value


def replay(commands: list[Decimal], width: Decimal, initial: Decimal) -> list[Decimal]:
    """Use finite Decimal values in one output-side, unwrapped frame."""
    if not width.is_finite() or width < 0:
        raise ValueError("width must be finite and nonnegative")
    if not initial.is_finite() or any(not x.is_finite() for x in commands):
        raise ValueError("initial angle and commands must be finite")
    if not commands:
        raise ValueError("at least one command is required")
    half = width / 2
    output = initial
    result = []
    for command in commands:
        # A held output stays inside [command - half, command + half].
        # When the gap closes, the nearer boundary carries the output.
        output = max(command - half, min(output, command + half))
        result.append(output)
    return result


def load_commands(path: Path) -> list[Decimal]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        rows = csv.reader(stream, strict=True)
        if next(rows, None) != ["command_deg"]:
            raise ValueError("CSV must start with the single column command_deg")
        commands = []
        for line, row in enumerate(rows, start=2):
            if len(row) != 1:
                raise ValueError(f"record {line}: expected exactly one command")
            try:
                commands.append(angle(row[0]))
            except ValueError as error:
                raise ValueError(f"record {line}: {error}") from error
        return commands


def display(value: Decimal) -> str:
    return format(value, ".3f") if value == value.quantize(Decimal(".001")) else format(value, "f")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="CSV with one command_deg column")
    parser.add_argument("--width", required=True, help="full reversal play in output degrees")
    parser.add_argument("--initial", default="0", help="output before the first sample, in degrees")
    args = parser.parse_args()
    try:
        width, initial = angle(args.width), angle(args.initial)
        commands = load_commands(args.input)
        outputs = replay(commands, width, initial)
    except (OSError, ValueError, csv.Error) as error:
        parser.error(str(error))
    writer = csv.writer(sys.stdout, lineterminator="\n")
    writer.writerow(("sample", "command_deg", "output_deg", "movement"))
    previous = initial
    for sample, (command, output) in enumerate(zip(commands, outputs)):
        movement = "positive" if output > previous else "negative" if output < previous else "held"
        writer.writerow((sample, display(command), display(output), movement))
        previous = output


if __name__ == "__main__":
    main()
