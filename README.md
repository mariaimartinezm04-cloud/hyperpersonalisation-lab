# Hyperpersonalisation Lab

A short interactive vignette task on **AI-hyperpersonalised executive fraud**, built as a prototype for my undergraduate thesis in Law and Criminology (Universidad Europea de Valencia).

## Research question

Generative AI makes it cheap to scrape a target's public footprint and weave those details into a fraudulent message. Does an accurate personal detail make people trust a message even when that detail is publicly available online, and therefore says nothing about who the sender is?

## How the task works

Participants act as observers of the inbox of a fictional bank branch director in Valencia. His profile is split into details that are **public** (findable online) and **private** (known only to people close to him).

For each of eight messages (email, WhatsApp, LinkedIn) participants:

1. rate how legitimate it looks (0 to 100), and
2. choose an action (proceed, verify through another channel, report).

The stimuli cross two factors:

| | Public detail | Private detail |
|---|---|---|
| **Fraudulent** | 4 messages | none (by design, attackers only have public data) |
| **Legitimate** | 2 messages | 2 messages |

Message order is randomised for each session.

## Analysis

Ratings below 50 are treated as a "fraud" judgement. Performance is summarised with signal detection theory:

- **Hit rate** (frauds correctly flagged) and **false alarm rate** (legitimate messages flagged)
- **d'** (sensitivity) and **criterion c** (response bias), using the log-linear correction for extreme rates

Results also show mean legitimacy ratings by message type and data source, plus per-message feedback on the cues present.

## Design decisions

- All people, organisations and messages are fictional.
- Fraudulent messages reproduce patterns documented in real executive fraud (urgency, secrecy, channel switching, credential requests) without operational detail.
- Legitimate messages also use public details, so that "contains public data" cannot be used as a shortcut for "fraud".
- No data is stored on a server. Responses stay in the browser session and can be downloaded as CSV.

## Limitations and next steps

This is a demonstration, not a validated instrument: eight items are too few for reliable individual d' estimates and the threshold of 50 is arbitrary. The next step is to rebuild the task in oTree with a preregistered design, a larger stimulus set and a proper participant panel.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Tools

Built in Python with Streamlit. Code was developed with AI assistance (Claude); research design, stimuli and analysis choices are my own.

María Martínez Melero
