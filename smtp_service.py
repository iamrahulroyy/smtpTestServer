import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from models import SMTPConnection, EmailToSend
import uuid
from typing import Dict

# Define the global storage HERE
stored_connections: Dict[str, dict] = {}

class SMTPService:
    
    @staticmethod
    def test_connection(config: SMTPConnection) -> dict:
        try:
            # Create SMTP connection based on SSL/TLS choice
            if config.use_ssl:
                # SSL connection (usually port 465)
                server = smtplib.SMTP_SSL(config.smtp_host, config.smtp_port)
            else:
                # Regular connection (usually port 587 with TLS)
                server = smtplib.SMTP(config.smtp_host, config.smtp_port)
                
                if config.use_tls:
                    server.starttls()  # Enable TLS
            
            # Test login
            username = config.username if config.username else config.email
            server.login(username, config.password)
            server.quit()
            
            return {
                "success": True,
                "message": f"SMTP connection successful to {config.smtp_host}"
            }
            
        except smtplib.SMTPAuthenticationError:
            return {
                "success": False,
                "message": "Authentication failed. Check email and password."
            }
        except smtplib.SMTPConnectError:
            return {
                "success": False,
                "message": f"Cannot connect to SMTP server {config.smtp_host}:{config.smtp_port}"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"SMTP connection failed: {str(e)}"
            }
    
    @staticmethod
    def send_email(config: SMTPConnection, email_data: EmailToSend) -> dict:
        try:
            # Create email message
            message = MIMEMultipart()
            message["From"] = config.email
            message["To"] = ", ".join(email_data.to)
            message["Subject"] = email_data.subject
            
            # Add body
            if email_data.is_html:
                message.attach(MIMEText(email_data.body, "html"))
            else:
                message.attach(MIMEText(email_data.body, "plain"))
            
            # Connect and send
            if config.use_ssl:
                server = smtplib.SMTP_SSL(config.smtp_host, config.smtp_port)
            else:
                server = smtplib.SMTP(config.smtp_host, config.smtp_port)
                if config.use_tls:
                    server.starttls()
            
            username = config.username if config.username else config.email
            server.login(username, config.password)
            server.sendmail(config.email, email_data.to, message.as_string())
            server.quit()
            
            return {
                "success": True,
                "message": f"Email sent successfully to {', '.join(email_data.to)}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to send email: {str(e)}"
            }

def store_connection(user_id: str, config: SMTPConnection) -> str:
    connection_id = str(uuid.uuid4())
    stored_connections[connection_id] = {
        "user_id": user_id,
        "config": config,  # Store the Pydantic model directly
        "created_at": "2025-08-21T15:35:00"
    }
    return connection_id

def get_connection(connection_id: str) -> SMTPConnection:
    if connection_id in stored_connections:
        return stored_connections[connection_id]["config"]
    return None

def get_all_connections() -> Dict[str, dict]:
    return stored_connections
