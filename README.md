# HR FAQ Assistant

An AI-powered chatbot that answers common HR/policy questions instantly from
a company policy document, instead of employees waiting on HR for a reply.

Built for Microsoft Innovate 2026 — Problem Statement #10, "The HR Team
Answering the Same 20 Questions."

---

## 1. How to run it

```bash
pip install -r requirements.txt
streamlit run app.py
```

This opens the chat app in your browser. Type a question like "how many
leave days do I get" and it will answer from `policy.txt`.

### Getting a free AI API key (takes 2 minutes)
1. Go to https://aistudio.google.com
2. Sign in with any Google account, click "Get API key" → "Create API key"
3. Copy the key, then set it before running (quotes matter on Windows!):
   - Mac/Linux: `export GEMINI_API_KEY=your_key_here`
   - Windows (PowerShell): `$env:GEMINI_API_KEY="your_key_here"`

**No key, or the AI call fails/times out? The app still works.** It
automatically falls back to "offline mode" and shows the raw policy text
instead of an AI-rewritten answer, with a small note saying so. This is
intentional — it's your safety net if venue wifi is bad tomorrow. There's
a 10-second timeout on the AI call specifically so a slow/blocked network
can't freeze the whole app during your demo.

### Trying different roles
Use the sidebar to switch between Employee / Manager / HR before asking a
question. A few sample questions only Manager/HR can get answered:
- "can I start a performance improvement plan for someone"
- "how is termination handled"
- "can I change someone's salary"
As an Employee, those come back as "not confident, contact HR" — not
because the bot is broken, but because those policies are scoped away
from that role on purpose. Good live demo moment.

---

## 2. Code walkthrough cheat sheet (for presenting to the panel)

Say this in your own words — don't read it verbatim, just know the idea of each line:

**`policy.txt`** — "This is our company's policy document. We wrote it
ourselves as sample data — leave, WFH, expenses, and a few other common
topics."

**`search.py`** — "When someone asks a question, this file figures out
which policy section is actually relevant. It compares the words in the
question to the words in each section and picks the best match. If
nothing matches well, it says so instead of guessing — that's the
`CONFIDENCE_THRESHOLD` check in `app.py`."

**`ai.py`** — "Once we know the right section, this file sends it to
Google's Gemini model along with the question, and asks it to turn that
policy text into a clear, friendly answer — without adding any
information that isn't actually in our policy."

**`app.py`** — "This is the actual chat interface, built with Streamlit.
It ties the other two files together: get the question, find the
section, generate the answer, show it with its source cited underneath."

### Four design choices worth mentioning out loud
- **Citation**: every answer shows which policy section it came from, so
  it's never a black box — you can always check the source.
- **Confidence threshold + human hand-off**: if the question doesn't
  match anything well, the bot says "I'm not sure, contact HR" instead
  of confidently making something up. This matters a lot for something
  like leave or compliance, where a wrong answer actually causes
  problems.
- **Role-based scoping**: Employees, Managers, and HR see different
  slices of the policy document. A Manager-only or HR-only section is
  filtered out before search even runs for an Employee — it's not just
  hidden in the UI, the bot genuinely can't retrieve it for that role.
- **Session log**: every question asked, by which role, and what it
  matched, is logged in the sidebar. In a real company this is what lets
  HR see which questions keep coming up — which is the whole point of
  the original problem.

---

## 3. If a judge asks "did you use AI to build this?"

Answer honestly — this is not a weakness to hide:

> "Yes, we used AI tools to help us write and structure the code, since
> none of us had built something like this before. What's ours is the
> architecture decisions — why we split search and the AI call into
> separate files, why we added a confidence threshold, why we chose to
> cite sources. We understand what every part does and can walk you
> through any of it."

Then actually do that — open the file they ask about and explain it in
your own words using the cheat sheet above.
