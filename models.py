from pydantic import BaseModel, EmailStr
from typing import List, Optional

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

# Updated for fast metadata listing
class FetchEmailsResponse(BaseModel):
    success: bool
    message: str
    emails: List[dict] = []
    count: int = 0

# New model for full email details
class EmailDetailsResponse(BaseModel):
    success: bool
    message: str
    email: Optional[dict] = None
