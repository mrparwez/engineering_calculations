from dataclasses import dataclass
M_PER_FT = 0.3048
KN_PER_KIP = 4.4482216152605
MM_PER_IN = 25.4
MPA_PER_KSI = 6.894757293168
CM3_PER_IN3 = (MM_PER_IN ** 3) / 1000.0     # mm^3 -> cm^3
CM4_PER_IN4 = (MM_PER_IN ** 4) / 10_000.0   # mm^4 -> cm^4


@dataclass(frozen=True)
class BeamCheckResult:
    self_weight_kN_per_m: float
    total_udl_kN_per_m: float
    M_kNm: float
    sigma_MPa: float
    utilisation: float
    stress_check: str
    delta_mm: float
    delta_limit_mm: float
    deflection_check: str


@dataclass(frozen=True)
class BeamCheckResultImperial:
    si: BeamCheckResult
    M_kip_ft: float
    sigma_ksi: float
    delta_in: float
    delta_limit_in: float
    stress_check: str
    deflection_check: str


def check_simply_supported_beam(
    span_m: float,
    udl_kN_per_m: float,
    section_modulus_cm3: float,
    second_moment_area_cm4: float,
    youngs_modulus_GPa: float,
    yield_strength_MPa: float,
    deflection_limit_ratio: float,
    self_weight_kN_per_m: float = 0.0,
) -> BeamCheckResult:
    if span_m <= 0:
        raise ValueError(f"span_m must be > 0, got {span_m!r}")
    if udl_kN_per_m <= 0:
        raise ValueError(f"udl_kN_per_m must be > 0, got {udl_kN_per_m!r}")
    if section_modulus_cm3 <= 0:
        raise ValueError(
            f"section_modulus_cm3 must be > 0, got {section_modulus_cm3!r}"
        )
    if second_moment_area_cm4 <= 0:
        raise ValueError(
            f"second_moment_area_cm4 must be > 0, got {second_moment_area_cm4!r}"
        )
    if youngs_modulus_GPa <= 0:
        raise ValueError(
            f"youngs_modulus_GPa must be > 0, got {youngs_modulus_GPa!r}"
        )
    if yield_strength_MPa <= 0:
        raise ValueError(
            f"yield_strength_MPa must be > 0, got {yield_strength_MPa!r}"
        )
    if deflection_limit_ratio <= 0:
        raise ValueError(
            f"deflection_limit_ratio must be > 0, got {deflection_limit_ratio!r}"
        )
    if self_weight_kN_per_m < 0:
        raise ValueError(
            f"self_weight_kN_per_m must be >= 0, got {self_weight_kN_per_m!r}"
        )

    total_udl_kN_per_m = udl_kN_per_m + self_weight_kN_per_m

    # --- convert every input to consistent SI base units (N, m, Pa) ---
    w_N_per_m = total_udl_kN_per_m * 1000.0            # kN/m -> N/m
    S_m3 = section_modulus_cm3 * 1e-6                  # cm^3 -> m^3
    I_m4 = second_moment_area_cm4 * 1e-8                # cm^4 -> m^4
    E_Pa = youngs_modulus_GPa * 1e9                     # GPa -> Pa

    # --- bending moment and stress ---
    M_Nm = w_N_per_m * span_m ** 2 / 8.0
    sigma_Pa = M_Nm / S_m3
    sigma_MPa = sigma_Pa / 1e6
    utilisation = sigma_MPa / yield_strength_MPa
    stress_check = "PASS" if utilisation <= 1.0 else "FAIL"

    # --- deflection ---
    delta_m = 5.0 * w_N_per_m * span_m ** 4 / (384.0 * E_Pa * I_m4)
    delta_mm = delta_m * 1000.0
    delta_limit_mm = (span_m * 1000.0) / deflection_limit_ratio
    deflection_check = "PASS" if delta_mm <= delta_limit_mm else "FAIL"

    return BeamCheckResult(
        self_weight_kN_per_m=self_weight_kN_per_m,
        total_udl_kN_per_m=total_udl_kN_per_m,
        M_kNm=M_Nm / 1000.0,
        sigma_MPa=sigma_MPa,
        utilisation=utilisation,
        stress_check=stress_check,
        delta_mm=delta_mm,
        delta_limit_mm=delta_limit_mm,
        deflection_check=deflection_check,
    )


def check_simply_supported_beam_imperial(
    span_ft: float,
    udl_kip_per_ft: float,
    section_modulus_in3: float,
    second_moment_area_in4: float,
    youngs_modulus_ksi: float,
    yield_strength_ksi: float,
    deflection_limit_ratio: float,
    self_weight_kip_per_ft: float = 0.0,
) -> BeamCheckResultImperial:
    span_m = span_ft * M_PER_FT
    udl_kN_per_m = udl_kip_per_ft * KN_PER_KIP / M_PER_FT
    self_weight_kN_per_m = self_weight_kip_per_ft * KN_PER_KIP / M_PER_FT
    section_modulus_cm3 = section_modulus_in3 * CM3_PER_IN3
    second_moment_area_cm4 = second_moment_area_in4 * CM4_PER_IN4
    youngs_modulus_GPa = youngs_modulus_ksi * MPA_PER_KSI / 1000.0
    yield_strength_MPa = yield_strength_ksi * MPA_PER_KSI

    si_result = check_simply_supported_beam(
        span_m=span_m,
        udl_kN_per_m=udl_kN_per_m,
        section_modulus_cm3=section_modulus_cm3,
        second_moment_area_cm4=second_moment_area_cm4,
        youngs_modulus_GPa=youngs_modulus_GPa,
        yield_strength_MPa=yield_strength_MPa,
        deflection_limit_ratio=deflection_limit_ratio,
        self_weight_kN_per_m=self_weight_kN_per_m,
    )

    # --- convert results back to imperial for reporting ---
    # M_kNm [kN*m] -> kip*ft : divide by (kN per kip), divide by (m per ft)
    M_kip_ft = (si_result.M_kNm / KN_PER_KIP) / M_PER_FT
    sigma_ksi = si_result.sigma_MPa / MPA_PER_KSI
    delta_in = si_result.delta_mm / MM_PER_IN
    delta_limit_in = si_result.delta_limit_mm / MM_PER_IN

    return BeamCheckResultImperial(
        si=si_result,
        M_kip_ft=M_kip_ft,
        sigma_ksi=sigma_ksi,
        delta_in=delta_in,
        delta_limit_in=delta_limit_in,
        stress_check=si_result.stress_check,
        deflection_check=si_result.deflection_check,
    )
