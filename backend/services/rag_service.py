import os
from pinecone import Pinecone
from llama_index.core import VectorStoreIndex, Document, Settings, StorageContext
from llama_index.core.vector_stores import ExactMatchFilter, MetadataFilters
from llama_index.llms.google_genai import GoogleGenAI
from llama_index.embeddings.google_genai import GoogleGenAIEmbedding
from llama_index.vector_stores.pinecone import PineconeVectorStore

Settings.llm = GoogleGenAI(model="gemini-3.1-flash-lite-preview")
Settings.embed_model = GoogleGenAIEmbedding(model_name="gemini-embedding-2-preview")

# Connect to the remote Pinecone database
_pinecone_index_instance = None

def get_index():
    global _pinecone_index_instance
    if _pinecone_index_instance is None:
        index_name = os.getenv("PINECONE_INDEX_NAME")
        pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        
        # Connect to your specific index
        pinecone_index = pc.Index("crag")
        
        # Bind LlamaIndex to Pinecone
        vector_store = PineconeVectorStore(pinecone_index=pinecone_index)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        
        # Initialize global reference for usage later
        _pinecone_index_instance = VectorStoreIndex.from_vector_store(
            vector_store=vector_store,
            storage_context=storage_context
        )
        
    return _pinecone_index_instance

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
    if response is None or str(response) == "Empty Response":
        return ("No relevant information found for the given query. Try double checking the tenant/module ID.")
    return str(response)
