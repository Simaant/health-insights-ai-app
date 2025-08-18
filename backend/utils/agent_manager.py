# backend/utils/agent_manager.py
import os
import re
from typing import Optional, List, Dict, Any
from .rag_manager import rag_manager

# Optional lazy initialization to avoid model download during import time in tests
_model = None

def _get_model():
    global _model
    if _model is None:
        # For development, use a simple text generation approach
        # This avoids downloading large models during startup
        _model = "simple_text_generator"
    return _model

def run_agent(prompt: str, markers: Optional[List[Dict[str, Any]]] = None, chat_history: Optional[List[Dict[str, str]]] = None, user_id: Optional[str] = None) -> str:
    """
    Enhanced intelligent AI agent with RAG capabilities that understands context and provides personalized responses.
    """
    # Normalize the prompt
    prompt_lower = prompt.lower().strip()
    
    # Use RAG to retrieve relevant context if user_id is provided
    if user_id:
        try:
            # Index current markers and chat history for future retrieval
            if markers:
                rag_manager.index_user_markers(user_id, markers, "manual")
            
            if chat_history:
                rag_manager.index_chat_history(user_id, chat_history)
            
            # Retrieve relevant context using RAG
            context = rag_manager.retrieve_relevant_context(user_id, prompt)
            
            # Generate response using RAG-enhanced context
            return _generate_rag_enhanced_response(prompt, markers, chat_history, context, user_id)
            
        except Exception as e:
            print(f"RAG error: {e}")
            # Fallback to original method if RAG fails
            pass
    
    # If we have markers, provide context-aware responses FIRST
    if markers and len(markers) > 0:
        return _generate_intelligent_response(markers, prompt, chat_history)
    
    # Check if this is a general health question that doesn't relate to uploaded markers
    if _is_general_health_question(prompt_lower):
        return _handle_general_health_questions(prompt, chat_history)
    
    # Handle general health questions without specific marker data
    return _handle_general_health_questions(prompt, chat_history)

def _generate_rag_enhanced_response(prompt: str, markers: Optional[List[Dict[str, Any]]], chat_history: Optional[List[Dict[str, str]]], context: Dict[str, Any], user_id: str) -> str:
    """Generate RAG-enhanced responses using retrieved context."""
    prompt_lower = prompt.lower()
    
    # Extract relevant information from RAG context
    user_markers = context.get("user_markers", {})
    medical_knowledge = context.get("medical_knowledge", {})
    chat_context = context.get("chat_history", {})
    
    # Get user's markers from RAG if not provided directly
    if not markers and user_markers.get("documents"):
        markers = _extract_markers_from_rag(user_markers)
    
    # Get medical knowledge for relevant markers
    medical_info = _extract_medical_knowledge(medical_knowledge)
    
    # Analyze the specific question and context
    question_analysis = _analyze_user_question(prompt_lower, markers, chat_history)
    
    # Route to appropriate handler based on question analysis
    if question_analysis["question_type"] == "specific_marker":
        return _handle_specific_marker_question_enhanced(markers, prompt, medical_info, question_analysis, user_id)
    
    if question_analysis["question_type"] == "food_diet":
        return _handle_food_question_enhanced(markers, prompt, medical_info, question_analysis, user_id)
    
    if question_analysis["question_type"] == "testing":
        return _handle_testing_question_enhanced(markers, prompt, medical_info, question_analysis, user_id)
    
    if question_analysis["question_type"] == "general_info":
        return _handle_general_info_question(markers, prompt, medical_info, question_analysis, user_id)
    
    # Default comprehensive response with RAG
    return _generate_comprehensive_marker_response_enhanced(markers, prompt, medical_info, question_analysis, user_id)

def _analyze_user_question(prompt: str, markers: Optional[List[Dict[str, Any]]], chat_history: Optional[List[Dict[str, str]]]) -> Dict[str, Any]:
    """Analyze user question to understand intent and context."""
    prompt_lower = prompt.lower()
    
    # Extract mentioned markers from the question
    mentioned_markers = []
    if markers:
        for marker in markers:
            marker_name = marker.get("name", "").lower()
            marker_words = marker_name.split()
            
            # Check for exact match or partial matches
            if (marker_name in prompt_lower or 
                any(word in prompt_lower for word in marker_words if len(word) > 2)):
                mentioned_markers.append(marker)
    
    # Determine question type
    question_type = "general_info"
    
    if any(word in prompt_lower for word in ["food", "eat", "diet", "nutrition", "vitamin", "supplement"]):
        question_type = "food_diet"
    elif any(word in prompt_lower for word in ["test", "retest", "monitor", "check", "when", "schedule"]):
        question_type = "testing"
    elif mentioned_markers:
        question_type = "specific_marker"
    
    return {
        "question_type": question_type,
        "mentioned_markers": mentioned_markers,
        "prompt": prompt,
        "prompt_lower": prompt_lower
    }

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
    """Check if user is asking about a specific marker - generalized for ANY marker."""
    prompt_lower = prompt.lower()
    
    # Check for ANY marker name mentioned in the prompt
    for marker in markers:
        marker_name = marker.get("name", "").lower()
        
        # Direct name match
        if marker_name in prompt_lower:
            return True
        
        # Check for partial matches (e.g., "cholesterol" matches "Total Cholesterol")
        marker_words = marker_name.split()
        for word in marker_words:
            if len(word) > 3 and word in prompt_lower:  # Only significant words
                return True
    
    return False

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
        "what to eat", "foods to", "dietary", "nutritional", "foods", "vitamin c", 
        "vitamin d", "iron", "ferritin", "supplements", "dietary", "include", "add"
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
    """Handle follow-up questions with context awareness using chat history."""
    prompt_lower = user_prompt.lower()
    
    # Analyze chat history to understand context
    context = _analyze_chat_context(chat_history, markers)
    
    # Check for specific follow-up patterns
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
    
    # Use context from previous messages to provide better responses
    if context.get("previous_topic") == "ferritin" and ("food" in prompt_lower or "vitamin c" in prompt_lower):
        return _handle_food_question(markers, user_prompt)
    
    if context.get("previous_topic") == "diet" and ("supplement" in prompt_lower or "vitamin" in prompt_lower):
        return _handle_supplement_question(markers, user_prompt)
    
    return _generate_comprehensive_marker_response(markers, user_prompt)

def _analyze_chat_context(chat_history: Optional[List[Dict[str, str]]], markers: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze chat history to understand conversation context."""
    if not chat_history:
        return {}
    
    context = {
        "previous_topic": None,
        "mentioned_markers": [],
        "discussed_issues": []
    }
    
    # Look at last few messages for context
    recent_messages = chat_history[-3:] if len(chat_history) >= 3 else chat_history
    
    for message in recent_messages:
        content = message.get("content", "").lower()
        
        # Check for marker mentions
        for marker in markers:
            marker_name = marker.get("name", "").lower()
            if marker_name in content:
                context["mentioned_markers"].append(marker_name)
        
        # Check for topic mentions
        if any(word in content for word in ["ferritin", "iron", "anemia"]):
            context["previous_topic"] = "ferritin"
        elif any(word in content for word in ["food", "diet", "nutrition", "eat"]):
            context["previous_topic"] = "diet"
        elif any(word in content for word in ["supplement", "vitamin", "pill"]):
            context["previous_topic"] = "supplements"
        elif any(word in content for word in ["symptom", "feel", "experience"]):
            context["previous_topic"] = "symptoms"
    
    return context

def _handle_supplement_question(markers: List[Dict[str, Any]], user_prompt: str) -> str:
    """Handle supplement-related questions."""
    prompt_lower = user_prompt.lower()
    
    # Check for specific deficiencies
    iron_deficient = any(m.get("name", "").lower() in ["ferritin", "iron"] and m.get("status") == "low" for m in markers)
    vitamin_d_deficient = any(m.get("name", "").lower() in ["vitamin d", "25-oh vitamin d"] and m.get("status") in ["low", "deficient"] for m in markers)
    
    if iron_deficient:
        return ("## 💊 Iron Supplement Recommendations\n\n"
                "**For Low Ferritin Levels:**\n"
                "• **Iron Supplements:** Ferrous sulfate, ferrous gluconate, or ferrous fumarate\n"
                "• **Dosage:** 30-60mg elemental iron daily (consult your doctor)\n"
                "• **Timing:** Take on empty stomach for best absorption\n"
                "• **With Vitamin C:** Take with orange juice or vitamin C supplement\n"
                "• **Avoid:** Coffee, tea, calcium supplements within 2 hours\n\n"
                "**Important:** Always consult your healthcare provider before starting supplements.")
    
    if vitamin_d_deficient:
        return ("## 💊 Vitamin D Supplement Recommendations\n\n"
                "**For Low Vitamin D Levels:**\n"
                "• **Vitamin D3:** Preferred form for supplementation\n"
                "• **Dosage:** 1000-4000 IU daily (consult your doctor)\n"
                "• **Timing:** Take with fatty foods for better absorption\n"
                "• **Monitor:** Retest levels after 3-6 months\n\n"
                "**Important:** Always consult your healthcare provider before starting supplements.")
    
    return ("## 💊 General Supplement Guidelines\n\n"
            "**Before Taking Supplements:**\n"
            "• **Consult Your Doctor:** Always get medical advice first\n"
            "• **Get Tested:** Know your current levels before supplementing\n"
            "• **Quality Matters:** Choose reputable brands\n"
            "• **Monitor Progress:** Retest levels periodically\n\n"
            "**Remember:** Supplements are not a substitute for a balanced diet.")

def _handle_specific_marker_question(markers: List[Dict[str, Any]], user_prompt: str) -> str:
    """Handle questions about ANY specific marker - completely generalized."""
    prompt_lower = user_prompt.lower()
    
    # Find the most relevant marker mentioned in the prompt
    best_match = None
    best_score = 0
    
    for marker in markers:
        marker_name = marker.get("name", "").lower()
        score = 0
        
        # Direct name match (highest score)
        if marker_name in prompt_lower:
            score += 10
        
        # Partial word matches
        marker_words = marker_name.split()
        for word in marker_words:
            if len(word) > 3 and word in prompt_lower:
                score += 5
        
        # Check for common variations
        if any(variation in prompt_lower for variation in ['level', 'value', 'result', 'test']):
            score += 2
        
        if score > best_score:
            best_score = score
            best_match = marker
    
    # If we found a good match, provide specific response
    if best_match and best_score >= 5:
        return _get_marker_specific_response(best_match, user_prompt)
    
    # If no specific marker found, provide comprehensive response
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
    
    return ("## 🏥 Treatment Approach\n\n"
            "**Step-by-Step Plan:**\n"
            "1. **Prioritize Critical Markers:** Address the most concerning results first\n"
            "2. **Lifestyle Modifications:** Implement diet and exercise changes\n"
            "3. **Medical Intervention:** Consider medications if lifestyle changes aren't sufficient\n"
            "4. **Regular Monitoring:** Schedule follow-up tests and appointments\n\n"
            "**Important:** Always consult your healthcare provider for personalized treatment plans.")

def _handle_food_question(markers: List[Dict[str, Any]], user_prompt: str) -> str:
    """Handle diet and nutrition questions with personalized recommendations based on user's markers."""
    prompt_lower = user_prompt.lower()
    abnormal_markers = [m for m in markers if m.get("status") != "normal"]
    
    # Check for specific nutrient deficiencies
    iron_deficient = any(m.get("name", "").lower() in ["ferritin", "iron"] and m.get("status") == "low" for m in markers)
    vitamin_d_deficient = any(m.get("name", "").lower() in ["vitamin d", "25-oh vitamin d"] and m.get("status") in ["low", "deficient"] for m in markers)
    vitamin_b12_deficient = any(m.get("name", "").lower() in ["vitamin b12", "b12"] and m.get("status") in ["low", "deficient"] for m in markers)
    vitamin_c_mentioned = "vitamin c" in prompt_lower or "vit c" in prompt_lower
    
    # Build personalized recommendations
    recommendations = []
    
    if iron_deficient:
        recommendations.append("🥩 **Iron-Rich Foods for Low Ferritin**\n\n"
                              "**High-Iron Foods:**\n"
                              "• Red Meat: Lean beef, lamb, and pork\n"
                              "• Poultry: Chicken and turkey (dark meat)\n"
                              "• Fish: Tuna, salmon, and sardines\n"
                              "• Legumes: Beans, lentils, and chickpeas\n"
                              "• Dark Leafy Greens: Spinach, kale, and Swiss chard\n"
                              "• Fortified Foods: Cereals, breads, and pasta\n\n"
                              "**Enhance Iron Absorption:**\n"
                              "• Vitamin C Foods: Citrus fruits, bell peppers, tomatoes\n"
                              "• Avoid with Coffee/Tea: Wait 1-2 hours after meals\n"
                              "• Cook in Cast Iron: Can increase iron content\n\n"
                              "**Recommended Daily Intake:** 18mg for women, 8mg for men")
    
    if vitamin_c_mentioned and iron_deficient:
        recommendations.append("🍊 **Vitamin C Foods for Iron Absorption**\n\n"
                              "**Best Vitamin C Sources:**\n"
                              "• Citrus Fruits: Oranges, grapefruits, lemons, limes\n"
                              "• Bell Peppers: Red, yellow, and green peppers\n"
                              "• Berries: Strawberries, raspberries, blueberries\n"
                              "• Tropical Fruits: Kiwi, pineapple, mango\n"
                              "• Vegetables: Broccoli, Brussels sprouts, tomatoes\n"
                              "• Leafy Greens: Spinach, kale, and mustard greens\n\n"
                              "**Pro Tip:** Eat vitamin C foods with iron-rich meals to boost absorption by up to 3x!")
    
    if vitamin_d_deficient:
        recommendations.append("## 🐟 Vitamin D Sources\n\n"
                              "**Food Sources:**\n"
                              "• **Fatty Fish:** Salmon, tuna, mackerel, sardines\n"
                              "• **Egg Yolks:** From pasture-raised chickens\n"
                              "• **Fortified Dairy:** Milk, yogurt, and cheese\n"
                              "• **Mushrooms:** Exposed to UV light\n"
                              "• **Fortified Plant Milk:** Almond, soy, oat milk\n\n"
                              "**Sunlight:** 10-15 minutes daily on arms/face")
    
    if vitamin_b12_deficient:
        recommendations.append("## 🥩 Vitamin B12 Sources\n\n"
                              "**Animal Sources:**\n"
                              "• **Meat:** Beef, pork, lamb, and poultry\n"
                              "• **Fish:** Salmon, tuna, trout, and sardines\n"
                              "• **Eggs:** Especially the yolks\n"
                              "• **Dairy:** Milk, cheese, and yogurt\n\n"
                              "**Fortified Sources:**\n"
                              "• **Plant Milks:** Almond, soy, oat milk\n"
                              "• **Cereals:** Fortified breakfast cereals\n"
                              "• **Nutritional Yeast:** Great for vegetarians")
    
    # If we have specific recommendations, return them
    if recommendations:
        return "\n\n".join(recommendations)
    
    # General dietary advice if no specific deficiencies
    if not abnormal_markers:
        return "## ✅ All Markers Normal\n\nSince all your markers are normal, maintain a balanced diet with plenty of fruits, vegetables, lean proteins, and whole grains."
    
    return ("🍎 **General Dietary Recommendations**\n\n"
            "**Balanced Nutrition Guidelines:**\n"
            "• Whole Foods: Focus on fresh fruits, vegetables, whole grains, and lean proteins\n"
            "• Reduce Processed Foods: Limit packaged foods, added sugars, and refined carbohydrates\n"
            "• Healthy Fats: Include nuts, seeds, olive oil, and fatty fish\n"
            "• Fiber: Aim for 25-30 grams of fiber daily from fruits, vegetables, and whole grains\n\n"
            "**Daily Recommendations:**\n"
            "• Proteins: Lean meats, fish, eggs, legumes, and plant-based proteins\n"
            "• Vegetables: Aim for 2-3 cups daily, including leafy greens\n"
            "• Fruits: 1-2 servings daily, focusing on low-sugar options\n"
            "• Hydration: Drink 8-10 glasses of water daily\n\n"
            "**Next Steps:**\n"
            "Consider consulting a registered dietitian for personalized meal planning and guidance.")

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
            return ("🩸 **Ferritin Testing Schedule**\n\n"
                   "**Recommended Testing:**\n"
                   "• Retest in 3-6 months after starting treatment\n"
                   "• Monitor iron levels (serum iron, TIBC)\n"
                   "• Check for underlying causes if levels don't improve\n\n"
                   "**What to Expect:**\n"
                   "• Ferritin levels should increase with proper treatment\n"
                   "• Your doctor may also check complete blood count (CBC)\n"
                   "• Follow-up testing helps monitor treatment effectiveness")
        
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
    """Get a specific response for ANY marker - completely generalized with proper formatting."""
    name = marker.get("name", "")
    value = marker.get("value", "")
    unit = marker.get("unit", "")
    status = marker.get("status", "")
    recommendation = marker.get("recommendation", "")
    normal_range = marker.get("normal_range", {})
    
    # Build comprehensive response with proper formatting
    response_parts = []
    
    # Header with marker info
    response_parts.append(f"## 📊 {name} Analysis")
    response_parts.append("")
    response_parts.append("**Your Results:**")
    response_parts.append(f"• **Value:** {value} {unit}")
    response_parts.append(f"• **Status:** {status.upper()}")
    
    # Add normal range if available
    if normal_range:
        min_val = normal_range.get('min')
        max_val = normal_range.get('max')
        if min_val is not None and max_val is not None:
            response_parts.append(f"• **Normal Range:** {min_val}-{max_val} {unit}")
        elif min_val is not None:
            response_parts.append(f"• **Normal Range:** >{min_val} {unit}")
        elif max_val is not None:
            response_parts.append(f"• **Normal Range:** <{max_val} {unit}")
    
    response_parts.append("")
    
    # Add intelligent explanation
    explanation = _get_generalized_marker_explanation(marker)
    response_parts.append("## 📋 What This Means")
    response_parts.append(explanation)
    response_parts.append("")
    
    # Add intelligent severity assessment
    severity = _get_generalized_severity(marker)
    response_parts.append("## ⚠️ Severity Assessment")
    response_parts.append(severity)
    response_parts.append("")
    
    # Add intelligent causes if abnormal
    if status != "normal":
        causes = _get_generalized_causes(marker)
        response_parts.append("## 🔍 Possible Causes")
        response_parts.append(causes)
        response_parts.append("")
        
        # Add intelligent treatment advice
        treatment = _get_generalized_treatment(marker)
        response_parts.append("## 💊 Treatment Approach")
        response_parts.append(treatment)
        response_parts.append("")
    
    # Add recommendation if available
    if recommendation:
        response_parts.append("## 💡 Recommendations")
        response_parts.append(recommendation)
        response_parts.append("")
    
    # Add next steps
    response_parts.append("## 🎯 Next Steps")
    response_parts.append("Discuss these results with your healthcare provider for personalized guidance.")
    
    return "\n".join(response_parts)

def _get_generalized_marker_explanation(marker: Dict[str, Any]) -> str:
    """Provide intelligent explanation for ANY marker."""
    name = marker.get("name", "")
    value = marker.get("value", "")
    unit = marker.get("unit", "")
    
    # Try to get specific explanation first
    specific_explanation = _get_marker_explanation(marker)
    if specific_explanation and "is a health marker" not in specific_explanation:
        return specific_explanation
    
    # Provide intelligent general explanation
    if "cholesterol" in name.lower():
        return f"{name} is a type of fat in your blood that your body uses for energy and cell building. High levels can increase heart disease risk."
    elif "glucose" in name.lower() or "sugar" in name.lower():
        return f"{name} is your body's main source of energy. It comes from the food you eat and is regulated by insulin."
    elif "hemoglobin" in name.lower():
        return f"{name} is a protein in red blood cells that carries oxygen throughout your body."
    elif "creatinine" in name.lower():
        return f"{name} is a waste product filtered by your kidneys. It's used to assess kidney function."
    elif "ferritin" in name.lower():
        return f"{name} is a protein that stores iron in your body. It's the best indicator of iron stores."
    else:
        return f"{name} is a health marker that your doctor uses to assess your overall health status. Your level of {value} {unit} helps determine if this marker is within normal ranges."

def _get_generalized_severity(marker: Dict[str, Any]) -> str:
    """Provide intelligent severity assessment for ANY marker."""
    name = marker.get("name", "")
    value = marker.get("value", "")
    status = marker.get("status", "")
    normal_range = marker.get("normal_range", {})
    
    if status == "normal":
        return f"Your {name} level is within normal range and doesn't require immediate attention."
    
    # Calculate how far from normal
    min_val = normal_range.get('min')
    max_val = normal_range.get('max')
    
    if status == "high" and max_val:
        deviation = ((value - max_val) / max_val) * 100
        if deviation > 50:
            return f"Your {name} level is significantly elevated ({deviation:.0f}% above normal). This requires prompt medical attention."
        elif deviation > 20:
            return f"Your {name} level is moderately elevated ({deviation:.0f}% above normal). This should be addressed with lifestyle changes and medical guidance."
        else:
            return f"Your {name} level is slightly elevated. This can often be managed with lifestyle modifications."
    
    elif status == "low" and min_val:
        deviation = ((min_val - value) / min_val) * 100
        if deviation > 50:
            return f"Your {name} level is significantly low ({deviation:.0f}% below normal). This requires prompt medical attention."
        elif deviation > 20:
            return f"Your {name} level is moderately low ({deviation:.0f}% below normal). This should be addressed with dietary changes and medical guidance."
        else:
            return f"Your {name} level is slightly low. This can often be managed with dietary modifications."
    
    else:
        return f"Your {name} level appears to be outside normal ranges. The severity should be evaluated by your healthcare provider."

def _get_generalized_causes(marker: Dict[str, Any]) -> str:
    """Provide intelligent causes for ANY abnormal marker."""
    name = marker.get("name", "")
    status = marker.get("status", "")
    
    if status == "high":
        return f"High {name} levels can be caused by: poor diet, lack of exercise, obesity, stress, certain medications, genetic factors, or underlying medical conditions. Consult your healthcare provider for a thorough evaluation."
    elif status == "low":
        return f"Low {name} levels can be caused by: inadequate nutrition, poor absorption, blood loss, certain medications, genetic factors, or underlying medical conditions. Consult your healthcare provider for a thorough evaluation."
    else:
        return f"Abnormal {name} levels can have various causes. A comprehensive evaluation by your healthcare provider is recommended."

def _get_generalized_treatment(marker: Dict[str, Any]) -> str:
    """Provide intelligent treatment advice for ANY abnormal marker."""
    name = marker.get("name", "")
    status = marker.get("status", "")
    
    # Try specific treatment first
    specific_treatment = _get_default_treatment_advice(name, status)
    if specific_treatment and "Consult your healthcare provider" not in specific_treatment:
        return specific_treatment
    
    # Provide generalized treatment advice
    if status == "high":
        return f"For high {name} levels: focus on lifestyle changes (diet, exercise, weight management), reduce stress, and consider medication if lifestyle changes aren't sufficient. Always work with your healthcare provider for personalized treatment."
    elif status == "low":
        return f"For low {name} levels: focus on dietary improvements, consider supplements under medical supervision, and address any underlying causes. Always work with your healthcare provider for personalized treatment."
    else:
        return f"For abnormal {name} levels: implement lifestyle changes, consider dietary modifications, and work closely with your healthcare provider for personalized treatment recommendations."

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
    """Generate a comprehensive response about all markers with proper formatting."""
    abnormal_markers = [m for m in markers if m.get("status") != "normal"]
    normal_markers = [m for m in markers if m.get("status") == "normal"]
    
    if not abnormal_markers:
        return (
            f"## ✅ All Markers Normal\n\n"
            f"Great news! All {len(markers)} of your health markers are within normal ranges.\n\n"
            "**Keep up the good work:** Continue maintaining your healthy lifestyle!"
        )
    
    # Build response for abnormal markers
    response_parts = []
    response_parts.append(f"## 📊 Health Markers Summary")
    response_parts.append(f"**Analysis of {len(markers)} Health Markers**")
    response_parts.append("")
    
    if abnormal_markers:
        response_parts.append(f"## ⚠️ Abnormal Markers ({len(abnormal_markers)})")
        for marker in abnormal_markers:
            name = marker.get("name", "")
            value = marker.get("value", "")
            unit = marker.get("unit", "")
            status = marker.get("status", "")
            response_parts.append(f"• **{name}:** {value} {unit} ({status.upper()})")
        response_parts.append("")
    
    if normal_markers:
        response_parts.append(f"## ✅ Normal Markers ({len(normal_markers)})")
        for marker in normal_markers:
            name = marker.get("name", "")
            value = marker.get("value", "")
            unit = marker.get("unit", "")
            response_parts.append(f"• **{name}:** {value} {unit}")
        response_parts.append("")
    
    response_parts.append("## 💡 Recommendations")
    response_parts.append("• **Prioritize Abnormal Markers:** Focus on addressing the concerning results first")
    response_parts.append("• **Lifestyle Changes:** Implement diet and exercise modifications")
    response_parts.append("• **Medical Consultation:** Consider consulting your healthcare provider")
    response_parts.append("• **Follow-up Testing:** Schedule repeat testing as recommended")
    response_parts.append("")
    response_parts.append("**Next Steps:** Discuss these results with your healthcare provider for personalized guidance.")
    
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
        return ("## 📋 How to Get Personalized Analysis\n\n"
                "**To provide you with personalized recommendations, please:**\n\n"
                "1. **Upload Reports:** Use the 'Upload Reports' tab to upload your lab results\n"
                "2. **Manual Entry:** Use the 'Manual Entry' tab to input your health markers\n\n"
                "**Once you have data uploaded, I can:**\n"
                "• Analyze your specific results\n"
                "• Provide personalized recommendations\n"
                "• Answer questions about your health markers\n"
                "• Suggest lifestyle modifications\n\n"
                "**Ready to get started?** Upload your data and ask me anything about your health!")
    
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

# RAG Helper Functions
def _extract_markers_from_rag(user_markers: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract marker information from RAG results."""
    markers = []
    if not user_markers.get("documents"):
        return markers
    
    for i, doc in enumerate(user_markers["documents"]):
        metadata = user_markers["metadatas"][i] if i < len(user_markers["metadatas"]) else {}
        
        # Parse marker information from document
        marker_info = {
            "name": metadata.get("marker_name", "Unknown"),
            "value": metadata.get("marker_value", ""),
            "status": metadata.get("marker_status", "normal"),
            "source": metadata.get("source", "unknown")
        }
        
        # Extract additional info from document text
        if "Normal Range:" in doc:
            marker_info["normal_range"] = doc.split("Normal Range:")[1].split("\n")[0].strip()
        
        if "Recommendation:" in doc:
            marker_info["recommendation"] = doc.split("Recommendation:")[1].split("\n")[0].strip()
        
        markers.append(marker_info)
    
    return markers

def _extract_medical_knowledge(medical_knowledge: Dict[str, Any]) -> Dict[str, Any]:
    """Extract medical knowledge from RAG results."""
    knowledge = {}
    if not medical_knowledge.get("documents"):
        return knowledge
    
    for i, doc in enumerate(medical_knowledge["documents"]):
        metadata = medical_knowledge["metadatas"][i] if i < len(medical_knowledge["metadatas"]) else {}
        marker_name = metadata.get("marker", "unknown")
        
        if marker_name not in knowledge:
            knowledge[marker_name] = []
        
        knowledge[marker_name].append(doc)
    
    return knowledge

def _handle_specific_marker_question_enhanced(markers: Optional[List[Dict[str, Any]]], prompt: str, medical_info: Dict[str, Any], question_analysis: Dict[str, Any], user_id: str) -> str:
    """Handle specific marker questions with enhanced context understanding."""
    prompt_lower = question_analysis["prompt_lower"]
    mentioned_markers = question_analysis["mentioned_markers"]
    
    # If no markers mentioned in question, try to find from user data
    if not mentioned_markers and markers:
        # Find the most relevant marker based on the question
        best_match = None
        best_score = 0
        
        for marker in markers:
            marker_name = marker.get("name", "").lower()
            score = 0
            
            # Check for exact match
            if marker_name in prompt_lower:
                score += 10
            
            # Check for partial matches
            marker_words = marker_name.split()
            for word in marker_words:
                if len(word) > 2 and word in prompt_lower:
                    score += 5
            
            # Check for synonyms
            synonyms = _get_marker_synonyms(marker_name)
            for synonym in synonyms:
                if synonym in prompt_lower:
                    score += 8
            
            if score > best_score:
                best_score = score
                best_match = marker
        
        if best_match and best_score >= 5:
            mentioned_markers = [best_match]
    
    # If still no markers found, search RAG
    if not mentioned_markers:
        try:
            search_results = rag_manager.search_similar_markers(user_id, prompt)
            if search_results.get("documents"):
                rag_markers = _extract_markers_from_rag(search_results)
                if rag_markers:
                    mentioned_markers = rag_markers[:1]  # Take the most relevant one
        except:
            pass
    
    if not mentioned_markers:
        return _handle_unknown_marker_question(prompt, medical_info)
    
    # Generate response for the most relevant marker
    target_marker = mentioned_markers[0]
    return _get_marker_specific_response_enhanced(target_marker, prompt, medical_info, question_analysis)

def _get_marker_specific_response_enhanced(marker: Dict[str, Any], prompt: str, medical_info: Dict[str, Any], question_analysis: Dict[str, Any]) -> str:
    """Get a specific response for a marker with enhanced formatting."""
    name = marker.get("name", "")
    value = marker.get("value", "")
    unit = marker.get("unit", "")
    status = marker.get("status", "")
    normal_range = marker.get("normal_range", "")
    medical_knowledge = medical_info.get(name.lower(), [])
    
    response_parts = []
    response_parts.append(f"📊 **{name} Analysis**")
    response_parts.append("")
    
    # Results section
    response_parts.append("**Your Results:**")
    response_parts.append(f"• Value: {value} {unit}")
    response_parts.append(f"• Status: {status.upper()}")
    if normal_range:
        response_parts.append(f"• Normal Range: {normal_range}")
    response_parts.append("")
    
    # Medical information section
    if medical_knowledge:
        response_parts.append("📋 **Medical Information**")
        for knowledge in medical_knowledge[:2]:
            response_parts.append(knowledge)
        response_parts.append("")
    
    # Personalized recommendations based on status
    if status != "normal":
        response_parts.append("💡 **Personalized Recommendations**")
        
        if "low" in status.lower():
            response_parts.append("Based on your low levels, consider:")
            response_parts.append("• Dietary Changes: Focus on foods rich in this nutrient")
            response_parts.append("• Supplements: Consider supplementation under medical supervision")
            response_parts.append("• Lifestyle: Address underlying causes")
        elif "high" in status.lower():
            response_parts.append("Based on your elevated levels, consider:")
            response_parts.append("• Medical Evaluation: Consult your healthcare provider")
            response_parts.append("• Monitoring: Regular follow-up testing")
            response_parts.append("• Lifestyle: Address contributing factors")
        
        response_parts.append("")
    
    # Next steps
    response_parts.append("🎯 **Next Steps**")
    response_parts.append("Discuss these results with your healthcare provider for personalized guidance.")
    
    return "\n".join(response_parts)

def _get_marker_synonyms(marker_name: str) -> List[str]:
    """Get synonyms for common medical markers."""
    synonyms = {
        "ferritin": ["iron", "iron stores", "iron level", "iron deficiency"],
        "vitamin d": ["vit d", "25-oh vitamin d", "25-hydroxyvitamin d", "vitamin d3"],
        "vitamin b12": ["b12", "cobalamin", "vitamin b-12"],
        "cholesterol": ["total cholesterol", "hdl", "ldl", "lipids"],
        "glucose": ["blood sugar", "blood glucose", "sugar"],
        "tsh": ["thyroid stimulating hormone", "thyroid", "thyroid function"],
        "hemoglobin": ["hgb", "hb", "red blood cells"],
        "creatinine": ["kidney function", "renal function", "kidney"],
        "alt": ["alanine aminotransferase", "liver function", "liver"],
        "ast": ["aspartate aminotransferase", "liver function", "liver"]
    }
    return synonyms.get(marker_name.lower(), [])

def _handle_unknown_marker_question(prompt: str, medical_info: Dict[str, Any]) -> str:
    """Handle questions about markers not in user's data."""
    prompt_lower = prompt.lower()
    
    # Check if we have medical knowledge about this marker
    for marker_name, knowledge in medical_info.items():
        if marker_name.lower() in prompt_lower:
            return _get_general_marker_info(marker_name, knowledge)
    
    return ("## 🔍 Marker Not Found\n\n"
            "I don't see this marker in your uploaded data. To get personalized analysis:\n\n"
            "**Options:**\n"
            "• **Upload Lab Report:** Use the 'Upload Reports' tab to add your lab results\n"
            "• **Manual Entry:** Use the 'Manual Entry' tab to input your marker values\n"
            "• **Ask General Question:** I can provide general information about health markers\n\n"
            "**What would you like to do?**")

def _get_marker_specific_response_rag(marker: Dict[str, Any], prompt: str, medical_info: Dict[str, Any]) -> str:
    """Get a specific response for a marker with RAG context."""
    name = marker.get("name", "")
    value = marker.get("value", "")
    status = marker.get("status", "")
    medical_knowledge = medical_info.get(name.lower(), [])
    
    response_parts = []
    response_parts.append(f"📊 **{name} Analysis**")
    response_parts.append("")
    response_parts.append("**Your Results:**")
    response_parts.append(f"• Value: {value}")
    response_parts.append(f"• Status: {status.upper()}")
    
    # Add medical knowledge if available
    if medical_knowledge:
        response_parts.append("")
        response_parts.append("📋 **Medical Information**")
        for knowledge in medical_knowledge[:2]:  # Limit to 2 most relevant pieces
            response_parts.append(knowledge)
    
    # Add personalized recommendations
    if status != "normal":
        response_parts.append("")
        response_parts.append("💡 **Personalized Recommendations**")
        response_parts.append("Based on your results, consider:")
        
        if "low" in status.lower():
            response_parts.append("• Dietary Changes: Focus on foods rich in this nutrient")
            response_parts.append("• Supplements: Consider supplementation under medical supervision")
            response_parts.append("• Lifestyle: Address underlying causes")
        elif "high" in status.lower():
            response_parts.append("• Medical Evaluation: Consult your healthcare provider")
            response_parts.append("• Monitoring: Regular follow-up testing")
            response_parts.append("• Lifestyle: Address contributing factors")
    
    response_parts.append("")
    response_parts.append("🎯 **Next Steps**")
    response_parts.append("Discuss these results with your healthcare provider for personalized guidance.")
    
    return "\n".join(response_parts)

def _get_general_marker_info(marker_name: str, knowledge: List[str]) -> str:
    """Get general information about a marker from medical knowledge."""
    response_parts = []
    response_parts.append(f"## 📋 {marker_name.upper()} Information")
    response_parts.append("")
    
    for info in knowledge[:3]:  # Limit to 3 most relevant pieces
        response_parts.append(info)
        response_parts.append("")
    
    response_parts.append("**Note:** For personalized analysis, please upload your lab results or use manual entry.")
    
    return "\n".join(response_parts)

def _generate_comprehensive_marker_response_rag(markers: Optional[List[Dict[str, Any]]], prompt: str, medical_info: Dict[str, Any], user_id: str) -> str:
    """Generate comprehensive response with RAG context."""
    if not markers:
        return _handle_unknown_marker_question(prompt, medical_info)
    
    abnormal_markers = [m for m in markers if m.get("status") != "normal"]
    normal_markers = [m for m in markers if m.get("status") == "normal"]
    
    if not abnormal_markers:
        return ("## ✅ All Markers Normal\n\n"
                f"Great news! All {len(markers)} of your health markers are within normal ranges.\n\n"
                "**Keep up the good work:** Continue maintaining your healthy lifestyle!")
    
    response_parts = []
    response_parts.append(f"📊 **Health Markers Summary**")
    response_parts.append(f"Analysis of {len(markers)} Health Markers")
    response_parts.append("")
    
    if abnormal_markers:
        response_parts.append(f"⚠️ **Abnormal Markers ({len(abnormal_markers)})**")
        for marker in abnormal_markers:
            name = marker.get("name", "")
            value = marker.get("value", "")
            status = marker.get("status", "")
            response_parts.append(f"• {name}: {value} ({status.upper()})")
        response_parts.append("")
    
    if normal_markers:
        response_parts.append(f"✅ **Normal Markers ({len(normal_markers)})**")
        for marker in normal_markers:
            name = marker.get("name", "")
            value = marker.get("value", "")
            response_parts.append(f"• {name}: {value}")
        response_parts.append("")
    
    response_parts.append("💡 **Recommendations**")
    response_parts.append("• Prioritize Abnormal Markers: Focus on addressing the concerning results first")
    response_parts.append("• Lifestyle Changes: Implement diet and exercise modifications")
    response_parts.append("• Medical Consultation: Consider consulting your healthcare provider")
    response_parts.append("• Follow-up Testing: Schedule repeat testing as recommended")
    response_parts.append("")
    response_parts.append("**Next Steps:** Discuss these results with your healthcare provider for personalized guidance.")
    
    return "\n".join(response_parts)

# Placeholder functions for other RAG handlers (to be implemented as needed)
def _handle_doctor_question_rag(markers, prompt, medical_info, user_id):
    return _handle_doctor_question(markers or [], prompt)

def _handle_treatment_question_rag(markers, prompt, medical_info, user_id):
    return _handle_treatment_question(markers or [], prompt)

def _handle_food_question_enhanced(markers: Optional[List[Dict[str, Any]]], prompt: str, medical_info: Dict[str, Any], question_analysis: Dict[str, Any], user_id: str) -> str:
    """Handle food and diet questions with enhanced context understanding."""
    prompt_lower = question_analysis["prompt_lower"]
    mentioned_markers = question_analysis["mentioned_markers"]
    
    # If specific markers mentioned, provide targeted food advice
    if mentioned_markers:
        target_marker = mentioned_markers[0]
        marker_name = target_marker.get("name", "").lower()
        status = target_marker.get("status", "")
        
        if "cholesterol" in marker_name:
            if "low" in status:
                return _get_cholesterol_food_advice_low()
            elif "high" in status:
                return _get_cholesterol_food_advice_high()
            else:
                return _get_cholesterol_food_advice_general()
        
        elif "ferritin" in marker_name or "iron" in marker_name:
            if "low" in status:
                return _get_iron_food_advice_low()
            else:
                return _get_iron_food_advice_general()
        
        elif "vitamin d" in marker_name:
            if "low" in status:
                return _get_vitamin_d_food_advice_low()
            else:
                return _get_vitamin_d_food_advice_general()
        
        elif "glucose" in marker_name or "blood sugar" in marker_name:
            if "high" in status:
                return _get_glucose_food_advice_high()
            else:
                return _get_glucose_food_advice_general()
    
    # If no specific markers mentioned, provide general advice
    return _get_general_food_advice()

def _get_cholesterol_food_advice_low() -> str:
    """Get food advice for low cholesterol."""
    return ("🥩 **Foods for Low Cholesterol**\n\n"
            "**Foods to Include:**\n"
            "• Healthy Fats: Avocados, nuts, seeds, olive oil\n"
            "• Fatty Fish: Salmon, tuna, mackerel, sardines\n"
            "• Eggs: Whole eggs in moderation\n"
            "• Dairy: Full-fat dairy products\n"
            "• Coconut: Coconut oil, coconut milk\n\n"
            "**Foods to Avoid:**\n"
            "• Trans fats: Processed foods, fried foods\n"
            "• Excessive sugar: Sugary drinks, desserts\n\n"
            "**Note:** Low cholesterol is usually beneficial, but consult your doctor if levels are extremely low.")

def _get_cholesterol_food_advice_high() -> str:
    """Get food advice for high cholesterol."""
    return ("🥗 **Foods for High Cholesterol**\n\n"
            "**Foods to Include:**\n"
            "• Fiber-Rich Foods: Oats, beans, lentils, fruits, vegetables\n"
            "• Omega-3 Sources: Fatty fish, walnuts, flaxseeds\n"
            "• Plant Sterols: Fortified margarines, nuts\n"
            "• Lean Proteins: Skinless poultry, fish, legumes\n\n"
            "**Foods to Limit:**\n"
            "• Saturated Fats: Red meat, full-fat dairy, butter\n"
            "• Trans Fats: Processed foods, fried foods\n"
            "• Added Sugars: Sugary drinks, desserts\n\n"
            "**Lifestyle Tips:**\n"
            "• Exercise regularly (150 minutes/week)\n"
            "• Maintain a healthy weight\n"
            "• Consider medication if lifestyle changes aren't sufficient")

def _get_cholesterol_food_advice_general() -> str:
    """Get general cholesterol food advice."""
    return ("🥗 **Cholesterol-Friendly Diet**\n\n"
            "**Heart-Healthy Foods:**\n"
            "• Fiber: Oats, beans, fruits, vegetables\n"
            "• Omega-3: Fatty fish, walnuts, flaxseeds\n"
            "• Healthy Fats: Olive oil, avocados, nuts\n"
            "• Lean Proteins: Fish, poultry, legumes\n\n"
            "**Foods to Limit:**\n"
            "• Saturated fats: Red meat, full-fat dairy\n"
            "• Trans fats: Processed foods, fried foods\n"
            "• Added sugars: Sugary drinks, desserts\n\n"
            "**General Guidelines:**\n"
            "• Focus on whole, unprocessed foods\n"
            "• Include plenty of fruits and vegetables\n"
            "• Choose lean protein sources\n"
            "• Limit processed and fried foods")

def _get_iron_food_advice_low() -> str:
    """Get food advice for low iron/ferritin."""
    return ("🥩 **Iron-Rich Foods for Low Ferritin**\n\n"
            "**High-Iron Foods:**\n"
            "• Red Meat: Lean beef, lamb, and pork\n"
            "• Poultry: Chicken and turkey (dark meat)\n"
            "• Fish: Tuna, salmon, and sardines\n"
            "• Legumes: Beans, lentils, and chickpeas\n"
            "• Dark Leafy Greens: Spinach, kale, and Swiss chard\n"
            "• Fortified Foods: Cereals, breads, and pasta\n\n"
            "**Enhance Iron Absorption:**\n"
            "• Vitamin C Foods: Citrus fruits, bell peppers, tomatoes\n"
            "• Avoid with Coffee/Tea: Wait 1-2 hours after meals\n"
            "• Cook in Cast Iron: Can increase iron content\n\n"
            "**Recommended Daily Intake:** 18mg for women, 8mg for men")

def _get_iron_food_advice_general() -> str:
    """Get general iron food advice."""
    return ("🥩 **Iron-Rich Diet**\n\n"
            "**Good Iron Sources:**\n"
            "• Animal Sources: Red meat, poultry, fish\n"
            "• Plant Sources: Beans, lentils, spinach, fortified cereals\n"
            "• Absorption Boosters: Vitamin C-rich foods\n\n"
            "**Tips for Better Absorption:**\n"
            "• Pair iron foods with vitamin C\n"
            "• Avoid coffee/tea with meals\n"
            "• Cook in cast iron pans")

def _get_vitamin_d_food_advice_low() -> str:
    """Get food advice for low vitamin D."""
    return ("🐟 **Vitamin D-Rich Foods**\n\n"
            "**Food Sources:**\n"
            "• Fatty Fish: Salmon, tuna, mackerel, sardines\n"
            "• Egg Yolks: From pasture-raised chickens\n"
            "• Fortified Dairy: Milk, yogurt, cheese\n"
            "• Mushrooms: Exposed to UV light\n"
            "• Fortified Plant Milk: Almond, soy, oat milk\n\n"
            "**Additional Sources:**\n"
            "• Sunlight: 10-15 minutes daily on arms/face\n"
            "• Supplements: Consider vitamin D3 supplements\n\n"
            "**Note:** Food sources alone may not be sufficient for low levels")

def _get_vitamin_d_food_advice_general() -> str:
    """Get general vitamin D food advice."""
    return ("🐟 **Vitamin D Sources**\n\n"
            "**Food Sources:**\n"
            "• Fatty Fish: Salmon, tuna, mackerel\n"
            "• Egg Yolks: Especially from pasture-raised chickens\n"
            "• Fortified Foods: Milk, cereals, plant milks\n"
            "• Mushrooms: UV-exposed varieties\n\n"
            "**Lifestyle:**\n"
            "• Moderate sun exposure\n"
            "• Consider supplements if needed")

def _get_glucose_food_advice_high() -> str:
    """Get food advice for high glucose."""
    return ("🥗 **Blood Sugar Management Diet**\n\n"
            "**Foods to Include:**\n"
            "• Complex Carbs: Whole grains, legumes, vegetables\n"
            "• Fiber: Fruits, vegetables, nuts, seeds\n"
            "• Lean Proteins: Fish, poultry, legumes\n"
            "• Healthy Fats: Nuts, olive oil, avocados\n\n"
            "**Foods to Limit:**\n"
            "• Simple Sugars: Candy, soda, desserts\n"
            "• Refined Carbs: White bread, pasta, rice\n"
            "• Processed Foods: Packaged snacks, fast food\n\n"
            "**Lifestyle Tips:**\n"
            "• Eat regular meals\n"
            "• Exercise regularly\n"
            "• Monitor blood sugar levels")

def _get_glucose_food_advice_general() -> str:
    """Get general glucose food advice."""
    return ("🥗 **Blood Sugar-Friendly Diet**\n\n"
            "**Good Choices:**\n"
            "• Complex carbohydrates: Whole grains, legumes\n"
            "• High-fiber foods: Fruits, vegetables, nuts\n"
            "• Lean proteins: Fish, poultry, legumes\n"
            "• Healthy fats: Nuts, olive oil\n\n"
            "**Limit:**\n"
            "• Simple sugars and refined carbs\n"
            "• Processed foods\n\n"
            "**Tips:**\n"
            "• Eat regular meals\n"
            "• Include protein with carbs\n"
            "• Exercise regularly")

def _get_general_food_advice() -> str:
    """Get general healthy eating advice."""
    return ("🍎 **General Healthy Eating Guidelines**\n\n"
            "**Balanced Nutrition:**\n"
            "• Whole Foods: Fresh fruits, vegetables, whole grains\n"
            "• Lean Proteins: Fish, poultry, legumes, eggs\n"
            "• Healthy Fats: Nuts, seeds, olive oil, avocados\n"
            "• Fiber: 25-30 grams daily from various sources\n\n"
            "**Daily Recommendations:**\n"
            "• Vegetables: 2-3 cups daily\n"
            "• Fruits: 1-2 servings daily\n"
            "• Proteins: Lean sources with each meal\n"
            "• Hydration: 8-10 glasses of water daily\n\n"
            "**Tips:**\n"
            "• Limit processed foods\n"
            "• Reduce added sugars\n"
            "• Cook at home when possible\n"
            "• Practice portion control")

def _handle_symptom_question_rag(markers, prompt, medical_info, user_id):
    return _handle_symptom_question(markers or [], prompt)

def _handle_testing_question_enhanced(markers: Optional[List[Dict[str, Any]]], prompt: str, medical_info: Dict[str, Any], question_analysis: Dict[str, Any], user_id: str) -> str:
    """Handle testing questions with enhanced context understanding."""
    prompt_lower = question_analysis["prompt_lower"]
    mentioned_markers = question_analysis["mentioned_markers"]
    
    # If specific markers mentioned, provide targeted testing advice
    if mentioned_markers:
        target_marker = mentioned_markers[0]
        marker_name = target_marker.get("name", "").lower()
        status = target_marker.get("status", "")
        
        if "cholesterol" in marker_name:
            return _get_cholesterol_testing_advice(status)
        elif "ferritin" in marker_name or "iron" in marker_name:
            return _get_ferritin_testing_advice(status)
        elif "vitamin d" in marker_name:
            return _get_vitamin_d_testing_advice(status)
        elif "glucose" in marker_name or "blood sugar" in marker_name:
            return _get_glucose_testing_advice(status)
    
    # General testing advice
    return _get_general_testing_advice()

def _get_cholesterol_testing_advice(status: str) -> str:
    """Get cholesterol testing advice."""
    if "high" in status.lower():
        return ("🩸 **Cholesterol Testing Schedule**\n\n"
                "**For High Cholesterol:**\n"
                "• Retest in 3-6 months after lifestyle changes\n"
                "• Monitor other cardiovascular risk factors\n"
                "• Consider more frequent testing if very high\n"
                "• Your doctor may recommend medication\n\n"
                "**What to Expect:**\n"
                "• Lifestyle changes can improve levels\n"
                "• Medication may be needed for very high levels\n"
                "• Regular monitoring helps track progress")
    else:
        return ("🩸 **Cholesterol Testing Schedule**\n\n"
                "**General Guidelines:**\n"
                "• Adults: Every 4-6 years if normal\n"
                "• More frequent if risk factors present\n"
                "• Fasting required for accurate results\n\n"
                "**Risk Factors for More Frequent Testing:**\n"
                "• Family history of heart disease\n"
                "• Diabetes or other health conditions\n"
                "• Smoking or obesity\n"
                "• Previous high results")

def _get_ferritin_testing_advice(status: str) -> str:
    """Get ferritin testing advice."""
    if "low" in status.lower():
        return ("🩸 **Ferritin Testing Schedule**\n\n"
                "**For Low Ferritin:**\n"
                "• Retest in 3-6 months after starting treatment\n"
                "• Monitor iron levels (serum iron, TIBC)\n"
                "• Check for underlying causes if levels don't improve\n"
                "• Consider additional iron studies\n\n"
                "**What to Expect:**\n"
                "• Ferritin levels should increase with proper treatment\n"
                "• Your doctor may also check complete blood count (CBC)\n"
                "• Follow-up testing helps monitor treatment effectiveness")
    else:
        return ("🩸 **Ferritin Testing Schedule**\n\n"
                "**General Guidelines:**\n"
                "• Part of routine iron studies\n"
                "• May be checked with CBC\n"
                "• Fasting not usually required\n\n"
                "**When to Test:**\n"
                "• Symptoms of iron deficiency\n"
                "• Routine health checkups\n"
                "• Monitoring iron supplementation")

def _get_vitamin_d_testing_advice(status: str) -> str:
    """Get vitamin D testing advice."""
    if "low" in status.lower():
        return ("🩸 **Vitamin D Testing Schedule**\n\n"
                "**For Low Vitamin D:**\n"
                "• Retest in 3-6 months after supplementation\n"
                "• Monitor calcium levels if supplementing\n"
                "• Check for underlying causes\n"
                "• Seasonal testing may be recommended\n\n"
                "**What to Expect:**\n"
                "• Levels should improve with supplementation\n"
                "• Sunlight exposure affects levels\n"
                "• Regular monitoring ensures proper dosing")
    else:
        return ("🩸 **Vitamin D Testing Schedule**\n\n"
                "**General Guidelines:**\n"
                "• 25-OH Vitamin D is the standard test\n"
                "• Fasting not required\n"
                "• Seasonal variations are normal\n\n"
                "**When to Test:**\n"
                "• Symptoms of deficiency\n"
                "• Risk factors (limited sun exposure)\n"
                "• Monitoring supplementation")

def _get_glucose_testing_advice(status: str) -> str:
    """Get glucose testing advice."""
    if "high" in status.lower():
        return ("🩸 **Blood Sugar Testing Schedule**\n\n"
                "**For High Glucose:**\n"
                "• More frequent monitoring may be needed\n"
                "• Consider HbA1c testing\n"
                "• Monitor fasting and post-meal levels\n"
                "• Your doctor may recommend medication\n\n"
                "**What to Expect:**\n"
                "• Lifestyle changes can improve levels\n"
                "• Regular monitoring is important\n"
                "• Medication may be needed for diabetes")
    else:
        return ("🩸 **Blood Sugar Testing Schedule**\n\n"
                "**General Guidelines:**\n"
                "• Fasting glucose: Every 3 years if normal\n"
                "• More frequent if risk factors present\n"
                "• Fasting required for accurate results\n\n"
                "**Risk Factors for More Frequent Testing:**\n"
                "• Family history of diabetes\n"
                "• Obesity or sedentary lifestyle\n"
                "• Previous high results\n"
                "• Age over 45")

def _get_general_testing_advice() -> str:
    """Get general testing advice."""
    return ("🩸 **General Health Testing Guidelines**\n\n"
            "**Routine Testing:**\n"
            "• Annual physical exam with basic labs\n"
            "• Follow your doctor's recommended schedule\n"
            "• More frequent testing if risk factors present\n\n"
            "**When to Test More Frequently:**\n"
            "• Abnormal previous results\n"
            "• New symptoms or health changes\n"
            "• Starting new medications\n"
            "• Family history of health conditions\n\n"
            "**Tips:**\n"
            "• Keep records of your test results\n"
            "• Discuss any concerns with your doctor\n"
            "• Follow preparation instructions (fasting, etc.)")

def _handle_followup_question_rag(markers, prompt, medical_info, chat_history, user_id):
    return _handle_followup_question(markers or [], prompt, chat_history)
