import os
from llama_index.core import VectorStoreIndex, Document, Settings, StorageContext
from llama_index.core.vector_stores import ExactMatchFilter, MetadataFilters
from llama_index.llms.google_genai import GoogleGenAI
from llama_index.embeddings.google_genai import GoogleGenAIEmbedding
from llama_index.vector_stores.postgres import PGVectorStore
from sqlalchemy import make_url
from dotenv import load_dotenv

load_dotenv()

Settings.llm = GoogleGenAI(model="gemini-3.1-flash-lite-preview")
Settings.embed_model = GoogleGenAIEmbedding(model_name="gemini-embedding-2-preview")

# Connect to Postgres database
_pg_index_instance = None

def get_index():
    global _pg_index_instance
    if _pg_index_instance is None:
        # Provide a default connection string assuming a local postgres instance 
        db_url = os.getenv("PG_CONNECTION_STRING", "postgresql://postgres:password@localhost:5433/crag_db")
        url = make_url(db_url)
        
        # Bind LlamaIndex to Postgres with pgvector
        vector_store = PGVectorStore.from_params(
            database=url.database,
            host=url.host,
            password=url.password,
            port=url.port,
            user=url.username,
            table_name="course_embeddings",
            embed_dim=3072
        )
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        
        # Initialize global reference for usage later
        _pg_index_instance = VectorStoreIndex.from_vector_store(
            vector_store=vector_store,
            storage_context=storage_context
        )
        
    return _pg_index_instance

def ingest_module_content(tenant_id: str, module_id: str, text_content: str):
    """
    Ingests text for a specific educational module, applying strict tenant metadata 
    for multi-tenant data isolation.
    """
    index = get_index()
    
    # Create the document with explicit filtering metadata 
    doc = Document(
        text=text_content,
        metadata={
            "tenant_id": tenant_id,
            "module_id": module_id
        },
        excluded_llm_metadata_keys=["tenant_id", "module_id"] # Don't pass raw IDs to the LLM context directly
    )
    
    index.insert(doc)
    return {"status": "success", "doc_id": doc.doc_id}

def query_module_content(tenant_id: str, module_id: str, query_str: str):
    """
    Retrieves and answers a query strictly constrained to a single tenant and module.
    """
    index = get_index()
    
    # Apply hard pre-filters enforcing isolation (as requested in Security & Multi-Tenancy)
    filters = MetadataFilters(
        filters=[
            ExactMatchFilter(key="tenant_id", value=tenant_id),
            ExactMatchFilter(key="module_id", value=module_id)
        ]
    )
    
    # Configure retriever with filters
    
    # Assemble query engine
    query_engine = index.as_query_engine(
        similarity_top_k=3,
        filters=filters
    )
    
    # Execute RAG pipeline
    try:
        response = query_engine.query(query_str)
    except Exception as e:
        if "503" in str(e) or "UNAVAILABLE" in str(e):
            print("503 encountered, falling back to gemini-2.5-flash-lite...")
            from llama_index.llms.google_genai import GoogleGenAI
            fallback_llm = GoogleGenAI(model="gemini-2.5-flash-lite")
            query_engine = index.as_query_engine(
                similarity_top_k=3,
                filters=filters,
                llm=fallback_llm
            )
            response = query_engine.query(query_str)
        else:
            raise e

    if response is None or str(response) == "Empty Response":
        return ("No relevant information found for the given query. Try double checking tenant/module ID.")
    return str(response)
