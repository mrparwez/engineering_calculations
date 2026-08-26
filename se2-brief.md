# Take-home task — Software Engineer II

Thanks for your time so far. This task mirrors the day job you'd be leading: converting an Excel engineering calculation into verified Python, to a standard two junior engineers will learn from. Budget **2–4 hours**. If you hit 4 hours, stop and note what's unfinished — a clean partial with honest notes beats a rushed complete.

## The calculation

`source_workbook.xlsx` checks a simply-supported steel beam under a uniform load: a bending-stress check and a midspan-deflection check. No structural background needed, but working out **what the spreadsheet computes is part of the task**. The formulas are in the cells and every quantity is labelled with its units; these are standard textbook checks. Read the formulas out of the workbook, find the engineering references they correspond to, and cite what you used — a textbook, a design code, a URL, anything we can check.

Read the spreadsheet carefully: **it contains at least one undocumented hard-coded constant. Identify it, work out what it is, and document it.**

## Requirements

1. **`beam_check.py`** — a Python module with a function that takes the workbook's inputs and returns the workbook's outputs (M, σ, utilisation, δ, limit, and the two PASS/FAIL results).
   - **Imperial input option**: accept inputs in ft / kip/ft / in³ / in⁴ / ksi, convert at the input boundary, compute in SI, report both. Look up the conversion factors yourself; state the values you used and where they came from.
   - The check should also account for the beam's self-weight.
   - Invalid inputs (zero or negative span, load, section properties) raise `ValueError`.
   - **Structure the code however you judge best** — write it the way you write real production code. One constraint to design for: downstream, a deterministic parser reads this code to build a UI, so it must be able to infer the inputs, the calculation steps and the outputs from your code. Explicit symbols and units in names and docstrings help it — and us. Your code is also the reference example two SE I engineers will be onboarded with.
2. **`test_beam_check.py`** — pytest, explicit tolerances (`pytest.approx`). We're interested in which test points you choose.
3. **`VV.md`** — max one page, treating verification and validation distinctly, in the NAFEMS senses of the words.
   - **Validation — are these the right equations?** The governing formulas you identified from the workbook, the references you checked them against, and the assumptions under which they apply.
   - **Verification — does your code solve them correctly?** A table mapping each output to the workbook's value for the workbook's pre-filled inputs, tolerances and why, and any discrepancy found and what you did about it. An honest unresolved discrepancy scores better than a massaged match.

If anything in this brief is ambiguous or underspecified, handle it the way you would with a real client: state your assumptions in writing, and list the questions you would send before starting.

## AI policy

Use any AI tools you like — we do, daily. We're not grading whether you used AI; we're grading whether **you** verified what it gave you. In `VV.md` (or a separate note), tell us:

- which tools you used, and for what — identifying the formulas, writing the code, the tests, this note;
- the most significant thing you had to check, correct or reject from an AI's output, and how you checked it. (If you used no AI, say so — that's fine too.)

If your tool makes it easy to export your prompts or session, feel free to include it — we'd find it interesting, but it's optional and not scored.

## Submission

Reply to the email this brief arrived with, attaching a zip of the files or a link to a GitHub repo, by the deadline given in that email. Questions about the brief are welcome the same way — just reply.
