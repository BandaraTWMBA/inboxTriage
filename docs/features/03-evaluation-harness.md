# Feature 03 — Evaluation Harness

**Status:** In progress
**Week:** 3
**Depends on:** `features/02-classification-agent.md`

## Goal

Stop eyeballing classification accuracy. Build a real, repeatable eval pipeline that measures classification quality and tracks it across prompt iterations. This is the single most interview-differentiating artifact in the whole project — treat it with more care than a "nice to have."

## Context / why this matters

Most self-taught AI projects skip proper evaluation. Having a golden dataset, real metrics, and a documented history of accuracy improving across iterations is what separates a demo from an engineered system.

## What to build

1. `golden_set.jsonl` — hand-labeled ground truth dataset
2. An eval script computing accuracy, per-category precision/recall, confusion matrix
3. An LLM-as-judge scorer for the non-exact-match fields (`action_items`, `reasoning`)
4. A running log of eval scores per prompt version
5. (Optional but recommended) a small script to plot accuracy over iterations

## Requirements — what to follow

- Build the golden set from the 30-50 manually-reviewed emails from Week 2 — correct any wrong labels by hand. Do not let the model generate its own ground truth.
- Aim for at least 10 examples per category (pad with additional real emails if any category is under-represented)
- Golden set format — one JSON object per line:
  ```json
  {"message_id": "...", "true_category": "urgent_action", "true_deadline": "2026-09-05", "notes": "optional human note"}
  ```
- Use `scikit-learn`'s `classification_report` for accuracy/precision/recall/confusion matrix — don't hand-roll metric calculations
- LLM-as-judge: a separate, distinct prompt/call scoring `action_items` completeness on a 1-5 scale given the email and the extracted items — log this score separately from hard-accuracy metrics, never averaged together into one number
- Every eval run must log: timestamp, `prompt_version`, accuracy, per-category breakdown, and free-text notes on what changed
- Log format: append-only CSV or JSONL — don't overwrite prior runs, you need the history

## What NOT to do

- Do not skip building a real golden set and rely on "it looks right" — that's the exact failure mode this feature exists to prevent
- Do not conflate LLM-judge scores with hard-accuracy metrics in the same aggregate number
- Do not discard old eval run logs when re-running — always append
- Do not let this eval harness call the same prompt version it's evaluating in a way that silently mutates production classification logic — the eval should run in isolation against the golden set, not against live inbox data

## Step-by-step tasks

1. Assemble and hand-verify `golden_set.jsonl` from Week 2's reviewed data
2. Write `eval.py`: loads golden set, runs current classification prompt against each entry, compares predicted vs. true category
3. Compute and print `classification_report` output
4. Write the LLM-as-judge scoring function for `action_items`/`reasoning` completeness
5. Write the run-logging function (append to CSV/JSONL with timestamp + prompt_version + scores)
6. Run the eval once as a baseline, record the score
7. Iterate on the Week 2 prompt at least 2-3 times based on observed failure patterns (e.g., "model over-classifies as urgent_action") — rerun eval after each change, log each iteration
8. Write a short summary of what changed and why accuracy moved (keep this — it becomes README/interview material later)

## Acceptance criteria / expected outcome

- `golden_set.jsonl` exists with at least 40+ hand-verified labeled examples across all 4 categories
- `eval.py` runs end-to-end and outputs a full classification report
- At least 2-3 logged eval runs across different prompt versions, with documented reasoning for each change
- Demonstrable accuracy improvement (or at minimum, a documented understanding of remaining failure modes if accuracy plateaus)

## Edge cases to handle

- Golden set entries where the "correct" answer is genuinely ambiguous — note these explicitly rather than forcing a single confident label
- Eval run where the model fails schema validation on a golden-set email — this should be caught and reported as a distinct failure type, not silently excluded from the accuracy calculation

## Testing

- Test that the eval script correctly computes known metrics against a small synthetic golden set with a known expected accuracy (sanity check the metric calculation itself, independent of the LLM)
- Test that the run-logger correctly appends without overwriting prior entries
