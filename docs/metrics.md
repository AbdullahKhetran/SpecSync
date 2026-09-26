# Metrics — TicketSeed

Captured by Person B on Sunday midday, using the three sample PRDs.  
These numbers go into the demo slides (section 18 of the PRD) and the video narration.

---

## How to capture

Run each sample PRD through both capabilities on the **deployed Vercel URL** (not localhost).  
Record the raw validation report returned by the backend alongside each result.

```
python scripts/run_metrics.py samples/prd-clean.md
python scripts/run_metrics.py samples/prd-vague.md
python scripts/run_metrics.py samples/prd-messy.md
```

If the script does not exist yet, capture numbers manually from the validation panel in the UI and fill in the table below.

---

## 1. Traceability

Percentage of `source_quote` fields whose text was found verbatim (or near-verbatim after normalisation) in the PRD, as reported by the backend validator.

**Target: ≥ 95%**

| Sample | Requirements with verified quote | Total requirements | % |
|---|---|---|---|
| prd-clean.md | | | |
| prd-vague.md | | | |
| prd-messy.md | | | |
| **Total** | | | |

**Tickets (Capability 2, run on one sprint per sample):**

| Sample | Sprint used | Tickets with all req. quotes verified | Total tickets | % |
|---|---|---|---|---|
| prd-clean.md | | | | |
| prd-vague.md | | | | |
| prd-messy.md | | | | |

---

## 2. Coverage

Percentage of requirements covered by at least one sprint (Capability 1), and percentage of sprint requirements covered by at least one ticket (Capability 2).

**Target: 100% for both**

**Sprint coverage (Capability 1):**

| Sample | Requirements assigned to a sprint | Total requirements | % |
|---|---|---|---|
| prd-clean.md | | | |
| prd-vague.md | | | |
| prd-messy.md | | | |

**Ticket coverage (Capability 2):**

| Sample | Sprint used | Sprint requirements covered by ≥1 ticket | Total sprint requirements | % |
|---|---|---|---|---|
| prd-clean.md | | | | |
| prd-vague.md | | | | |
| prd-messy.md | | | | |

---

## 3. Client questions generated

Number of client questions produced by Capability 1 per sample. The vague PRD should produce the most; the clean PRD the fewest.

| Sample | Questions generated | Notable examples |
|---|---|---|
| prd-clean.md | | |
| prd-vague.md | | |
| prd-messy.md | | |

---

## 4. End-to-end time

Time from uploading the PRD to having a full ticket list for one sprint, measured on the deployed URL.

**Manual baseline:** time for one team member to write tickets for one sprint by hand (measure this once, then extrapolate).

| Measurement | Time |
|---|---|
| PRD upload → sprint plan generated (prd-messy.md) | |
| Sprint plan shown → tickets generated (one sprint) | |
| **Total: PRD to ticket list** | |
| Manual baseline: one sprint ticketed by hand | |
| **Estimated time saved per sprint** | |
| **Extrapolated: full project (N sprints) saved** | |

Note: state this as an extrapolation in the demo — "based on N sprints, the app saves approximately X minutes of planning work."

---

## 5. Validator warnings observed

Qualitative notes on what the validator flagged during test runs, and whether prompt tuning fixed them.

| Issue | Sample | Fixed by prompt change? | Notes |
|---|---|---|---|
| Unverified source quote | | | |
| Uncovered requirement | | | |
| XL ticket not flagged | | | |
| Dependency cycle | | | |
| Other | | | |

---

## 6. Summary for demo slides

> Fill this in last, after all numbers above are captured.

- **Traceability:** X% of requirements and Y% of tickets have verified source quotes.
- **Coverage:** 100% of requirements assigned to sprints; 100% of sprint requirements covered by tickets (across N test runs).
- **Client questions:** an average of N questions generated per PRD; up to N on a vague document.
- **Speed:** PRD to full ticket list in under N minutes, vs N minutes by hand — approximately Nx faster.
