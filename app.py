"""
Hyperpersonalisation Lab
A small vignette task on AI-hyperpersonalised executive fraud.

Participants act as observers of the messages received by a fictional bank
branch director in Valencia. For each message they rate how legitimate it
looks (0-100) and choose an action. At the end, performance is summarised
with signal detection measures (hit rate, false alarm rate, d', criterion c).
"""

import random
from statistics import NormalDist

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Hyperpersonalisation Lab", layout="centered")

# ---------------------------------------------------------------------------
# Fictional target profile
# ---------------------------------------------------------------------------
PROFILE = {
    "name": "Javier Ortega",
    "role": "Branch Director, fictional bank, Valencia (Ruzafa branch)",
    "public": [
        "Finished the Valencia Half Marathon in 1:38 (posted on Instagram)",
        "Spoke on a panel about digital banking at a fintech event in Madrid (LinkedIn)",
        "Studied Business at the Universitat de València (LinkedIn)",
        "Local news article about the renovation of his branch",
    ],
    "private": [
        "His daughter Lucía has a school play next Friday",
        "An internal audit of his branch is scheduled for this month",
        "His usual internal reporting portal is called 'Gestor'",
    ],
}

# ---------------------------------------------------------------------------
# Stimuli. is_fraud: True = fraudulent. data_source: which kind of personal
# detail the message uses (public = findable online, private = not online).
# ---------------------------------------------------------------------------
MESSAGES = [
    {
        "id": "F1", "is_fraud": True, "data_source": "public", "channel": "Email",
        "sender": "Ana Ferrer, Regional Director",
        "text": "Javier, congrats on the 1:38 in the half, impressive. I need a favour "
                "before the acquisition goes public: a transfer of €48,000 to a new "
                "supplier today. Keep it between us until Monday, I'm in meetings all day.",
        "cues": "Urgency, secrecy and an unusual payment request. The personal detail "
                "(race time) is public on Instagram, so it proves nothing about the sender.",
    },
    {
        "id": "F2", "is_fraud": True, "data_source": "public", "channel": "WhatsApp",
        "sender": "Unknown number",
        "text": "Hi Javier, it's Marcos, we met at the digital banking panel in Madrid. "
                "New phone. One of my clients banks with you and needs an urgent wire "
                "approved before 2pm, can you help me out?",
        "cues": "New number plus a favour that bypasses procedure. The panel is listed "
                "on LinkedIn, so anyone could reference it.",
    },
    {
        "id": "F3", "is_fraud": True, "data_source": "public", "channel": "LinkedIn",
        "sender": "Recruiter, executive search firm",
        "text": "Fellow UV alumnus here. We have a confidential senior role that fits "
                "your profile. Please log in to our candidate portal with your corporate "
                "email and password to see the offer.",
        "cues": "Asks for corporate credentials. Shared university is public on LinkedIn "
                "and is used to build false familiarity.",
    },
    {
        "id": "F4", "is_fraud": True, "data_source": "public", "channel": "Email",
        "sender": "IT Security Team",
        "text": "Following the renovation works at the Ruzafa branch, all branch "
                "accounts must be re-verified today. Use the link below to confirm "
                "your access or it will be suspended.",
        "cues": "Threat of suspension and an external link. The renovation was in the "
                "local press, so it lends false credibility.",
    },
    {
        "id": "L1", "is_fraud": False, "data_source": "private", "channel": "Email",
        "sender": "Ana Ferrer, Regional Director",
        "text": "Hi Javier, ahead of this month's audit could you upload the usual "
                "branch report to Gestor when you get a chance? No rush, end of week is fine.",
        "cues": "Uses private details (the audit, the internal portal name), follows the "
                "normal channel and has no time pressure.",
    },
    {
        "id": "L2", "is_fraud": False, "data_source": "private", "channel": "WhatsApp",
        "sender": "Sister (saved contact)",
        "text": "Are you coming to Lucía's play on Friday? Mum is saving seats.",
        "cues": "Known contact, private family detail, no request involving money or access.",
    },
    {
        "id": "L3", "is_fraud": False, "data_source": "public", "channel": "Email",
        "sender": "HR, Wellbeing Programme",
        "text": "We saw your half marathon post, well done! We're putting together a "
                "staff team for the 10K in spring. Reply to this email if you're interested.",
        "cues": "Uses a public detail but asks for nothing sensitive and has no urgency. "
                "Public data alone does not make a message fraudulent.",
    },
    {
        "id": "L4", "is_fraud": False, "data_source": "public", "channel": "LinkedIn",
        "sender": "Former classmate",
        "text": "Javier! Saw you on the fintech panel, great talk. I'm back in Valencia "
                "next month, coffee?",
        "cues": "Public details, but the request is harmless and easy to verify.",
    },
]

ACTIONS = ["Proceed as asked", "Verify through another channel", "Report as suspicious"]
THRESHOLD = 50  # ratings below this count as a "fraud" judgement



# ---------------------------------------------------------------------------
# Opening screen (legal notice + instructions)
# ---------------------------------------------------------------------------
INTRO_CSS = """
<style>
.hl-section {margin: 1.6rem 0 0.8rem 0; display:flex; align-items:center; gap:.6rem;}
.hl-section .num {width:1.9rem; height:1.9rem; border-radius:50%; display:flex;
  align-items:center; justify-content:center; font-weight:700; font-size:.95rem;
  background:#4f6bed; color:#fff;}
.hl-section h3 {margin:0; padding:0; font-size:1.25rem;}
.hl-grid {display:grid; grid-template-columns:repeat(auto-fit,minmax(230px,1fr)); gap:.8rem;}
.hl-card {border:1px solid rgba(128,128,128,.25); border-radius:14px; padding:1rem 1.1rem;
  background:rgba(128,128,128,.06); border-left:4px solid #4f6bed;}
.hl-card .title {font-weight:700; margin-bottom:.3rem; font-size:.98rem;}
.hl-card .body {font-size:.88rem; opacity:.85; line-height:1.45;}
.hl-card.wide {grid-column:1/-1;}
.hl-steps {position:relative; margin-left:.9rem; padding-left:1.6rem;
  border-left:2px solid rgba(79,107,237,.45);}
.hl-step {position:relative; margin-bottom:1.1rem;}
.hl-step:last-child {margin-bottom:0;}
.hl-step .dot {position:absolute; left:-2.45rem; top:0; width:1.6rem; height:1.6rem;
  border-radius:50%; background:#4f6bed; color:#fff; font-size:.8rem; font-weight:700;
  display:flex; align-items:center; justify-content:center;}
.hl-step .title {font-weight:700; font-size:.98rem;}
.hl-step .body {font-size:.88rem; opacity:.85; line-height:1.45;}
.hl-time {display:inline-block; margin-top:1rem; padding:.3rem .8rem; border-radius:999px;
  background:rgba(79,107,237,.15); font-size:.85rem; font-weight:600;}
</style>
"""

INTRO_HTML = """
<div class="hl-section"><div class="num">1</div><h3>Legal notice</h3></div>
<div class="hl-grid">
  <div class="hl-card"><div class="title">Fictional content</div>
    <div class="body">Javier Ortega, the bank, the senders and every message are invented
    for teaching and research. Any resemblance to real people or organisations is coincidental.</div></div>
  <div class="hl-card"><div class="title">Educational demo</div>
    <div class="body">Not a security tool and not professional, legal or financial advice.
    If you get a suspicious message in real life, follow your organisation's procedures and
    verify through an independent channel.</div></div>
  <div class="hl-card"><div class="title">Your answers stay with you</div>
    <div class="body">No personal data is requested and nothing is stored or sent. Answers live
    only in this browser session and vanish when you close the tab, unless you download them.</div></div>
  <div class="hl-card"><div class="title">Hosting</div>
    <div class="body">The app runs on Streamlit Community Cloud, which may process technical
    data such as your IP address under its own privacy notice.</div></div>
  <div class="hl-card wide"><div class="title">Authorship</div>
    <div class="body">Research design and content by Mar&iacute;a Mart&iacute;nez Melero.
    Please do not reuse the stimuli without permission.</div></div>
</div>

<div class="hl-section"><div class="num">2</div><h3>How it works</h3></div>
<div class="hl-steps">
  <div class="hl-step"><div class="dot">1</div>
    <div class="title">Read the target profile first</div>
    <div class="body">It is in the column on the left (on a phone, tap the arrow at the top
    left). It shows what anyone can find about Javier online and what only people close to him
    know. You can check it at any time.</div></div>
  <div class="hl-step"><div class="dot">2</div>
    <div class="title">Eight messages, random order</div>
    <div class="body">Sent to Javier by email, WhatsApp or LinkedIn. Some are fraudulent,
    some are legitimate.</div></div>
  <div class="hl-step"><div class="dot">3</div>
    <div class="title">Rate and decide</div>
    <div class="body">Rate how legitimate each message looks from 0 (certainly fraud) to 100
    (certainly legitimate) and choose what Javier should do.</div></div>
  <div class="hl-step"><div class="dot">4</div>
    <div class="title">No going back</div>
    <div class="body">Once you press <i>Next</i>, that answer is final, so take your time.</div></div>
  <div class="hl-step"><div class="dot">5</div>
    <div class="title">See your results</div>
    <div class="body">How well you told fraud from legitimate messages, your response bias,
    and the cues hidden in each message.</div></div>
</div>
<div class="hl-time">About 5 minutes</div>
<br><br>
"""

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
def init_state():
    order = MESSAGES.copy()
    random.shuffle(order)
    st.session_state.order = order
    st.session_state.idx = 0
    st.session_state.responses = []


if "order" not in st.session_state:
    init_state()
if "started" not in st.session_state:
    st.session_state.started = False


def sdt(responses):
    """Hit rate, false alarm rate, d' and c with the log-linear correction."""
    frauds = [r for r in responses if r["is_fraud"]]
    legits = [r for r in responses if not r["is_fraud"]]
    hits = sum(r["judged_fraud"] for r in frauds)
    fas = sum(r["judged_fraud"] for r in legits)
    hr = (hits + 0.5) / (len(frauds) + 1)
    far = (fas + 0.5) / (len(legits) + 1)
    z = NormalDist().inv_cdf
    d_prime = z(hr) - z(far)
    c = -0.5 * (z(hr) + z(far))
    return hits / len(frauds), fas / len(legits), d_prime, c


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------
st.title("Hyperpersonalisation Lab")
st.caption(
    "A vignette task on AI-hyperpersonalised executive fraud. "
    "All people, companies and messages are fictional."
)

with st.sidebar:
    st.subheader("Target profile")
    st.markdown(f"**{PROFILE['name']}**  \n{PROFILE['role']}")
    st.markdown("**Publicly available online**")
    for item in PROFILE["public"]:
        st.markdown(f"- {item}")
    st.markdown("**Private (not online)**")
    for item in PROFILE["private"]:
        st.markdown(f"- {item}")

total = len(st.session_state.order)
idx = st.session_state.idx

if not st.session_state.started:
    st.markdown(INTRO_CSS, unsafe_allow_html=True)
    st.markdown(INTRO_HTML, unsafe_allow_html=True)

    agreed = st.checkbox("I have read the notice above and want to start the task.")
    if st.button("Start", type="primary", disabled=not agreed):
        st.session_state.started = True
        st.rerun()

elif idx < total:
    msg = st.session_state.order[idx]
    st.progress(idx / total, text=f"Message {idx + 1} of {total}")

    with st.container(border=True):
        st.markdown(f"**{msg['channel']}** · from *{msg['sender']}*")
        st.write(msg["text"])

    with st.form(key=f"form_{msg['id']}"):
        rating = st.slider(
            "How legitimate does this message look? (0 = certainly fraud, 100 = certainly legitimate)",
            0, 100, 50,
        )
        action = st.radio("What should Javier do?", ACTIONS, index=None)
        submitted = st.form_submit_button("Next")

    if submitted:
        if action is None:
            st.warning("Please choose an action before continuing.")
        else:
            st.session_state.responses.append({
                "id": msg["id"],
                "is_fraud": msg["is_fraud"],
                "data_source": msg["data_source"],
                "channel": msg["channel"],
                "rating": rating,
                "action": action,
                "judged_fraud": rating < THRESHOLD,
            })
            st.session_state.idx += 1
            st.rerun()

else:
    responses = st.session_state.responses
    hr, far, d_prime, c = sdt(responses)

    st.subheader("Your results")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Frauds caught", f"{hr:.0%}")
    col2.metric("False alarms", f"{far:.0%}")
    col3.metric("d'", f"{d_prime:.2f}")
    col4.metric("Criterion c", f"{c:.2f}")

    st.markdown(
        "**d'** measures how well you told fraud from legitimate messages "
        "(0 = chance, higher = better). **c** shows your bias: negative means you "
        "tended to call messages fraud, positive means you tended to trust them."
    )

    df = pd.DataFrame(responses)
    df["type"] = df["is_fraud"].map({True: "Fraud", False: "Legitimate"})

    st.subheader("Mean legitimacy rating")
    means = df.groupby(["type", "data_source"])["rating"].mean().unstack()
    st.bar_chart(means)
    st.caption(
        "The key question: do public personal details make fraudulent messages "
        "look as trustworthy as legitimate ones?"
    )

    st.subheader("Message by message")
    lookup = {m["id"]: m for m in MESSAGES}
    for r in responses:
        m = lookup[r["id"]]
        correct = r["judged_fraud"] == r["is_fraud"]
        label = "Fraud" if m["is_fraud"] else "Legitimate"
        mark = "Correct" if correct else "Missed"
        with st.expander(f"{mark} · {m['channel']} from {m['sender']} · {label} · you rated {r['rating']}"):
            st.write(m["text"])
            st.info(m["cues"])

    st.download_button(
        "Download your responses (CSV)",
        df.drop(columns=["type"]).to_csv(index=False).encode("utf-8"),
        file_name="responses.csv",
        mime="text/csv",
    )

    if st.button("Start again"):
        init_state()
        st.rerun()
