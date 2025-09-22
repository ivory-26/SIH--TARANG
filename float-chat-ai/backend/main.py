"""
Float-Chat-AI Backend
Main entry point for the FastAPI application.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import os
from dotenv import load_dotenv
from loguru import logger

# Load environment variables from a .env file
load_dotenv()

# --- IMPROVEMENT: Use relative imports for robustness ---
from .services.data_processor import DataProcessor
from .services.ai_service import AIService
from .services.database import DatabaseService

# Initialize FastAPI app
app = FastAPI(
    title="Float-Chat-AI",
    description="Conversational AI interface for ARGO oceanographic data",
    version="1.0.0"
)

# --- IMPROVEMENT: More secure CORS configuration for development ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
data_processor = DataProcessor()
ai_service = AIService()
db_service = DatabaseService()

# Pydantic models for request/response validation
class QueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = None
    user_id: Optional[str] = "anonymous"

class QueryResponse(BaseModel):
    response: str
    data: Optional[Dict[str, Any]] = None
    visualization: Optional[Dict[str, Any]] = None
    session_id: str
    query_id: str

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint to confirm the server is running."""
    return {"status": "healthy", "service": "float-chat-ai-backend"}

# Main query endpoint
@app.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """Processes a user's natural language query."""
    try:
        logger.info(f"Processing query: '{request.query}'")
        
        parsed_query = await ai_service.parse_query(request.query)
        data_result = await data_processor.execute_query(parsed_query)
        
        ai_response = await ai_service.generate_response(
            original_query=request.query,
            data_result=data_result,
            parsed_query=parsed_query
        )
        
        visualization = None
        if data_result and data_result.get("success") and "data" in data_result:
            visualization = await data_processor.create_visualization(
                data_result["data"], 
                parsed_query.get("viz_type", "table")
            )
        
        session_id = request.session_id or f"session_{request.user_id}_{os.urandom(4).hex()}"
        
        # --- BUG FIX: Added the missing parsed_query to the database call ---
        query_id = await db_service.save_query_history(
            session_id=session_id, 
            user_query=request.query, 
            ai_response=ai_response, 
            data_result=data_result,
            parsed_query=parsed_query
        )
        
        return QueryResponse(
            response=ai_response,
            data=data_result,
            visualization=visualization,
            session_id=session_id,
            query_id=query_id
        )
        
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while processing your query.")

# Session management endpoints
@app.get("/sessions/{session_id}/history")
async def get_session_history(session_id: str):
    """Get query history for a session."""
    try:
        history = await db_service.get_session_history(session_id)
        return {"session_id": session_id, "history": history}
    except Exception as e:
        logger.error(f"Error retrieving session history: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve session history")

@app.get("/export/{query_id}")
async def export_results(query_id: str, format: str = "csv"):
    """Export query results in various formats."""
    try:
        exported_data = await data_processor.export_results(query_id, format)
        return {"query_id": query_id, "format": format, "download_url": exported_data}
    except Exception as e:
        logger.error(f"Error exporting results: {e}")
        raise HTTPException(status_code=500, detail="Export failed")

# This block allows running the server directly for development `python -m app.main`
if __name__ == "__main__":
    import uvicorn
    # Note: When running with `uvicorn app.main:app`, this block is not executed.
    # It's primarily for direct script execution.
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

