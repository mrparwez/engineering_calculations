# VV.md — Verification & Validation

## Validation — are these the right equations?

For a simply-supported beam of span `L` under a uniform load `w`, `source_workbook.xlsx`
computes (`Calculation` sheet, formula view):

| Quantity | Cell | Formula |
|---|---|---|
| Max moment, M | B2 | `=Inputs!B3*Inputs!B2^2/8` → `w*L^2/8` |
| Bending stress, σ | B3 | `=B2*1000/Inputs!B4` → `M/S` (with a kN·m→N·mm unit conversion) |
| Utilisation | B4 | `=B3/Inputs!B7` → `σ/fy` |
| Stress check | B5 | `IF(util<=1, PASS, FAIL)` |
| Midspan deflection, δ | B6 | `=5*Inputs!B3*Inputs!B2^4/(384*Inputs!B6*Inputs!B5)*E2` → `5wL^4/(384EI)`, times the constant discussed below |
| Deflection limit | B7 | `=Inputs!B2*1000/Inputs!B8` → `L/n` |
| Deflection check | B8 | `IF(δ<=limit, PASS, FAIL)` |

These are the standard closed-form results for a **simply-supported beam under a full-span
uniform load**, elastic, small-deflection (Euler–Bernoulli) beam theory:

- `M_max = wL²/8` and `δ_max = 5wL⁴/(384EI)` — standard simply-supported/UDL beam formulas.
  Checked against Gere & Goodno, *Mechanics of Materials* (beam-deflection tables) and the
  AISC *Steel Construction Manual*, Table 3-23 ("Shears, Moments and Deflections").
- `σ = M/S` — the elastic flexure formula `σ = Mc/I` rewritten with section modulus `S = I/c`.
  Standard strength-of-materials result.
- `L/360` as the deflection *value* the workbook happens to use is a common serviceability
  limit (e.g. IBC Table 1604.3, "floor members — live load"); the workbook treats `n` as a
  free input (cell `Inputs!B8`), which is the right approach since the correct limit depends
  on what the beam supports (floor vs. roof vs. cantilever, live-load-only vs. total-load).

**Assumptions under which these formulas apply** (not stated in the workbook, worth flagging
to a client):
- Load is uniformly distributed over the *full* span; no point loads, partial UDLs, or moving loads.
- Both supports are simple (pin/roller) — no moment continuity, cantilevers, or fixity.
- Material is linear-elastic up to `fy`; deflection formula assumes small deflections and
  doesn't account for shear deformation (fine for typical span/depth ratios, not for very
  deep/short beams).
- `σ = M/S` is an *elastic* check against yield strength, not a plastic/LRFD capacity check —
  it says nothing about lateral-torsional buckling, web crippling, shear capacity, or combined
  loading, all of which a full beam design would also need.
- The self-weight extension added in `beam_check.py` assumes self-weight acts as a UDL over
  the same span (reasonable) and is supplied directly as a load intensity, since the workbook
  gives no cross-section area or material density to derive it from.

## Verification — does the code solve them correctly?

Workbook inputs (`Inputs` sheet): L=6 m, w=10 kN/m, S=597 cm³, I=8503 cm⁴, E=200 GPa,
fy=275 MPa, n=360.

| Output | Workbook value | `beam_check.py` value | Tolerance | Match |
|---|---|---|---|---|
| M | 45 kN·m | 45.0 kN·m | abs 1e-9 | ✅ exact |
| σ | 75.37688442 MPa | 75.37688442211056 MPa | abs 1e-6 | ✅ |
| Utilisation | 0.274097762 | 0.2740977615349475 | abs 1e-8 | ✅ |
| Stress check | PASS | PASS | — | ✅ |
| δ | 9.922968364 mm | 9.922968364106785 mm | abs 1e-6 | ✅ |
| δ limit | 16.66666667 mm | 16.666666666666668 mm | abs 1e-6 | ✅ |
| Deflection check | PASS | PASS | — | ✅ |

Tolerances are set at the precision the workbook itself reports (~9–10 significant figures),
tightened slightly below that so the test is meaningful but not brittle to the workbook's own
display rounding. No discrepancy was found once the deflection formula's unit handling was
implemented correctly (see below) — every output matches to full float precision.

### The undocumented constant

Cell `Calculation!E2 = 100000` is unlabeled and sits off to the side of the M row, but is
referenced **only** inside the deflection formula `B6`:

```
=5*Inputs!B3*Inputs!B2^4/(384*Inputs!B6*Inputs!B5)*E2
```

The deflection formula plugs `w` (kN/m), `L` (m), `E` (GPa) and `I` (cm⁴) directly into
`5wL⁴/(384EI)` **without converting any of them to consistent base units first**. Doing that
arithmetic on the raw numbers gives a result that is dimensionally wrong by exactly 10⁵:

```
raw = 5*10*6^4 / (384*200*8503) = 9.92296...e-5
correct δ (m→mm)                = 9.92296...
ratio                            = 100000  (exact)
```

`E2` is that patch factor. It decomposes cleanly and exactly into the unit mismatches it's
correcting for:

```
(kN→N: ×1000) × (m→mm output: ×1000) / (GPa→Pa: ×10⁹) / (cm⁴→m⁴: ×10⁻⁸)
= (1000 × 1000) / (10⁹ × 10⁻⁸)
= 1,000,000 / 10
= 100,000
```

It produces the *right* numeric answer for this specific combination of input units, but it's
fragile: change any one input's unit elsewhere in the sheet (e.g. `I` entered in mm⁴ instead
of cm⁴) and the answer would silently become wrong, with no error and no flag. `beam_check.py`
avoids this entirely by converting every input to consistent SI base units (m, N, Pa) *before*
computing, so no such patch constant is needed anywhere in the Python port — see the module
docstring and the named conversion constants at the top of `beam_check.py`.

## Assumptions & questions I'd send a real client

- Assumed "self-weight" should be supplied as a direct UDL (kN/m or kip/ft) rather than
  derived from a density × cross-sectional area, since the workbook provides neither. I'd ask:
  should the function instead accept unit weight (kg/m or density + area) so a UI could
  compute it from a section catalog?
- Assumed the deflection limit `L/n` should stay a free input (matching the workbook), not a
  hardcoded L/360 — I'd confirm this is intentional given serviceability limits vary by
  application.
- Assumed "invalid... load" in the brief means the *applied* UDL must be `>0`, while
  self-weight (a separate, optional addition to the workbook's calc) may be `0` but not
  negative. I'd confirm that split is what's wanted.
- I did not add checks beyond bending stress and deflection (e.g. shear, lateral-torsional
  buckling) since the brief scopes the task to the two checks in the workbook — I'd flag to a
  client that a full design check would need more than this.

## AI tool disclosure

I used Claude (Anthropic) throughout: to read the workbook's formulas via a Python script
(openpyxl) rather than by inspection, to help identify/confirm the standard beam-formula
references, to draft `beam_check.py`, `test_beam_check.py`, and this note, and to reason
through the unit-conversion boundary for the imperial-input requirement.

The most significant thing I checked rather than trusted: the decomposition of the `100000`
constant. It would have been easy to accept "it's a unit fudge factor" without pinning down
exactly *which* units it reconciles or confirming the factorization is exact. I verified it
numerically (raw unconverted formula vs. correct SI computation, ratio computed to full float
precision — see `100000.0` printed above, not "approximately 100000") and then independently
re-derived the same number from the four individual unit-conversion factors (kN→N, m→mm,
GPa→Pa, cm⁴→m⁴) to confirm the ratio wasn't a coincidental rounding artifact. I also
independently verified every other formula (M, σ, utilisation, δ limit) against the workbook's
computed cell values before writing any Python, rather than assuming the "standard textbook
formula" was what the sheet actually implemented.
