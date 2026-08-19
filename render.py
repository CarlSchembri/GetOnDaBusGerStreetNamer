"""Renders a generated street sign as a character-capacity bar, and flags
if the suffix isn't a valid abbreviation - both violations visible at once."""
import matplotlib.pyplot as plt
import matplotlib.patches as patches

from evaluator import SIGN_MAX_CHARS, VALID_SUFFIXES


def render_sign(sign, out_path, title="Street sign"):
    name = sign.get("street_name", "")
    suffix = sign.get("suffix", "")
    combined = f"{name} {suffix}".strip()

    length = len(combined)
    over = max(0, length - SIGN_MAX_CHARS)
    suffix_valid = suffix.upper() in VALID_SUFFIXES
    color = "#3f9142" if (over == 0 and suffix_valid) else "#d94040"

    fig, ax = plt.subplots(figsize=(9, 1.8))

    filled = min(length, SIGN_MAX_CHARS)
    ax.add_patch(patches.Rectangle((0, 0.5), filled, 0.6, facecolor=color,
                                    edgecolor="black", linewidth=1))
    if over:
        ax.add_patch(patches.Rectangle((SIGN_MAX_CHARS, 0.5), over, 0.6,
                                        facecolor="#d94040", edgecolor="black",
                                        linewidth=1, hatch="//", alpha=0.85))
    ax.axvline(SIGN_MAX_CHARS, color="black", linewidth=1.5, linestyle="--",
               ymin=0.5 / 1.8, ymax=1.1 / 1.8)

    status_bits = []
    if over:
        status_bits.append(f"{over} chars over")
    if not suffix_valid:
        status_bits.append(f'"{suffix}" not a valid abbreviation')
    status = " / ".join(status_bits) if status_bits else "fits, valid suffix"

    ax.text(-0.5, 0.8, f'"{combined}" ({length}/{SIGN_MAX_CHARS} chars, {status})',
            ha="right", va="center", fontsize=9)

    max_len = max(length, SIGN_MAX_CHARS)
    ax.set_xlim(-18, max_len + 2)
    ax.set_ylim(0, 1.8)
    ax.axis("off")
    ax.set_title(title, fontsize=12)
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
