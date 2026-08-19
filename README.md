# Get On Da Bus — Street Sign GER Pipeline

## Game
*Get On Da Bus* — arcade bus-driving game set in the fictional town of Fairweather.

## What this pipeline generates
Street name signs for Fairweather intersections: a `street_name` and a `suffix`
(e.g. "Founders" + "BLVD"), meant to be dropped into the WBP_StreetSign widget.

## What rule the Evaluator enforces
Three checks pulled directly from the sign asset and Fairweather's signage convention:
1. **Panel fit** — combined "name + suffix" must fit the physical sign panel
   (`SIGN_MAX_CHARS` in `evaluator.py` — calibrated against a confirmed real
   in-game example, "Fairweather AVE" at 15 characters).
2. **Valid suffix abbreviation** — suffix must be one of the standard abbreviations
   (ST, AVE, BLVD, RD, LN, DR, WAY, CT, PL), matching real-world street sign
   convention instead of spelling the word out.
3. **No real-world street names** — Fairweather streets must be original, not
   references to real, recognizable streets.

## Did it catch something useful?
Yes. In a real `--batch 6` run, the Generator proposed "No Bridge Wharf WAY"
for a waterfront-district sign (19 characters). The Evaluator rejected it —
5 characters over `SIGN_MAX_CHARS` (16), so it would have overflowed the
physical sign panel — and the Refiner corrected it to "No Bridge WAY" (13
characters) on the next attempt, which passed. Full attempt history:
`output/batch/item_03/log.json`. See `output/pass/log.json` and
`output/escalate/log.json` for the demo scenarios, and
`output/batch/batch_summary.json` for the rest of that batch, including
on-theme results like "Ejecto Seato WAY" and "Olde Yeete LN" — the
Generator's prompt explicitly steers toward the GDD's meme-slapstick flavor
tone (Section "Tone Register") rather than generic fantasy-town names.

## Pipeline architecture
- **Generator** (`generator.py`) — proposes a street sign via `claude -p`
  (runs on Claude subscription auth, no API key needed), with a mock fallback
  for environments without the Claude Code CLI installed.
- **Evaluator** (`evaluator.py`) — checks the three rules above, pure code,
  no API call.
- **Refiner** (`refiner.py`) — takes the Evaluator's rejection reason and
  rewrites via `claude -p`, same auth as the Generator.
- **Circuit Breaker** — two layers:
  - Per-item: `MAX_ATTEMPTS = 3` in `streetnamer.py` — one stubborn sign
    gets flagged for manual review instead of looping forever.
  - Per-run: `usage_guard.py` hard-caps total `claude -p` calls at 10 for
    the whole run, so a bug can't silently spend subscription usage
    unattended. Every call prints live as it happens.

## Running it for real
1. Confirm `claude -p "test"` works in this project's terminal (subscription
   login active).
2. `python3 streetnamer.py` — runs the two demo scenarios (pass case,
   escalate case) and writes logs + capacity-bar renders to `output/`. Note:
   the "escalate case" seed only forces a guaranteed circuit-breaker trip
   through the mock fallback (no `claude` CLI on PATH) — with the real
   `claude -p` path, Claude usually self-corrects within the 3-attempt
   budget, so a live run isn't guaranteed to escalate every time even though
   the escalation code path is real and exercised whenever a sign can't be
   fixed in time (see `run_pipeline` in `streetnamer.py`).
3. `python3 streetnamer.py --batch 40 --chunk-size 10` — generates a real
   batch of street names, 10 at a time. Re-run the exact same command to
   continue with the next chunk; progress is saved incrementally in
   `output/batch/batch_summary.json` so nothing is lost between runs.
4. `SIGN_MAX_CHARS` in `evaluator.py` is calibrated against a confirmed
   real example - update it if you find the real limit is different.
