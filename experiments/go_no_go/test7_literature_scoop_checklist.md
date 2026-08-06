# Go/No-Go Test 7 — Fresh Literature Scoop Check

Run this as a recurring 10-minute task, not just once. Suggested cadence: **biweekly**, throughout both semesters — do not treat this as a one-time week-1 gate only.

## Search queries to run every time (same queries, so you can compare result sets over time)

1. "pause-aware early exit LLM"
2. "predictive prefetch layer skipping conversational"
3. "speculative decoding conversational pause"
4. "early exit self-speculative CPU edge inference"
5. "dialogue act driven speculative decoding"
6. "turn-taking layer skip LLM"

## What to do with results

- **No close match found** → log `Test 7: PASSED (as of <date>)` in `experiments/go_no_go_results.md`, continue as planned.
- **A partial overlap found** (addresses one half of the fusion, not both) → log the citation, add it to the related-work section, and re-verify the *combination* is still the gap — do not panic-pivot over a partial overlap.
- **The exact fusion found, published** → this is a real event requiring a team decision: reposition the paper's framing (e.g., emphasize the CPU-only characterization angle more heavily, or differentiate on the dialogue-act-driven trigger specifically), do not simply abandon the project. Document the decision and the reasoning in `experiments/go_no_go_results.md`.

## Log template (append an entry each time this is run)

```
### Scoop check — <date>
Queries run: [1-6 above, or note which subset]
Findings: <none / partial overlap: <citation> / exact match: <citation>>
Decision: <continue as-is / add citation & continue / reposition — see note>
```
