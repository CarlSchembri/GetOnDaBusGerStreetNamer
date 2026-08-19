"""
Orchestrator: runs Generator -> Evaluator -> Refiner for street signs,
with a Circuit Breaker cap, logging every attempt.
"""
import os
import json

import usage_guard
from generator import generate_sign
from evaluator import evaluate
from refiner import refine
from render import render_sign
from usage_guard import UsageLimitExceeded

MAX_ATTEMPTS = 3  # per-item Circuit Breaker: stops one stubborn sign

AREA_HINTS = [
    "downtown intersection", "residential street", "waterfront district",
    "historic district", "shopping district", "industrial district",
    "highway frontage road", "park-adjacent street",
]


def run_pipeline(seed=None, area_hint="downtown intersection", out_dir="output"):
    os.makedirs(out_dir, exist_ok=True)
    log = []

    try:
        sign = generate_sign(seed=seed, area_hint=area_hint)
    except UsageLimitExceeded as e:
        print(f"STOPPED: {e}")
        with open(f"{out_dir}/log.json", "w") as f:
            json.dump({"status": "usage_limit_stopped", "reason": str(e)}, f, indent=2)
        return {"status": "usage_limit_stopped", "attempts": 0}

    for attempt in range(1, MAX_ATTEMPTS + 1):
        passed, reason = evaluate(sign)
        log.append({"attempt": attempt, "passed": passed, "reason": reason, "sign": sign})
        print(f"Attempt {attempt}: {'PASS' if passed else 'FAIL'} - {reason}")

        if passed:
            render_sign(sign, f"{out_dir}/accepted_sign.png", title="Accepted street sign")
            with open(f"{out_dir}/log.json", "w") as f:
                json.dump(log, f, indent=2)
            return {"status": "accepted", "sign": sign, "attempts": attempt}

        if attempt == MAX_ATTEMPTS:
            render_sign(sign, f"{out_dir}/escalated_sign.png",
                        title="ESCALATED - needs manual review")
            with open(f"{out_dir}/log.json", "w") as f:
                json.dump(log, f, indent=2)
            print(f"Circuit breaker triggered: could not self-correct after "
                  f"{MAX_ATTEMPTS} attempts. Flagged for manual review.")
            return {"status": "escalated", "sign": sign, "attempts": attempt, "reason": reason}

        try:
            sign = refine(sign, reason)
        except UsageLimitExceeded as e:
            print(f"STOPPED: {e}")
            log.append({"status": "usage_limit_stopped", "reason": str(e)})
            with open(f"{out_dir}/log.json", "w") as f:
                json.dump(log, f, indent=2)
            return {"status": "usage_limit_stopped", "attempts": attempt}

    return None


def run_batch(count, out_dir="output/batch", chunk_size=None):
    """Generates a list of `count` street signs, resumable across multiple
    invocations. If chunk_size is set, this run stops after generating that
    many NEW items and tells you to re-run the same command to continue -
    each chunk is a separate, supervised invocation rather than one long
    unattended run, and existing results are never regenerated or lost."""
    os.makedirs(out_dir, exist_ok=True)
    summary_path = f"{out_dir}/batch_summary.json"

    results = []
    if os.path.exists(summary_path):
        with open(summary_path) as f:
            results = json.load(f)
        print(f"Resuming - {len(results)} of {count} already done.")

    already_done = len(results)
    remaining = count - already_done
    if remaining <= 0:
        print(f"All {count} already generated. Nothing to do - see {summary_path}")
        return results

    this_chunk = min(chunk_size, remaining) if chunk_size else remaining
    usage_guard.set_ceiling(3 * this_chunk + 2)
    print(f"Generating {this_chunk} more (of {remaining} remaining, "
          f"{already_done}/{count} already done)...")

    for i in range(already_done, already_done + this_chunk):
        hint = AREA_HINTS[i % len(AREA_HINTS)]
        print(f"\n--- Sign {i + 1} of {count} ({hint}) ---")
        result = run_pipeline(area_hint=hint, out_dir=f"{out_dir}/item_{i + 1:02d}")
        results.append({
            "index": i + 1,
            "area_hint": hint,
            "status": result["status"],
            "attempts": result["attempts"],
            "sign": result.get("sign"),
        })
        with open(summary_path, "w") as f:
            json.dump(results, f, indent=2)

        if result["status"] == "usage_limit_stopped":
            print("Chunk stopped early - usage ceiling reached.")
            break

    print("\n=== This chunk ===")
    for r in results[already_done:]:
        if r["sign"]:
            name = f"{r['sign'].get('street_name', '?')} {r['sign'].get('suffix', '?')}"
        else:
            name = "(none)"
        print(f"  {r['index']:>2}. {name:<28} [{r['status']}] ({r['attempts']} attempts, {r['area_hint']})")

    done_now = len(results)
    if done_now < count:
        print(f"\n{done_now}/{count} done. Re-run the exact same command to continue with the next chunk.")
    else:
        accepted = sum(1 for r in results if r["status"] == "accepted")
        print(f"\nAll {count} done - {accepted} accepted. Full detail in {summary_path}")
    return results


if __name__ == "__main__":
    import sys

    if "--batch" in sys.argv:
        idx = sys.argv.index("--batch")
        n = int(sys.argv[idx + 1]) if len(sys.argv) > idx + 1 else 10
        chunk_size = None
        if "--chunk-size" in sys.argv:
            cidx = sys.argv.index("--chunk-size")
            chunk_size = int(sys.argv[cidx + 1])
        run_batch(n, chunk_size=chunk_size)
    else:
        print("=== Scenario 1: normal case (wrong suffix, should pass after one refine) ===")
        result1 = run_pipeline(seed=42, out_dir="output/pass")
        print(json.dumps({"status": result1["status"], "attempts": result1["attempts"]}, indent=2))

        print("\n=== Scenario 2: unfixable case (should trigger circuit breaker) ===")
        result2 = run_pipeline(seed="unfixable", out_dir="output/escalate")
        print(json.dumps({"status": result2["status"], "attempts": result2["attempts"]}, indent=2))
