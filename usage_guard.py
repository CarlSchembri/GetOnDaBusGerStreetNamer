"""
Usage guard: a run-level Circuit Breaker, separate from the per-item retry
cap in streetnamer.py.

The per-item cap (MAX_ATTEMPTS=3 in streetnamer.py) stops one stubborn
layout from looping forever. This guard stops the WHOLE RUN from quietly
spending your subscription's shared usage window if the pipeline is ever
extended to generate many districts in one go.

This pipeline is meant to be run interactively, once per invocation, with
you watching the output. Do not wire this into a cron job, file watcher,
or background service - "should not be left alone" is a design constraint,
not just a comment.
"""
import time

MAX_TOTAL_CLAUDE_CALLS = 10   # hard ceiling for the entire run, across all items
CALL_PACING_SECONDS = 1.0     # small delay between calls so nothing hammers the CLI

_call_count = 0


class UsageLimitExceeded(Exception):
    pass


def register_call():
    """Call this immediately before every claude -p invocation, real calls
    only (the mock path never touches this - it doesn't cost anything)."""
    global _call_count
    _call_count += 1
    print(f"[usage] claude -p call #{_call_count} of {MAX_TOTAL_CLAUDE_CALLS} max this run")

    if _call_count > MAX_TOTAL_CLAUDE_CALLS:
        raise UsageLimitExceeded(
            f"Hit the {MAX_TOTAL_CLAUDE_CALLS}-call ceiling for this run. "
            "Stopping the pipeline entirely instead of continuing to spend "
            "subscription usage unattended. Re-run manually if you want to continue."
        )

    time.sleep(CALL_PACING_SECONDS)


def reset():
    """Only for tests - a real run should never reset mid-session."""
    global _call_count
    _call_count = 0


def set_ceiling(n):
    """Explicitly declare a new ceiling for this run. Used by batch mode to
    size the budget to the actual job instead of the demo-scale default -
    this is still a hard limit, just one sized on purpose rather than left
    at 10. Prints so the new budget is visible before anything runs."""
    global MAX_TOTAL_CLAUDE_CALLS
    MAX_TOTAL_CLAUDE_CALLS = n
    print(f"[usage] ceiling set to {n} calls for this run")
