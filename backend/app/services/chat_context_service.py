from typing import Dict, Any, List, Optional
import uuid
import time
import logging

logger = logging.getLogger(__name__)

class ChatContextService:
    def __init__(self):
        # In-memory storage for chat contexts (in production, use Redis or database)
        self.chat_contexts: Dict[str, Dict[str, Any]] = {}
        # Cache for processed file summaries to avoid reprocessing
        self.file_processing_cache: Dict[str, str] = {}
    
    def create_session(self) -> str:
        """Create a new chat session and return session ID"""
        session_id = str(uuid.uuid4())
        self.chat_contexts[session_id] = {
            'session_id': session_id,
            'created_at': time.time(),
            'messages': [],
            'attached_files': [],
            'context_summary': "",
            'processed_file_summaries': []  # Cache processed summaries
        }
        return session_id
    
    def add_message(self, session_id: str, message: str, role: str = 'user') -> bool:
        """Add a message to the chat session"""
        if session_id not in self.chat_contexts:
            return False
        
        self.chat_contexts[session_id]['messages'].append({
            'role': role,
            'content': message,
            'timestamp': time.time()
        })
        return True
    
    def add_attached_file(self, session_id: str, file_data: Dict[str, Any]) -> bool:
        """Add an attached file to the chat context"""
        if session_id not in self.chat_contexts:
            return False
        
        # Add file to session context
        file_info = {
            'file_id': str(uuid.uuid4()),
            'name': file_data.get('name'),
            'type': file_data.get('type'),
            'content': file_data.get('content'),
            'processed_content': None,  # Will be filled when processed
            'uploaded_at': time.time()
        }
        
        self.chat_contexts[session_id]['attached_files'].append(file_info)
        return True
    
    def cache_file_summary(self, file_id: str, summary: str):
        """Cache processed file summary to avoid reprocessing"""
        self.file_processing_cache[file_id] = summary
    
    def get_cached_file_summary(self, file_id: str) -> Optional[str]:
        """Get cached file summary if available"""
        return self.file_processing_cache.get(file_id)
    
    def get_context(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get full context for a chat session"""
        return self.chat_contexts.get(session_id)
    
    def get_attached_files(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all attached files for a session"""
        context = self.chat_contexts.get(session_id, {})
        return context.get('attached_files', [])
    
    def get_optimized_context(self, session_id: str) -> str:
        """Get optimized context for LLM processing (reduced size)"""
        context = self.chat_contexts.get(session_id)
        if not context:
            return ""
        
        # Get last 3 message exchanges for context (not all messages)
        recent_messages = context['messages'][-6:]  # Last 6 messages (3 exchanges)
        message_context = "\n".join([f"{msg['role']}: {msg['content'][:200]}..." for msg in recent_messages])
        
        # Get cached file summaries instead of full content
        file_summaries = context.get('processed_file_summaries', [])
        file_context = "\n".join(file_summaries)
        
        return f"Recent conversation:\n{message_context}\n\nFile summaries:\n{file_context}"
    
    def add_processed_file_summary(self, session_id: str, summary: str):
        """Add processed file summary to session context"""
        if session_id in self.chat_contexts:
            self.chat_contexts[session_id]['processed_file_summaries'].append(summary)
    
    def update_context_summary(self, session_id: str, summary: str) -> bool:
        """Update the context summary for a session"""
        if session_id not in self.chat_contexts:
            return False
        
        self.chat_contexts[session_id]['context_summary'] = summary
        return True
    
    def get_session_list(self) -> List[Dict[str, Any]]:
        """Get list of all chat sessions"""
        sessions = []
        for session_id, context in self.chat_contexts.items():
            sessions.append({
                'session_id': session_id,
                'created_at': context['created_at'],
                'message_count': len(context['messages']),
                'file_count': len(context['attached_files'])
            })
        return sessions
    
    def clear_session(self, session_id: str) -> bool:
        """Clear a chat session"""
        if session_id in self.chat_contexts:
            del self.chat_contexts[session_id]
            return True
        return False

# Global instance
chat_context_service = ChatContextService()