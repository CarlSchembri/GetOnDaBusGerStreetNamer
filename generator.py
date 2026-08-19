"""
Generator: proposes a street name sign for a Fairweather intersection.

Runs on your Claude subscription via `claude -p` - no ANTHROPIC_API_KEY.
Falls back to a local mock when the `claude` CLI isn't on PATH.
"""
import json
import shutil
import subprocess

import usage_guard

CLAUDE_CLI_PATH = shutil.which("claude")
CLAUDE_CLI_AVAILABLE = CLAUDE_CLI_PATH is not None

PROMPT_TEMPLATE = """You are a street sign generator for the arcade
bus-driving game "Get On Da Bus", set in the fictional town of Fairweather -
a town whose bridges all collapsed, where instead of driving passengers all
the way around, you launch ("yeet") them the last hundred feet off the bus
via ragdoll physics.

TONE (per the GDD's Tone Register): dry civic deadpan is for systems text
(report cards, damage receipts). Street signs are flavor/environment text,
which is where the game gets to be LOUD and meme-slapstick instead. Real
examples already in the game: "Bussin BLVD", "Yeet Street". Street names
should sound like current internet slang, memes, or wordplay tied to the
bus/launch/ragdoll fantasy - NOT generic fantasy-town names like "Marrowgate"
or "Brackenholt".

Generate ONE street sign as strict JSON with this exact schema, and return
ONLY the JSON with no prose, no markdown code fences:
{{
  "street_name": string,
  "suffix": string (a standard abbreviation like ST, AVE, BLVD, RD, LN, DR, WAY, CT, or PL)
}}

Style: funny and current, like "Bussin BLVD" or "Yeet Street" - lean on
slang, puns, or references to launching/yeeting passengers, ragdolls, bus
chaos, or Fairweather's running bridge-collapse joke. Original Fairweather
names only, never a real-world street.
Area: {area_hint}
"""


def _strip_code_fences(text):
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text
        if text.endswith("```"):
            text = text.rsplit("```", 1)[0]
    return text.strip()


def _call_claude_code(prompt, timeout=120):
    usage_guard.register_call()
    result = subprocess.run(
        [CLAUDE_CLI_PATH, "-p", "--safe-mode"], input=prompt,
        capture_output=True, text=True, timeout=timeout,
    )
    if result.returncode != 0:
        raise RuntimeError(f"claude -p failed: {result.stderr}")
    return json.loads(_strip_code_fences(result.stdout))


def _mock_generate(seed=None):
    """Deterministic stand-in used when the claude CLI isn't available.
    Two named seeds:
    - default / any int: unabbreviated suffix, fails first, refiner
      abbreviates it to pass
    - "unfixable": too long AND wrong suffix, mock refiner deliberately
      can't fix it, to demonstrate the Circuit Breaker firing
    """
    if seed == "unfixable":
        return {
            "street_name": "Old Historical Fairweather Founders",
            "suffix": "BOULEVARD",
            "_fixable": False,
        }
    return {
        "street_name": "Founders",
        "suffix": "BOULEVARD",
        "_fixable": True,
    }


def generate_sign(seed=None, area_hint="downtown intersection"):
    if CLAUDE_CLI_AVAILABLE:
        prompt = PROMPT_TEMPLATE.format(area_hint=area_hint)
        return _call_claude_code(prompt)
    return _mock_generate(seed)
