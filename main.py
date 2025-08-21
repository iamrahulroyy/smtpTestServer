from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from models import SMTPConnection, EmailToSend, ConnectionResponse, SendEmailResponse
from smtp_service import SMTPService, store_connection, get_connection, get_all_connections

app = FastAPI(title="SMTP Email Integration")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "SMTP Email Integration API"}

@app.post("/api/smtp/test-connection")
def test_smtp_connection(config: SMTPConnection) -> ConnectionResponse:
    result = SMTPService.test_connection(config)
    
    return ConnectionResponse(
        success=result["success"],
        message=result["message"]
    )

@app.post("/api/smtp/connect") 
def connect_smtp(config: SMTPConnection, user_id: str) -> ConnectionResponse:
    # First test the connection
    test_result = SMTPService.test_connection(config)
    
    if test_result["success"]:
        # Store the connection
        connection_id = store_connection(user_id, config)
        
        return ConnectionResponse(
            success=True,
            message="SMTP connection stored successfully",
            connection_id=connection_id
        )
    else:
        return ConnectionResponse(
            success=False,
            message=test_result["message"]
        )

@app.post("/api/smtp/send-email")
def send_email(connection_id: str, email_data: EmailToSend) -> SendEmailResponse:
    # Get stored connection
    config = get_connection(connection_id)
    if not config:
        raise HTTPException(404, "SMTP connection not found")
    
    # Send email
    result = SMTPService.send_email(config, email_data)
    
    return SendEmailResponse(
        success=result["success"],
        message=result["message"]
    )

@app.get("/api/smtp/connections")
def get_connections():
    connections = []
    stored_connections = get_all_connections()
    
    for conn_id, data in stored_connections.items():
        connections.append({
            "connection_id": conn_id,
            "user_id": data["user_id"],
            "email": data["config"].email,
            "smtp_host": data["config"].smtp_host,
            "smtp_port": data["config"].smtp_port,
            "created_at": data["created_at"]
        })
    return {"connections": connections}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
