from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import structlog
from datetime import datetime

from config import config
from agent import agent

logger = structlog.get_logger()

app = FastAPI(
    title="Calendar Booking Agent API",
    description="API for the conversational AI calendar booking agent",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatMessage(BaseModel):
    """Model for a chat message."""
    role: str  
    content: str
    timestamp: Optional[datetime] = None

class ChatRequest(BaseModel):
    """Model for chat request."""
    message: str
    chat_history: Optional[List[ChatMessage]] = None

class ChatResponse(BaseModel):
    """Model for chat response."""
    response: str
    timestamp: datetime

class HealthResponse(BaseModel):
    """Model for health check response."""
    status: str
    timestamp: datetime
    version: str

@app.on_event("startup")
async def startup_event():
    """Initialize the application on startup."""
    logger.info("Starting Calendar Booking Agent API")
    
    if not config.validate():
        logger.error("Configuration validation failed")
        raise RuntimeError("Configuration validation failed")
    
    logger.info("Calendar Booking Agent API started successfully")

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        version="1.0.0"
    )

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        logger.info("Received chat request", message_length=len(request.message))
        chat_history = []
        if request.chat_history:
            for msg in request.chat_history:
                if msg.role == "user":
                    from langchain.schema import HumanMessage
                    chat_history.append(HumanMessage(content=msg.content))
                elif msg.role == "assistant":
                    from langchain.schema import AIMessage
                    chat_history.append(AIMessage(content=msg.content))
        
        response = agent.process_message(request.message, chat_history)
        
        logger.info("Chat request processed successfully", 
                   response_length=len(response))
        
        return ChatResponse(
            response=response,
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error("Error processing chat request", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/")
async def root():
    
    return {
        "message": "Calendar Booking Agent API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "chat": "/chat"
        }
    }

@app.get("/docs")
async def get_docs():
   return {"message": "API documentation available at /docs"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=config.BACKEND_HOST,
        port=config.BACKEND_PORT,
        reload=True
    ) 