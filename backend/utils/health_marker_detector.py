import re
import json
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass

@dataclass
class HealthMarker:
    name: str
    value: float
    unit: str
    normal_range: Dict[str, float]
    status: str  # "normal", "low", "high", "critical"
    raw_text: str
    recommendation: str = ""

class HealthMarkerDetector:
    def __init__(self):
        # Common health markers with their patterns and normal ranges
        self.marker_patterns = {
            # Blood Chemistry
            "Glucose": {
                "patterns": [r"glucose[:\s]*(\d+\.?\d*)\s*(mg/dL|mmol/L)", r"blood sugar[:\s]*(\d+\.?\d*)\s*(mg/dL|mmol/L)"],
                "normal": {"min": 70, "max": 100, "unit": "mg/dL"},
                "aliases": ["Blood Sugar", "Fasting Glucose"]
            },
            "Hemoglobin A1C": {
                "patterns": [
                    r"hba1c[:\s]*(\d+\.?\d*)\s*(%|percent)", 
                    r"hemoglobin a1c[:\s]*(\d+\.?\d*)\s*(%|percent)",
                    r"hba1c[:\s]*[-=]\s*(\d+\.?\d*)",
                    r"glycated haemoglobin[:\s]*[-=]\s*(\d+\.?\d*)",
                    r"glycated hemoglobin[:\s]*[-=]\s*(\d+\.?\d*)",
                    r"hba1c[:\s]*(\d+\.?\d*)",
                    r"a1c[:\s]*(\d+\.?\d*)",
                    r"glycated[:\s]*(\d+\.?\d*)",
                    r"hemoglobin[:\s]*a1c[:\s]*(\d+\.?\d*)"
                ],
                "normal": {"min": 4.0, "max": 5.6, "unit": "%"},
                "aliases": ["HbA1C", "A1C", "Glycated Haemoglobin", "Glycated Hemoglobin", "HBA1C", "hba1c", "a1c", "A1C"]
            },
            "Creatinine": {
                "patterns": [r"creatinine[:\s]*(\d+\.?\d*)\s*(mg/dL|µmol/L)"],
                "normal": {"min": 0.6, "max": 1.2, "unit": "mg/dL"},
                "aliases": ["Serum Creatinine"]
            },
            "BUN": {
                "patterns": [r"bun[:\s]*(\d+\.?\d*)\s*(mg/dL)", r"blood urea nitrogen[:\s]*(\d+\.?\d*)\s*(mg/dL)"],
                "normal": {"min": 7, "max": 20, "unit": "mg/dL"},
                "aliases": ["Blood Urea Nitrogen"]
            },
            
            # Lipid Panel
            "Total Cholesterol": {
                "patterns": [r"total cholesterol[:\s]*(\d+\.?\d*)\s*(mg/dL)", r"cholesterol[:\s]*(\d+\.?\d*)\s*(mg/dL)"],
                "normal": {"max": 200, "unit": "mg/dL"},
                "aliases": ["Cholesterol"]
            },
            "LDL": {
                "patterns": [r"ldl[:\s]*(\d+\.?\d*)\s*(mg/dL)", r"low-density lipoprotein[:\s]*(\d+\.?\d*)\s*(mg/dL)"],
                "normal": {"max": 100, "unit": "mg/dL"},
                "aliases": ["Low-Density Lipoprotein", "LDL Cholesterol"]
            },
            "HDL": {
                "patterns": [r"hdl[:\s]*(\d+\.?\d*)\s*(mg/dL)", r"high-density lipoprotein[:\s]*(\d+\.?\d*)\s*(mg/dL)"],
                "normal": {"min": 40, "unit": "mg/dL"},
                "aliases": ["High-Density Lipoprotein", "HDL Cholesterol"]
            },
            "Triglycerides": {
                "patterns": [r"triglycerides[:\s]*(\d+\.?\d*)\s*(mg/dL)", r"triacylglycerols[:\s]*(\d+\.?\d*)\s*(mg/dL)"],
                "normal": {"max": 150, "unit": "mg/dL"},
                "aliases": ["Triacylglycerols"]
            },
            
            # Complete Blood Count
            "Hemoglobin": {
                "patterns": [r"hemoglobin[:\s]*(\d+\.?\d*)\s*(g/dL|g/L)"],
                "normal": {"min": 12, "max": 16, "unit": "g/dL"},
                "aliases": ["Hgb", "Hb"]
            },
            "Hematocrit": {
                "patterns": [r"hematocrit[:\s]*(\d+\.?\d*)\s*(%|percent)"],
                "normal": {"min": 36, "max": 46, "unit": "%"},
                "aliases": ["Hct"]
            },
            "White Blood Cells": {
                "patterns": [r"white blood cells[:\s]*(\d+\.?\d*)\s*(K/µL|×10³/µL)", r"wbc[:\s]*(\d+\.?\d*)\s*(K/µL|×10³/µL)"],
                "normal": {"min": 4.5, "max": 11.0, "unit": "K/µL"},
                "aliases": ["WBC", "Leukocytes"]
            },
            "Platelets": {
                "patterns": [r"platelets[:\s]*(\d+\.?\d*)\s*(K/µL|×10³/µL)"],
                "normal": {"min": 150, "max": 450, "unit": "K/µL"},
                "aliases": ["Plt"]
            },
            
            # Thyroid Function
            "TSH": {
                "patterns": [r"tsh[:\s]*(\d+\.?\d*)\s*(µIU/mL|mIU/L)"],
                "normal": {"min": 0.4, "max": 4.0, "unit": "µIU/mL"},
                "aliases": ["Thyroid-Stimulating Hormone"]
            },
            "T4": {
                "patterns": [r"t4[:\s]*(\d+\.?\d*)\s*(µg/dL|nmol/L)"],
                "normal": {"min": 0.8, "max": 1.8, "unit": "µg/dL"},
                "aliases": ["Thyroxine", "Free T4"]
            },
            "T3": {
                "patterns": [r"t3[:\s]*(\d+\.?\d*)\s*(ng/dL|nmol/L)"],
                "normal": {"min": 80, "max": 200, "unit": "ng/dL"},
                "aliases": ["Triiodothyronine", "Free T3"]
            },
            
            # Liver Function
            "ALT": {
                "patterns": [r"alt[:\s]*(\d+\.?\d*)\s*(U/L|IU/L)", r"alanine aminotransferase[:\s]*(\d+\.?\d*)\s*(U/L|IU/L)"],
                "normal": {"max": 41, "unit": "U/L"},
                "aliases": ["Alanine Aminotransferase", "SGPT"]
            },
            "AST": {
                "patterns": [r"ast[:\s]*(\d+\.?\d*)\s*(U/L|IU/L)", r"aspartate aminotransferase[:\s]*(\d+\.?\d*)\s*(U/L|IU/L)"],
                "normal": {"max": 40, "unit": "U/L"},
                "aliases": ["Aspartate Aminotransferase", "SGOT"]
            },
            "Alkaline Phosphatase": {
                "patterns": [r"alkaline phosphatase[:\s]*(\d+\.?\d*)\s*(U/L|IU/L)", r"alp[:\s]*(\d+\.?\d*)\s*(U/L|IU/L)"],
                "normal": {"min": 44, "max": 147, "unit": "U/L"},
                "aliases": ["ALP"]
            },
            "Bilirubin": {
                "patterns": [r"bilirubin[:\s]*(\d+\.?\d*)\s*(mg/dL|µmol/L)"],
                "normal": {"max": 1.2, "unit": "mg/dL"},
                "aliases": ["Total Bilirubin"]
            },
            
            # Kidney Function
            "eGFR": {
                "patterns": [r"egfr[:\s]*(\d+\.?\d*)\s*(mL/min/1.73m²)", r"estimated glomerular filtration rate[:\s]*(\d+\.?\d*)\s*(mL/min/1.73m²)"],
                "normal": {"min": 90, "unit": "mL/min/1.73m²"},
                "aliases": ["Estimated GFR"]
            },
            
            # Vitamins and Minerals
            "Vitamin D": {
                "patterns": [r"vitamin d[:\s]*(\d+\.?\d*)\s*(ng/mL|nmol/L)", r"25-hydroxy vitamin d[:\s]*(\d+\.?\d*)\s*(ng/mL|nmol/L)"],
                "normal": {"min": 30, "max": 100, "unit": "ng/mL"},
                "aliases": ["25-Hydroxy Vitamin D", "Vit D"]
            },
            "FERRITIN": {
                "patterns": [
                    r"ferritin[:\s]*(\d+\.?\d*)\s*(ng/mL|µg/L|ng/ml|ng/ML|ng/ML)",
                    r"ferritin[:\s]*(\d+\.?\d*)\s*(ng/mL|µg/L|ng/ml|ng/ML|ng/ML).*?(low|high|normal)",
                    r"ferritin[:\s]*(\d+\.?\d*)\s*(ng/mL|µg/L|ng/ml|ng/ML|ng/ML).*?\(low\)",
                    r"ferritin[:\s]*(\d+\.?\d*)\s*(ng/mL|µg/L|ng/ml|ng/ML|ng/ML).*?\(high\)",
                    r"ferritin[:\s]*(\d+\.?\d*)\s*(ng/mL|µg/L|ng/ml|ng/ML|ng/ML).*?\(normal\)",
                    # Handle OCR errors where 'g' might be read as '9' or other characters
                    r"ferritin[:\s]*(\d+\.?\d*)\s*(n9/mL|n9/ml|n9/ML)",
                    r"ferritin[:\s]*(\d+\.?\d*)\s*(nal|nal.)",
                    r"ferritin[:\s]*(\d+\.?\d*)\s*(ng|n9)",
                    # Handle more OCR errors
                    r"ferritin[:\s]*(\d+\.?\d*)\s*(namL|naml|namL.)",
                    r"ferritin[:\s]*(\d+\.?\d*)\s*(n9mL|n9ml|n9mL.)",
                ],
                "normal": {"min": 38, "max": 380, "unit": "ng/mL"},
                "aliases": ["Serum Ferritin"]
            },
            "Iron": {
                "patterns": [r"iron[:\s]*(\d+\.?\d*)\s*(µg/dL|µmol/L)"],
                "normal": {"min": 60, "max": 170, "unit": "µg/dL"},
                "aliases": ["Serum Iron"]
            },
            "B12": {
                "patterns": [r"vitamin b12[:\s]*(\d+\.?\d*)\s*(pg/mL|pmol/L)", r"b12[:\s]*(\d+\.?\d*)\s*(pg/mL|pmol/L)"],
                "normal": {"min": 200, "max": 900, "unit": "pg/mL"},
                "aliases": ["Vitamin B12", "Cobalamin"]
            },
            "Folate": {
                "patterns": [r"folate[:\s]*(\d+\.?\d*)\s*(ng/mL|nmol/L)", r"folic acid[:\s]*(\d+\.?\d*)\s*(ng/mL|nmol/L)"],
                "normal": {"min": 2.0, "max": 20.0, "unit": "ng/mL"},
                "aliases": ["Folic Acid"]
            },
            
            # Inflammatory Markers
            "CRP": {
                "patterns": [r"crp[:\s]*(\d+\.?\d*)\s*(mg/L)", r"c-reactive protein[:\s]*(\d+\.?\d*)\s*(mg/L)"],
                "normal": {"max": 3.0, "unit": "mg/L"},
                "aliases": ["C-Reactive Protein"]
            },
            "ESR": {
                "patterns": [r"esr[:\s]*(\d+\.?\d*)\s*(mm/hr)", r"erythrocyte sedimentation rate[:\s]*(\d+\.?\d*)\s*(mm/hr)"],
                "normal": {"max": 20, "unit": "mm/hr"},
                "aliases": ["Erythrocyte Sedimentation Rate"]
            },
            
            # Cardiac Markers
            "Troponin": {
                "patterns": [r"troponin[:\s]*(\d+\.?\d*)\s*(ng/mL|µg/L)"],
                "normal": {"max": 0.04, "unit": "ng/mL"},
                "aliases": ["Cardiac Troponin"]
            },
            "BNP": {
                "patterns": [r"bnp[:\s]*(\d+\.?\d*)\s*(pg/mL)", r"brain natriuretic peptide[:\s]*(\d+\.?\d*)\s*(pg/mL)"],
                "normal": {"max": 100, "unit": "pg/mL"},
                "aliases": ["Brain Natriuretic Peptide"]
            }
        }

    def extract_markers_from_text(self, text: str) -> List[HealthMarker]:
        """
        Extract health markers from text with improved pattern matching and dynamic detection.
        """
        markers = []
        text_lower = text.lower()
        
        # First, try to extract known markers
        for marker_name, marker_info in self.marker_patterns.items():
            patterns = marker_info["patterns"]
            normal_range = marker_info["normal"]
            
            for pattern in patterns:
                matches = re.finditer(pattern, text_lower, re.IGNORECASE)
                for match in matches:
                    try:
                        value = float(match.group(1))
                        unit = match.group(2) if len(match.groups()) > 1 else normal_range.get("unit", "")
                        
                        # Determine status
                        status = self._determine_status(value, normal_range)
                        
                        # Create marker
                        marker = HealthMarker(
                            name=marker_name,
                            value=value,
                            unit=unit,
                            normal_range=normal_range,
                            status=status,
                            raw_text=match.group(0),
                            recommendation=self._get_recommendation(marker_name, status)
                        )
                        markers.append(marker)
                    except (ValueError, IndexError) as e:
                        print(f"Error parsing marker {marker_name}: {e}")
                        continue
        
        # Dynamic marker detection for unknown markers
        dynamic_markers = self._extract_dynamic_markers(text)
        markers.extend(dynamic_markers)
        
        return markers
    
    def _extract_dynamic_markers(self, text: str) -> List[HealthMarker]:
        """
        Extract markers that are not in the predefined patterns but follow common formats.
        """
        markers = []
        text_lower = text.lower()
        
        # Pattern for dynamic marker detection
        # Matches: "marker_name: value unit" or "marker_name = value unit"
        dynamic_patterns = [
            r"([a-zA-Z\s]+)[:\s=]+(\d+\.?\d*)\s*([a-zA-Z/%]+)",
            r"([a-zA-Z\s]+)[:\s=]+(\d+\.?\d*)\s*(mg/dL|ng/mL|pg/mL|mEq/L|U/L|%|mmol/L)",
            r"([a-zA-Z\s]+)[:\s=]+(\d+\.?\d*)\s*(mg/dl|ng/ml|pg/ml|meq/l|u/l|mmol/l)"
        ]
        
        for pattern in dynamic_patterns:
            matches = re.finditer(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                try:
                    marker_name = match.group(1).strip()
                    value = float(match.group(2))
                    unit = match.group(3)
                    
                    # Skip if it's a known marker (already processed)
                    if any(marker_name.lower() in known_marker.lower() for known_marker in self.marker_patterns.keys()):
                        continue
                    
                    # Create dynamic marker with estimated normal range
                    normal_range = self._estimate_normal_range(marker_name, unit)
                    status = self._determine_status(value, normal_range)
                    
                    marker = HealthMarker(
                        name=marker_name.title(),
                        value=value,
                        unit=unit,
                        normal_range=normal_range,
                        status=status,
                        raw_text=match.group(0),
                        recommendation=f"Consult your healthcare provider about {marker_name.title()} levels."
                    )
                    markers.append(marker)
                except (ValueError, IndexError) as e:
                    continue
        
        return markers
    
    def _estimate_normal_range(self, marker_name: str, unit: str) -> Dict[str, float]:
        """
        Estimate normal range for unknown markers based on common patterns.
        """
        marker_lower = marker_name.lower()
        
        # Vitamin patterns
        if "vitamin" in marker_lower:
            if "d" in marker_lower:
                return {"min": 30, "max": 100, "unit": "ng/mL"}
            elif "b12" in marker_lower or "b 12" in marker_lower:
                return {"min": 200, "max": 900, "unit": "pg/mL"}
            else:
                return {"min": 0, "max": 100, "unit": unit}
        
        # Mineral patterns
        if any(mineral in marker_lower for mineral in ["calcium", "magnesium", "zinc", "copper", "selenium"]):
            if "calcium" in marker_lower:
                return {"min": 8.5, "max": 10.5, "unit": "mg/dL"}
            elif "magnesium" in marker_lower:
                return {"min": 1.7, "max": 2.2, "unit": "mg/dL"}
            elif "zinc" in marker_lower:
                return {"min": 60, "max": 120, "unit": "mcg/dL"}
            else:
                return {"min": 0, "max": 100, "unit": unit}
        
        # Hormone patterns
        if any(hormone in marker_lower for hormone in ["tsh", "t3", "t4", "cortisol", "insulin"]):
            if "tsh" in marker_lower:
                return {"min": 0.4, "max": 4.0, "unit": "µIU/mL"}
            elif "t3" in marker_lower:
                return {"min": 80, "max": 200, "unit": "ng/dL"}
            elif "t4" in marker_lower:
                return {"min": 0.8, "max": 1.8, "unit": "µg/dL"}
            else:
                return {"min": 0, "max": 100, "unit": unit}
        
        # Default estimation
        return {"min": 0, "max": 100, "unit": unit}
    
    def add_custom_marker_pattern(self, marker_name: str, patterns: List[str], normal_range: Dict[str, float], aliases: List[str] = None):
        """
        Add a custom marker pattern for dynamic marker detection.
        """
        self.marker_patterns[marker_name] = {
            "patterns": patterns,
            "normal": normal_range,
            "aliases": aliases or []
        }
    
    def get_marker_by_name(self, marker_name: str) -> Optional[Dict]:
        """
        Get marker information by name (case-insensitive).
        """
        marker_name_lower = marker_name.lower()
        
        # Direct match
        if marker_name in self.marker_patterns:
            return self.marker_patterns[marker_name]
        
        # Alias match
        for name, info in self.marker_patterns.items():
            if marker_name_lower in name.lower() or any(alias.lower() == marker_name_lower for alias in info.get("aliases", [])):
                return info
        
        return None
    
    def _determine_status(self, value: float, normal_range: Dict[str, float]) -> str:
        """
        Determine the status (low, normal, high) based on value and normal range.
        """
        min_val = normal_range.get("min", 0)
        max_val = normal_range.get("max", 100)
        
        if value < min_val:
            return "low"
        elif value > max_val:
            return "high"
        else:
            return "normal"
    
    def _get_recommendation(self, marker_name: str, status: str) -> str:
        """
        Get recommendation based on marker name and status.
        """
        if status == "normal":
            return f"Your {marker_name} levels are within normal range. Continue maintaining a healthy lifestyle."
        elif status == "low":
            return f"Your {marker_name} levels are low. Consider dietary changes and consult your healthcare provider."
        elif status == "high":
            return f"Your {marker_name} levels are high. Consult your healthcare provider for guidance."
        else:
            return f"Consult your healthcare provider about your {marker_name} levels."
