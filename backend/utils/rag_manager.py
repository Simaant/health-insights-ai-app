import os
import json
from typing import List, Dict, Any, Optional
import numpy as np
from datetime import datetime
import uuid
import re

# Optional imports for RAG functionality
try:
    import chromadb
    from sentence_transformers import SentenceTransformer
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False
    print("Warning: RAG dependencies not available. Using fallback mode.")

class RAGManager:
    def __init__(self):
        """Initialize RAG manager with vector database and embedding model."""
        if not RAG_AVAILABLE:
            # Fallback mode - use simple in-memory storage
            self.markers_storage = {}
            self.chat_history_storage = {}
            self.medical_knowledge = self._initialize_medical_knowledge_fallback()
            # Initialize a simple text splitter for fallback mode
            self.text_splitter = self._create_simple_text_splitter()
            return
        
        try:
            # Initialize embedding model
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            
            # Initialize ChromaDB
            self.client = chromadb.PersistentClient(path="./chroma_db")
            
            # Create collections for different types of data
            self.markers_collection = self.client.get_or_create_collection(
                name="health_markers",
                metadata={"hnsw:space": "cosine"}
            )
            
            self.chat_history_collection = self.client.get_or_create_collection(
                name="chat_history",
                metadata={"hnsw:space": "cosine"}
            )
            
            self.medical_knowledge_collection = self.client.get_or_create_collection(
                name="medical_knowledge",
                metadata={"hnsw:space": "cosine"}
            )
            
            # Text splitter for chunking
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=500,
                chunk_overlap=50,
                separators=["\n\n", "\n", ". ", " ", ""]
            )
            
            # Initialize medical knowledge base
            self._initialize_medical_knowledge()
        except Exception as e:
            print(f"RAG initialization failed: {e}")
            # Fallback to simple storage
            self.markers_storage = {}
            self.chat_history_storage = {}
            self.medical_knowledge = self._initialize_medical_knowledge_fallback()
            # Initialize a simple text splitter for fallback mode
            self.text_splitter = self._create_simple_text_splitter()

    def _create_simple_text_splitter(self):
        """Create a simple text splitter for fallback mode."""
        class SimpleTextSplitter:
            def split_text(self, text):
                # Simple splitting by sentences
                sentences = text.split('. ')
                chunks = []
                current_chunk = ""
                
                for sentence in sentences:
                    if len(current_chunk) + len(sentence) < 500:
                        current_chunk += sentence + ". "
                    else:
                        if current_chunk:
                            chunks.append(current_chunk.strip())
                        current_chunk = sentence + ". "
                
                if current_chunk:
                    chunks.append(current_chunk.strip())
                
                return chunks
        
        return SimpleTextSplitter()

    def _initialize_medical_knowledge(self):
        """Initialize the medical knowledge base with comprehensive health markers."""
        medical_knowledge = [
            # Existing markers
            {
                "marker": "ferritin",
                "description": "Ferritin is a protein that stores iron in the body. Low levels indicate iron deficiency anemia.",
                "normal_range": "20-250 ng/mL for women, 30-400 ng/mL for men",
                "low_symptoms": "Fatigue, weakness, shortness of breath, pale skin, dizziness",
                "low_causes": "Iron deficiency, blood loss, poor diet, malabsorption",
                "low_treatment": "Iron supplements, iron-rich diet, vitamin C for absorption",
                "high_symptoms": "Joint pain, fatigue, abdominal pain, heart problems",
                "high_causes": "Iron overload, inflammation, liver disease, hemochromatosis",
                "high_treatment": "Phlebotomy, iron chelation therapy, dietary changes"
            },
            {
                "marker": "vitamin d",
                "description": "Vitamin D is essential for bone health, immune function, and calcium absorption.",
                "normal_range": "30-100 ng/mL (25-OH Vitamin D)",
                "low_symptoms": "Bone pain, muscle weakness, fatigue, frequent infections",
                "low_causes": "Limited sun exposure, poor diet, malabsorption, obesity",
                "low_treatment": "Vitamin D supplements, sun exposure, fortified foods",
                "high_symptoms": "Nausea, vomiting, kidney problems, calcium buildup",
                "high_causes": "Excessive supplementation, hyperparathyroidism",
                "high_treatment": "Reduce supplementation, monitor calcium levels"
            },
            {
                "marker": "vitamin b12",
                "description": "Vitamin B12 is essential for nerve function, red blood cell formation, and DNA synthesis.",
                "normal_range": "200-900 pg/mL",
                "low_symptoms": "Fatigue, numbness, tingling, memory problems, anemia",
                "low_causes": "Pernicious anemia, vegan diet, malabsorption, medications",
                "low_treatment": "B12 injections, oral supplements, dietary changes",
                "high_symptoms": "Usually asymptomatic, may indicate underlying condition",
                "high_causes": "Liver disease, certain cancers, supplementation",
                "high_treatment": "Address underlying cause, monitor levels"
            },
            {
                "marker": "cholesterol",
                "description": "Cholesterol is a fatty substance essential for cell membranes and hormone production.",
                "normal_range": "Total: <200 mg/dL, HDL: >40 mg/dL, LDL: <100 mg/dL",
                "high_symptoms": "Usually asymptomatic, may cause chest pain, heart disease",
                "high_causes": "Poor diet, genetics, obesity, diabetes, smoking",
                "high_treatment": "Diet changes, exercise, medications (statins)",
                "low_symptoms": "Rare, may indicate malnutrition or liver disease",
                "low_causes": "Malnutrition, liver disease, hyperthyroidism",
                "low_treatment": "Address underlying cause, dietary changes"
            },
            {
                "marker": "glucose",
                "description": "Glucose is the primary source of energy for cells and is regulated by insulin.",
                "normal_range": "Fasting: 70-99 mg/dL, Postprandial: <140 mg/dL",
                "high_symptoms": "Increased thirst, frequent urination, fatigue, blurred vision",
                "high_causes": "Diabetes, stress, medications, poor diet",
                "high_treatment": "Diet changes, exercise, medications, insulin",
                "low_symptoms": "Shakiness, confusion, sweating, hunger, dizziness",
                "low_causes": "Insulin overdose, skipping meals, excessive exercise",
                "low_treatment": "Glucose tablets, regular meals, medication adjustment"
            },
            # Add more comprehensive markers
            {
                "marker": "calcium",
                "description": "Calcium is essential for bone health, muscle function, and nerve transmission.",
                "normal_range": "8.5-10.5 mg/dL",
                "low_symptoms": "Muscle cramps, numbness, tingling, bone pain, fatigue",
                "low_causes": "Vitamin D deficiency, parathyroid problems, poor diet, malabsorption",
                "low_treatment": "Calcium supplements, vitamin D, dairy products, leafy greens",
                "high_symptoms": "Nausea, vomiting, confusion, muscle weakness, kidney stones",
                "high_causes": "Hyperparathyroidism, cancer, excessive supplementation",
                "high_treatment": "Address underlying cause, reduce calcium intake, medications"
            },
            {
                "marker": "magnesium",
                "description": "Magnesium is involved in over 300 enzymatic reactions and is essential for muscle and nerve function.",
                "normal_range": "1.7-2.2 mg/dL",
                "low_symptoms": "Muscle cramps, fatigue, weakness, irregular heartbeat, anxiety",
                "low_causes": "Poor diet, alcohol abuse, diabetes, medications, malabsorption",
                "low_treatment": "Magnesium supplements, nuts, seeds, leafy greens, whole grains",
                "high_symptoms": "Nausea, vomiting, muscle weakness, irregular heartbeat",
                "high_causes": "Kidney disease, excessive supplementation, certain medications",
                "high_treatment": "Address underlying cause, reduce supplementation"
            },
            {
                "marker": "potassium",
                "description": "Potassium is essential for heart function, muscle contractions, and fluid balance.",
                "normal_range": "3.5-5.0 mEq/L",
                "low_symptoms": "Muscle weakness, fatigue, irregular heartbeat, constipation",
                "low_causes": "Diuretics, vomiting, diarrhea, poor diet, kidney disease",
                "low_treatment": "Potassium supplements, bananas, potatoes, leafy greens",
                "high_symptoms": "Muscle weakness, irregular heartbeat, numbness, tingling",
                "high_causes": "Kidney disease, medications, excessive supplementation",
                "high_treatment": "Address underlying cause, dietary restrictions, medications"
            },
            {
                "marker": "sodium",
                "description": "Sodium is essential for fluid balance, nerve function, and muscle contractions.",
                "normal_range": "135-145 mEq/L",
                "low_symptoms": "Confusion, fatigue, muscle cramps, nausea, headache",
                "low_causes": "Excessive water intake, diuretics, heart failure, kidney disease",
                "low_treatment": "Reduce fluid intake, address underlying cause, sodium supplements",
                "high_symptoms": "Thirst, confusion, muscle twitching, seizures",
                "high_causes": "Dehydration, excessive salt intake, kidney disease",
                "high_treatment": "Increase fluid intake, reduce salt intake, address underlying cause"
            },
            {
                "marker": "zinc",
                "description": "Zinc is essential for immune function, wound healing, and protein synthesis.",
                "normal_range": "60-120 mcg/dL",
                "low_symptoms": "Frequent infections, slow wound healing, hair loss, taste changes",
                "low_causes": "Poor diet, malabsorption, chronic illness, vegetarian diet",
                "low_treatment": "Zinc supplements, meat, shellfish, legumes, nuts",
                "high_symptoms": "Nausea, vomiting, diarrhea, copper deficiency",
                "high_causes": "Excessive supplementation, occupational exposure",
                "high_treatment": "Reduce supplementation, address underlying cause"
            },
            {
                "marker": "copper",
                "description": "Copper is essential for iron metabolism, nerve function, and connective tissue formation.",
                "normal_range": "70-140 mcg/dL",
                "low_symptoms": "Anemia, fatigue, bone problems, neurological issues",
                "low_causes": "Poor diet, malabsorption, excessive zinc intake",
                "low_treatment": "Copper supplements, shellfish, nuts, seeds, whole grains",
                "high_symptoms": "Liver problems, neurological issues, psychiatric symptoms",
                "high_causes": "Wilson's disease, excessive supplementation",
                "high_treatment": "Chelation therapy, dietary restrictions, medications"
            },
            {
                "marker": "selenium",
                "description": "Selenium is an antioxidant that supports thyroid function and immune health.",
                "normal_range": "70-150 mcg/L",
                "low_symptoms": "Muscle weakness, fatigue, thyroid problems, immune issues",
                "low_causes": "Poor diet, malabsorption, certain medications",
                "low_treatment": "Selenium supplements, Brazil nuts, fish, meat, eggs",
                "high_symptoms": "Hair loss, nail changes, gastrointestinal issues",
                "high_causes": "Excessive supplementation, occupational exposure",
                "high_treatment": "Reduce supplementation, address underlying cause"
            },
            {
                "marker": "creatinine",
                "description": "Creatinine is a waste product filtered by the kidneys, used to assess kidney function.",
                "normal_range": "0.6-1.2 mg/dL",
                "low_symptoms": "Usually asymptomatic, may indicate muscle loss",
                "low_causes": "Muscle loss, aging, malnutrition, liver disease",
                "low_treatment": "Address underlying cause, protein-rich diet, exercise",
                "high_symptoms": "Fatigue, swelling, changes in urination, confusion",
                "high_causes": "Kidney disease, dehydration, medications, muscle injury",
                "high_treatment": "Address underlying cause, dietary changes, medications"
            },
            {
                "marker": "bun",
                "description": "Blood Urea Nitrogen measures kidney function and protein metabolism.",
                "normal_range": "7-20 mg/dL",
                "low_symptoms": "Usually asymptomatic",
                "low_causes": "Liver disease, malnutrition, overhydration",
                "low_treatment": "Address underlying cause, protein-rich diet",
                "high_symptoms": "Fatigue, confusion, swelling, changes in urination",
                "high_causes": "Kidney disease, dehydration, high protein diet, heart failure",
                "high_treatment": "Address underlying cause, dietary changes, medications"
            },
            {
                "marker": "albumin",
                "description": "Albumin is a protein made by the liver that helps maintain fluid balance.",
                "normal_range": "3.4-5.4 g/dL",
                "low_symptoms": "Swelling, fatigue, weakness, poor wound healing",
                "low_causes": "Liver disease, malnutrition, inflammation, kidney disease",
                "low_treatment": "Address underlying cause, protein-rich diet, albumin infusions",
                "high_symptoms": "Usually asymptomatic",
                "high_causes": "Dehydration, certain medications",
                "high_treatment": "Address underlying cause, increase fluid intake"
            },
            {
                "marker": "bilirubin",
                "description": "Bilirubin is a waste product from red blood cell breakdown, processed by the liver.",
                "normal_range": "0.3-1.2 mg/dL",
                "low_symptoms": "Usually asymptomatic",
                "low_causes": "Certain medications, genetic factors",
                "low_treatment": "Usually no treatment needed",
                "high_symptoms": "Yellowing of skin/eyes, dark urine, fatigue, abdominal pain",
                "high_causes": "Liver disease, bile duct problems, blood disorders",
                "high_treatment": "Address underlying cause, medications, dietary changes"
            },
            {
                "marker": "alt",
                "description": "Alanine Aminotransferase is a liver enzyme that indicates liver health.",
                "normal_range": "7-55 U/L",
                "low_symptoms": "Usually asymptomatic",
                "low_causes": "Vitamin B6 deficiency, certain medications",
                "low_treatment": "Address underlying cause, vitamin B6 supplementation",
                "high_symptoms": "Fatigue, abdominal pain, jaundice, nausea",
                "high_causes": "Liver disease, medications, alcohol, obesity",
                "high_treatment": "Address underlying cause, dietary changes, medications"
            },
            {
                "marker": "ast",
                "description": "Aspartate Aminotransferase is a liver enzyme that indicates liver and heart health.",
                "normal_range": "8-48 U/L",
                "low_symptoms": "Usually asymptomatic",
                "low_causes": "Vitamin B6 deficiency, certain medications",
                "low_treatment": "Address underlying cause, vitamin B6 supplementation",
                "high_symptoms": "Fatigue, abdominal pain, jaundice, chest pain",
                "high_causes": "Liver disease, heart problems, medications, alcohol",
                "high_treatment": "Address underlying cause, dietary changes, medications"
            },
            {
                "marker": "alkaline phosphatase",
                "description": "Alkaline Phosphatase is an enzyme found in liver, bones, and other tissues.",
                "normal_range": "44-147 U/L",
                "low_symptoms": "Usually asymptomatic",
                "low_causes": "Malnutrition, certain medications, genetic factors",
                "low_treatment": "Address underlying cause, nutritional support",
                "high_symptoms": "Bone pain, fatigue, jaundice, abdominal pain",
                "high_causes": "Liver disease, bone problems, pregnancy, certain medications",
                "high_treatment": "Address underlying cause, medications, dietary changes"
            },
            {
                "marker": "hemoglobin",
                "description": "Hemoglobin carries oxygen in red blood cells throughout the body.",
                "normal_range": "12-18 g/dL",
                "low_symptoms": "Fatigue, weakness, shortness of breath, pale skin, dizziness",
                "low_causes": "Iron deficiency, blood loss, chronic disease, bone marrow problems",
                "low_treatment": "Iron supplements, blood transfusions, address underlying cause",
                "high_symptoms": "Headache, dizziness, fatigue, vision problems",
                "high_causes": "Dehydration, lung disease, bone marrow disorders, high altitude",
                "high_treatment": "Address underlying cause, phlebotomy, medications"
            },
            {
                "marker": "hematocrit",
                "description": "Hematocrit measures the percentage of red blood cells in blood volume.",
                "normal_range": "36-50%",
                "low_symptoms": "Fatigue, weakness, shortness of breath, pale skin",
                "low_causes": "Anemia, blood loss, chronic disease, bone marrow problems",
                "low_treatment": "Iron supplements, blood transfusions, address underlying cause",
                "high_symptoms": "Headache, dizziness, fatigue, vision problems",
                "high_causes": "Dehydration, lung disease, bone marrow disorders, high altitude",
                "high_treatment": "Address underlying cause, phlebotomy, medications"
            },
            {
                "marker": "wbc",
                "description": "White Blood Cell count indicates immune system function and infection status.",
                "normal_range": "4.5-11.0 K/μL",
                "low_symptoms": "Frequent infections, fatigue, fever",
                "low_causes": "Viral infections, bone marrow problems, medications, autoimmune disease",
                "low_treatment": "Address underlying cause, medications, bone marrow transplant",
                "high_symptoms": "Fever, fatigue, pain, infection symptoms",
                "high_causes": "Infection, inflammation, stress, medications, bone marrow disorders",
                "high_treatment": "Address underlying cause, antibiotics, medications"
            },
            {
                "marker": "platelets",
                "description": "Platelets are essential for blood clotting and wound healing.",
                "normal_range": "150-450 K/μL",
                "low_symptoms": "Easy bruising, bleeding, petechiae, fatigue",
                "low_causes": "Viral infections, medications, autoimmune disease, bone marrow problems",
                "low_treatment": "Address underlying cause, platelet transfusions, medications",
                "high_symptoms": "Blood clots, headache, chest pain, stroke symptoms",
                "high_causes": "Inflammation, infection, bone marrow disorders, medications",
                "high_treatment": "Address underlying cause, blood thinners, medications"
            }
        ]
        
        # Store in memory for fallback
        self.medical_knowledge = medical_knowledge
        
        # Index in vector database if available
        if hasattr(self, 'medical_knowledge_collection'):
            try:
                for i, knowledge in enumerate(medical_knowledge):
                    self.medical_knowledge_collection.add(
                        documents=[f"{knowledge['marker']}: {knowledge['description']} Normal range: {knowledge['normal_range']}"],
                        metadatas=[knowledge],
                        ids=[f"medical_{i}"]
                    )
            except Exception as e:
                print(f"Failed to index medical knowledge: {e}")

    def _initialize_medical_knowledge_fallback(self) -> Dict[str, Any]:
        """Initialize medical knowledge for fallback mode."""
        return {
            "ferritin": {
                "description": "Ferritin is a protein that stores iron in the body. Low levels indicate iron deficiency anemia.",
                "normal_range": "20-250 ng/mL for women, 30-400 ng/mL for men",
                "low_symptoms": "Fatigue, weakness, shortness of breath, pale skin, dizziness",
                "low_causes": "Iron deficiency, blood loss, poor diet, malabsorption",
                "low_treatment": "Iron supplements, iron-rich diet, vitamin C for absorption",
                "high_symptoms": "Joint pain, fatigue, abdominal pain, heart problems",
                "high_causes": "Iron overload, inflammation, liver disease, hemochromatosis",
                "high_treatment": "Phlebotomy, iron chelation therapy, dietary changes"
            },
            "vitamin d": {
                "description": "Vitamin D is essential for bone health, immune function, and calcium absorption.",
                "normal_range": "30-100 ng/mL (25-OH Vitamin D)",
                "low_symptoms": "Bone pain, muscle weakness, fatigue, frequent infections",
                "low_causes": "Limited sun exposure, poor diet, malabsorption, obesity",
                "low_treatment": "Vitamin D supplements, sun exposure, fortified foods",
                "high_symptoms": "Nausea, vomiting, kidney problems, calcium buildup",
                "high_causes": "Excessive supplementation, hyperparathyroidism",
                "high_treatment": "Reduce supplementation, monitor calcium levels"
            },
            "vitamin b12": {
                "description": "Vitamin B12 is essential for nerve function, red blood cell formation, and DNA synthesis.",
                "normal_range": "200-900 pg/mL",
                "low_symptoms": "Fatigue, numbness, tingling, memory problems, anemia",
                "low_causes": "Pernicious anemia, vegan diet, malabsorption, medications",
                "low_treatment": "B12 injections, oral supplements, dietary changes",
                "high_symptoms": "Usually asymptomatic, may indicate underlying condition",
                "high_causes": "Liver disease, certain cancers, supplementation",
                "high_treatment": "Address underlying cause, monitor levels"
            }
        }
    
    def add_medical_knowledge(self, knowledge: Dict[str, Any]):
        """Add medical knowledge to the vector database."""
        content = f"""
        Marker: {knowledge['marker']}
        Description: {knowledge['description']}
        Normal Range: {knowledge['normal_range']}
        Low Symptoms: {knowledge.get('low_symptoms', 'N/A')}
        Low Causes: {knowledge.get('low_causes', 'N/A')}
        Low Treatment: {knowledge.get('low_treatment', 'N/A')}
        High Symptoms: {knowledge.get('high_symptoms', 'N/A')}
        High Causes: {knowledge.get('high_causes', 'N/A')}
        High Treatment: {knowledge.get('high_treatment', 'N/A')}
        """
        
        chunks = self.text_splitter.split_text(content)
        
        for i, chunk in enumerate(chunks):
            self.medical_knowledge_collection.add(
                documents=[chunk],
                metadatas=[{
                    "marker": knowledge['marker'],
                    "type": "medical_knowledge",
                    "chunk_id": i
                }],
                ids=[f"medical_{knowledge['marker']}_{i}_{uuid.uuid4()}"]
            )
    
    def index_user_markers(self, user_id: str, markers: List[Dict[str, Any]], source: str = "manual"):
        """Index user's health markers for retrieval."""
        if not RAG_AVAILABLE or not hasattr(self, 'markers_collection'):
            # Fallback mode
            if user_id not in self.markers_storage:
                self.markers_storage[user_id] = []
            self.markers_storage[user_id].extend(markers)
            return
        
        for marker in markers:
            content = f"""
            User Marker: {marker.get('name', 'Unknown')}
            Value: {marker.get('value', 'N/A')} {marker.get('unit', '')}
            Status: {marker.get('status', 'normal')}
            Normal Range: {marker.get('normal_range', 'N/A')}
            Recommendation: {marker.get('recommendation', 'N/A')}
            Source: {source}
            """
            
            chunks = self.text_splitter.split_text(content)
            
            for i, chunk in enumerate(chunks):
                self.markers_collection.add(
                    documents=[chunk],
                    metadatas=[{
                        "user_id": user_id,
                        "marker_name": marker.get('name', 'Unknown'),
                        "marker_value": str(marker.get('value', '')),
                        "marker_status": marker.get('status', 'normal'),
                        "source": source,
                        "timestamp": datetime.now().isoformat(),
                        "chunk_id": i
                    }],
                    ids=[f"marker_{user_id}_{marker.get('name', 'Unknown')}_{i}_{uuid.uuid4()}"]
                )
    
    def index_chat_history(self, user_id: str, chat_history: List[Dict[str, str]]):
        """Index chat history for context retrieval."""
        for message in chat_history:
            content = f"Role: {message.get('role', 'unknown')}\nContent: {message.get('content', '')}"
            
            chunks = self.text_splitter.split_text(content)
            
            for i, chunk in enumerate(chunks):
                self.chat_history_collection.add(
                    documents=[chunk],
                    metadatas=[{
                        "user_id": user_id,
                        "role": message.get('role', 'unknown'),
                        "timestamp": datetime.now().isoformat(),
                        "chunk_id": i
                    }],
                    ids=[f"chat_{user_id}_{message.get('role', 'unknown')}_{i}_{uuid.uuid4()}"]
                )
    
    def retrieve_relevant_context(self, user_id: str, query: str, top_k: int = 5) -> Dict[str, Any]:
        """Retrieve relevant context for a user query using semantic search."""
        if not RAG_AVAILABLE or not hasattr(self, 'markers_collection'):
            # Fallback mode - simple keyword matching
            return self._retrieve_context_fallback(user_id, query)
        
        # Get user's markers
        user_markers = self.markers_collection.query(
            query_texts=[query],
            n_results=top_k,
            where={"user_id": user_id}
        )
        
        # Get relevant medical knowledge
        medical_knowledge = self.medical_knowledge_collection.query(
            query_texts=[query],
            n_results=top_k
        )
        
        # Get recent chat history
        chat_history = self.chat_history_collection.query(
            query_texts=[query],
            n_results=top_k,
            where={"user_id": user_id}
        )
        
        # Combine and rank results
        all_results = {
            "user_markers": user_markers,
            "medical_knowledge": medical_knowledge,
            "chat_history": chat_history
        }
        
        return all_results
    
    def _retrieve_context_fallback(self, user_id: str, query: str) -> Dict[str, Any]:
        """Fallback context retrieval using simple keyword matching."""
        query_lower = query.lower()
        
        # Get user's markers with better matching
        user_markers = []
        if user_id in self.markers_storage:
            for marker in self.markers_storage[user_id]:
                marker_name = marker.get('name', '').lower()
                marker_words = marker_name.split()
                
                # Check for exact match or partial matches
                if (marker_name in query_lower or 
                    any(word in query_lower for word in marker_words if len(word) > 2) or
                    any(synonym in query_lower for synonym in self._get_marker_synonyms(marker_name))):
                    user_markers.append(marker)
        
        # Get relevant medical knowledge with better matching
        medical_knowledge = []
        for marker_name, knowledge in self.medical_knowledge.items():
            if (marker_name.lower() in query_lower or 
                any(synonym in query_lower for synonym in self._get_marker_synonyms(marker_name))):
                medical_knowledge.append({
                    "marker": marker_name,
                    "content": str(knowledge)
                })
        
        return {
            "user_markers": {"documents": [str(m) for m in user_markers], "metadatas": [{"marker_name": m.get('name', '')} for m in user_markers]},
            "medical_knowledge": {"documents": [k["content"] for k in medical_knowledge], "metadatas": [{"marker": k["marker"]} for k in medical_knowledge]},
            "chat_history": {"documents": [], "metadatas": []}
        }
    
    def _get_marker_synonyms(self, marker_name: str) -> List[str]:
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
    
    def get_marker_context(self, user_id: str, marker_name: str) -> Dict[str, Any]:
        """Get specific context for a particular marker."""
        # Get user's specific marker data
        marker_data = self.markers_collection.query(
            query_texts=[marker_name],
            n_results=10,
            where={"user_id": user_id, "marker_name": marker_name.lower()}
        )
        
        # Get medical knowledge for this marker
        medical_knowledge = self.medical_knowledge_collection.query(
            query_texts=[marker_name],
            n_results=5,
            where={"marker": marker_name.lower()}
        )
        
        return {
            "marker_data": marker_data,
            "medical_knowledge": medical_knowledge
        }
    
    def search_similar_markers(self, user_id: str, query: str) -> List[Dict[str, Any]]:
        """Search for markers similar to the query."""
        results = self.markers_collection.query(
            query_texts=[query],
            n_results=10,
            where={"user_id": user_id}
        )
        
        return results
    
    def get_user_markers_summary(self, user_id: str) -> Dict[str, Any]:
        """Get a summary of all user's markers."""
        all_markers = self.markers_collection.get(
            where={"user_id": user_id}
        )
        
        # Group by marker name
        marker_summary = {}
        for i, metadata in enumerate(all_markers['metadatas']):
            marker_name = metadata.get('marker_name', 'Unknown')
            if marker_name not in marker_summary:
                marker_summary[marker_name] = {
                    'values': [],
                    'statuses': [],
                    'sources': set()
                }
            
            marker_summary[marker_name]['values'].append(all_markers['documents'][i])
            marker_summary[marker_name]['statuses'].append(metadata.get('marker_status', 'normal'))
            marker_summary[marker_name]['sources'].add(metadata.get('source', 'unknown'))
        
        # Convert sets to lists for JSON serialization
        for marker in marker_summary.values():
            marker['sources'] = list(marker['sources'])
        
        return marker_summary

    def extract_normal_range_from_text(self, marker_name: str, text: str) -> Optional[Dict[str, float]]:
        """Extract normal range for a marker from text using pattern matching."""
        text_lower = text.lower()
        marker_lower = marker_name.lower()
        
        # Look for patterns like "normal range: 1.7-2.2 mg/dL" or "reference: 3.5-5.0"
        patterns = [
            rf"{marker_lower}[^0-9]*normal[^0-9]*range[^0-9]*(\d+\.?\d*)[^0-9]*[-–—][^0-9]*(\d+\.?\d*)",
            rf"normal[^0-9]*range[^0-9]*(\d+\.?\d*)[^0-9]*[-–—][^0-9]*(\d+\.?\d*)[^0-9]*{marker_lower}",
            rf"{marker_lower}[^0-9]*reference[^0-9]*(\d+\.?\d*)[^0-9]*[-–—][^0-9]*(\d+\.?\d*)",
            rf"reference[^0-9]*(\d+\.?\d*)[^0-9]*[-–—][^0-9]*(\d+\.?\d*)[^0-9]*{marker_lower}",
            rf"{marker_lower}[^0-9]*(\d+\.?\d*)[^0-9]*[-–—][^0-9]*(\d+\.?\d*)[^0-9]*normal",
            rf"(\d+\.?\d*)[^0-9]*[-–—][^0-9]*(\d+\.?\d*)[^0-9]*{marker_lower}[^0-9]*normal"
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text_lower)
            if matches:
                try:
                    min_val = float(matches[0][0])
                    max_val = float(matches[0][1])
                    return {"min": min_val, "max": max_val}
                except (ValueError, IndexError):
                    continue
        
        # Look for single value patterns like "normal: <100" or "normal: >40"
        single_patterns = [
            rf"{marker_lower}[^0-9]*normal[^0-9]*[<>≤≥][^0-9]*(\d+\.?\d*)",
            rf"normal[^0-9]*[<>≤≥][^0-9]*(\d+\.?\d*)[^0-9]*{marker_lower}",
            rf"{marker_lower}[^0-9]*[<>≤≥][^0-9]*(\d+\.?\d*)[^0-9]*normal"
        ]
        
        for pattern in single_patterns:
            matches = re.findall(pattern, text_lower)
            if matches:
                try:
                    value = float(matches[0])
                    if '<' in pattern or '≤' in pattern:
                        return {"max": value}
                    elif '>' in pattern or '≥' in pattern:
                        return {"min": value}
                except (ValueError, IndexError):
                    continue
        
        return None

    def get_marker_knowledge(self, marker_name: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive knowledge for a specific marker."""
        if not RAG_AVAILABLE:
            return self.medical_knowledge.get(marker_name.lower())
        
        try:
            # Search in medical knowledge collection
            results = self.medical_knowledge_collection.query(
                query_texts=[f"marker {marker_name}"],
                n_results=5
            )
            
            if results['documents'] and results['documents'][0]:
                # Parse the knowledge from the retrieved text
                return self._parse_marker_knowledge(results['documents'][0][0], marker_name)
            
            return None
        except Exception as e:
            print(f"Error retrieving marker knowledge: {e}")
            return None

    def _parse_marker_knowledge(self, text: str, marker_name: str) -> Dict[str, Any]:
        """Parse marker knowledge from retrieved text."""
        knowledge = {
            "marker": marker_name,
            "description": "",
            "normal_range": "",
            "low_symptoms": "",
            "low_causes": "",
            "low_treatment": "",
            "high_symptoms": "",
            "high_causes": "",
            "high_treatment": ""
        }
        
        # Extract information using pattern matching
        lines = text.split('\n')
        for line in lines:
            line_lower = line.lower()
            if 'description:' in line_lower:
                knowledge["description"] = line.split(':', 1)[1].strip()
            elif 'normal range:' in line_lower:
                knowledge["normal_range"] = line.split(':', 1)[1].strip()
            elif 'low symptoms:' in line_lower:
                knowledge["low_symptoms"] = line.split(':', 1)[1].strip()
            elif 'low causes:' in line_lower:
                knowledge["low_causes"] = line.split(':', 1)[1].strip()
            elif 'low treatment:' in line_lower:
                knowledge["low_treatment"] = line.split(':', 1)[1].strip()
            elif 'high symptoms:' in line_lower:
                knowledge["high_symptoms"] = line.split(':', 1)[1].strip()
            elif 'high causes:' in line_lower:
                knowledge["high_causes"] = line.split(':', 1)[1].strip()
            elif 'high treatment:' in line_lower:
                knowledge["high_treatment"] = line.split(':', 1)[1].strip()
        
        return knowledge

    def get_intelligent_normal_range(self, marker_name: str, value: float, text: str = "") -> Dict[str, float]:
        """Get intelligent normal range for any marker."""
        # First, try to extract from provided text
        if text:
            extracted_range = self.extract_normal_range_from_text(marker_name, text)
            if extracted_range:
                return extracted_range
        
        # Get from medical knowledge base
        knowledge = self.get_marker_knowledge(marker_name)
        if knowledge and knowledge.get("normal_range"):
            return self._parse_normal_range_string(knowledge["normal_range"])
        
        # Fallback to intelligent estimation
        return self._estimate_normal_range(marker_name, value)

    def _parse_normal_range_string(self, range_str: str) -> Dict[str, float]:
        """Parse normal range from string like '1.7-2.2 mg/dL' or '<100'."""
        range_str = range_str.lower().strip()
        
        # Handle range patterns like "1.7-2.2" or "20-250"
        range_match = re.search(r'(\d+\.?\d*)[^0-9]*[-–—][^0-9]*(\d+\.?\d*)', range_str)
        if range_match:
            try:
                min_val = float(range_match.group(1))
                max_val = float(range_match.group(2))
                return {"min": min_val, "max": max_val}
            except ValueError:
                pass
        
        # Handle single value patterns like "<100" or ">40"
        single_match = re.search(r'([<>≤≥])\s*(\d+\.?\d*)', range_str)
        if single_match:
            try:
                operator = single_match.group(1)
                value = float(single_match.group(2))
                if operator in ['<', '≤']:
                    return {"max": value}
                elif operator in ['>', '≥']:
                    return {"min": value}
            except ValueError:
                pass
        
        return {}

    def _estimate_normal_range(self, marker_name: str, value: float) -> Dict[str, float]:
        """Estimate normal range based on marker type and value."""
        marker_lower = marker_name.lower()
        
        # Use more specific ranges based on marker characteristics
        if any(word in marker_lower for word in ['magnesium']):
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
        elif any(word in marker_lower for word in ['creatinine']):
            return {"min": 0.6, "max": 1.2}
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
        elif any(word in marker_lower for word in ['hemoglobin']):
            return {"min": 12, "max": 18}
        elif any(word in marker_lower for word in ['hematocrit']):
            return {"min": 36, "max": 50}
        elif any(word in marker_lower for word in ['wbc']):
            return {"min": 4.5, "max": 11.0}
        elif any(word in marker_lower for word in ['platelets']):
            return {"min": 150, "max": 450}
        elif any(word in marker_lower for word in ['rdw']):
            return {"min": 11.5, "max": 14.5}
        elif any(word in marker_lower for word in ['mcv']):
            return {"min": 80, "max": 100}
        elif any(word in marker_lower for word in ['mch']):
            return {"min": 27, "max": 32}
        elif any(word in marker_lower for word in ['mchc']):
            return {"min": 32, "max": 36}
        else:
            # Conservative estimate for unknown markers
            if value < 1:
                return {"min": 0, "max": 1}
            elif value < 10:
                return {"min": 0, "max": 10}
            elif value < 100:
                return {"min": 0, "max": 100}
            else:
                return {"min": 0, "max": value * 2}

    def _generate_marker_knowledge(self, marker_name: str, value: float, status: str) -> Dict[str, Any]:
        """Dynamically generate knowledge for unknown markers based on patterns."""
        marker_lower = marker_name.lower()
        
        # Generate basic knowledge structure
        knowledge = {
            "marker": marker_name,
            "description": f"{marker_name} is a health marker that your doctor uses to assess your overall health status.",
            "normal_range": "Consult your healthcare provider for normal ranges",
            "status": status,
            "value": value
        }
        
        # Add specific knowledge based on marker patterns
        if any(word in marker_lower for word in ["vitamin", "vit"]):
            knowledge["description"] = f"{marker_name} is a vitamin essential for various bodily functions."
            knowledge["low_treatment"] = f"Increase {marker_name} intake through diet and supplements under medical supervision."
            knowledge["high_treatment"] = f"Reduce {marker_name} supplementation and consult your healthcare provider."
        
        elif any(word in marker_lower for word in ["mineral", "calcium", "magnesium", "zinc", "iron", "copper", "selenium"]):
            knowledge["description"] = f"{marker_name} is a mineral essential for various bodily functions."
            knowledge["low_treatment"] = f"Increase {marker_name} intake through diet and supplements under medical supervision."
            knowledge["high_treatment"] = f"Reduce {marker_name} intake and consult your healthcare provider."
        
        elif any(word in marker_lower for word in ["enzyme", "alt", "ast", "alkaline", "phosphatase"]):
            knowledge["description"] = f"{marker_name} is an enzyme that indicates organ function and health."
            knowledge["low_treatment"] = f"Address underlying causes and consult your healthcare provider."
            knowledge["high_treatment"] = f"Address underlying causes and consult your healthcare provider."
        
        elif any(word in marker_lower for word in ["protein", "albumin", "globulin"]):
            knowledge["description"] = f"{marker_name} is a protein that plays important roles in bodily functions."
            knowledge["low_treatment"] = f"Increase protein intake and address underlying causes."
            knowledge["high_treatment"] = f"Address underlying causes and consult your healthcare provider."
        
        elif any(word in marker_lower for word in ["hormone", "thyroid", "insulin", "cortisol"]):
            knowledge["description"] = f"{marker_name} is a hormone that regulates various bodily processes."
            knowledge["low_treatment"] = f"Hormone replacement therapy may be needed under medical supervision."
            knowledge["high_treatment"] = f"Medications or surgery may be needed under medical supervision."
        
        return knowledge

# Global RAG manager instance
rag_manager = RAGManager()
