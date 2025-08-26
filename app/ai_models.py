import os
import json
import numpy as np
import torch
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Any, Tuple, Optional
import logging
from app.config import settings
import pickle
import faiss
from pathlib import Path

class LegalAIModels:
    def __init__(self):
        self.embedding_model = None
        self.llm_model = None
        self.tokenizer = None
        self.vector_index = None
        self.models_loaded = False
        self.logger = logging.getLogger(__name__)
        
        # Load models
        self._load_models()
    
    def _load_models(self):
        """Load AI models and create vector index."""
        try:
            # Load embedding model
            self.logger.info("Loading embedding model...")
            self.embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)
            
            # Load LLM model
            self.logger.info("Loading LLM model...")
            self.tokenizer = AutoTokenizer.from_pretrained(settings.LLM_MODEL)
            self.llm_model = AutoModelForCausalLM.from_pretrained(settings.LLM_MODEL)
            
            # Create or load vector index
            self._setup_vector_index()
            
            self.models_loaded = True
            self.logger.info("All AI models loaded successfully")
            
        except Exception as e:
            self.logger.error(f"Error loading AI models: {e}")
            raise
    
    def _setup_vector_index(self):
        """Setup FAISS vector index for similarity search."""
        index_path = Path(settings.VECTOR_DB_PATH) / "legal_vectors.index"
        
        if index_path.exists():
            self.logger.info("Loading existing vector index...")
            self.vector_index = faiss.read_index(str(index_path))
        else:
            self.logger.info("Creating new vector index...")
            # Create a simple index for 768-dimensional vectors
            dimension = 768
            self.vector_index = faiss.IndexFlatIP(dimension)
    
    def get_embeddings(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for a list of texts."""
        if not self.models_loaded:
            raise RuntimeError("AI models not loaded")
        
        try:
            embeddings = self.embedding_model.encode(texts, convert_to_tensor=True)
            return embeddings.cpu().numpy()
        except Exception as e:
            self.logger.error(f"Error generating embeddings: {e}")
            raise
    
    def get_single_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for a single text."""
        return self.get_embeddings([text])[0]
    
    def add_vectors_to_index(self, vectors: np.ndarray, ids: List[str]):
        """Add vectors to the FAISS index."""
        if self.vector_index is None:
            raise RuntimeError("Vector index not initialized")
        
        try:
            # Normalize vectors for cosine similarity
            faiss.normalize_L2(vectors)
            self.vector_index.add(vectors)
            
            # Save updated index
            index_path = Path(settings.VECTOR_DB_PATH) / "legal_vectors.index"
            faiss.write_index(self.vector_index, str(index_path))
            
            self.logger.info(f"Added {len(vectors)} vectors to index")
            
        except Exception as e:
            self.logger.error(f"Error adding vectors to index: {e}")
            raise
    
    def search_similar_vectors(self, query_vector: np.ndarray, k: int = 10) -> Tuple[np.ndarray, np.ndarray]:
        """Search for similar vectors in the index."""
        if self.vector_index is None:
            raise RuntimeError("Vector index not initialized")
        
        try:
            # Normalize query vector
            query_vector = query_vector.reshape(1, -1)
            faiss.normalize_L2(query_vector)
            
            # Search
            similarities, indices = self.vector_index.search(query_vector, k)
            
            return similarities[0], indices[0]
            
        except Exception as e:
            self.logger.error(f"Error searching vectors: {e}")
            raise
    
    def semantic_search(self, query: str, k: int = 10) -> List[Tuple[float, int]]:
        """Perform semantic search using embeddings."""
        try:
            # Get query embedding
            query_embedding = self.get_single_embedding(query)
            
            # Search similar vectors
            similarities, indices = self.search_similar_vectors(query_embedding, k)
            
            # Return results as (similarity, index) tuples
            results = list(zip(similarities, indices))
            results.sort(key=lambda x: x[0], reverse=True)  # Sort by similarity
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error in semantic search: {e}")
            raise
    
    def generate_text(self, prompt: str, max_length: int = 200) -> str:
        """Generate text using the LLM model."""
        if not self.models_loaded:
            raise RuntimeError("AI models not loaded")
        
        try:
            # Encode input
            inputs = self.tokenizer.encode(prompt, return_tensors="pt", max_length=512, truncation=True)
            
            # Generate
            with torch.no_grad():
                outputs = self.llm_model.generate(
                    inputs,
                    max_length=max_length,
                    num_return_sequences=1,
                    temperature=0.7,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            # Decode output
            generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Remove the original prompt
            if generated_text.startswith(prompt):
                generated_text = generated_text[len(prompt):].strip()
            
            return generated_text
            
        except Exception as e:
            self.logger.error(f"Error generating text: {e}")
            raise
    
    def analyze_legal_text(self, text: str) -> Dict[str, Any]:
        """Analyze legal text and extract key information."""
        try:
            # Get embedding
            embedding = self.get_single_embedding(text)
            
            # Basic text analysis
            words = text.split()
            sentences = text.split('.')
            
            analysis = {
                'embedding': embedding.tolist(),
                'word_count': len(words),
                'sentence_count': len(sentences),
                'avg_sentence_length': len(words) / len(sentences) if sentences else 0,
                'complexity_score': self._calculate_complexity(text)
            }
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing legal text: {e}")
            raise
    
    def _calculate_complexity(self, text: str) -> float:
        """Calculate text complexity score."""
        # Simple complexity calculation based on word length and sentence structure
        words = text.split()
        if not words:
            return 0.0
        
        avg_word_length = sum(len(word) for word in words) / len(words)
        sentences = text.split('.')
        avg_sentence_length = len(words) / len(sentences) if sentences else 0
        
        # Normalize scores
        complexity = (avg_word_length * 0.3 + avg_sentence_length * 0.7) / 100
        return min(complexity, 1.0)
    
    def compare_texts(self, text1: str, text2: str) -> Dict[str, float]:
        """Compare two texts and return similarity metrics."""
        try:
            # Get embeddings
            embedding1 = self.get_single_embedding(text1)
            embedding2 = self.get_single_embedding(text2)
            
            # Calculate cosine similarity
            similarity = cosine_similarity([embedding1], [embedding2])[0][0]
            
            # Calculate other metrics
            jaccard_similarity = self._jaccard_similarity(text1, text2)
            
            return {
                'cosine_similarity': float(similarity),
                'jaccard_similarity': jaccard_similarity,
                'overall_similarity': (similarity + jaccard_similarity) / 2
            }
            
        except Exception as e:
            self.logger.error(f"Error comparing texts: {e}")
            raise
    
    def _jaccard_similarity(self, text1: str, text2: str) -> float:
        """Calculate Jaccard similarity between two texts."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    def save_models(self):
        """Save models to disk."""
        try:
            models_path = Path(settings.MODEL_PATH)
            models_path.mkdir(exist_ok=True)
            
            # Save embedding model
            embedding_path = models_path / "embedding_model"
            self.embedding_model.save(str(embedding_path))
            
            # Save LLM model
            llm_path = models_path / "llm_model"
            self.llm_model.save_pretrained(str(llm_path))
            self.tokenizer.save_pretrained(str(llm_path))
            
            self.logger.info("Models saved successfully")
            
        except Exception as e:
            self.logger.error(f"Error saving models: {e}")
            raise

# Global instance
ai_models = LegalAIModels()