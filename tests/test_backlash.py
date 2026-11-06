import csv
from decimal import Decimal as D
import io
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest

from backlash import angle, replay

ROOT = Path(__file__).resolve().parents[1]


def run(values, width="2", initial="0"):
    return replay([D(str(x)) for x in values], D(width), D(initial))


class ReplayTests(unittest.TestCase):
    def test_full_reversal_with_exact_contact(self):
        self.assertEqual(run([0, 1, 2, 3, 2, 1, 0, -1, 0, 1, 2, 3]),
                         [0, 0, 1, 2, 2, 2, 1, 0, 0, 0, 1, 2])

    def test_short_reversal_does_not_restart_the_gap(self):
        self.assertEqual(run([0, 3, "2.5", 2, "2.5", 3, "3.5"]),
                         list(map(D, ["0", "2", "2", "2", "2", "2", "2.5"])))

    def test_identical_command_differs_by_history(self):
        up = run([0, 3, 2])[-1]
        down = run([0, -3, 2])[-1]
        self.assertEqual((up, down), (D(2), D(1)))

    def test_nonzero_initial_and_subdegree_change(self):
        self.assertEqual(run([11, "11.25", "10.75", "9.25", 9, "8.75"], initial="10"),
                         list(map(D, ["10", "10.25", "10.25", "10.25", "10", "9.75"])))

    def test_fractional_boundary_is_exact(self):
        self.assertEqual(run([0, "0.000001", 0], width="0.000001"),
                         [D(0), D("0.0000005"), D("0.0000005")])

    def test_first_command_reconciles_outside_initial_gap(self):
        self.assertEqual(run([10, -10]), [9, -9])

    def test_zero_width_tracks_every_sample(self):
        values = [0, "2.5", -1, -1, "0.002"]
        self.assertEqual(run(values, width="0", initial="15"), [D(str(x)) for x in values])

    def test_incremental_contact_oracle(self):
        # Independent incremental model: clearance stored in the relative gap,
        # and only travel remaining after reaching a flank moves the output.
        rng = random.Random(165)
        for width in (0, 2, 4, 10):
            old_input, old_output = 0, 0
            commands = [0] + [rng.randrange(-20, 21) for _ in range(250)]
            want = []
            for command in commands:
                delta = command - old_input
                gap = old_input - old_output
                if delta >= 0:
                    old_output += max(0, delta - (width // 2 - gap))
                else:
                    old_output -= max(0, -delta - (width // 2 + gap))
                want.append(old_output)
                old_input = command
            self.assertEqual(run(commands, str(width)), want)

    def test_rejects_invalid_model_or_numbers(self):
        for bad in ("NaN", "inf", "1e9", "1000001", "0.0000001", "1,2"):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                angle(bad)
        for args in (([], D(1), D(0)), ([D(0)], D(-1), D(0)),
                     ([D("Infinity")], D(1), D(0)), ([D(0)], D(1), D("NaN"))):
            with self.assertRaises(ValueError):
                replay(*args)


class CliTests(unittest.TestCase):
    def invoke(self, path, *extra):
        return subprocess.run([sys.executable, str(ROOT / "backlash.py"), str(path),
                               "--width", "2", *extra], capture_output=True, text=True)

    def test_csv_and_state_labels(self):
        result = self.invoke(ROOT / "examples/reversal.csv")
        self.assertEqual(result.returncode, 0, result.stderr)
        rows = list(csv.DictReader(io.StringIO(result.stdout)))
        self.assertEqual((rows[5]["output_deg"], rows[5]["movement"]), ("2.000", "held"))
        self.assertEqual((rows[6]["output_deg"], rows[6]["movement"]), ("1.000", "negative"))

    def test_malformed_csv_exits_without_partial_output(self):
        for text in ("angle\n2\n", "command_deg\n2\n3,4\n", "command_deg\n", 'command_deg\n"2\n'):
            with self.subTest(text=text), tempfile.TemporaryDirectory() as temp:
                bad = Path(temp) / "bad.csv"
                bad.write_text(text, encoding="utf-8")
                result = self.invoke(bad)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, "")
                self.assertIn("error:", result.stderr)


if __name__ == "__main__":
    unittest.main()
