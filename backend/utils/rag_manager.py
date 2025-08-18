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
    
    def _initialize_medical_knowledge(self):
        """Initialize the medical knowledge base with common health markers."""
        medical_knowledge = [
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
                "low_treatment": "Glucose tablets, juice, regular meals, medication adjustment"
            },
            {
                "marker": "tsh",
                "description": "Thyroid Stimulating Hormone regulates thyroid function and metabolism.",
                "normal_range": "0.4-4.0 mIU/L",
                "high_symptoms": "Fatigue, weight gain, cold intolerance, depression",
                "high_causes": "Hypothyroidism, thyroiditis, iodine deficiency",
                "high_treatment": "Thyroid hormone replacement (levothyroxine)",
                "low_symptoms": "Weight loss, heat intolerance, anxiety, rapid heartbeat",
                "low_causes": "Hyperthyroidism, Graves' disease, thyroid nodules",
                "low_treatment": "Anti-thyroid medications, radioactive iodine, surgery"
            }
        ]
        
        # Add medical knowledge to vector database
        for knowledge in medical_knowledge:
            self.add_medical_knowledge(knowledge)
    
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

# Global RAG manager instance
rag_manager = RAGManager()
