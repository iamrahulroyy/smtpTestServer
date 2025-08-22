import smtplib
import imaplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from models import SMTPConnection, EmailToSend
import uuid
from typing import Dict
from datetime import datetime

stored_connections: Dict[str, dict] = {}

class SMTPService:
    
    @staticmethod
    def test_connection(config: SMTPConnection) -> dict:
        try:
            if config.use_ssl:
                server = smtplib.SMTP_SSL(config.smtp_host, config.smtp_port)
            else:
                server = smtplib.SMTP(config.smtp_host, config.smtp_port)
                if config.use_tls:
                    server.starttls()
            
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
            message = MIMEMultipart()
            message["From"] = config.email
            message["To"] = ", ".join(email_data.to)
            message["Subject"] = email_data.subject
            
            if email_data.is_html:
                message.attach(MIMEText(email_data.body, "html"))
            else:
                message.attach(MIMEText(email_data.body, "plain"))
            
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
    
    @staticmethod
    def fetch_emails_metadata(config: SMTPConnection, limit: int = 20) -> dict:
        """Ultra-fast bulk metadata fetching - only essential info"""
        try:
            imap_host = SMTPService._get_imap_host(config.smtp_host)
            
            mail = imaplib.IMAP4_SSL(imap_host, 993)
            username = config.username if config.username else config.email
            mail.login(username, config.password)
            mail.select('INBOX')
            
            # Search for all emails
            typ, data = mail.search(None, 'ALL')
            if typ != 'OK':
                return {
                    "success": False,
                    "message": "Failed to search emails",
                    "emails": []
                }
            
            ids = data[0].split()
            latest_ids = ids[-limit:] if len(ids) >= limit else ids
            
            if not latest_ids:
                mail.logout()
                return {
                    "success": True,
                    "message": "No emails found",
                    "emails": []
                }
             
            # Create comma-separated list of message IDs
            id_list = b','.join(latest_ids)
            
            # Fetch all headers at once - much faster!
            typ, msg_data_list = mail.fetch(id_list, '(ENVELOPE INTERNALDATE)')
            
            if typ != 'OK':
                mail.logout()
                return {
                    "success": False,
                    "message": "Failed to fetch email envelopes",
                    "emails": []
                }
            
            emails = []
            
            for i in range(0, len(msg_data_list), 2):  
                try:
                    if i + 1 >= len(msg_data_list):
                        break
                        
                    envelope_data = msg_data_list[i][1]
                    if not envelope_data:
                        continue
                    
                    email_id = latest_ids[len(emails)].decode() if len(emails) < len(latest_ids) else str(len(emails))
                    
                    envelope_str = envelope_data.decode('utf-8', errors='ignore')
                    
                    emails.append({
                        "id": email_id,
                        "message_id": f"msg_{email_id}",  
                        "from": "Loading...",  
                        "to": config.email,
                        "subject": "Click to load subject",  
                        "date": "Recent",  
                        "fetched_at": datetime.now().isoformat()
                    })
                    
                except Exception as e:
                    continue
            
            if not emails:
                for num in reversed(latest_ids):  
                    emails.append({
                        "id": num.decode(),
                        "message_id": f"msg_{num.decode()}",
                        "from": "📧 Click to load",
                        "to": config.email,
                        "subject": "📧 Click to view subject and content",
                        "date": "Recent",
                        "fetched_at": datetime.now().isoformat()
                    })
            
            mail.logout()
            
            return {
                "success": True,
                "message": f"Fetched {len(emails)} email IDs instantly",
                "emails": emails
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to fetch email metadata: {str(e)}",
                "emails": []
            }
    
    @staticmethod
    def fetch_email_details(config: SMTPConnection, email_id: str) -> dict:
        """Fetch complete email content when user clicks on specific email"""
        try:
            imap_host = SMTPService._get_imap_host(config.smtp_host)
            
            mail = imaplib.IMAP4_SSL(imap_host, 993)
            username = config.username if config.username else config.email
            mail.login(username, config.password)
            mail.select('INBOX')
            
            # Fetch complete email content
            typ, msg_data = mail.fetch(email_id.encode(), '(RFC822)')
            if typ != 'OK':
                mail.logout()
                return {
                    "success": False,
                    "message": "Failed to fetch email content",
                    "email": None
                }
            
            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)
            
            # Extract all email information
            subject = msg.get('Subject', 'No Subject')
            from_addr = msg.get('From', 'Unknown')
            to_addr = msg.get('To', 'Unknown')
            date = msg.get('Date', '')
            message_id = msg.get('Message-ID', '')
            
            # Extract body and attachments
            body = ""
            attachments = []
            
            if msg.is_multipart():
                for part in msg.walk():
                    content_disposition = str(part.get("Content-Disposition", ""))
                    
                    # Handle attachments
                    if "attachment" in content_disposition:
                        filename = part.get_filename()
                        if filename:
                            payload = part.get_payload(decode=True)
                            attachments.append({
                                "filename": filename,
                                "content_type": part.get_content_type(),
                                "size": len(payload) if payload else 0
                            })
                    else:
                        # Handle email body
                        content_type = part.get_content_type()
                        if content_type == "text/plain" and not body:
                            try:
                                payload = part.get_payload(decode=True)
                                body = payload.decode('utf-8', errors='ignore') if payload else ''
                            except:
                                body = str(part.get_payload())
                        elif content_type == "text/html" and not body:
                            try:
                                payload = part.get_payload(decode=True)
                                body = payload.decode('utf-8', errors='ignore') if payload else ''
                            except:
                                body = str(part.get_payload())
            else:
                # Non-multipart email
                try:
                    payload = msg.get_payload(decode=True)
                    body = payload.decode('utf-8', errors='ignore') if payload else ''
                except:
                    body = str(msg.get_payload())
            
            mail.logout()
            
            return {
                "success": True,
                "email": {
                    "id": email_id,
                    "message_id": message_id,
                    "subject": subject,
                    "from": from_addr,
                    "to": to_addr,
                    "date": date,
                    "body": body,
                    "attachments": attachments,
                    "attachment_count": len(attachments),
                    "fetched_at": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to fetch email details: {str(e)}",
                "email": None
            }
    
    @staticmethod
    def _get_imap_host(smtp_host: str) -> str:
        """Determine IMAP host from SMTP host"""
        if 'gmail' in smtp_host.lower():
            return 'imap.gmail.com'
        elif 'zoho' in smtp_host.lower():
            return 'imap.zoho.com'
        elif 'outlook' in smtp_host.lower() or 'office365' in smtp_host.lower():
            return 'outlook.office365.com'
        elif 'yahoo' in smtp_host.lower():
            return 'imap.mail.yahoo.com'
        else:
            return smtp_host.replace('smtp', 'imap')

def store_connection(user_id: str, config: SMTPConnection) -> str:
    """Store SMTP connection"""
    connection_id = str(uuid.uuid4())
    stored_connections[connection_id] = {
        "user_id": user_id,
        "config": config,
        "created_at": datetime.now().isoformat()
    }
    return connection_id

def get_connection(connection_id: str) -> SMTPConnection:
    """Get stored SMTP connection"""
    if connection_id in stored_connections:
        return stored_connections[connection_id]["config"]
    return None

def get_all_connections() -> Dict[str, dict]:
    """Get all stored connections"""
    return stored_connections
