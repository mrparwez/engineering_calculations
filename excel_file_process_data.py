import sys
import openpyxl
from beam_check import check_simply_supported_beam


def read_inputs_from_workbook(path: str) -> dict:
    wb = openpyxl.load_workbook(path, data_only=True) 
    inputs_sheet = wb["Inputs"]

    return dict(
        span_m=inputs_sheet["B2"].value,
        udl_kN_per_m=inputs_sheet["B3"].value,
        section_modulus_cm3=inputs_sheet["B4"].value,
        second_moment_area_cm4=inputs_sheet["B5"].value,
        youngs_modulus_GPa=inputs_sheet["B6"].value,
        yield_strength_MPa=inputs_sheet["B7"].value,
        deflection_limit_ratio=inputs_sheet["B8"].value,
    )


def main():
    if len(sys.argv) != 2:
        print("Usage: python excel_file_process_data.py <path_to_workbook.xlsx>")
        sys.exit(1)

    workbook_path = sys.argv[1]
    inputs = read_inputs_from_workbook(workbook_path)
    for key, value in inputs.items():
        print(f"  {key} = {value}")
    print()

    result = check_simply_supported_beam(**inputs)

    print("Result:")
    print(f"  M               = {result.M_kNm:.4f} kN·m")
    print(f"  sigma           = {result.sigma_MPa:.4f} MPa")
    print(f"  utilisation     = {result.utilisation:.4f}")
    print(f"  stress_check    = {result.stress_check}")
    print(f"  delta           = {result.delta_mm:.4f} mm")
    print(f"  delta_limit     = {result.delta_limit_mm:.4f} mm")
    print(f"  deflection_check= {result.deflection_check}")


if __name__ == "__main__":
    main()