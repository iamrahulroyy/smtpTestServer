from pydantic import BaseModel, EmailStr
from typing import List, Optional
from enum import Enum

class SMTPConnection(BaseModel):
    email: EmailStr
    username: Optional[str] = None
    password: str
    smtp_host: str
    smtp_port: int
    use_ssl: bool = False
    use_tls: bool = False

class EmailToSend(BaseModel):
    to: List[EmailStr]
    subject: str
    body: str
    is_html: bool = True

class ConnectionResponse(BaseModel):
    success: bool
    message: str
    connection_id: Optional[str] = None

class SendEmailResponse(BaseModel):
    success: bool
    message: str
