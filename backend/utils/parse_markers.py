import json
import re
from pathlib import Path

# Load marker config dynamically from same folder
MARKERS_CONFIG = json.loads(
    Path(__file__).parent.joinpath("markers.json").read_text()
)

def parse_markers(text: str):
    """
    Parses lab report text and identifies abnormal markers based on markers.json config.
    Handles aliases, case-insensitive matching, and decimal values.
    """

    extracted = {}
    flagged = {}

    for marker, props in MARKERS_CONFIG.items():
        # List of all names to search for (marker + aliases)
        names_to_check = [marker] + props.get("aliases", [])

        for name in names_to_check:
            # Regex: match marker name, then number (int or decimal)
            pattern = rf"{name}.*?(\d+\.?\d*)"
            match = re.search(pattern, text, re.IGNORECASE)

            if match:
                try:
                    value = float(match.group(1))
                    extracted[marker] = {
                        "value": value,
                        "unit": props["unit"],
                        "normal": props["normal"]
                    }

                    # Check abnormal ranges
                    normal = props["normal"]
                    if ("min" in normal and value < normal["min"]) or \
                       ("max" in normal and value > normal["max"]):
                        flagged[marker] = extracted[marker]

                except ValueError:
                    # If conversion to float fails, skip
                    pass

                break  # Stop checking aliases once a match is found

    return extracted, flagged
