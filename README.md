# Robot joint backlash lab

Predict where a joint stops when a simulated transmission changes direction. The code replays input positions, compares them with the output, and shows when the output holds or moves. It never connects to hardware.

The [full WIFA Robotics lesson](https://wifarobotics.com/learn/robot-joint-backlash/) includes the derivation, worked examples, and what to check before interpreting a real log.

## Start from zero

1. Install [Python 3](https://docs.python.org/3/using/index.html) (3.10 or newer) and check it with `python3 --version`. On Windows use `py -3 --version` and replace every `python3` below with `py -3`.
2. Download the repository ZIP from **Code → Download ZIP**, unzip it, and open a terminal in the extracted folder, where `backlash.py` and `examples` are visible. Git users can run `git clone https://github.com/williamfarokhzad/wifa-robot-joint-backlash.git` and `cd wifa-robot-joint-backlash`.
3. Run the examples below. No packages, virtual environment, or internet connection are required after the download.

```sh
python3 backlash.py examples/reversal.csv --width 2
python3 backlash.py examples/short-reversal.csv --width 2
python3 backlash.py examples/offset-start.csv --width 2 --initial 10
python3 backlash.py examples/reversal.csv --width 0
python3 -m unittest discover -s tests -v
```

Expected checks:

| Example | Look for |
| --- | --- |
| Full reversal | At samples 3, 4 and 5, input is 3°, 2° and 1° while output stays at 2°. At sample 6, output falls to 1°. |
| Short reversal | Samples 2 through 5 hold the output at 2° after the initial move to 3°; sample 6 raises it to 2.5°. |
| Offset start | The initial output is 10°. The first input, 11°, reaches the positive flank without moving the output. The last output is 9.75°. |
| Zero width | Every output equals its input, including direction changes. |

The CSV has one column, `command_deg`. All angles are unwrapped, output side degrees; convert motor shaft angles through the ratio and the correct sign before using the model. For example, a 50:1 reduction means 50 motor degrees per output degree in magnitude. `--width` is the entire gap from flank to flank. `--initial` is the previous output, before processing row one. Output index starts at zero. `held` means no change in the simulated output, including samples exactly at contact. The CLI accepts finite plain decimal angles with up to six fractional digits and magnitude at most 1,000,000°. The output retains extra digits when halving the width creates a half step.

## Troubleshooting

- **Cannot open the example:** move to the directory that contains `backlash.py`; make sure the ZIP was extracted.
- **CSV header error:** use one column named `command_deg`, with a decimal point and one value per record. Blank records, scientific notation and commas as decimal separators are rejected.
- **Output moves at the first sample:** the initial output was outside that command's clearance interval. Set the correct initial angle or prepend the observed starting command.
- **Unexpected large jump near 360°:** unwrap the command first. The model does not infer whether 359° to 1° means +2° or −358°.
- **Small real movement during the simulated hold:** encoder resolution, compliance, friction, load or a controller can affect measurements. Do not use this file to command a live axis or infer gearbox clearance from a single trace.

## Rebuild the figures (optional)

The WebP images and editable SVGs are under `diagrams/`. The CLI and its tests need only the standard library. If you want to edit the figure source, create a separate environment for the plotting dependencies:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install matplotlib Pillow
.venv/bin/python diagrams/render.py
```

On Windows, use `py -3 -m venv .venv` and `.venv\Scripts\python.exe` for the final two commands.

Figure alt text: **Full reversal** shows command dropping from 3° to 1° while output stays at 2°, then output drops at the next sample. **Short reversal** shows the command dipping from 3° to 2° and returning to 3° while the output stays at 2°.

The model describes ideal, symmetric geometric play. It does not model contact forces, compliance, friction, external disturbances, controller timing or wear, and has not been validated on hardware. See the [MathWorks backlash model](https://www.mathworks.com/help/simulink/slref/backlash.html) for the held and engaged regions.
