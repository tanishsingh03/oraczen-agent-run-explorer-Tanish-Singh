import os
from typing import AsyncIterator
from google import genai
from providers.base import ExplainProvider


class GeminiProvider(ExplainProvider):

    MODEL = "gemini-3.8-flash"

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY not set. Add it to backend/.env")
        self._client = genai.Client(api_key=api_key)

    async def explain(self, run: dict) -> AsyncIterator[str]:
        prompt = self._build_prompt(run)
        try:
            # generate_content (non-streaming) — avoids chunked-encoding crash
            # when Gemini returns 503 before any tokens are sent
            response = self._client.models.generate_content(
                model=self.MODEL,
                contents=prompt,
            )
            text = response.text or ""
            # Simulate streaming word-by-word so the UI still animates
            import asyncio
            words = text.split()
            for i, word in enumerate(words):
                yield ("" if i == 0 else " ") + word
                await asyncio.sleep(0.03)
        except Exception as e:
            msg = str(e)
            # if "503" in msg or "UNAVAILABLE" in msg:
            #     yield "Gemini is currently overloaded. Please try again in a moment."
            # else:
            #     yield f"Error calling Gemini: {type(e).__name__} — {msg[:120]}"
            if "503" in msg:
                yield "Gemini server is temporarily overloaded. Please try again shortly."
            elif "UNAVAILABLE" in msg:
                yield "Gemini service is temporarily unavailable. Please try again later."
            else:
                yield f"Error calling Gemini: {type(e).__name__} — {msg[:120]}"
            

    @staticmethod
    def _build_prompt(run: dict) -> str:
        run_id      = run.get("id", "unknown")
        agent       = run.get("agent", "unknown")
        status      = run.get("status", "unknown")
        prompt_text = run.get("prompt", "")
        steps       = run.get("steps", [])
        error       = run.get("error")
        duration_ms = run.get("duration_ms")
        cost_usd    = run.get("cost_usd")

        duration_str = (
            f"{duration_ms / 1000:.1f}s" if duration_ms and duration_ms > 0
            else "unknown duration"
        )
        cost_str = f"${cost_usd:.4f}" if cost_usd is not None else "unknown"

        if steps:
            step_lines = [
                f"  Step {s.get('index')}: {s.get('name')} "
                f"[tool={s.get('tool')}] status={s.get('status')} "
                f"duration={s.get('duration_ms')}ms"
                for s in steps
            ]
            steps_summary = "\n".join(step_lines)
        else:
            steps_summary = "  No steps recorded."

        error_block = ""
        if error:
            error_block = (
                f"\nError: {error.get('type')} at step {error.get('step_index')}: "
                f"{error.get('message')}"
            )

        return (
            f"You are a helpful assistant explaining AI agent run traces to support engineers.\n\n"
            f"Explain this agent run in 3-4 clear sentences. Be specific about what the agent did, "
            f"which tools it used, and if it failed, exactly what went wrong and where.\n\n"
            f"Run ID: {run_id}\n"
            f"Agent: {agent}\n"
            f"Status: {status}\n"
            f"Duration: {duration_str}\n"
            f"Cost: {cost_str}\n"
            f"Prompt: {prompt_text}\n\n"
            f"Steps:\n{steps_summary}{error_block}\n\n"
            f"Write a clear, concise explanation. Do not use markdown formatting."
        )
