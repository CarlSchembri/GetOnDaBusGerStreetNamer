"""
Evaluator: checks generated Fairweather street signs against rules tied to
the actual sign asset and real-world street sign convention.

RULES:
1. Combined "name + suffix" must fit the physical sign panel - max
   SIGN_MAX_CHARS characters. Note: this is character count, not true
   physical width - the sign uses a proportional font, so this is an
   approximation calibrated against a real confirmed-fitting example
   ("Fairweather AVE"), not an exact pixel measurement. Narrow-letter-heavy
   names may fit slightly over this count; wide-letter-heavy names may not
   fit slightly under it. Good enough as a rule, not perfectly precise.

2. Suffix must be a standard abbreviation (ST, AVE, BLVD, etc.) - real
   street signs abbreviate, they don't spell out "Boulevard" in full, and
   Fairweather's signage should follow that convention for authenticity.

3. No real-world street or place names - Fairweather streets must be
   original, not references to real, recognizable streets.
"""

SIGN_MAX_CHARS = 16  # calibrated against a confirmed real example: "Fairweather AVE" (15 chars) fits in-game

VALID_SUFFIXES = {"ST", "AVE", "BLVD", "RD", "LN", "DR", "WAY", "CT", "PL"}

REAL_WORLD_PLACES = {
    "sunset blvd", "sunset boulevard", "hollywood blvd", "hollywood boulevard",
    "broadway", "wall street", "rodeo drive", "bourbon street", "fifth avenue",
    "5th avenue",
}


def evaluate(sign):
    name = sign.get("street_name", "")
    suffix = sign.get("suffix", "")
    combined = f"{name} {suffix}".strip()

    if len(combined) > SIGN_MAX_CHARS:
        return False, (
            f'"{combined}" is {len(combined)} characters, but the sign '
            f'panel only fits {SIGN_MAX_CHARS}. It will overflow.'
        )

    if suffix.upper() not in VALID_SUFFIXES:
        return False, (
            f'"{suffix}" is not a standard street sign abbreviation. '
            f'Use one of: {", ".join(sorted(VALID_SUFFIXES))}.'
        )

    lowered = combined.lower()
    for place in REAL_WORLD_PLACES:
        if place in lowered:
            return False, (
                f'"{combined}" references the real-world street "{place}". '
                f'Fairweather streets must be original.'
            )

    return True, "Sign fits the panel, uses a valid suffix, and is an original street name."
