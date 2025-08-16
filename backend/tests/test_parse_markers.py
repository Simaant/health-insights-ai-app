import pytest
from backend.utils.parse_markers import parse_markers

def test_parse_with_normal_and_abnormal():
    text = "LDL: 160 mg/dL\nHDL: 50 mg/dL\nGlucose: 85 mg/dL"
    extracted, flagged = parse_markers(text)

    # Check parsing worked
    assert "LDL" in extracted
    assert "HDL" in extracted
    assert "Glucose" in extracted

    # LDL is abnormal (> 100)
    assert "LDL" in flagged

    # HDL is normal (>= 40)
    assert "HDL" not in flagged

    # Glucose is normal (70–100)
    assert "Glucose" not in flagged


def test_parse_with_aliases():
    text = "High-Density Lipoprotein: 35 mg/dL\nBlood Sugar: 120 mg/dL"
    extracted, flagged = parse_markers(text)

    # HDL alias detected
    assert "HDL" in extracted
    assert "HDL" in flagged  # abnormal (< 40)

    # Glucose alias detected
    assert "Glucose" in extracted
    assert "Glucose" in flagged  # abnormal (> 100)


def test_parse_with_missing_marker():
    text = "Only Vitamin D: 25 ng/mL"
    extracted, flagged = parse_markers(text)

    assert "Vitamin D" in extracted
    assert "Vitamin D" in flagged  # abnormal (< 30)

    # LDL should not be in extracted
    assert "LDL" not in extracted


def test_parse_with_different_units():
    # Should still extract the number even if unit is different/missing
    text = "TSH: 6.2 someunit"
    extracted, flagged = parse_markers(text)

    assert "TSH" in extracted
    assert "TSH" in flagged  # abnormal (> 4.0)
