import os
from dotenv import load_dotenv
from pinecone import Pinecone
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext, Settings
from llama_index.vector_stores.pinecone import PineconeVectorStore
from llama_index.embeddings.openai import OpenAIEmbedding

# 1. Load Environment Variables
load_dotenv()

def ingest_factory_manuals():
    print("Initializing Pinecone connection...")

    # 2. Configure OpenAI Embeddings (1536 dimensions)
    Settings.embed_model = OpenAIEmbedding(
        model="text-embedding-ada-002",
        api_key=os.getenv("OPENAI_API_KEY")
    )

    # 3. Connect to your specific Pinecone Index
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    pinecone_index = pc.Index("nexus-giga-hybrid")

    # 4. Configure the Vector Store for Hybrid Search
    vector_store = PineconeVectorStore(
        pinecone_index=pinecone_index,
        add_sparse_vector=True,
    )
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    print("Reading V-101 Technical Manual from data/ directory...")
    # 5. Load the unstructured PDF data
    documents = SimpleDirectoryReader("./data").load_data()
    print(f"Loaded {len(documents)} document chunks.")

    print("Generating Hybrid Embeddings (Dense + Sparse) via OpenAI and pushing to Pinecone...")
    # 6. Build the index and push to the cloud
    index = VectorStoreIndex.from_documents(
        documents,
        storage_context=storage_context
    )

    print("✅ Phase 2 Ingestion Complete: Manual successfully embedded into Pinecone using OpenAI!")

if __name__ == "__main__":
    ingest_factory_manuals() 