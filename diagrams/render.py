"""Rebuild the WebP and editable SVG figures from the CSV examples."""

from decimal import Decimal as D
from io import BytesIO
from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))
from backlash import load_commands, replay

plt.rcParams.update({"svg.fonttype": "none", "svg.hashsalt": "wifa-backlash",
                     "font.size": 13, "text.color": "#142f36", "axes.labelcolor": "#142f36",
                     "axes.edgecolor": "#507075", "xtick.color": "#142f36",
                     "ytick.color": "#142f36", "axes.titleweight": "bold"})
blue, ochre = "#005a75", "#924821"


def trace(name):
    commands = load_commands(ROOT / "examples" / (name + ".csv"))
    return [float(x) for x in commands], [float(y) for y in replay(commands, D(2), D(0))]


def canvas(title, ylabel):
    fig, ax = plt.subplots(figsize=(10, 5.6), facecolor="#f3f8f8", layout="constrained")
    ax.set(title=title, xlabel="Sample index", ylabel=ylabel)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color="#d9e5e5", linewidth=0.85)
    return fig, ax


def save(fig, name):
    fig.savefig(HERE / (name + ".svg"), metadata={"Date": None})
    buf = BytesIO()
    fig.savefig(buf, dpi=100, format="png")
    with Image.open(buf) as source:
        img = source.convert("RGB")
        img.save(HERE / (name + ".webp"), quality=86, method=6)
        img.resize((600, 336), Image.Resampling.LANCZOS).save(
            HERE / (name + "-600.webp"), quality=85, method=6)
    plt.close(fig)


x, y = trace("reversal")
fig, ax = canvas("A full reversal consumes 2° of input travel", "Joint angle (°)")
ax.axvspan(3, 5, color="#e4dbbe", alpha=0.62)
ax.plot(x, "o--", color=blue, label="Input, output-side degrees", linewidth=2)
ax.plot(y, "s-", color=ochre, label="Simulated output", linewidth=2.5)
ax.set(xticks=range(len(x)), yticks=range(-1, 5), ylim=(-1.35, 4.15))
ax.text(4, 3.45, "Gap crossing", ha="center", color="#664213")
ax.legend(loc="lower right", facecolor="white", framealpha=1)
save(fig, "joint-backlash-full-reversal")

x, y = trace("short-reversal")
fig, ax = canvas("A short reversal leaves the output in place", "Joint angle (°)")
ax.axvspan(1, 5, color="#e4dbbe", alpha=0.62)
ax.plot(x, "o--", color=blue, label="Input, output-side degrees", linewidth=2)
ax.plot(y, "s-", color=ochre, label="Simulated output", linewidth=2.5)
ax.set(xticks=range(len(x)), yticks=range(5), ylim=(-0.3, 4.2))
ax.text(3, 3.58, "Output holds at 2°", ha="center", color="#664213")
ax.legend(loc="lower right", facecolor="white", framealpha=1)
save(fig, "joint-backlash-short-reversal")
