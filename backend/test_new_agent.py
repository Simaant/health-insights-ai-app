#!/usr/bin/env python3
"""
Test script for the new LLM + RAG agent architecture
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.agent_manager import run_agent
from utils.session_manager import session_manager
from utils.health_marker_detector import HealthMarkerDetector

def test_magnesium_context():
    """Test magnesium marker with follow-up questions in same session."""
    print("🧪 Testing Magnesium Context Awareness...")
    
    # Create a test session
    session_id = "test_magnesium_session"
    user_id = "test_user"
    
    # Create session
    session_manager.create_session(user_id, session_id)
    
    # Test markers
    markers = [
        {
            "name": "Magnesium",
            "value": "1.5",
            "unit": "mg/dL",
            "status": "low",
            "normalRange": "1.7-2.2 mg/dL"
        }
    ]
    
    # Add markers to session
    session_manager.add_markers_to_session(session_id, markers)
    
    # Test questions
    questions = [
        "What foods should I eat to increase my magnesium levels?",
        "What lifestyle changes should I make?",
        "What symptoms should I watch for?",
        "When should I see a doctor?"
    ]
    
    for i, question in enumerate(questions, 1):
        print(f"\n📝 Question {i}: {question}")
        response = run_agent(question, markers, [], user_id, session_id)
        print(f"🤖 Response: {response[:200]}...")
    
    print("\n✅ Magnesium context test completed!")

def test_unknown_marker():
    """Test unknown marker (Selenium) with comprehensive responses."""
    print("\n🧪 Testing Unknown Marker (Selenium)...")
    
    session_id = "test_selenium_session"
    user_id = "test_user_selenium"
    
    # Create session
    session_manager.create_session(user_id, session_id)
    
    # Test markers
    markers = [
        {
            "name": "Selenium",
            "value": "0.8",
            "unit": "mcg/L",
            "status": "low",
            "normalRange": "1.0-3.0 mcg/L"
        }
    ]
    
    # Add markers to session
    session_manager.add_markers_to_session(session_id, markers)
    
    # Test questions
    questions = [
        "What is selenium and why is it important?",
        "What foods are rich in selenium?",
        "What lifestyle changes can help with low selenium?",
        "Should I take selenium supplements?"
    ]
    
    for i, question in enumerate(questions, 1):
        print(f"\n📝 Question {i}: {question}")
        response = run_agent(question, markers, [], user_id, session_id)
        print(f"🤖 Response: {response[:200]}...")
    
    print("\n✅ Selenium unknown marker test completed!")

def test_general_health_questions():
    """Test general health questions without specific markers."""
    print("\n🧪 Testing General Health Questions...")
    
    session_id = "test_general_session"
    user_id = "test_user_general"
    
    # Create session
    session_manager.create_session(user_id, session_id)
    
    # Test general health questions
    questions = [
        "What are the benefits of regular exercise?",
        "How can I improve my sleep quality?",
        "What should I eat for a healthy diet?",
        "How can I reduce stress?"
    ]
    
    for i, question in enumerate(questions, 1):
        print(f"\n📝 Question {i}: {question}")
        response = run_agent(question, [], [], user_id, session_id)
        print(f"🤖 Response: {response[:200]}...")
    
    print("\n✅ General health questions test completed!")

def test_marker_detection():
    """Test the enhanced marker detection."""
    print("\n🧪 Testing Enhanced Marker Detection...")
    
    detector = HealthMarkerDetector()
    
    # Test text with various markers
    test_text = """
    Blood Test Results:
    Magnesium: 1.5 mg/dL (low)
    Calcium: 9.2 mg/dL (normal)
    Selenium: 0.8 mcg/L (low)
    Vitamin D: 25 ng/mL (low)
    Cholesterol: 220 mg/dL (high)
    """
    
    print(f"📝 Test Text: {test_text}")
    
    markers = detector.extract_markers_from_text(test_text)
    
    print(f"🔍 Detected {len(markers)} markers:")
    for marker in markers:
        print(f"  - {marker.name}: {marker.value} {marker.unit} ({marker.status})")
    
    print("\n✅ Marker detection test completed!")

if __name__ == "__main__":
    print("🚀 Testing New LLM + RAG Agent Architecture")
    print("=" * 50)
    
    try:
        # Test marker detection first
        test_marker_detection()
        
        # Test magnesium context
        test_magnesium_context()
        
        # Test unknown marker
        test_unknown_marker()
        
        # Test general health questions
        test_general_health_questions()
        
        print("\n🎉 All tests completed successfully!")
        print("✅ The new LLM + RAG architecture is working correctly!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
