"""
ai.py

Calls a free AI model (Google Gemini) to turn the matched policy section
into a clear, plain-language answer to the employee's question.

Why Gemini: Google AI Studio (aistudio.google.com) gives a free API key
with no payment details required, which is why we picked it for this
project. If your panel asks "why this model" - that's the honest answer.

Uses the "google-genai" package (Google's current, supported SDK - the
older "google-generativeai" package has been officially discontinued).

Why this is in its own file: if you ever want to swap providers (OpenAI,
Groq, etc.), this is the ONLY function you need to rewrite. Nothing in
app.py or search.py needs to change - that separation is itself a small
but real piece of "good technical implementation" worth mentioning.

IMPORTANT: this never lets the app crash. If the API key is missing, the
model call fails, or the venue wifi is down, it falls back to showing the
raw policy text instead - this is what makes the demo resilient.
"""

import os
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError

# Try the newer model name first, fall back to an older one in case the
# first one isn't available on this API key's tier.
_MODEL_CANDIDATES = ["gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-flash-lite-latest"]

# Max seconds to wait for the AI before giving up and falling back.
# Without this, a slow/blocked venue network can freeze the whole app
# instead of just failing over to offline mode - this is the fix for that.
_TIMEOUT_SECONDS = 10


def generate_answer(question, section, api_key=None):
    """
    Given a question and the matched policy section, asks the AI to
    write a short, friendly answer using ONLY that section's text.

    Returns a tuple: (answer_text, used_ai: bool)
    used_ai is False whenever we fell back to raw policy text, so the UI
    can show a small note explaining why - never a silent lie about how
    the answer was produced.
    """
    api_key = api_key or os.getenv("GEMINI_API_KEY")
    offline_answer = f"(Offline mode) Based on our policy:\n\n{section['content']}"

    if not api_key:
        return offline_answer, False

    try:
        from google import genai

        client = genai.Client(api_key=api_key)

        prompt = f"""You are a helpful HR assistant. Answer the employee's
question using ONLY the policy text given below. Keep the answer to
2-3 sentences, in a friendly, plain tone. Do not invent any information
that isn't in the policy text. If the policy text doesn't actually
answer the question, say you're not fully sure and recommend the
employee contact HR directly.

Policy section: {section['title']}
Policy text: {section['content']}

Employee question: {question}
"""

        def _call(model_name):
            response = client.models.generate_content(model=model_name, contents=prompt)
            return response.text.strip()

        last_error = None
        for model_name in _MODEL_CANDIDATES:
            # Note: deliberately NOT using "with ThreadPoolExecutor(...) as executor"
            # here - that form blocks on shutdown() until the thread finishes,
            # which would silently cancel the whole point of the timeout below.
            executor = ThreadPoolExecutor(max_workers=1)
            future = executor.submit(_call, model_name)
            try:
                result = future.result(timeout=_TIMEOUT_SECONDS)
                executor.shutdown(wait=False)
                return result, True
            except FutureTimeoutError:
                executor.shutdown(wait=False)
                last_error = f"timed out after {_TIMEOUT_SECONDS}s"
                continue
            except Exception as e:  # noqa: BLE001 - deliberately broad, see docstring
                executor.shutdown(wait=False)
                last_error = e
                continue

        # Every model name failed - fall back instead of crashing.
        print(f"[ai.py] All Gemini model attempts failed: {last_error}")
        return offline_answer, False

    except Exception as e:  # noqa: BLE001 - network issues, bad key, etc.
        print(f"[ai.py] AI call failed, falling back to offline mode: {e}")
        return offline_answer, False
