import re
import json
from typing import Dict, List, Tuple, Optional
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

    def detect_markers(self, text: str) -> List[HealthMarker]:
        """Detect health markers in the given text with improved flexibility."""
        detected_markers = []
        text_lower = text.lower()
        
        # First pass: Try exact pattern matching
        for marker_name, marker_info in self.marker_patterns.items():
            marker_found = False
            for pattern in marker_info["patterns"]:
                if marker_found:
                    break
                    
                matches = re.finditer(pattern, text_lower, re.IGNORECASE)
                for match in matches:
                    try:
                        value = float(match.group(1))
                        unit = match.group(2) if len(match.groups()) > 1 else marker_info["normal"]["unit"]
                        
                        status = self._determine_status(value, marker_info["normal"])
                        start = max(0, match.start() - 50)
                        end = min(len(text), match.end() + 50)
                        raw_text = text[start:end].strip()
                        recommendation = self._get_marker_recommendation(marker_name, status)
                        
                        marker = HealthMarker(
                            name=marker_name,
                            value=value,
                            unit=unit,
                            normal_range=marker_info["normal"],
                            status=status,
                            raw_text=raw_text,
                            recommendation=recommendation
                        )
                        detected_markers.append(marker)
                        marker_found = True
                        break
                    except (ValueError, IndexError):
                        continue
        
        # Second pass: Try flexible matching for common variations
        if not detected_markers:
            detected_markers = self._flexible_detect_markers(text)
        
        return detected_markers

    def _flexible_detect_markers(self, text: str) -> List[HealthMarker]:
        """Flexible detection for common variations and misspellings."""
        detected_markers = []
        text_lower = text.lower()
        
        # Common variations and their mappings
        variations = {
            "hba1c": "Hemoglobin A1C",
            "a1c": "Hemoglobin A1C", 
            "glycated": "Hemoglobin A1C",
            "ferritin": "FERRITIN",
            "glucose": "Glucose",
            "blood sugar": "Glucose",
            "cholesterol": "Total Cholesterol",
            "ldl": "LDL",
            "hdl": "HDL",
            "triglycerides": "Triglycerides",
            "creatinine": "Creatinine",
            "bun": "BUN",
            "hemoglobin": "Hemoglobin",
            "hematocrit": "Hematocrit",
            "wbc": "White Blood Cells",
            "platelets": "Platelets",
            "tsh": "TSH",
            "t4": "T4",
            "t3": "T3",
            "alt": "ALT",
            "ast": "AST"
        }
        
        # Look for number patterns near marker names
        number_pattern = r'(\d+\.?\d*)'
        
        for variation, marker_name in variations.items():
            if variation in text_lower and marker_name in self.marker_patterns:
                # Find numbers near the marker name
                marker_pos = text_lower.find(variation)
                if marker_pos != -1:
                    # Look for numbers in a 100-character window around the marker
                    start = max(0, marker_pos - 50)
                    end = min(len(text), marker_pos + 50)
                    window = text_lower[start:end]
                    
                    # Find all numbers in the window
                    numbers = re.findall(number_pattern, window)
                    if numbers:
                        try:
                            # Try to find the most likely value (usually the first number)
                            value = float(numbers[0])
                            marker_info = self.marker_patterns[marker_name]
                            
                            # Determine status
                            status = self._determine_status(value, marker_info["normal"])
                            
                            # Get raw text
                            raw_start = max(0, marker_pos - 30)
                            raw_end = min(len(text), marker_pos + 30)
                            raw_text = text[raw_start:raw_end].strip()
                            
                            # Get recommendation
                            recommendation = self._get_marker_recommendation(marker_name, status)
                            
                            marker = HealthMarker(
                                name=marker_name,
                                value=value,
                                unit=marker_info["normal"]["unit"],
                                normal_range=marker_info["normal"],
                                status=status,
                                raw_text=raw_text,
                                recommendation=recommendation
                            )
                            detected_markers.append(marker)
                        except (ValueError, IndexError):
                            continue
        
        return detected_markers

    def _determine_status(self, value: float, normal_range: Dict[str, float]) -> str:
        """Determine if a value is normal, low, high, or critical."""
        min_val = normal_range.get("min")
        max_val = normal_range.get("max")
        
        if min_val is not None and max_val is not None:
            if value < min_val:
                return "low"
            elif value > max_val:
                return "high"
            else:
                return "normal"
        elif min_val is not None:
            if value < min_val:
                return "low"
            else:
                return "normal"
        elif max_val is not None:
            if value > max_val:
                return "high"
            else:
                return "normal"
        else:
            return "unknown"

    def _get_marker_recommendation(self, marker_name: str, status: str) -> str:
        """Get a recommendation for a specific marker and status."""
        if status == "normal":
            return ""
            
        if marker_name == "FERRITIN" and status == "low":
            return (
                "Low ferritin levels indicate iron deficiency. Recommendations: "
                "1) Increase iron-rich foods (red meat, spinach, beans, fortified cereals), "
                "2) Consider iron supplements under medical supervision, "
                "3) Avoid coffee/tea with meals as they inhibit iron absorption, "
                "4) Include vitamin C-rich foods to enhance iron absorption, "
                "5) Consult your doctor for proper iron supplementation."
            )
        elif marker_name in ["LDL", "Total Cholesterol"] and status == "high":
            return (
                "High cholesterol levels increase cardiovascular risk. Recommendations: "
                "1) Reduce saturated and trans fats in your diet, "
                "2) Increase fiber intake (oats, fruits, vegetables), "
                "3) Exercise regularly (150 minutes/week), "
                "4) Maintain a healthy weight, "
                "5) Consider medication if lifestyle changes aren't sufficient."
            )
        elif marker_name == "HDL" and status == "low":
            return (
                "Low HDL cholesterol increases cardiovascular risk. Recommendations: "
                "1) Exercise regularly (aerobic activity), "
                "2) Quit smoking if applicable, "
                "3) Include healthy fats (olive oil, nuts, avocados), "
                "4) Limit refined carbohydrates, "
                "5) Consider omega-3 supplements."
            )
        elif marker_name == "Glucose" and status == "high":
            return (
                "High glucose levels may indicate prediabetes or diabetes. Recommendations: "
                "1) Reduce refined carbohydrates and sugars, "
                "2) Exercise regularly, "
                "3) Maintain a healthy weight, "
                "4) Monitor blood sugar levels, "
                "5) Consult your doctor for proper diabetes management."
            )
        elif marker_name == "TSH" and status == "high":
            return (
                "High TSH levels may indicate hypothyroidism. Recommendations: "
                "1) Consult your doctor for thyroid function evaluation, "
                "2) Consider thyroid hormone replacement therapy, "
                "3) Maintain a balanced diet with adequate iodine, "
                "4) Regular thyroid function monitoring, "
                "5) Address any underlying causes."
            )
        elif marker_name == "TSH" and status == "low":
            return (
                "Low TSH levels may indicate hyperthyroidism. Recommendations: "
                "1) Consult your doctor for thyroid function evaluation, "
                "2) Consider anti-thyroid medications if needed, "
                "3) Monitor for symptoms of hyperthyroidism, "
                "4) Regular thyroid function monitoring, "
                "5) Address any underlying causes."
            )
        else:
            return f"Abnormal {marker_name} levels detected. Please consult your healthcare provider for personalized recommendations."

    def get_recommendations(self, markers: List[HealthMarker]) -> Dict[str, str]:
        """Get recommendations based on detected markers."""
        recommendations = {}
        
        for marker in markers:
            if marker.status == "normal":
                continue
                
            if marker.name == "FERRITIN" and marker.status == "low":
                recommendations[marker.name] = (
                    "Low ferritin levels indicate iron deficiency. Recommendations: "
                    "1) Increase iron-rich foods (red meat, spinach, beans, fortified cereals), "
                    "2) Consider iron supplements under medical supervision, "
                    "3) Avoid coffee/tea with meals as they inhibit iron absorption, "
                    "4) Include vitamin C-rich foods to enhance iron absorption, "
                    "5) Consult your doctor for proper iron supplementation."
                )
            elif marker.name in ["LDL", "Total Cholesterol"] and marker.status == "high":
                recommendations[marker.name] = (
                    "High cholesterol levels increase cardiovascular risk. Recommendations: "
                    "1) Reduce saturated and trans fats in your diet, "
                    "2) Increase fiber intake (oats, fruits, vegetables), "
                    "3) Exercise regularly (150 minutes/week), "
                    "4) Maintain a healthy weight, "
                    "5) Consider medication if lifestyle changes aren't sufficient."
                )
            elif marker.name == "HDL" and marker.status == "low":
                recommendations[marker.name] = (
                    "Low HDL cholesterol increases cardiovascular risk. Recommendations: "
                    "1) Exercise regularly (aerobic activity), "
                    "2) Quit smoking if applicable, "
                    "3) Include healthy fats (olive oil, nuts, avocados), "
                    "4) Limit refined carbohydrates, "
                    "5) Consider omega-3 supplements."
                )
            elif marker.name == "Glucose" and marker.status == "high":
                recommendations[marker.name] = (
                    "High blood glucose may indicate prediabetes or diabetes. Recommendations: "
                    "1) Monitor carbohydrate intake, "
                    "2) Exercise regularly, "
                    "3) Maintain a healthy weight, "
                    "4) Follow a balanced diet, "
                    "5) Consult your doctor for proper evaluation and management."
                )
            elif marker.name == "Vitamin D" and marker.status == "low":
                recommendations[marker.name] = (
                    "Low vitamin D levels can affect bone health and immunity. Recommendations: "
                    "1) Get 10-30 minutes of sun exposure daily, "
                    "2) Include vitamin D-rich foods (fatty fish, egg yolks, fortified dairy), "
                    "3) Consider vitamin D supplements under medical supervision, "
                    "4) Maintain adequate calcium intake, "
                    "5) Regular exercise for bone health."
                )
            elif marker.name in ["ALT", "AST"] and marker.status == "high":
                recommendations[marker.name] = (
                    "Elevated liver enzymes may indicate liver stress. Recommendations: "
                    "1) Avoid alcohol consumption, "
                    "2) Maintain a healthy weight, "
                    "3) Follow a balanced diet low in processed foods, "
                    "4) Exercise regularly, "
                    "5) Consult your doctor for further evaluation."
                )
            elif marker.name == "Creatinine" and marker.status == "high":
                recommendations[marker.name] = (
                    "Elevated creatinine may indicate kidney function issues. Recommendations: "
                    "1) Stay well hydrated, "
                    "2) Follow a kidney-friendly diet if recommended, "
                    "3) Control blood pressure and diabetes, "
                    "4) Avoid NSAIDs unless prescribed, "
                    "5) Consult your doctor for proper evaluation."
                )
            else:
                # Generic recommendation for other markers
                status_text = "high" if marker.status == "high" else "low"
                recommendations[marker.name] = (
                    f"Your {marker.name} level is {status_text} ({marker.value} {marker.unit}). "
                    "Please consult with your healthcare provider for personalized recommendations "
                    "and to determine if further testing or treatment is needed."
                )
        
        return recommendations
