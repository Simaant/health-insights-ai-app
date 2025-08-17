# backend/utils/agent_manager.py
import os
import re
from typing import Optional, List, Dict, Any

# Optional lazy initialization to avoid model download during import time in tests
_model = None

def _get_model():
    global _model
    if _model is None:
        # For development, use a simple text generation approach
        # This avoids downloading large models during startup
        _model = "simple_text_generator"
    return _model

def run_agent(prompt: str, markers: Optional[List[Dict[str, Any]]] = None, chat_history: Optional[List[Dict[str, str]]] = None) -> str:
    """
    Enhanced intelligent AI agent that understands context and provides personalized responses.
    """
    # Normalize the prompt
    prompt_lower = prompt.lower().strip()
    
    # Check if this is a general health question that doesn't relate to uploaded markers
    if _is_general_health_question(prompt_lower):
        return _handle_general_health_questions(prompt, chat_history)
    
    # If we have markers, provide context-aware responses
    if markers and len(markers) > 0:
        return _generate_intelligent_response(markers, prompt, chat_history)
    
    # Handle general health questions without specific marker data
    return _handle_general_health_questions(prompt, chat_history)

def _generate_intelligent_response(markers: List[Dict[str, Any]], user_prompt: str, chat_history: Optional[List[Dict[str, str]]] = None) -> str:
    """Generate intelligent, context-aware responses based on user's health markers."""
    
    prompt_lower = user_prompt.lower()
    
    # Extract abnormal markers
    abnormal_markers = [m for m in markers if m.get("status") != "normal"]
    normal_markers = [m for m in markers if m.get("status") == "normal"]
    
    # Check for specific question types (order matters - more specific first)
    if _is_doctor_question(prompt_lower):
        return _handle_doctor_question(markers, user_prompt)
    
    if _is_treatment_question(prompt_lower):
        return _handle_treatment_question(markers, user_prompt)
    
    if _is_food_question(prompt_lower):
        return _handle_food_question(markers, user_prompt)
    
    if _is_symptom_question(prompt_lower):
        return _handle_symptom_question(markers, user_prompt)
    
    if _is_testing_question(prompt_lower):
        return _handle_testing_question(markers, user_prompt)
    
    if _is_specific_marker_question(prompt_lower, markers):
        return _handle_specific_marker_question(markers, user_prompt)
    
    if _is_followup_question(prompt_lower, chat_history):
        return _handle_followup_question(markers, user_prompt, chat_history)
    
    # Default comprehensive response
    return _generate_comprehensive_marker_response(markers, user_prompt)

def _is_followup_question(prompt: str, chat_history: Optional[List[Dict[str, str]]] = None) -> bool:
    """Check if this is a follow-up question based on chat history."""
    followup_indicators = [
        "what about", "how about", "what if", "can you explain", "tell me more",
        "what does this mean", "why", "how", "when", "where", "which",
        "is this serious", "should i worry", "is this normal", "what next"
    ]
    return any(indicator in prompt for indicator in followup_indicators)

def _is_specific_marker_question(prompt: str, markers: List[Dict[str, Any]]) -> bool:
    """Check if user is asking about a specific marker."""
    marker_names = [m.get("name", "").lower() for m in markers]
    return any(name in prompt for name in marker_names)

def _is_treatment_question(prompt: str) -> bool:
    """Check if user is asking about treatment options."""
    treatment_keywords = [
        "treatment", "cure", "fix", "medicine", "medication", "supplement",
        "therapy", "remedy", "solution", "what should i do", "how to treat"
    ]
    return any(keyword in prompt for keyword in treatment_keywords)

def _is_food_question(prompt: str) -> bool:
    """Check if user is asking about diet/food recommendations."""
    food_keywords = [
        "food", "diet", "eat", "nutrition", "meal", "supplement", "vitamin",
        "what to eat", "foods to", "dietary", "nutritional"
    ]
    return any(keyword in prompt for keyword in food_keywords)

def _is_symptom_question(prompt: str) -> bool:
    """Check if user is asking about symptoms."""
    symptom_keywords = [
        "symptom", "sign", "feel", "experience", "notice", "suffer",
        "what are the signs", "how do i know", "what to look for"
    ]
    return any(keyword in prompt for keyword in symptom_keywords)

def _is_testing_question(prompt: str) -> bool:
    """Check if user is asking about testing/monitoring."""
    testing_keywords = [
        "test", "monitor", "check", "retest", "follow up", "when to test",
        "how often", "frequency", "schedule", "appointment"
    ]
    return any(keyword in prompt for keyword in testing_keywords)

def _is_general_health_question(prompt: str) -> bool:
    """Check if this is a general health question that doesn't relate to uploaded markers."""
    general_health_keywords = [
        "vitamin d", "vitamin c", "vitamin b", "vitamin a", "vitamin e", "vitamin k",
        "ideal range", "normal range", "healthy range", "optimal level",
        "what is", "what are", "how much", "how many", "recommended",
        "daily value", "daily requirement", "rda", "recommended daily",
        "blood pressure", "heart rate", "bmi", "body mass index",
        "cholesterol", "triglycerides", "hdl", "ldl", "total cholesterol",
        "blood sugar", "glucose", "a1c", "hemoglobin a1c",
        "thyroid", "tsh", "t3", "t4", "thyroid stimulating hormone",
        "kidney", "creatinine", "egfr", "bun", "blood urea nitrogen",
        "liver", "alt", "ast", "alkaline phosphatase", "bilirubin",
        "electrolytes", "sodium", "potassium", "chloride", "bicarbonate",
        "calcium", "magnesium", "phosphorus",
        "complete blood count", "cbc", "white blood cells", "red blood cells",
        "platelets", "hemoglobin", "hematocrit"
    ]
    return any(keyword in prompt for keyword in general_health_keywords)

def _is_doctor_question(prompt: str) -> bool:
    """Check if user is asking about seeing a doctor."""
    doctor_keywords = [
        "see my doctor", "see a doctor", "see the doctor", "see your doctor",
        "consult a doctor", "consult my doctor", "consult the doctor",
        "visit a doctor", "visit my doctor", "visit the doctor",
        "go to doctor", "go to my doctor", "go to the doctor",
        "when should i see", "when to see", "when to visit",
        "schedule appointment", "make appointment", "book appointment",
        "emergency", "urgent care", "urgent medical"
    ]
    return any(keyword in prompt for keyword in doctor_keywords)

def _handle_followup_question(markers: List[Dict[str, Any]], user_prompt: str, chat_history: Optional[List[Dict[str, str]]] = None) -> str:
    """Handle follow-up questions with context awareness."""
    prompt_lower = user_prompt.lower()
    
    if "what about" in prompt_lower or "how about" in prompt_lower:
        # Extract the specific topic they're asking about
        if "ferritin" in prompt_lower or "iron" in prompt_lower:
            return _get_detailed_ferritin_info(markers)
        elif "cholesterol" in prompt_lower:
            return _get_detailed_cholesterol_info(markers)
        elif "glucose" in prompt_lower or "blood sugar" in prompt_lower:
            return _get_detailed_glucose_info(markers)
        elif "thyroid" in prompt_lower or "tsh" in prompt_lower:
            return _get_detailed_thyroid_info(markers)
    
    if "what does this mean" in prompt_lower:
        return _explain_marker_meaning(markers, user_prompt)
    
    if "why" in prompt_lower:
        return _explain_causes(markers, user_prompt)
    
    if "how serious" in prompt_lower or "is this serious" in prompt_lower:
        return _assess_severity(markers, user_prompt)
    
    return _generate_comprehensive_marker_response(markers, user_prompt)

def _handle_specific_marker_question(markers: List[Dict[str, Any]], user_prompt: str) -> str:
    """Handle questions about specific markers."""
    prompt_lower = user_prompt.lower()
    
    for marker in markers:
        marker_name = marker.get("name", "").lower()
        if marker_name in prompt_lower:
            return _get_marker_specific_response(marker, user_prompt)
    
    return _generate_comprehensive_marker_response(markers, user_prompt)

def _handle_treatment_question(markers: List[Dict[str, Any]], user_prompt: str) -> str:
    """Handle treatment-related questions."""
    abnormal_markers = [m for m in markers if m.get("status") != "normal"]
    
    if not abnormal_markers:
        return "Since all your markers are within normal ranges, no specific treatment is needed. Continue maintaining your healthy lifestyle!"
    
    if len(abnormal_markers) == 1:
        marker = abnormal_markers[0]
        name = marker.get("name", "")
        status = marker.get("status", "")
        
        if name == "FERRITIN" and status == "low":
            return ("**Treatment for low ferritin:**\n"
                   "1. **Dietary changes:** Increase iron-rich foods\n"
                   "2. **Supplements:** Iron supplements (consult your doctor first)\n"
                   "3. **Address underlying causes:** Check for blood loss or absorption issues\n"
                   "4. **Monitor:** Retest in 3-6 months")
        
        elif name in ["LDL", "Total Cholesterol"] and status == "high":
            return ("**Treatment for high cholesterol:**\n"
                   "1. **Lifestyle changes:** Diet, exercise, weight management\n"
                   "2. **Medication:** May be needed if lifestyle changes aren't sufficient\n"
                   "3. **Regular monitoring:** Follow your doctor's testing schedule")
    
    return ("**Treatment approach:**\n"
            "1. Address the most critical markers first\n"
            "2. Implement lifestyle changes (diet, exercise)\n"
            "3. Consider medications if needed\n"
            "4. Regular monitoring and follow-up\n"
            "**Always consult your healthcare provider for personalized treatment plans.**")

def _handle_food_question(markers: List[Dict[str, Any]], user_prompt: str) -> str:
    """Handle diet and nutrition questions."""
    prompt_lower = user_prompt.lower()
    abnormal_markers = [m for m in markers if m.get("status") != "normal"]
    
    if not abnormal_markers:
        return "Since all your markers are normal, maintain a balanced diet with plenty of fruits, vegetables, lean proteins, and whole grains."
    
    # Focus on the specific marker mentioned or the most relevant one
    if len(abnormal_markers) == 1:
        marker = abnormal_markers[0]
        name = marker.get("name", "")
        status = marker.get("status", "")
        
        if name == "FERRITIN" and status == "low":
            return ("**For low ferritin:**\n"
                   "• **Iron-rich foods:** Red meat, spinach, beans, lentils, fortified cereals\n"
                   "• **Enhance absorption:** Include vitamin C-rich foods (citrus, bell peppers)\n"
                   "• **Avoid with meals:** Coffee, tea, calcium supplements\n"
                   "• **Consider:** Iron supplements under medical supervision")
        
        elif name in ["LDL", "Total Cholesterol"] and status == "high":
            return ("**For high cholesterol:**\n"
                   "• **Reduce:** Saturated fats, trans fats, processed foods\n"
                   "• **Increase:** Fiber (oats, fruits, vegetables), omega-3 fatty acids\n"
                   "• **Choose:** Lean proteins, whole grains, healthy fats (olive oil, nuts)")
    
    # Multiple markers - give focused advice
    return ("**Dietary recommendations:**\n"
            "• Focus on whole foods, lean proteins, and plenty of vegetables\n"
            "• Reduce processed foods and added sugars\n"
            "• Include healthy fats and fiber\n"
            "• Consider consulting a registered dietitian for personalized advice")

def _handle_symptom_question(markers: List[Dict[str, Any]], user_prompt: str) -> str:
    """Handle symptom-related questions."""
    abnormal_markers = [m for m in markers if m.get("status") != "normal"]
    
    if not abnormal_markers:
        return "Since all your markers are normal, you shouldn't experience symptoms related to these health indicators."
    
    if len(abnormal_markers) == 1:
        marker = abnormal_markers[0]
        name = marker.get("name", "")
        status = marker.get("status", "")
        
        if name == "FERRITIN" and status == "low":
            return ("**Low ferritin symptoms:**\n"
                   "• Fatigue and weakness\n"
                   "• Shortness of breath\n"
                   "• Pale skin\n"
                   "• Dizziness\n"
                   "• Cold hands and feet\n"
                   "• Brittle nails")
        
        elif name in ["LDL", "Total Cholesterol"] and status == "high":
            return ("**High cholesterol symptoms:**\n"
                   "• Usually no visible symptoms\n"
                   "• May cause chest pain (angina)\n"
                   "• Shortness of breath\n"
                   "• Pain in arms, shoulders, or jaw")
    
    return ("**Watch for symptoms** related to your abnormal markers. "
            "Many conditions are asymptomatic initially, so regular monitoring is important.")

def _handle_testing_question(markers: List[Dict[str, Any]], user_prompt: str) -> str:
    """Handle testing and monitoring questions."""
    abnormal_markers = [m for m in markers if m.get("status") != "normal"]
    
    if not abnormal_markers:
        return "Continue with routine annual check-ups as recommended by your healthcare provider."
    
    if len(abnormal_markers) == 1:
        marker = abnormal_markers[0]
        name = marker.get("name", "")
        status = marker.get("status", "")
        
        if name == "FERRITIN" and status == "low":
            return ("**Ferritin testing:**\n"
                   "• Retest in 3-6 months after starting treatment\n"
                   "• Monitor iron levels (serum iron, TIBC)\n"
                   "• Check for underlying causes if levels don't improve")
        
        elif name in ["LDL", "Total Cholesterol"] and status == "high":
            return ("**Cholesterol testing:**\n"
                   "• Retest in 3-6 months after lifestyle changes\n"
                   "• Consider more frequent monitoring if very high\n"
                   "• Monitor other cardiovascular risk factors")
    
    return ("**Testing schedule:**\n"
            "• Follow your doctor's recommended testing schedule\n"
            "• Keep track of your results over time\n"
            "• Discuss any significant changes with your healthcare provider")

def _handle_doctor_question(markers: List[Dict[str, Any]], user_prompt: str) -> str:
    """Handle questions about seeing a doctor."""
    abnormal_markers = [m for m in markers if m.get("status") != "normal"]
    
    if not abnormal_markers:
        return "Since all your markers are within normal ranges, continue with your regular healthcare routine. Schedule your next annual check-up as usual."
    
    # For doctor questions, be direct and specific
    if len(abnormal_markers) == 1:
        marker = abnormal_markers[0]
        name = marker.get("name", "")
        status = marker.get("status", "")
        
        if name == "FERRITIN" and status == "low":
            return ("**Schedule an appointment with your primary care physician** to discuss your low ferritin levels. "
                   "They can help determine the cause and recommend appropriate treatment, which may include iron supplements "
                   "or further testing to identify underlying issues.")
        
        elif name in ["LDL", "Total Cholesterol"] and status == "high":
            return ("**Consult your primary care physician** about your elevated cholesterol. "
                   "They can assess your cardiovascular risk and recommend lifestyle changes or medication if needed.")
    
    # Multiple abnormal markers
    marker_names = [m.get("name", "") for m in abnormal_markers]
    return (f"**Schedule an appointment with your healthcare provider** to discuss your abnormal markers: {', '.join(marker_names)}. "
            "Multiple markers outside normal ranges may indicate underlying health conditions that require medical evaluation.")

def _get_detailed_ferritin_info(markers: List[Dict[str, Any]]) -> str:
    """Provide detailed information about ferritin."""
    ferritin_markers = [m for m in markers if m.get("name", "").upper() == "FERRITIN"]
    
    if not ferritin_markers:
        return "I don't see ferritin data in your current lab results. If you have ferritin concerns, please upload a lab report that includes ferritin levels."
    
    marker = ferritin_markers[0]
    status = marker.get("status", "")
    
    if status == "low":
        return """**Detailed Ferritin Information:**

**What is Ferritin?**
Ferritin is a protein that stores iron in your body. Low ferritin levels indicate iron deficiency, even before anemia develops.

**Your Level:** {value} {unit} (Low - Normal range: 38-380 ng/mL)

**Why This Matters:**
• Iron is essential for oxygen transport in blood
• Low iron can cause fatigue, weakness, and cognitive issues
• Iron deficiency is common, especially in women and vegetarians

**Common Causes:**
• Inadequate dietary iron intake
• Blood loss (heavy periods, gastrointestinal bleeding)
• Poor iron absorption (celiac disease, gastric bypass)
• Pregnancy or breastfeeding

**Treatment Options:**
1. **Dietary Changes:** Increase iron-rich foods
2. **Supplements:** Iron supplements under medical supervision
3. **Address Underlying Causes:** Treat any medical conditions causing blood loss

**Monitoring:** Retest in 3-6 months after starting treatment.""".format(
            value=marker.get("value", ""),
            unit=marker.get("unit", "")
        )
    
    return "Your ferritin levels appear to be within normal range. Continue maintaining a balanced diet with adequate iron intake."

def _get_detailed_cholesterol_info(markers: List[Dict[str, Any]]) -> str:
    """Provide detailed information about cholesterol."""
    cholesterol_markers = [m for m in markers if m.get("name", "").upper() in ["LDL", "HDL", "TOTAL CHOLESTEROL"]]
    
    if not cholesterol_markers:
        return "I don't see cholesterol data in your current lab results. If you have cholesterol concerns, please upload a lab report that includes lipid panel results."
    
    response_parts = ["**Detailed Cholesterol Information:**\n"]
    
    for marker in cholesterol_markers:
        name = marker.get("name", "")
        value = marker.get("value", "")
        unit = marker.get("unit", "")
        status = marker.get("status", "")
        
        response_parts.append(f"**{name}:** {value} {unit} ({status})")
        
        if name == "LDL" and status == "high":
            response_parts.append("• LDL is 'bad' cholesterol that can build up in arteries")
            response_parts.append("• High LDL increases heart disease and stroke risk")
            response_parts.append("• Target: <100 mg/dL for most people")
        
        elif name == "HDL" and status == "low":
            response_parts.append("• HDL is 'good' cholesterol that helps remove LDL")
            response_parts.append("• Low HDL increases cardiovascular risk")
            response_parts.append("• Target: >40 mg/dL for men, >50 mg/dL for women")
    
    response_parts.append("\n**Risk Factors:** Age, family history, diet, exercise, smoking, diabetes")
    response_parts.append("**Treatment:** Lifestyle changes first, then medication if needed")
    
    return "\n".join(response_parts)

def _get_detailed_glucose_info(markers: List[Dict[str, Any]]) -> str:
    """Provide detailed information about glucose."""
    glucose_markers = [m for m in markers if m.get("name", "").upper() in ["GLUCOSE", "BLOOD SUGAR"]]
    
    if not glucose_markers:
        return "I don't see glucose data in your current lab results. If you have blood sugar concerns, please upload a lab report that includes glucose levels."
    
    marker = glucose_markers[0]
    status = marker.get("status", "")
    
    if status == "high":
        return f"""**Detailed Glucose Information:**

**Your Level:** {marker.get('value', '')} {marker.get('unit', '')} (High)

**What This Means:**
• Elevated blood sugar may indicate prediabetes or diabetes
• High glucose can damage blood vessels and organs over time
• Early detection and management is crucial

**Risk Factors:**
• Family history of diabetes
• Overweight or obesity
• Physical inactivity
• Poor diet high in refined carbohydrates

**Symptoms to Watch For:**
• Increased thirst and urination
• Fatigue and blurred vision
• Slow-healing wounds
• Frequent infections

**Management Strategies:**
1. **Diet:** Reduce refined carbs, increase fiber
2. **Exercise:** Regular physical activity
3. **Weight Management:** Achieve and maintain healthy weight
4. **Monitoring:** Regular blood sugar checks
5. **Medical Care:** Consult your doctor for proper management"""

    return "Your glucose levels appear to be within normal range. Continue maintaining a healthy lifestyle."

def _get_detailed_thyroid_info(markers: List[Dict[str, Any]]) -> str:
    """Provide detailed information about thyroid function."""
    thyroid_markers = [m for m in markers if m.get("name", "").upper() in ["TSH", "T4", "T3"]]
    
    if not thyroid_markers:
        return "I don't see thyroid data in your current lab results. If you have thyroid concerns, please upload a lab report that includes thyroid function tests."
    
    response_parts = ["**Detailed Thyroid Information:**\n"]
    
    for marker in thyroid_markers:
        name = marker.get("name", "")
        value = marker.get("value", "")
        unit = marker.get("unit", "")
        status = marker.get("status", "")
        
        response_parts.append(f"**{name}:** {value} {unit} ({status})")
        
        if name == "TSH" and status == "high":
            response_parts.append("• High TSH suggests hypothyroidism (underactive thyroid)")
            response_parts.append("• Common symptoms: fatigue, weight gain, cold intolerance")
        
        elif name == "TSH" and status == "low":
            response_parts.append("• Low TSH suggests hyperthyroidism (overactive thyroid)")
            response_parts.append("• Common symptoms: weight loss, rapid heartbeat, anxiety")
    
    response_parts.append("\n**Treatment:** Thyroid hormone replacement or anti-thyroid medications")
    response_parts.append("**Monitoring:** Regular thyroid function tests")
    
    return "\n".join(response_parts)

def _explain_marker_meaning(markers: List[Dict[str, Any]], user_prompt: str) -> str:
    """Explain what specific markers mean."""
    prompt_lower = user_prompt.lower()
    
    for marker in markers:
        marker_name = marker.get("name", "").lower()
        if marker_name in prompt_lower:
            return _get_marker_explanation(marker)
    
    return "I'm not sure which marker you're asking about. Could you please specify which health marker you'd like me to explain?"

def _explain_causes(markers: List[Dict[str, Any]], user_prompt: str) -> str:
    """Explain potential causes of abnormal markers."""
    prompt_lower = user_prompt.lower()
    
    for marker in markers:
        marker_name = marker.get("name", "").lower()
        if marker_name in prompt_lower:
            return _get_marker_causes(marker)
    
    return "I'm not sure which marker you're asking about. Could you please specify which health marker you'd like me to explain the causes for?"

def _assess_severity(markers: List[Dict[str, Any]], user_prompt: str) -> str:
    """Assess the severity of abnormal markers."""
    prompt_lower = user_prompt.lower()
    
    for marker in markers:
        marker_name = marker.get("name", "").lower()
        if marker_name in prompt_lower:
            return _get_marker_severity(marker)
    
    return "I'm not sure which marker you're asking about. Could you please specify which health marker you'd like me to assess?"

def _get_marker_specific_response(marker: Dict[str, Any], user_prompt: str) -> str:
    """Get a specific response for a particular marker."""
    name = marker.get("name", "")
    value = marker.get("value", "")
    unit = marker.get("unit", "")
    status = marker.get("status", "")
    recommendation = marker.get("recommendation", "")
    
    if status == "normal":
        return f"Your {name} level of {value} {unit} is within the normal range. Continue maintaining your healthy lifestyle!"
    
    # Be more concise for specific marker questions
    response_parts = [f"**{name}:** {value} {unit} ({status})"]
    
    if recommendation:
        response_parts.append(f"\n{recommendation}")
    
    response_parts.append(f"\n**Next steps:** Discuss with your healthcare provider and follow their recommendations.")
    
    return "\n".join(response_parts)

def _get_default_treatment_advice(marker_name: str, status: str) -> str:
    """Get default treatment advice for a marker."""
    if marker_name == "FERRITIN" and status == "low":
        return "Consider iron supplements and dietary changes under medical supervision."
    elif marker_name in ["LDL", "Total Cholesterol"] and status == "high":
        return "Focus on lifestyle changes: diet, exercise, and weight management."
    elif marker_name == "HDL" and status == "low":
        return "Increase physical activity and include healthy fats in your diet."
    elif marker_name == "Glucose" and status == "high":
        return "Monitor carbohydrate intake and increase physical activity."
    elif marker_name in ["HEMOGLOBIN A1C", "HBA1C"] and status == "high":
        return "High HbA1C indicates poor blood sugar control. Focus on diet, exercise, and medication compliance. Work closely with your healthcare team."
    else:
        return "Consult your healthcare provider for personalized treatment recommendations."

def _get_marker_explanation(marker: Dict[str, Any]) -> str:
    """Explain what a specific marker means."""
    name = marker.get("name", "")
    
    explanations = {
        "FERRITIN": "Ferritin is a protein that stores iron in your body. It's the best indicator of iron stores and helps diagnose iron deficiency.",
        "LDL": "LDL (Low-Density Lipoprotein) is often called 'bad cholesterol' because it can build up in artery walls, increasing heart disease risk.",
        "HDL": "HDL (High-Density Lipoprotein) is 'good cholesterol' that helps remove LDL from arteries, protecting against heart disease.",
        "GLUCOSE": "Glucose is your body's main source of energy. High levels may indicate diabetes or prediabetes.",
        "TSH": "TSH (Thyroid-Stimulating Hormone) controls thyroid function. High levels suggest hypothyroidism, low levels suggest hyperthyroidism.",
        "HEMOGLOBIN A1C": "HbA1C (Hemoglobin A1C) measures your average blood sugar over the past 2-3 months. It's the gold standard for diabetes diagnosis and monitoring.",
        "HBA1C": "HbA1C (Hemoglobin A1C) measures your average blood sugar over the past 2-3 months. It's the gold standard for diabetes diagnosis and monitoring."
    }
    
    return explanations.get(name, f"{name} is a health marker that your doctor uses to assess your overall health status.")

def _get_marker_causes(marker: Dict[str, Any]) -> str:
    """Explain potential causes of abnormal markers."""
    name = marker.get("name", "")
    status = marker.get("status", "")
    
    if name == "FERRITIN" and status == "low":
        return "Low ferritin can be caused by: inadequate dietary iron, blood loss (heavy periods, GI bleeding), poor absorption (celiac disease), pregnancy, or chronic inflammation."
    elif name in ["LDL", "Total Cholesterol"] and status == "high":
        return "High cholesterol can be caused by: poor diet (high in saturated fats), lack of exercise, obesity, smoking, diabetes, or genetic factors."
    elif name == "HDL" and status == "low":
        return "Low HDL can be caused by: smoking, obesity, lack of exercise, poor diet, diabetes, or genetic factors."
    elif name == "Glucose" and status == "high":
        return "High glucose can be caused by: poor diet, lack of exercise, obesity, stress, certain medications, or underlying diabetes."
    elif name in ["HEMOGLOBIN A1C", "HBA1C"] and status == "high":
        return "High HbA1C can be caused by: poor diet (high in refined carbs/sugars), lack of exercise, obesity, stress, medication non-compliance, or uncontrolled diabetes."
    
    return f"Abnormal {name} levels can have various causes. Consult your healthcare provider for a thorough evaluation."

def _get_marker_severity(marker: Dict[str, Any]) -> str:
    """Assess the severity of an abnormal marker."""
    name = marker.get("name", "")
    status = marker.get("status", "")
    value = marker.get("value", "")
    
    if name == "FERRITIN" and status == "low":
        if value < 10:
            return "Severe iron deficiency requiring immediate medical attention."
        elif value < 20:
            return "Moderate iron deficiency that should be addressed promptly."
        else:
            return "Mild iron deficiency that can be managed with dietary changes and supplements."
    
    elif name in ["LDL", "Total Cholesterol"] and status == "high":
        if name == "LDL" and value > 190:
            return "Very high LDL requiring aggressive treatment and medical supervision."
        elif name == "LDL" and value > 160:
            return "High LDL requiring lifestyle changes and possibly medication."
        else:
            return "Moderately elevated cholesterol that can often be managed with lifestyle changes."
    elif name in ["HEMOGLOBIN A1C", "HBA1C"] and status == "high":
        if value >= 9.0:
            return "Very high HbA1C indicating poor diabetes control. Requires immediate medical attention and medication adjustment."
        elif value >= 7.0:
            return "High HbA1C indicating suboptimal diabetes control. Requires lifestyle changes and possibly medication adjustment."
        else:
            return "Elevated HbA1C that can often be managed with lifestyle changes and close monitoring."
    
    return f"The severity of your {name} level should be evaluated by your healthcare provider in the context of your overall health."

def _generate_comprehensive_marker_response(markers: List[Dict[str, Any]], user_prompt: str) -> str:
    """Generate a comprehensive response about all markers."""
    abnormal_markers = [m for m in markers if m.get("status") != "normal"]
    normal_markers = [m for m in markers if m.get("status") == "normal"]
    
    if not abnormal_markers:
        return (
            f"All {len(markers)} of your health markers are within normal ranges. "
            "Continue maintaining your healthy lifestyle!"
        )
    
    # Be more concise for general questions
    response_parts = [f"You have {len(abnormal_markers)} marker(s) outside normal range:"]
    
    for marker in abnormal_markers:
        name = marker.get("name", "")
        value = marker.get("value", "")
        unit = marker.get("unit", "")
        status = marker.get("status", "")
        
        response_parts.append(f"• **{name}:** {value} {unit} ({status})")
    
    response_parts.append("\n**Recommendation:** Discuss these results with your healthcare provider for personalized guidance.")
    
    return "\n".join(response_parts)

def _handle_general_health_questions(prompt: str, chat_history: Optional[List[Dict[str, str]]] = None) -> str:
    """Handle general health questions without specific marker data."""
    prompt_lower = prompt.lower()
    
    # Vitamin D specific questions
    if "vitamin d" in prompt_lower:
        if "range" in prompt_lower or "level" in prompt_lower or "normal" in prompt_lower or "ideal" in prompt_lower:
            return """**Vitamin D Normal Ranges:**
• **25-OH Vitamin D:**
  - Deficient: < 20 ng/mL
  - Insufficient: 20-30 ng/mL  
  - Optimal: 30-50 ng/mL
  - High: > 50 ng/mL

**Note:** Ranges may vary by lab. For personalized analysis, upload your lab results."""
    
    # Vitamin C specific questions
    if "vitamin c" in prompt_lower:
        if "range" in prompt_lower or "level" in prompt_lower or "normal" in prompt_lower:
            return """**Vitamin C Normal Ranges:**
• **Serum Vitamin C:**
  - Deficient: < 0.2 mg/dL
  - Low: 0.2-0.4 mg/dL
  - Normal: 0.4-2.0 mg/dL
  - High: > 2.0 mg/dL

**Note:** Ranges may vary by lab. For personalized analysis, upload your lab results."""
    
    # Cholesterol specific questions
    if "cholesterol" in prompt_lower:
        if "range" in prompt_lower or "level" in prompt_lower or "normal" in prompt_lower:
            return """**Cholesterol Normal Ranges:**
• **Total Cholesterol:** < 200 mg/dL
• **HDL (Good):** > 40 mg/dL (men), > 50 mg/dL (women)
• **LDL (Bad):** < 100 mg/dL (optimal), < 130 mg/dL (near optimal)
• **Triglycerides:** < 150 mg/dL

**Note:** Ranges may vary by lab. For personalized analysis, upload your lab results."""
    
    # Blood pressure specific questions
    if "blood pressure" in prompt_lower:
        if "range" in prompt_lower or "normal" in prompt_lower or "ideal" in prompt_lower:
            return """**Blood Pressure Normal Ranges:**
• **Normal:** < 120/80 mmHg
• **Elevated:** 120-129/< 80 mmHg
• **High Blood Pressure (Stage 1):** 130-139/80-89 mmHg
• **High Blood Pressure (Stage 2):** ≥ 140/≥ 90 mmHg

**Note:** For personalized analysis, upload your lab results."""
    
    # Blood sugar/glucose specific questions
    if "blood sugar" in prompt_lower or "glucose" in prompt_lower:
        if "range" in prompt_lower or "normal" in prompt_lower or "ideal" in prompt_lower:
            return """**Blood Sugar Normal Ranges:**
• **Fasting Glucose:** 70-99 mg/dL
• **Postprandial (2 hours):** < 140 mg/dL
• **HbA1c:** < 5.7%

**Note:** Ranges may vary by lab. For personalized analysis, upload your lab results."""
    
    # Thyroid specific questions
    if "thyroid" in prompt_lower or "tsh" in prompt_lower:
        if "range" in prompt_lower or "normal" in prompt_lower or "ideal" in prompt_lower:
            return """**Thyroid Function Normal Ranges:**
• **TSH:** 0.4-4.0 mIU/L
• **Free T4:** 0.8-1.8 ng/dL
• **Free T3:** 2.3-4.2 pg/mL

**Note:** Ranges may vary by lab. For personalized analysis, upload your lab results."""
    
    # Upload/report specific questions
    if "upload" in prompt_lower or "report" in prompt_lower:
        return ("Upload your lab reports using the 'Upload Reports' tab, or manually enter your health markers using the 'Manual Entry' tab. "
                "Once you have data uploaded, I can provide personalized recommendations based on your results.")
    
    # Wearable device questions
    if "wearable" in prompt_lower or "device" in prompt_lower:
        return ("Add wearable device data using the 'Wearable Data' tab. This helps provide more comprehensive health insights "
                "by combining your lab results with activity, heart rate, sleep, and other health metrics.")
    
    # Manual entry questions
    if "manual" in prompt_lower or "enter" in prompt_lower:
        return ("Use the 'Manual Entry' tab to manually input your health markers if OCR doesn't work with your lab report images. "
                "Simply paste the text from your lab report or type your markers in a format like: "
                "'FERRITIN: 22 ng/mL (Low) Normal Range: 38-380 ng/mL'")
    
    # General health information request
    return """I can provide general health information about various markers and their normal ranges. 

**Common health markers I can help with:**
• Vitamin levels (D, C, B12, etc.)
• Cholesterol and lipids
• Blood pressure
• Blood sugar and diabetes markers
• Thyroid function
• Kidney and liver function
• Complete blood count (CBC)
• Electrolytes

**For personalized analysis based on your specific results, please upload your lab reports or use the manual entry feature.**"""

def analyze_health_trends(markers_history: List[List[Dict[str, Any]]]) -> str:
    """Analyze trends in health markers over time."""
    if not markers_history or len(markers_history) < 2:
        return "Insufficient data to analyze trends. Continue monitoring your health markers over time."
    
    # This would be implemented with more sophisticated trend analysis
    # For now, provide a simple response
    return (
        "I can see you have multiple lab reports. To provide trend analysis, "
        "I would need to compare specific markers over time. Consider discussing "
        "trends with your healthcare provider who can access your complete medical history."
    )
