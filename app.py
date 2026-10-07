"""
app.py

The Streamlit chat interface. This is the file you run.

Flow: pick your role in the sidebar -> type a question -> search.py finds
the best matching policy section FROM THE SECTIONS YOUR ROLE CAN SEE ->
if the match is confident enough, ai.py turns it into a plain-language
answer (or falls back to the raw policy text if the AI is unreachable) ->
answer is shown with its source cited -> if nothing matched well, the app
admits it doesn't know instead of guessing.

Run with: streamlit run app.py
"""

from datetime import datetime

import streamlit as st
from search import load_sections, filter_by_role, find_best_section
from ai import generate_answer

# Below this match score, we don't trust the result enough to answer.
# Tune this after testing with your own questions - if the bot is
# answering things it shouldn't, raise this number; if it's saying
# "not sure" too often, lower it.
CONFIDENCE_THRESHOLD = 0.15

st.set_page_config(page_title="HR FAQ Assistant", page_icon="💬")
st.title("💬 HR FAQ Assistant")
st.caption(
    "Ask about leave, WFH, or expense policy. "
    "I only answer from our actual policy document - nothing made up."
)

all_sections = load_sections("policy.txt")

# --- Role toggle: this is the "scope answers to what the user is
# allowed to see" enterprise-grade feature. A Manager/HR-only policy
# (like termination procedures) simply isn't visible to an Employee -
# the search function never even considers it. ---
with st.sidebar:
    st.subheader("👤 Logged in as")
    role = st.radio(
        "Select your role",
        options=["Employee", "Manager", "HR"],
        index=0,
        label_visibility="collapsed",
    )
    st.caption(
        "Managers and HR can ask about additional topics "
        "(like performance plans or terminations) that regular "
        "employees can't query here."
    )

    if "log" not in st.session_state:
        st.session_state.log = []

    with st.expander(f"📋 Session log ({len(st.session_state.log)})"):
        if not st.session_state.log:
            st.caption("No questions asked yet.")
        for entry in reversed(st.session_state.log):
            st.markdown(
                f"**{entry['time']}** · `{entry['role']}`  \n"
                f"Q: {entry['question']}  \n"
                f"→ {entry['matched'] or 'no match'} "
                f"(score {entry['score']:.0%})"
            )
            st.divider()

sections = filter_by_role(all_sections, role)

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

question = st.chat_input("Type your question...")

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    section, score = find_best_section(question, sections)

    # Log every question for the "keep a log" enterprise-grade point,
    # regardless of whether it matched - this is what lets HR later see
    # what people are actually asking.
    st.session_state.log.append(
        {
            "time": datetime.now().strftime("%H:%M:%S"),
            "role": role,
            "question": question,
            "matched": section["title"] if section else None,
            "score": score,
        }
    )

    with st.chat_message("assistant"):
        if section is None or score < CONFIDENCE_THRESHOLD:
            # This is the "human hand-off" behaviour: admitting
            # uncertainty instead of confidently guessing wrong.
            answer = (
                "I'm not confident I have the right policy for that one. "
                "Please contact HR directly so you get an accurate answer."
            )
        else:
            answer, used_ai = generate_answer(question, section)
            answer += f"\n\n*Source: {section['title']}*"
            if not used_ai:
                answer += "\n\n*(AI model unavailable right now - showing the policy text directly.)*"

        st.markdown(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})
