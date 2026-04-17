from fastapi import FastAPI, Request, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import io
import pypdf
from dotenv import load_dotenv

# Load all secrets and API keys located in the '.env' file
load_dotenv()

# Import our new RAG service
from services.rag_service import ingest_module_content, query_module_content

app = FastAPI(title="CRAG Backend", description="Backend for Educational RAG System")

# Add CORS middleware specifically for the frontend local runtime 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all for local dev testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ModuleQueryRequest(BaseModel):
    tenant_id: str
    module_id: str
    query: str

@app.get("/")
def health_check():
    return {"status": "ok"}

@app.post("/rag/ingest")
async def test_rag_ingest(
    tenant_id: str = Form(...),
    module_id: str = Form(...),
    file: UploadFile = File(...)
):
    """Adds educational content to the vector store exclusively for this tenant and module."""
    if not os.getenv("GOOGLE_API_KEY"):
        raise HTTPException(status_code=500, detail="GOOGLE_API_KEY environment variable not found.")
        
    try:
        content = await file.read()
        
        if file.filename.lower().endswith('.pdf'):
            # Parse PDF bytes directly into text
            pdf_reader = pypdf.PdfReader(io.BytesIO(content))
            text_content = ""
            for page in pdf_reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text_content += extracted + "\n"
        else:
            # Fallback to simple decoding for txt/md formats
            text_content = content.decode('utf-8', errors='ignore') 
        
        result = ingest_module_content(tenant_id, module_id, text_content)
        return {"status": "success", "filename": file.filename, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/rag/query")
def test_rag_query(request: ModuleQueryRequest):
    """Retrieves answers constrained to a specific module and educator tenant ID."""
    if not os.getenv("GOOGLE_API_KEY"):
        raise HTTPException(status_code=500, detail="GOOGLE_API_KEY environment variable not found.")
        
    answer = query_module_content(request.tenant_id, request.module_id, request.query)
    return {"answer": answer}

@app.post("/discord/webhook")

async def discord_webhook(request: Request):
    # Immediate 200 OK for Discord acknowledgment
    return {"type": 4, "data": {"content": "Processing your request..."}}

@app.post("/lti/launch")
async def lti_launch(request: Request):
    # Webhook endpoint for LTI 1.3 Canvas launches
    return {"status": "lti_launch_received"}
