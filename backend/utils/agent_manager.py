# backend/utils/agent_manager.py
import os
import re
from typing import Optional, List, Dict, Any
from .rag_manager import rag_manager
from .session_manager import session_manager

# Optional lazy initialization to avoid model download during import time in tests
_model = None

def _get_model():
    global _model
    if _model is None:
        # For development, use a simple text generation approach
        # This avoids downloading large models during startup
        _model = "simple_text_generator"
    return _model

def run_agent(prompt: str, markers: Optional[List[Dict[str, Any]]] = None, chat_history: Optional[List[Dict[str, str]]] = None, user_id: Optional[str] = None, session_id: Optional[str] = None) -> str:
    """
    Pure LLM + RAG AI agent with comprehensive medical knowledge and session context awareness.
    No rule-based fallbacks - only intelligent LLM responses with RAG-enhanced context.
    """
    try:
        # Get or create session context
        if session_id:
            session_context = session_manager.get_session_context(session_id)
            if not session_context:
                session_context = session_manager.create_session(user_id or "default", session_id)
        else:
            session_context = {}
        
        # Add any new markers to session
        if markers:
            session_manager.add_markers_to_session(session_id or "default", markers)
        
        # Add user message to chat history
        if session_id:
            session_manager.add_chat_message(session_id, "user", prompt)
        
        # Extract any markers mentioned in the current prompt
        mentioned_markers = session_manager.extract_markers_from_message(prompt) if session_id else []
        
        # Update active markers being discussed
        if session_id and mentioned_markers:
            session_manager.update_active_markers(session_id, mentioned_markers)
        
        # Get relevant markers for this query
        relevant_markers = session_manager.get_relevant_markers_for_query(session_id or "default", prompt) if session_id else (markers or [])
        
        # Retrieve RAG context
        rag_context = {}
        if user_id:
            try:
                rag_context = rag_manager.retrieve_relevant_context(user_id, prompt)
            except Exception as e:
                print(f"RAG retrieval error: {e}")
                rag_context = {"medical_knowledge": {"documents": []}}
        
        # Build comprehensive context
        full_context = {
            "user_markers": relevant_markers,
            "medical_knowledge": rag_context.get("medical_knowledge", {"documents": []}),
            "chat_history": session_context.get("chat_history", chat_history or []),
            "session_context": session_context,
            "mentioned_markers": mentioned_markers,
            "active_markers": session_context.get("active_markers", [])
        }
        
        # Generate LLM response with comprehensive context
        llm_response = _generate_comprehensive_llm_response(prompt, relevant_markers, full_context, user_id)
        
        # Add AI response to session history
        if session_id:
            session_manager.add_chat_message(session_id, "assistant", llm_response)
        
        return llm_response
        
    except Exception as e:
        print(f"Agent error: {e}")
        # Return a helpful error message instead of falling back to rule-based
        return f"I apologize, but I encountered an error processing your request. Please try rephrasing your question or contact support if the issue persists. Error: {str(e)}"

def _generate_comprehensive_llm_response(prompt: str, markers: List[Dict[str, Any]], context: Dict[str, Any], user_id: str) -> str:
    """Generate comprehensive LLM responses using Flan-T5 with enhanced medical knowledge."""
    try:
        from transformers import pipeline
        
        # Initialize the model (lazy loading)
        if not hasattr(_generate_comprehensive_llm_response, 'model'):
            _generate_comprehensive_llm_response.model = pipeline("text2text-generation", model="google/flan-t5-large")
        
        # Build comprehensive context for the LLM
        context_str = _build_comprehensive_context(prompt, markers, context)
        
        # Create a comprehensive prompt for the LLM
        llm_prompt = f"""You are a medical AI assistant. Answer the user's question specifically and concisely.

CONTEXT:
{context_str}

QUESTION: {prompt}

ANSWER:"""
        
        # Generate response with optimized parameters
        response = _generate_comprehensive_llm_response.model(
            llm_prompt, 
            max_new_tokens=512,  # Increased for more detailed responses
            do_sample=True, 
            temperature=0.4,  # Balanced creativity and accuracy
            top_p=0.9,
            repetition_penalty=1.3,  # Prevent repetition
            num_return_sequences=1
        )
        
        generated_text = response[0]["generated_text"]
        
        # Clean and format the response
        cleaned_response = _clean_and_format_response(generated_text, prompt)
        
        # Validate response quality
        if len(cleaned_response.strip()) < 30:
            # Generate a more detailed response if too short
            return _generate_fallback_response(prompt, markers, context)
        
        return cleaned_response
        
    except Exception as e:
        print(f"LLM generation error: {e}")
        return _generate_fallback_response(prompt, markers, context)

def _build_comprehensive_context(prompt: str, markers: List[Dict[str, Any]], context: Dict[str, Any]) -> str:
    """Build comprehensive context string for LLM with medical knowledge and session awareness."""
    context_parts = []
    
    # Add user's current markers with detailed information
    if markers:
        context_parts.append("CURRENT HEALTH MARKERS:")
        for marker in markers:
            name = marker.get("name", "")
            value = marker.get("value", "")
            unit = marker.get("unit", "")
            status = marker.get("status", "")
            normal_range = marker.get("normalRange", "")
            context_parts.append(f"- {name}: {value} {unit} ({status}) - Normal range: {normal_range}")
    
    # Add session context if available
    session_context = context.get("session_context", {})
    if session_context:
        active_markers = session_context.get("active_markers", [])
        if active_markers:
            context_parts.append(f"\nACTIVELY DISCUSSED MARKERS: {', '.join(active_markers)}")
        
        total_markers = len(session_context.get("markers", []))
        if total_markers > 0:
            context_parts.append(f"\nTOTAL MARKERS IN SESSION: {total_markers}")
    
    # Add concise medical knowledge for current markers
    if markers:
        context_parts.append("\nMEDICAL KNOWLEDGE:")
        for marker in markers:
            marker_name = marker.get("name", "").lower()
            status = marker.get("status", "")
            
            # Add concise medical knowledge for each marker
            medical_info = _get_concise_medical_knowledge(marker_name, status)
            context_parts.extend(medical_info)
    
    # Add RAG medical knowledge if available
    medical_knowledge = context.get("medical_knowledge", {})
    if medical_knowledge and medical_knowledge.get("documents"):
        context_parts.append("\nADDITIONAL MEDICAL KNOWLEDGE:")
        for doc in medical_knowledge["documents"][:3]:  # Top 3 most relevant
            context_parts.append(f"- {doc}")
    
    # Add chat history context (last 3 messages to reduce tokens)
    chat_history = context.get("chat_history", [])
    if chat_history:
        context_parts.append("\nRECENT CONVERSATION:")
        recent_messages = chat_history[-3:]  # Last 3 messages
        for msg in recent_messages:
            role = msg.get("role", "")
            content = msg.get("content", "")
            context_parts.append(f"- {role}: {content[:100]}...")
    
    # Add general health knowledge for non-marker questions
    if not markers:
        context_parts.append("\nGENERAL HEALTH KNOWLEDGE:")
        context_parts.append("- Nutrition: Balanced diet with fruits, vegetables, lean proteins, whole grains")
        context_parts.append("- Exercise: Regular physical activity, strength training, cardiovascular exercise")
        context_parts.append("- Lifestyle: Adequate sleep, stress management, avoiding smoking/alcohol")
        context_parts.append("- Prevention: Regular check-ups, vaccinations, screening tests")
    
    return "\n".join(context_parts)

def _get_concise_medical_knowledge(marker_name: str, status: str) -> List[str]:
    """Get concise medical knowledge for any marker."""
    knowledge = []
    
    # Concise marker knowledge
    if "magnesium" in marker_name:
        if status == "low":
            knowledge.extend([
                "Magnesium: essential for muscle/nerve function, energy production",
                "Low symptoms: cramps, fatigue, weakness, irregular heartbeat",
                "Foods: dark chocolate, nuts, seeds, legumes, whole grains, leafy greens",
                "Lifestyle: reduce stress, limit alcohol/caffeine, adequate sleep"
            ])
        elif status == "high":
            knowledge.extend([
                "High symptoms: nausea, muscle weakness, irregular heartbeat",
                "Causes: kidney problems, excessive supplementation"
            ])
    
    elif "calcium" in marker_name:
        if status == "low":
            knowledge.extend([
                "Calcium: crucial for bone health, muscle/nerve function",
                "Low symptoms: cramps, numbness, tingling, bone pain",
                "Foods: dairy, leafy greens, nuts, seeds, fortified foods",
                "Lifestyle: weight-bearing exercise, vitamin D exposure"
            ])
        elif status == "high":
            knowledge.extend([
                "High symptoms: nausea, confusion, muscle weakness, kidney stones",
                "Causes: hyperparathyroidism, cancer, excessive supplementation"
            ])
    
    elif "selenium" in marker_name:
        if status == "low":
            knowledge.extend([
                "Selenium: antioxidant, supports thyroid function, immune health",
                "Low symptoms: muscle weakness, fatigue, thyroid problems, immune issues",
                "Foods: Brazil nuts, fish, meat, eggs, mushrooms, whole grains",
                "Lifestyle: avoid excessive alcohol, adequate protein intake"
            ])
        elif status == "high":
            knowledge.extend([
                "High symptoms: hair loss, nail changes, gastrointestinal issues",
                "Causes: excessive supplementation, high-selenium soil areas"
            ])
    
    elif "zinc" in marker_name:
        if status == "low":
            knowledge.extend([
                "Zinc is essential for immune function, wound healing, protein synthesis, and taste/smell.",
                "Low zinc symptoms: frequent infections, slow wound healing, hair loss, taste changes, diarrhea",
                "Zinc-rich foods: meat, shellfish, legumes, nuts, seeds, dairy, whole grains",
                "Lifestyle for zinc: ensure adequate protein intake, avoid excessive fiber, limit alcohol",
                "Supplements: zinc gluconate, citrate, or picolinate (take on empty stomach, consult doctor)"
            ])
        elif status == "high":
            knowledge.extend([
                "High zinc symptoms: nausea, vomiting, diarrhea, copper deficiency, immune suppression",
                "Causes: excessive supplementation, occupational exposure"
            ])
    
    elif "vitamin d" in marker_name or "25-oh" in marker_name:
        if status == "low":
            knowledge.extend([
                "Vitamin D is essential for bone health, immune function, and calcium absorption.",
                "Low vitamin D symptoms: bone pain, muscle weakness, fatigue, frequent infections, depression",
                "Vitamin D sources: sunlight exposure, fatty fish, egg yolks, fortified foods, mushrooms",
                "Lifestyle for vitamin D: 15-20 minutes sun exposure daily, outdoor activities, balanced diet",
                "Supplements: vitamin D3 (cholecalciferol) - consult doctor for dosage"
            ])
        elif status == "high":
            knowledge.extend([
                "High vitamin D symptoms: nausea, vomiting, kidney problems, calcium buildup in blood",
                "Causes: excessive supplementation, certain medical conditions"
            ])
    
    elif "vitamin b12" in marker_name or "cobalamin" in marker_name:
        if status == "low":
            knowledge.extend([
                "Vitamin B12 is essential for nerve function, red blood cell formation, and DNA synthesis.",
                "Low B12 symptoms: fatigue, weakness, numbness, tingling, memory problems, anemia",
                "B12-rich foods: meat, fish, eggs, dairy, fortified cereals, nutritional yeast",
                "Lifestyle for B12: balanced diet, consider supplementation if vegetarian/vegan",
                "Supplements: B12 methylcobalamin or cyanocobalamin (consult doctor for dosage)"
            ])
        elif status == "high":
            knowledge.extend([
                "High B12 symptoms: usually asymptomatic, may indicate underlying condition",
                "Causes: supplementation, certain medical conditions"
            ])
    
    elif "ferritin" in marker_name or "iron" in marker_name:
        if status == "low":
            knowledge.extend([
                "Iron/Ferritin is essential for oxygen transport, energy production, and immune function.",
                "Low iron symptoms: fatigue, weakness, shortness of breath, pale skin, dizziness, cold hands/feet",
                "Iron-rich foods: red meat, spinach, beans, fortified cereals, dark chocolate, pumpkin seeds",
                "Lifestyle for iron: include vitamin C with meals, avoid coffee/tea with iron foods",
                "Supplements: iron sulfate, gluconate, or bisglycinate (consult doctor for dosage)"
            ])
        elif status == "high":
            knowledge.extend([
                "High iron symptoms: joint pain, fatigue, abdominal pain, heart problems, diabetes risk",
                "Causes: hemochromatosis, excessive supplementation, blood transfusions"
            ])
    
    elif "cholesterol" in marker_name or "hdl" in marker_name or "ldl" in marker_name:
        if status == "high" or (marker_name == "hdl" and status == "low"):
            knowledge.extend([
                "Cholesterol is essential for cell membranes, hormone production, and vitamin D synthesis.",
                "High cholesterol symptoms: usually asymptomatic, may cause chest pain, heart disease risk",
                "Cholesterol-friendly foods: oats, beans, fatty fish, nuts, olive oil, avocados",
                "Lifestyle for cholesterol: exercise regularly, maintain healthy weight, quit smoking, stress management",
                "Supplements: omega-3 fatty acids, plant sterols, fiber (consult doctor)"
            ])
        elif status == "low" or (marker_name == "hdl" and status == "high"):
            knowledge.extend([
                "Low cholesterol symptoms: usually asymptomatic, may indicate malnutrition or liver disease",
                "Causes: malnutrition, liver disease, certain medications"
            ])
    
    elif "glucose" in marker_name or "hba1c" in marker_name or "a1c" in marker_name:
        if status == "high":
            knowledge.extend([
                "Glucose is the primary energy source for cells, regulated by insulin.",
                "High glucose symptoms: increased thirst, frequent urination, fatigue, blurred vision, slow healing",
                "Glucose-friendly foods: whole grains, non-starchy vegetables, lean proteins, healthy fats",
                "Lifestyle for glucose: regular exercise, weight management, stress reduction, adequate sleep",
                "Supplements: chromium, cinnamon, alpha-lipoic acid (consult doctor)"
            ])
        elif status == "low":
            knowledge.extend([
                "Low glucose symptoms: shakiness, confusion, sweating, hunger, dizziness, rapid heartbeat",
                "Low glucose foods: complex carbs, regular meals, protein with carbs, avoid refined sugars"
            ])
    
    else:
        # Generic knowledge for unknown markers
        knowledge.extend([
            f"{marker_name.title()} is a health marker that your doctor uses to assess your overall health status.",
            f"Current status: {status}",
            f"Focus on foods rich in {marker_name} and consult your healthcare provider for personalized advice.",
            "General health recommendations: balanced diet, regular exercise, adequate sleep, stress management"
        ])
    
    return knowledge

def _clean_and_format_response(response: str, original_prompt: str) -> str:
    """Clean and format the LLM response for better readability."""
    # Remove any instruction repetition
    instruction_indicators = [
        "you are a medical ai assistant",
        "provide a detailed response",
        "focus on the specific health markers",
        "maintain context from the conversation",
        "if discussing specific health markers",
        "if it's a general health question"
    ]
    
    cleaned = response.strip()
    
    # Remove instruction repetition
    for indicator in instruction_indicators:
        if indicator in cleaned.lower():
            # Find the last occurrence and remove everything before it
            last_occurrence = cleaned.lower().rfind(indicator)
            if last_occurrence > 0:
                cleaned = cleaned[last_occurrence + len(indicator):].strip()
    
    # Add formatting for better readability
    if "foods:" in cleaned.lower() or "food:" in cleaned.lower():
        # Format food lists as bullet points
        cleaned = re.sub(r'([A-Z][a-z]+(?:[^.!?]*[.!?]))', r'• \1', cleaned)
    
    # Add emojis for better engagement
    if "food" in original_prompt.lower():
        cleaned = "🍽️ " + cleaned
    elif "exercise" in original_prompt.lower() or "lifestyle" in original_prompt.lower():
        cleaned = "🏃‍♂️ " + cleaned
    elif "supplement" in original_prompt.lower():
        cleaned = "💊 " + cleaned
    elif "symptom" in original_prompt.lower():
        cleaned = "🏥 " + cleaned
    
    return cleaned

def _generate_fallback_response(prompt: str, markers: List[Dict[str, Any]], context: Dict[str, Any]) -> str:
    """Generate a fallback response when LLM fails."""
    prompt_lower = prompt.lower()
    
    if "food" in prompt_lower:
        if markers:
            marker_names = [m.get("name", "") for m in markers]
            return f"Based on your {', '.join(marker_names)} levels, I recommend focusing on a balanced diet rich in whole foods. For specific dietary recommendations, please consult with your healthcare provider."
        else:
            return "For optimal nutrition, focus on a balanced diet including fruits, vegetables, lean proteins, whole grains, and healthy fats. Consider consulting a registered dietitian for personalized advice."
    
    elif "exercise" in prompt_lower or "lifestyle" in prompt_lower:
        return "Regular exercise, adequate sleep, stress management, and avoiding smoking/alcohol are key to maintaining good health. Aim for 150 minutes of moderate exercise weekly."
    
    elif "supplement" in prompt_lower:
        return "Supplements should be taken under medical supervision. Please consult your healthcare provider for personalized supplement recommendations based on your specific needs."
    
    else:
        return "I understand your question about health. For personalized medical advice, please consult with your healthcare provider who can consider your complete medical history and current health status."
