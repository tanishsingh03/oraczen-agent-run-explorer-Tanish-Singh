import asyncio
from typing import AsyncIterator

from providers.base import ExplainProvider

class MockProvider(ExplainProvider):

    async def explain(self, run: dict) -> AsyncIterator[str]:
        text = self._build_explanation(run)
        words = text.split()
        for i, word in enumerate(words):
            chunk = (" " if i > 0 else "") + word
            yield chunk
            await asyncio.sleep(0.05)

    @staticmethod
    def _build_explanation(run: dict) -> str:
        run_id = run.get("id", "unknown")
        agent = run.get("agent", "unknown agent")
        status = run.get("status", "unknown")
        prompt = run.get("prompt", "")
        steps = run.get("steps", [])
        error = run.get("error")
        duration_ms = run.get("duration_ms")
        cost_usd = run.get("cost_usd")

        duration_str = (
            f"in {duration_ms / 1000:.1f}s" if duration_ms and duration_ms > 0 else "with an unknown duration"
        )
        cost_str = f"at a cost of ${cost_usd:.4f}" if cost_usd is not None else "with no recorded cost"

        lines = [
            f"Run {run_id} was executed by the {agent} agent and {status} {duration_str} {cost_str}."
        ]

        if prompt:
            lines.append(
                f"The run was triggered with the prompt: \"{prompt[:120]}{'...' if len(prompt) > 120 else ''}\"."
            )

        if steps:
            step_count = len(steps)
            tools_used = list(dict.fromkeys(s.get("tool", "none") for s in steps if s.get("tool") != "none"))
            tools_str = ", ".join(tools_used) if tools_used else "no external tools"
            lines.append(
                f"It completed {step_count} step{'s' if step_count != 1 else ''}, "
                f"using {tools_str}."
            )
        else:
            lines.append("No steps were recorded for this run.")

        if status == "failed" and error:
            err_type = error.get("type", "unknown error")
            err_msg = error.get("message", "")
            err_step = error.get("step_index")
            step_ref = f" at step {err_step}" if err_step is not None else ""
            lines.append(
                f"The run failed{step_ref} with a {err_type}: {err_msg}"
            )
            lines.append(
                "To investigate, check the step inputs and outputs on the detail page "
                "and look for upstream data quality issues or configuration mismatches."
            )
        elif status == "cancelled":
            lines.append(
                "The run was cancelled before it could complete. "
                "Check whether the cancellation was user-initiated or due to a timeout policy."
            )
        elif status == "running":
            lines.append(
                "This run is still in progress. No final outcome is available yet."
            )
        elif status == "succeeded":
            lines.append(
                "All steps completed successfully. Review the step outputs to verify the result meets expectations."
            )

        return " ".join(lines)
