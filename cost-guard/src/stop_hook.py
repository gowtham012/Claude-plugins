#!/usr/bin/env python3
"""Stop hook — tracks usage after every response, warns on budget."""
from __future__ import annotations
import json, os, sys
from datetime import datetime, timezone
from pathlib import Path


def main() -> None:
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            return
        data = json.loads(raw)
    except Exception:
        return

    cwd = data.get("cwd") or os.getcwd()
    try:
        d = Path(cwd) / "cost-guard"
        if not d.exists():
            return

        config_f = d / "config.json"
        state_f = d / "state.json"
        if not state_f.exists():
            return

        config = json.loads(config_f.read_text()) if config_f.exists() else {}
        state = json.loads(state_f.read_text())

        # Estimate tokens for this turn (rough heuristic from hook data size)
        input_est = max(100, len(raw) // 4)
        output_est = max(50, input_est // 3)

        model = config.get("default_model", "default")
        pricing = {
            "claude-sonnet-4-20250514": {"input": 3.00, "output": 15.00},
            "claude-opus-4-20250514": {"input": 15.00, "output": 75.00},
            "claude-haiku-4-5-20251001": {"input": 0.25, "output": 1.25},
            "default": {"input": 3.00, "output": 15.00},
        }
        prices = pricing.get(model, pricing["default"])
        cost = (input_est * prices["input"] + output_est * prices["output"]) / 1_000_000

        state["session_input_tokens"] = state.get("session_input_tokens", 0) + input_est
        state["session_output_tokens"] = state.get("session_output_tokens", 0) + output_est
        state["session_cost_usd"] = state.get("session_cost_usd", 0) + cost
        state["all_time_input_tokens"] = state.get("all_time_input_tokens", 0) + input_est
        state["all_time_output_tokens"] = state.get("all_time_output_tokens", 0) + output_est
        state["all_time_cost_usd"] = state.get("all_time_cost_usd", 0) + cost
        state["last_updated"] = datetime.now(timezone.utc).isoformat()

        tmp = state_f.with_suffix(".tmp")
        tmp.write_text(json.dumps(state, indent=2))
        tmp.rename(state_f)

        # Regenerate budget-status.md
        budget = config.get("budget_usd", 0)
        spent = state.get("all_time_cost_usd", 0)
        session_cost = state.get("session_cost_usd", 0)
        label = state.get("current_label", "")
        if budget > 0:
            pct = (spent / budget) * 100
            line = f"Budget: ${spent:.2f} / ${budget:.2f} ({pct:.1f}%) | Session: ${session_cost:.2f}"
        else:
            line = f"No budget set | Session: ${session_cost:.2f} | All-time: ${spent:.2f}"
        if label:
            line += f" | Label: {label}"
        (d / "budget-status.md").write_text(line + "\n")

        # Warn if approaching budget
        if budget > 0:
            pct = (spent / budget) * 100
            warn_at = config.get("warn_at_percent", 80.0)
            if pct >= warn_at:
                hard = config.get("hard_limit", False)
                msg = f"[cost-guard] WARNING: ${spent:.2f} of ${budget:.2f} spent ({pct:.1f}%)."
                if hard and pct >= 100:
                    msg += " HARD LIMIT ACTIVE — tool calls will be blocked."
                else:
                    msg += " Consider wrapping up soon."
                print(json.dumps({"systemMessage": msg}), flush=True)

    except Exception:
        pass


if __name__ == "__main__":
    main()
