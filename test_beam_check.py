import pytest

from beam_check import (
    check_simply_supported_beam,
    check_simply_supported_beam_imperial,
    M_PER_FT,
    KN_PER_KIP,
    MM_PER_IN,
    MPA_PER_KSI,
)


# Workbook reference inputs (source_workbook.xlsx, sheet "Inputs")
REF_INPUTS = dict(
    span_m=6.0,
    udl_kN_per_m=10.0,
    section_modulus_cm3=597.0,
    second_moment_area_cm4=8503.0,
    youngs_modulus_GPa=200.0,
    yield_strength_MPa=275.0,
    deflection_limit_ratio=360.0,
)

# Workbook's own computed outputs (source_workbook.xlsx, sheet "Calculation")
REF_M_kNm = 45.0
REF_SIGMA_MPa = 75.37688442
REF_UTIL = 0.274097762
REF_DELTA_mm = 9.922968364
REF_DELTA_LIMIT_mm = 16.66666667


def test_workbook_reference_case():
    """Reproduce the workbook's worked example to within float tolerance."""
    r = check_simply_supported_beam(**REF_INPUTS)

    assert r.M_kNm == pytest.approx(REF_M_kNm, abs=1e-9)
    assert r.sigma_MPa == pytest.approx(REF_SIGMA_MPa, abs=1e-6)
    assert r.utilisation == pytest.approx(REF_UTIL, abs=1e-8)
    assert r.delta_mm == pytest.approx(REF_DELTA_mm, abs=1e-6)
    assert r.delta_limit_mm == pytest.approx(REF_DELTA_LIMIT_mm, abs=1e-6)
    assert r.stress_check == "PASS"
    assert r.deflection_check == "PASS"


def test_imperial_round_trip_matches_si():
    si_ref = check_simply_supported_beam(**REF_INPUTS)

    r = check_simply_supported_beam_imperial(
        span_ft=REF_INPUTS["span_m"] / M_PER_FT,
        udl_kip_per_ft=REF_INPUTS["udl_kN_per_m"] * M_PER_FT / KN_PER_KIP,
        section_modulus_in3=REF_INPUTS["section_modulus_cm3"]
        / ((MM_PER_IN ** 3) / 1000.0),
        second_moment_area_in4=REF_INPUTS["second_moment_area_cm4"]
        / ((MM_PER_IN ** 4) / 10_000.0),
        youngs_modulus_ksi=REF_INPUTS["youngs_modulus_GPa"] * 1000.0 / MPA_PER_KSI,
        yield_strength_ksi=REF_INPUTS["yield_strength_MPa"] / MPA_PER_KSI,
        deflection_limit_ratio=REF_INPUTS["deflection_limit_ratio"],
    )

    assert r.si.M_kNm == pytest.approx(si_ref.M_kNm, rel=1e-9)
    assert r.si.sigma_MPa == pytest.approx(si_ref.sigma_MPa, rel=1e-9)
    assert r.si.delta_mm == pytest.approx(si_ref.delta_mm, rel=1e-9)
    assert r.si.delta_limit_mm == pytest.approx(si_ref.delta_limit_mm, rel=1e-9)
    assert r.stress_check == si_ref.stress_check
    assert r.deflection_check == si_ref.deflection_check

    # and the imperial-unit outputs should convert back to the SI ones
    assert r.M_kip_ft * KN_PER_KIP * M_PER_FT == pytest.approx(
        si_ref.M_kNm, rel=1e-9
    )
    assert r.sigma_ksi * MPA_PER_KSI == pytest.approx(si_ref.sigma_MPa, rel=1e-9)
    assert r.delta_in * MM_PER_IN == pytest.approx(si_ref.delta_mm, rel=1e-9)


def test_self_weight_increases_moment_and_deflection():
    """Self-weight adds to the applied UDL and increases M and delta accordingly."""
    r0 = check_simply_supported_beam(**REF_INPUTS, self_weight_kN_per_m=0.0)
    r1 = check_simply_supported_beam(**REF_INPUTS, self_weight_kN_per_m=2.0)

    assert r1.total_udl_kN_per_m == pytest.approx(12.0)
    # M and delta both scale linearly with total UDL for a fixed span/section
    assert r1.M_kNm == pytest.approx(r0.M_kNm * 12.0 / 10.0, rel=1e-9)
    assert r1.delta_mm == pytest.approx(r0.delta_mm * 12.0 / 10.0, rel=1e-9)


def test_stress_check_fails_when_utilisation_exceeds_one():
    """A yield strength below the computed stress must FAIL the stress check."""
    inputs = dict(REF_INPUTS)
    inputs["yield_strength_MPa"] = 50.0  # well below sigma ~= 75.4 MPa
    r = check_simply_supported_beam(**inputs)

    assert r.utilisation > 1.0
    assert r.stress_check == "FAIL"


def test_deflection_check_fails_when_deflection_exceeds_limit():
    """A very tight (large n) deflection ratio must FAIL the deflection check."""
    inputs = dict(REF_INPUTS)
    inputs["deflection_limit_ratio"] = 5000.0  # limit << computed delta ~= 9.9 mm
    r = check_simply_supported_beam(**inputs)

    assert r.delta_mm > r.delta_limit_mm
    assert r.deflection_check == "FAIL"


def test_utilisation_and_deflection_check_boundary_is_pass():
    """utilisation == 1.0 and delta == delta_limit must both PASS (<=, not <)."""
    r = check_simply_supported_beam(**REF_INPUTS)

    # set fy exactly to the computed sigma -> utilisation exactly 1.0
    inputs = dict(REF_INPUTS)
    inputs["yield_strength_MPa"] = r.sigma_MPa
    r_stress_boundary = check_simply_supported_beam(**inputs)
    assert r_stress_boundary.utilisation == pytest.approx(1.0, rel=1e-9)
    assert r_stress_boundary.stress_check == "PASS"

    # set n so that L/n exactly equals the computed delta -> deflection boundary
    inputs = dict(REF_INPUTS)
    inputs["deflection_limit_ratio"] = (REF_INPUTS["span_m"] * 1000.0) / r.delta_mm
    r_defl_boundary = check_simply_supported_beam(**inputs)
    assert r_defl_boundary.delta_mm == pytest.approx(
        r_defl_boundary.delta_limit_mm, rel=1e-9
    )
    assert r_defl_boundary.deflection_check == "PASS"


@pytest.mark.parametrize(
    "field,invalid_value",
    [
        ("span_m", 0.0),
        ("span_m", -1.0),
        ("udl_kN_per_m", 0.0),
        ("udl_kN_per_m", -10.0),
        ("section_modulus_cm3", 0.0),
        ("section_modulus_cm3", -597.0),
        ("second_moment_area_cm4", 0.0),
        ("second_moment_area_cm4", -8503.0),
        ("youngs_modulus_GPa", 0.0),
        ("youngs_modulus_GPa", -200.0),
        ("yield_strength_MPa", 0.0),
        ("yield_strength_MPa", -275.0),
        ("deflection_limit_ratio", 0.0),
        ("deflection_limit_ratio", -360.0),
    ],
)
def test_invalid_inputs_raise_value_error(field, invalid_value):
    """Zero/negative span, load, section properties, E, fy, or n must raise."""
    inputs = dict(REF_INPUTS)
    inputs[field] = invalid_value
    with pytest.raises(ValueError):
        check_simply_supported_beam(**inputs)


def test_negative_self_weight_raises_value_error():
    """Self-weight is optional (default 0) but must not be negative."""
    with pytest.raises(ValueError):
        check_simply_supported_beam(**REF_INPUTS, self_weight_kN_per_m=-1.0)
