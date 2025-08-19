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
        # Always run flexible detection to catch unknown markers
        flexible_markers = self._flexible_detect_markers(text)
        
        # Combine results, avoiding duplicates
        existing_names = {marker.name.lower() for marker in detected_markers}
        # Also check for partial matches (e.g., "cholesterol" vs "total cholesterol")
        existing_words = set()
        for marker in detected_markers:
            words = marker.name.lower().split()
            existing_words.update(words)
        
        for marker in flexible_markers:
            marker_words = set(marker.name.lower().split())
            # Skip if exact name match or if any word overlaps significantly
            if (marker.name.lower() not in existing_names and 
                not any(word in existing_words for word in marker_words if len(word) > 3)):
                detected_markers.append(marker)
        
        return detected_markers

    def _flexible_detect_markers(self, text: str) -> List[HealthMarker]:
        """Dynamic detection for ANY health markers in ANY format."""
        detected_markers = []
        text_lower = text.lower()
        
        # Dynamic pattern to find ANY marker name followed by a number
        # This will catch patterns like: "marker: value", "marker = value", "marker value", etc.
        dynamic_patterns = [
            r'([^:]+):\s*(\d+\.?\d*)\s*([a-zA-Z/%]+)?',  # "marker: value unit"
            r'([^=]+)=\s*(\d+\.?\d*)\s*([a-zA-Z/%]+)?',  # "marker = value unit"
            r'([a-zA-Z][a-zA-Z\s]*)\s+(\d+\.?\d*)\s*([a-zA-Z/%]+)?',  # "marker value unit"
        ]
        
        for pattern in dynamic_patterns:
            matches = re.finditer(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                try:
                    marker_name = match.group(1).strip()
                    value = float(match.group(2))
                    unit = match.group(3) if match.group(3) else self._guess_unit(marker_name)
                    
                    # Clean up marker name
                    marker_name = re.sub(r'[,\s]+', ' ', marker_name).strip()
                    
                    # Skip if it's not a health marker (too short, common words, etc.)
                    if len(marker_name) < 3 or marker_name in ['normal', 'range', 'value', 'test', 'result', 'reference']:
                        continue
                    
                    # Create a dynamic marker
                    marker = self._create_dynamic_marker(marker_name, value, unit, text)
                    if marker:
                        detected_markers.append(marker)
                        
                except (ValueError, IndexError):
                    continue
        
        return detected_markers
        
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

    def _guess_unit(self, marker_name: str) -> str:
        """Intelligently guess the unit based on marker name."""
        marker_lower = marker_name.lower()
        
        # Common unit patterns
        if any(word in marker_lower for word in ['glucose', 'sugar', 'cholesterol', 'ldl', 'hdl', 'triglycerides']):
            return 'mg/dL'
        elif any(word in marker_lower for word in ['hba1c', 'a1c', 'glycated', 'hematocrit']):
            return '%'
        elif any(word in marker_lower for word in ['ferritin', 'troponin', 'bnp']):
            return 'ng/mL'
        elif any(word in marker_lower for word in ['creatinine', 'bun']):
            return 'mg/dL'
        elif any(word in marker_lower for word in ['hemoglobin', 'albumin']):
            return 'g/dL'
        elif any(word in marker_lower for word in ['wbc', 'platelets', 'rbc']):
            return 'K/µL'
        elif any(word in marker_lower for word in ['tsh', 't4', 't3']):
            return 'µIU/mL'
        elif any(word in marker_lower for word in ['alt', 'ast', 'alkaline']):
            return 'U/L'
        else:
            return 'units'  # Generic fallback

    def _create_dynamic_marker(self, marker_name: str, value: float, unit: str, original_text: str) -> Optional[HealthMarker]:
        """Create a HealthMarker for dynamically detected markers with improved range detection."""
        try:
            # Try to get normal range from RAG system first
            try:
                from utils.rag_manager import rag_manager
                normal_range = rag_manager.get_intelligent_normal_range(marker_name, value, original_text)
            except ImportError:
                # Fallback to local method if RAG not available
                normal_range = self._get_intelligent_normal_range(marker_name, value)
            
            # Determine status using the improved normal range
            status = self._determine_status(value, normal_range)
            
            # Get recommendation using RAG knowledge if available
            try:
                from utils.rag_manager import rag_manager
                knowledge = rag_manager.get_marker_knowledge(marker_name)
                if knowledge:
                    recommendation = self._get_recommendation_from_knowledge(knowledge, value, status)
                else:
                    recommendation = self._get_intelligent_recommendation(marker_name, value, status, normal_range)
            except ImportError:
                recommendation = self._get_intelligent_recommendation(marker_name, value, status, normal_range)
            
            # Get raw text context
            marker_pos = original_text.lower().find(marker_name.lower())
            if marker_pos != -1:
                start = max(0, marker_pos - 30)
                end = min(len(original_text), marker_pos + 50)
                raw_text = original_text[start:end].strip()
            else:
                raw_text = f"{marker_name}: {value} {unit}"
            
            return HealthMarker(
                name=marker_name.upper(),
                value=value,
                unit=unit,
                status=status,
                normal_range=normal_range,
                raw_text=raw_text,
                recommendation=recommendation
            )
        except Exception as e:
            print(f"Error creating dynamic marker {marker_name}: {e}")
            return None

    def _get_recommendation_from_knowledge(self, knowledge: Dict[str, Any], value: float, status: str) -> str:
        """Get recommendation from RAG knowledge base."""
        if status == "normal":
            return f"Your {knowledge['marker']} level is within normal range. Continue maintaining your healthy lifestyle."
        
        if status == "low" and knowledge.get("low_treatment"):
            return f"Your {knowledge['marker']} level is low. {knowledge['low_treatment']}"
        elif status == "high" and knowledge.get("high_treatment"):
            return f"Your {knowledge['marker']} level is high. {knowledge['high_treatment']}"
        else:
            return f"Your {knowledge['marker']} level may be outside normal ranges. Consult your healthcare provider for proper evaluation and guidance."

    def _extract_normal_range(self, marker_name: str, text: str) -> Optional[Dict[str, float]]:
        """Extract normal range from text if available."""
        text_lower = text.lower()
        marker_lower = marker_name.lower()
        
        # Look for patterns like "normal range: 4-6", "reference: 70-100", etc.
        range_patterns = [
            r'normal\s+range[:\s]*(\d+\.?\d*)\s*[-–]\s*(\d+\.?\d*)',
            r'reference[:\s]*(\d+\.?\d*)\s*[-–]\s*(\d+\.?\d*)',
            r'range[:\s]*(\d+\.?\d*)\s*[-–]\s*(\d+\.?\d*)',
            r'(\d+\.?\d*)\s*[-–]\s*(\d+\.?\d*)',  # Generic range pattern
        ]
        
        for pattern in range_patterns:
            matches = re.findall(pattern, text_lower)
            if matches:
                try:
                    min_val, max_val = float(matches[0][0]), float(matches[0][1])
                    return {"min": min_val, "max": max_val}
                except (ValueError, IndexError):
                    continue
        
        return None

    def _get_intelligent_normal_range(self, marker_name: str, value: float) -> Dict[str, float]:
        """Intelligently estimate normal range based on marker name and value."""
        marker_lower = marker_name.lower()
        
        # Common normal ranges based on marker type
        if any(word in marker_lower for word in ['glucose', 'sugar']):
            return {"min": 70, "max": 100}
        elif any(word in marker_lower for word in ['hba1c', 'a1c', 'glycated']):
            return {"min": 4.0, "max": 5.6}
        elif any(word in marker_lower for word in ['cholesterol', 'ldl']):
            return {"max": 100}
        elif any(word in marker_lower for word in ['hdl']):
            return {"min": 40}
        elif any(word in marker_lower for word in ['triglycerides']):
            return {"max": 150}
        elif any(word in marker_lower for word in ['ferritin']):
            return {"min": 38, "max": 380}
        elif any(word in marker_lower for word in ['creatinine']):
            return {"min": 0.6, "max": 1.2}
        elif any(word in marker_lower for word in ['hemoglobin']):
            return {"min": 12, "max": 16}
        elif any(word in marker_lower for word in ['hematocrit']):
            return {"min": 36, "max": 46}
        elif any(word in marker_lower for word in ['wbc']):
            return {"min": 4.5, "max": 11.0}
        elif any(word in marker_lower for word in ['platelets']):
            return {"min": 150, "max": 450}
        elif any(word in marker_lower for word in ['tsh']):
            return {"min": 0.4, "max": 4.0}
        elif any(word in marker_lower for word in ['magnesium']):
            return {"min": 1.7, "max": 2.2}
        elif any(word in marker_lower for word in ['calcium']):
            return {"min": 8.5, "max": 10.5}
        elif any(word in marker_lower for word in ['potassium']):
            return {"min": 3.5, "max": 5.0}
        elif any(word in marker_lower for word in ['sodium']):
            return {"min": 135, "max": 145}
        elif any(word in marker_lower for word in ['zinc']):
            return {"min": 60, "max": 120}
        elif any(word in marker_lower for word in ['copper']):
            return {"min": 70, "max": 140}
        elif any(word in marker_lower for word in ['selenium']):
            return {"min": 70, "max": 150}
        elif any(word in marker_lower for word in ['iron']):
            return {"min": 60, "max": 170}
        elif any(word in marker_lower for word in ['bun']):
            return {"min": 7, "max": 20}
        elif any(word in marker_lower for word in ['albumin']):
            return {"min": 3.4, "max": 5.4}
        elif any(word in marker_lower for word in ['bilirubin']):
            return {"min": 0.3, "max": 1.2}
        elif any(word in marker_lower for word in ['alt']):
            return {"min": 7, "max": 55}
        elif any(word in marker_lower for word in ['ast']):
            return {"min": 8, "max": 48}
        elif any(word in marker_lower for word in ['alkaline phosphatase']):
            return {"min": 44, "max": 147}
        elif any(word in marker_lower for word in ['rdw']):
            return {"min": 11.5, "max": 14.5}
        elif any(word in marker_lower for word in ['mcv']):
            return {"min": 80, "max": 100}
        elif any(word in marker_lower for word in ['mch']):
            return {"min": 27, "max": 32}
        elif any(word in marker_lower for word in ['mchc']):
            return {"min": 32, "max": 36}
        else:
            # For unknown markers, use more sophisticated estimation based on value characteristics
            return self._estimate_range_for_unknown_marker(marker_name, value)

    def _estimate_range_for_unknown_marker(self, marker_name: str, value: float) -> Dict[str, float]:
        """Estimate normal range for unknown markers using sophisticated heuristics."""
        marker_lower = marker_name.lower()
        
        # Check for common patterns in marker names
        if any(word in marker_lower for word in ['vitamin', 'vit']):
            # Vitamin markers typically have ranges like 20-100 or 200-900
            if value < 50:
                return {"min": 20, "max": 100}
            elif value < 500:
                return {"min": 200, "max": 900}
            else:
                return {"min": 500, "max": 2000}
        
        elif any(word in marker_lower for word in ['hormone', 'testosterone', 'estrogen', 'progesterone']):
            # Hormone markers have varying ranges
            if value < 10:
                return {"min": 1, "max": 10}
            elif value < 100:
                return {"min": 10, "max": 100}
            else:
                return {"min": 100, "max": 1000}
        
        elif any(word in marker_lower for word in ['enzyme', 'protein', 'albumin', 'globulin']):
            # Enzyme/protein markers
            if value < 10:
                return {"min": 1, "max": 10}
            elif value < 100:
                return {"min": 10, "max": 100}
            else:
                return {"min": 100, "max": 500}
        
        elif any(word in marker_lower for word in ['mineral', 'electrolyte', 'phosphate', 'chloride']):
            # Mineral/electrolyte markers
            if value < 10:
                return {"min": 1, "max": 10}
            elif value < 100:
                return {"min": 10, "max": 150}
            else:
                return {"min": 100, "max": 200}
        
        elif any(word in marker_lower for word in ['antibody', 'immunoglobulin', 'iga', 'igg', 'igm']):
            # Antibody markers
            if value < 100:
                return {"min": 10, "max": 100}
            elif value < 1000:
                return {"min": 100, "max": 1000}
            else:
                return {"min": 1000, "max": 5000}
        
        else:
            # Default estimation based on value magnitude with more reasonable ranges
            if value < 0.1:
                return {"min": 0, "max": 0.1}
            elif value < 1:
                return {"min": 0.1, "max": 1}
            elif value < 10:
                return {"min": 1, "max": 10}
            elif value < 100:
                return {"min": 10, "max": 100}
            elif value < 1000:
                return {"min": 100, "max": 1000}
            else:
                # For very high values, use a more conservative approach
                return {"min": 0, "max": value * 1.5}

    def _get_intelligent_recommendation(self, marker_name: str, value: float, status: str, normal_range: Dict[str, float]) -> str:
        """Generate intelligent recommendations for ANY marker."""
        if status == "normal":
            return f"Your {marker_name} level is within normal range. Continue maintaining your healthy lifestyle."
        
        # Get the normal range for context
        min_val = normal_range.get('min')
        max_val = normal_range.get('max')
        
        if status == "high":
            if max_val:
                return f"Your {marker_name} level of {value} is above the normal range (max: {max_val}). Consider lifestyle changes and consult your healthcare provider for personalized guidance."
            else:
                return f"Your {marker_name} level of {value} appears elevated. Consult your healthcare provider for evaluation and personalized recommendations."
        
        elif status == "low":
            if min_val:
                return f"Your {marker_name} level of {value} is below the normal range (min: {min_val}). Consider dietary changes and consult your healthcare provider for evaluation."
            else:
                return f"Your {marker_name} level of {value} appears low. Consult your healthcare provider for evaluation and personalized recommendations."
        
        else:
            return f"Your {marker_name} level of {value} may be outside normal ranges. Consult your healthcare provider for proper evaluation and guidance."

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
