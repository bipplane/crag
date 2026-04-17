from llama_index.core import VectorStoreIndex, Document, Settings
from llama_index.core.vector_stores import ExactMatchFilter, MetadataFilters
from llama_index.llms.gemini import Gemini
from llama_index.embeddings.gemini import GeminiEmbedding

# Replace OpenAI with Gemini (default reads from GOOGLE_API_KEY environment variable)
Settings.llm = Gemini(model="models/gemini-3.1-flash-lite-preview")
Settings.embed_model = GeminiEmbedding(model_name="models/gemini-embedding-2-preview")

# Using a global dictionary-based index for quick prototyping.
# In production, this will be swapped to Pinecone as specified in agent.md.
_global_index = None

def get_index():
    global _global_index
    if _global_index is None:
        _global_index = VectorStoreIndex.from_documents([])
    return _global_index

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
    response = query_engine.query(query_str)
    
    return str(response)
