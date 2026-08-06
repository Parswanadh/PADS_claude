# Dialogue-Act Training Data

`train_classifier.py` currently trains on synthetic placeholder data
(`load_synthetic_data()`). Before any classifier accuracy is reportable,
replace it with a real corpus using `load_real_corpus()`, which expects a
JSONL file: `{"text": "<partial utterance>", "label": 0 or 1}` per line.

## Recommended sources (per PRD Sec 6, SKILL Sec 3)

- **Switchboard-DAMSL** — dialogue-act-tagged conversational telephone speech
  transcripts. Map tags to the project's binary scheme:
  - SHALLOW (0): greeting, backchannel (`b`), acknowledgement, statement-non-opinion
    where no downstream reasoning is needed, simple yes/no answers.
  - DEEP (1): action-directive, open-question requiring multi-step reasoning,
    requests for explanation/analysis/planning.
- **MultiWOZ** — task-oriented dialogue with intent annotations; map
  informational/simple-slot-filling intents to SHALLOW and complex
  multi-domain planning intents to DEEP.

## Do not collect new data from scratch

Per the pre-mortem (Detailed Report Sec 5.2) and mitigations (Sec 6), building
a bespoke labeled dataset was identified as a risk that could silently consume
a large fraction of the project timeline. Use the existing corpora above; only
consider bespoke data collection if both are demonstrated insufficient after
an honest attempt, and treat that decision as significant enough to log in
`experiments/go_no_go_results.md` even though it isn't one of the numbered tests.
