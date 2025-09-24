from pydantic import BaseModel
from typing import Optional, List

class ChatMessage(BaseModel):
    message: str
    context: Optional[str] = None
    chat_session_id: Optional[str] = None

class ChatResponse(BaseModel):
    message: str
    chat_session_id: str
    has_context: Optional[bool] = False

class ChatAttachment(BaseModel):
    filename: str
    content_type: str
    file_size: int
    attachment_type: str
    processed_at: str
    
class ChatSession(BaseModel):
    session_id: str
    created_at: str
    attachments: List[ChatAttachment] = []
    message_count: int = 0