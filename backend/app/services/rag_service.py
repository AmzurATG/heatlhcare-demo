import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
import os
try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None
import numpy as np
from app.services.database_service import DatabaseService
from app.database import SessionLocal
from app.services.gemini_service import GeminiService
import logging
from datetime import datetime
import uuid
import re
import json
import pandas as pd

try:
    import google.generativeai as genai  # Fallback embedding provider
except Exception:
    genai = None

logger = logging.getLogger(__name__)

class RAGService:
    def __init__(self):
        self.persist_dir = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
        self.client = chromadb.PersistentClient(path=self.persist_dir)
        # Main patient collection
        self.collection = self.client.get_or_create_collection(
            name="patient_data",
            metadata={"hnsw:space": "cosine"}
        )
        # Staging collection for latest uploads (not yet saved to DB)
        self.staging_collection = self.client.get_or_create_collection(
            name="patient_data_staging",
            metadata={"hnsw:space": "cosine"}
        )
        # Encoder setup
        self.embedding_model_name = os.getenv("EMBEDDING_MODEL", "paraphrase-multilingual-MiniLM-L12-v2")
        self.encoder = None
        self.remote_embedder = None
        if SentenceTransformer is not None:
            try:
                self.encoder = SentenceTransformer(self.embedding_model_name)
                logger.info(f"Loaded embedding model: {self.embedding_model_name}")
            except Exception as e:
                logger.error(f"Failed to load embedding model '{self.embedding_model_name}': {e}")
                self.encoder = None
        if self.encoder is None and genai is not None:
            # Configure Google GenAI embedding fallback
            api_key = os.getenv("GEMINI_API_KEY")
            if api_key:
                try:
                    genai.configure(api_key=api_key)  # type: ignore[attr-defined]
                    self.remote_embed_model = os.getenv("REMOTE_EMBEDDING_MODEL", "text-embedding-004")
                    logger.info(f"Using remote embedding model: {self.remote_embed_model}")
                    self.remote_embedder = "google_genai"
                except Exception as e:
                    logger.error(f"Failed to initialize remote embeddings: {e}")
            else:
                logger.warning("GEMINI_API_KEY not set; remote embedding fallback disabled")
        if self.encoder is None and self.remote_embedder is None:
            logger.warning("No embedding provider available. RAG functionality will be limited.")
        self.gemini_service = GeminiService()
    
    def _chunk_text(self, text: str, chunk_size: int = 800, overlap: int = 100) -> List[str]:
        safe_text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", " ", text or "").strip()
        if not safe_text:
            return []
        chunks = []
        start = 0
        length = len(safe_text)
        while start < length:
            end = min(start + chunk_size, length)
            chunks.append(safe_text[start:end])
            if end == length:
                break
            start = max(0, end - overlap)
        return chunks

    def _embed_texts(self, texts: List[str]) -> List[List[float]]:
        if self.encoder is not None:
            return self.encoder.encode(texts).tolist()
        # Remote fallback
        if self.remote_embedder == "google_genai" and genai is not None:
            try:
                # Batch embed using Google GenAI
                result = genai.embed_content(model=self.remote_embed_model, content=texts)  # type: ignore[attr-defined]
                # API may return a dict with 'embedding' or 'embeddings'
                if isinstance(result, dict) and 'embeddings' in result:
                    vectors = result['embeddings']
                elif isinstance(result, dict) and 'embedding' in result:
                    vectors = [result['embedding']]
                else:
                    # Some SDK versions return an object with .embeddings
                    vectors = getattr(result, 'embeddings', None) or getattr(result, 'embedding', None)
                    if vectors is None:
                        raise RuntimeError("Unexpected embedding response format")
                    if not isinstance(vectors[0], (list, tuple)):
                        vectors = [vectors]
                return [list(map(float, v)) for v in vectors]
            except Exception as e:
                logger.error(f"Remote embedding failed: {e}")
        raise RuntimeError("Encoder not available")
    
    def _create_patient_text(self, patient_data: Dict[str, Any], raw_text: Optional[str] = None) -> str:
        parts: List[str] = []
        if patient_data.get("name"):
            parts.append(f"Patient Name: {patient_data['name']}")
        if patient_data.get("date_of_birth"):
            parts.append(f"Date of Birth: {patient_data['date_of_birth']}")
        if patient_data.get("diagnosis"):
            parts.append(f"Diagnosis: {patient_data['diagnosis']}")
        if patient_data.get("prescription"):
            parts.append(f"Prescription: {patient_data['prescription']}")
        if raw_text:
            parts.append(f"Details: {raw_text}")
        return " | ".join(parts)

    def _sanitize_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        sanitized: Dict[str, Any] = {}
        for k, v in (metadata or {}).items():
            if isinstance(v, (str, int, float, bool)) or v is None:
                sanitized[k] = v
            else:
                try:
                    sanitized[k] = json.dumps(v, ensure_ascii=False)
                except Exception:
                    sanitized[k] = str(v)
        return sanitized

    async def add_patient_to_vector_store(self, patient_data: Dict[str, Any], raw_text: Optional[str] = None):
        """Add patient data to vector store for RAG (DB-backed, canonical)."""
        try:
            if self.encoder is None and self.remote_embedder is None:
                logger.warning("Encoder not available, skipping vector store update")
                return
            base_text = self._create_patient_text(patient_data, raw_text)
            chunks = self._chunk_text(base_text)
            if not chunks:
                chunks = [base_text]
            embeddings = self._embed_texts(chunks)
            embeddings_np = np.array(embeddings, dtype=np.float32)
            ids = [f"patient_{patient_data['id']}_{i}" for i in range(len(chunks))]
            base_meta = {
                "patient_id": patient_data["id"],
                "name": patient_data.get("name", ""),
                "date_of_birth": patient_data.get("date_of_birth", ""),
                "type": "patient_record"
            }
            metadatas = []
            for i in range(len(chunks)):
                item_meta = {**base_meta, "chunk_index": i}
                metadatas.append(self._sanitize_metadata(item_meta))
            self.collection.add(embeddings=embeddings_np, documents=chunks, metadatas=metadatas, ids=ids)
            logger.info(f"Indexed patient {patient_data['id']} with {len(chunks)} chunks")
        except Exception as e:
            logger.error(f"Error adding patient to vector store: {str(e)}")
            raise

    async def add_staging_documents(self, upload_batch_id: str, text: str, metadata: Dict[str, Any]):
        """Index latest uploaded docs into staging collection for immediate chat availability."""
        try:
            if self.encoder is None and self.remote_embedder is None:
                logger.warning("Encoder not available, skipping staging index")
                return
            chunks = self._chunk_text(text)
            if not chunks:
                chunks = [text]
            embeddings = self._embed_texts(chunks)
            embeddings_np = np.array(embeddings, dtype=np.float32)
            ids = [f"staging_{upload_batch_id}_{i}" for i in range(len(chunks))]
            base_meta = {
                "type": "staging_document",
                "upload_batch_id": upload_batch_id
            }
            # Sanitize provided metadata first
            safe_extra = self._sanitize_metadata(metadata or {})
            metadatas = []
            for i in range(len(chunks)):
                item_meta = {**base_meta, **safe_extra, "chunk_index": i}
                metadatas.append(self._sanitize_metadata(item_meta))
            self.staging_collection.add(embeddings=embeddings_np, documents=chunks, metadatas=metadatas, ids=ids)
            logger.info(f"Staged {len(chunks)} chunks for batch {upload_batch_id}")
        except Exception as e:
            logger.error(f"Error adding staging documents: {e}")
            raise

    def _query_collection(self, collection, query_embedding: List[float], top_k: int) -> List[Dict[str, Any]]:
        results = collection.query(query_embeddings=[query_embedding], n_results=top_k, include=["documents", "metadatas", "distances"])
        hits: List[Dict[str, Any]] = []
        if (results and isinstance(results.get('documents'), list) and len(results['documents']) > 0 and results['documents'][0] is not None):
            documents = results['documents'][0]
            metadatas = results.get('metadatas', [[]])[0] or []
            distances = results.get('distances', [[]])[0] or []
            for i in range(len(documents)):
                metadata = metadatas[i] if i < len(metadatas) else {}
                distance = distances[i] if i < len(distances) else 0.5
                hits.append({
                    "content": documents[i],
                    "metadata": metadata,
                    "similarity_score": 1 - distance
                })
        return hits

    async def search_similar_patients(self, query: str, top_k: int = 8, upload_batch_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search both patient and staging collections; fall back to SQL if empty."""
        try:
            if self.encoder is None and self.remote_embedder is None:
                logger.warning("No embedding provider available, using SQL fallback")
                return self._sql_fallback(query, top_k)
            query_embedding = self._embed_texts([query])[0]
            results: List[Dict[str, Any]] = []
            # Prioritize staging if batch provided
            if upload_batch_id:
                staging_hits = self._query_collection(self.staging_collection, query_embedding, top_k)
                results.extend(staging_hits)
            # Always search patient collection
            patient_hits = self._query_collection(self.collection, query_embedding, top_k)
            results.extend(patient_hits)
            # If empty, fallback to SQL
            if not results:
                results = self._sql_fallback(query, top_k)
            return results[:top_k]
        except Exception as e:
            logger.error(f"Error searching similar patients: {str(e)}")
            return []

    def _sql_fallback(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        db = SessionLocal()
        try:
            db_service = DatabaseService(db)
            all_patients = db_service.get_all_patients()
            q = query.lower()
            scored: List[Dict[str, Any]] = []
            for p in all_patients:
                hay = " ".join(filter(None, [p.name, p.date_of_birth, p.diagnosis or "", p.prescription or ""]))
                score = 1.0 if q in hay.lower() else 0.0
                if score > 0.0:
                    scored.append({
                        "content": self._create_patient_text({
                            "name": p.name,
                            "date_of_birth": p.date_of_birth,
                            "diagnosis": p.diagnosis,
                            "prescription": p.prescription,
                            "id": p.id
                        }),
                        "metadata": {"patient_id": p.id, "name": p.name, "type": "patient_record"},
                        "similarity_score": score
                    })
            # Return top scoring approximate matches
            return sorted(scored, key=lambda x: x["similarity_score"], reverse=True)[:top_k]
        except Exception as e:
            logger.error(f"SQL fallback error: {e}")
            return []
        finally:
            db.close()
    
    async def generate_rag_response(self, query: str, upload_batch_id: Optional[str] = None) -> Dict[str, Any]:
        """Generate response using RAG combining staging and patient records."""
        try:
            similar_patients = await self.search_similar_patients(query, top_k=8, upload_batch_id=upload_batch_id)
            context = "\n\n".join([
                f"Record {i+1} ({p['metadata'].get('type','unknown')}): {p['content']}"
                for i, p in enumerate(similar_patients)
            ])
            response = await self.gemini_service.generate_chat_response(query, context)
            patient_ids = [p['metadata'].get('patient_id', '') for p in similar_patients if p['metadata'].get('patient_id')]
            sources = [p['metadata'].get('name', 'Unknown Patient') for p in similar_patients if p['metadata'].get('name')]
            return {
                "response": response,
                "sources": sources,
                "patient_ids": patient_ids,
                "context_used": len(similar_patients)
            }
        except Exception as e:
            logger.error(f"Error generating RAG response: {str(e)}")
            return {
                "response": "I'm sorry, I encountered an error while processing your request.",
                "sources": [],
                "patient_ids": [],
                "context_used": 0
            }
    
    async def refresh_vector_store(self):
        """Refresh vector store with all patients from database (recreate collections)."""
        try:
            # Recreate collections from scratch
            try:
                self.client.delete_collection("patient_data")
            except Exception:
                pass
            self.collection = self.client.get_or_create_collection(name="patient_data", metadata={"hnsw:space": "cosine"})
            # Rebuild from DB
            db = SessionLocal()
            try:
                db_service = DatabaseService(db)
                patients = db_service.get_all_patients()
                for patient in patients:
                    patient_dict = {
                        "id": patient.id,
                        "name": patient.name,
                        "date_of_birth": patient.date_of_birth,
                        "diagnosis": patient.diagnosis,
                        "prescription": patient.prescription
                    }
                    await self.add_patient_to_vector_store(patient_dict)
                logger.info(f"Refreshed vector store with {len(patients)} patients")
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Error refreshing vector store: {str(e)}")
            raise

    async def add_chat_attachment(
        self, 
        chat_session_id: str, 
        content: str, 
        metadata: dict
    ) -> None:
        """Add attachment content to chat session context (separate from RAG database)"""
        try:
            # Create a document ID for this attachment
            attachment_id = f"chat_{chat_session_id}_attachment_{metadata.get('filename', 'unknown')}"
            
            # Store in session context (completely separate from RAG database)
            # This is for attached files only, not for general document retrieval
            if not hasattr(self, 'chat_contexts'):
                self.chat_contexts = {}
            
            if chat_session_id not in self.chat_contexts:
                self.chat_contexts[chat_session_id] = {
                    "attachments": [],
                    "attached_files_context": "",  # Separate context for attached files
                    "created_at": datetime.now().isoformat()
                }
            
            # Add attachment to session context
            self.chat_contexts[chat_session_id]["attachments"].append({
                "attachment_id": attachment_id,
                "content": content,
                "metadata": metadata,
                "added_at": datetime.now().isoformat()
            })
            
            # Update ONLY the attached files context (not RAG database)
            self.chat_contexts[chat_session_id]["attached_files_context"] += f"\n\n--- ATTACHED FILE: {metadata.get('filename')} ---\n{content}"
            
            print(f"Added attachment to chat session {chat_session_id} (separate from RAG database)")
            
        except Exception as e:
            print(f"Error adding chat attachment: {str(e)}")
            raise
    
    async def get_chat_attachments(self, chat_session_id: str) -> List[dict]:
        """Get all attachments for a chat session"""
        try:
            if not hasattr(self, 'chat_contexts'):
                self.chat_contexts = {}
            
            if chat_session_id not in self.chat_contexts:
                return []
            
            return self.chat_contexts[chat_session_id].get("attachments", [])
        
        except Exception as e:
            print(f"Error retrieving chat attachments: {str(e)}")
            return []
    
    def get_chat_context(self, chat_session_id: str) -> str:
        """Get ONLY the attached files context (not RAG database context)"""
        try:
            if not hasattr(self, 'chat_contexts'):
                self.chat_contexts = {}
            
            if chat_session_id not in self.chat_contexts:
                return ""
            
            # Return only attached files context, not RAG database context
            return self.chat_contexts[chat_session_id].get("attached_files_context", "")
        
        except Exception as e:
            print(f"Error retrieving chat context: {str(e)}")
            return ""
    
    def _split_text(self, text: str, chunk_size: int = 1000) -> List[str]:
        """Split text into manageable chunks"""
        chunks = []
        words = text.split()
        current_chunk = []
        current_length = 0
        
        for word in words:
            if current_length + len(word) + 1 > chunk_size:
                if current_chunk:
                    chunks.append(" ".join(current_chunk))
                    current_chunk = [word]
                    current_length = len(word)
                else:
                    chunks.append(word)
            else:
                current_chunk.append(word)
                current_length += len(word) + 1
        
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        
        return chunks
