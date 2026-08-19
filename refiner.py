"""
Refiner: takes rejected sign data plus the Evaluator's reason and produces
a corrected version. Same real/mock split as the Generator.
"""
import json
import copy
import subprocess

import usage_guard
from generator import CLAUDE_CLI_AVAILABLE, CLAUDE_CLI_PATH, _strip_code_fences


def _mock_refine(sign, reason):
    """Deterministic fix for local testing: abbreviates the suffix. The
    "_fixable" flag is set by the Generator per scenario purely for demo
    purposes - when False, this genuinely cannot satisfy the rule, which
    is what should trigger the Circuit Breaker."""
    fixed = copy.deepcopy(sign)
    if not fixed.get("_fixable", True):
        return fixed  # mock refiner can't actually fix this one
    fixed["suffix"] = "BLVD"
    return fixed


def _call_claude_code(sign, reason, timeout=120):
    usage_guard.register_call()
    prompt = f"""Original sign: {json.dumps(sign)}

Evaluator rejected it for this reason: {reason}

Rewrite it to fix ONLY this issue, keeping the same street name concept.
Keep the meme-slapstick flair (style like "Bussin BLVD" or "Yeet Street") -
don't flatten it into something generic while fixing this.
Return ONLY the corrected JSON in the same schema, no prose, no markdown
code fences."""
    result = subprocess.run(
        [CLAUDE_CLI_PATH, "-p", "--safe-mode"], input=prompt,
        capture_output=True, text=True, timeout=timeout,
    )
    if result.returncode != 0:
        raise RuntimeError(f"claude -p failed: {result.stderr}")
    return json.loads(_strip_code_fences(result.stdout))


def refine(sign, reason):
    if CLAUDE_CLI_AVAILABLE:
        return _call_claude_code(sign, reason)
    return _mock_refine(sign, reason)
