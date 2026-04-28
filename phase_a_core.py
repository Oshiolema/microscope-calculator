# ============================================================
#  PHASE A — Core Microscope Size Calculator
#  Accepts specimen size, microscope type, and output unit
#  then calculates and displays the real-life size.
# ============================================================

# Each microscope model is paired with its magnification factor.
# The user picks from this list — no free-text allowed.
SCOPE_CATALOGUE = {
    "Light Microscope (40x)":         40,
    "Light Microscope (100x)":        100,
    "Light Microscope (400x)":        400,
    "Light Microscope (1000x)":       1000,
    "Scanning Electron Microscope":   10000,
    "Transmission Electron Microscope": 100000,
    "Confocal Microscope":            600,
    "Fluorescence Microscope":        500,
}

# Conversion table: all values shift FROM micrometres (µm)
# because microscope measurements are typically in µm.
UNIT_SHIFT_TABLE = {
    "nm":  1000,        # 1 µm = 1000 nm
    "µm":  1,           # base unit
    "mm":  0.001,       # 1 µm = 0.001 mm
    "cm":  0.0001,      # 1 µm = 0.0001 cm
    "m":   0.000001,    # 1 µm = 0.000001 m
}


def prompt_microscope_choice():
    """Displays the microscope menu and returns the chosen name + factor."""
    scope_names = list(SCOPE_CATALOGUE.keys())
    print("\n--- Select Microscope Type ---")
    for slot_number, scope_label in enumerate(scope_names, start=1):
        factor = SCOPE_CATALOGUE[scope_label]
        print(f"  [{slot_number}] {scope_label}  (magnification: {factor}x)")

    while True:
        raw_pick = input("\nEnter the number of your microscope: ").strip()
        if raw_pick.isdigit():
            chosen_index = int(raw_pick) - 1
            if 0 <= chosen_index < len(scope_names):
                picked_name = scope_names[chosen_index]
                return picked_name, SCOPE_CATALOGUE[picked_name]
        print("  ⚠  Please enter a valid number from the list above.")


def prompt_output_unit():
    """Asks the user which unit they want the result displayed in."""
    available_units = list(UNIT_SHIFT_TABLE.keys())
    print("\n--- Select Output Unit ---")
    for slot_number, unit_tag in enumerate(available_units, start=1):
        print(f"  [{slot_number}] {unit_tag}")

    while True:
        raw_pick = input("\nEnter the number of your preferred unit: ").strip()
        if raw_pick.isdigit():
            chosen_index = int(raw_pick) - 1
            if 0 <= chosen_index < len(available_units):
                return available_units[chosen_index]
        print("  ⚠  Please enter a valid number from the list above.")


def compute_real_size(image_measurement_um, magnification_factor, target_unit):
    """
    Formula:
        real_size_in_um = image_measurement / magnification_factor
        real_size_in_target_unit = real_size_in_um * conversion_multiplier
    """
    real_size_um = image_measurement_um / magnification_factor
    conversion_multiplier = UNIT_SHIFT_TABLE[target_unit]
    final_answer = real_size_um * conversion_multiplier
    return real_size_um, final_answer


def display_calculation_breakdown(image_size, scope_name, magnification, unit, real_um, final_val):
    """Prints a clean step-by-step breakdown of the calculation."""
    print("\n" + "=" * 55)
    print("         CALCULATION BREAKDOWN")
    print("=" * 55)
    print(f"  Measured size on image   : {image_size} µm")
    print(f"  Microscope selected      : {scope_name}")
    print(f"  Magnification factor     : {magnification}x")
    print(f"  Formula used             : image size ÷ magnification")
    print(f"  Real size (in µm)        : {image_size} ÷ {magnification} = {real_um:.6f} µm")
    print(f"  Converted to {unit:<5}       : {final_val:.6f} {unit}")
    print("=" * 55)
    print(f"  ✅  REAL-LIFE SIZE = {final_val:.6f} {unit}")
    print("=" * 55 + "\n")


def run_phase_a():
    print("\n╔══════════════════════════════════════════╗")
    print("║   MICROSCOPE SIZE CALCULATOR — Phase A   ║")
    print("╚══════════════════════════════════════════╝")

    while True:
        # Step 1: get image measurement
        raw_size = input("\nEnter the specimen size as measured on the image (in µm): ").strip()
        try:
            image_measurement = float(raw_size)
            if image_measurement <= 0:
                raise ValueError
        except ValueError:
            print("  ⚠  Please enter a positive number.")
            continue

        # Step 2: pick microscope
        scope_name, magnification = prompt_microscope_choice()

        # Step 3: pick output unit
        output_unit = prompt_output_unit()

        # Step 4: calculate
        real_um, final_answer = compute_real_size(image_measurement, magnification, output_unit)

        # Step 5: show breakdown
        display_calculation_breakdown(
            image_measurement, scope_name, magnification,
            output_unit, real_um, final_answer
        )

        again = input("Perform another calculation? (yes/no): ").strip().lower()
        if again not in ("yes", "y"):
            print("\nExiting Phase A calculator. Goodbye!\n")
            break


if __name__ == "__main__":
    run_phase_a()