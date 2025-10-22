"""
complete_example.py - Full integration example
"""

from app.core.log_chunker import LogChunker
from app.core.embedding.embedder import Embedder
from app.core.embedding.indexer import InMemoryIndexer
from datetime import datetime


def main():
    print("=" * 70)
    print("Log Analysis System - Complete Example")
    print("=" * 70)
    
    # Configuration
    LOG_FILE_PATH = "data/python.log"
    INDEX_SAVE_PATH = "data/log_index"
    WINDOW_SIZE = 50
    OVERLAP = 10
    
    # Step 1: Initialize components
    print("\n[1/4] Initializing components...")
    chunker = LogChunker()
    embedder = Embedder(model_name="all-MiniLM-L6-v2")
    indexer = InMemoryIndexer(embedder=embedder, use_faiss=True)
    
    # Step 2: Chunk the log file
    print(f"\n[2/4] Chunking log file: {LOG_FILE_PATH}")
    print(f"  Window size: {WINDOW_SIZE}, Overlap: {OVERLAP}")
    
    chunks = list(chunker.invoke(
        file_path=LOG_FILE_PATH,
        window_size=WINDOW_SIZE,
        overlap=OVERLAP
    ))
    
    print(f"  Created {len(chunks)} chunks")
    
    # Step 3: Index the chunks
    print("\n[3/4] Indexing chunks (generating embeddings)...")
    indexer.add_chunks(chunks)
    
    # Show statistics
    stats = indexer.get_stats()
    print(f"\n  Index Statistics:")
    print(f"    Total chunks: {stats['num_documents']}")
    print(f"    Error chunks: {stats['num_errors']}")
    print(f"    Embedding dimension: {stats['dimension']}")
    print(f"    Time range: {stats['earliest_log']} to {stats['latest_log']}")
    
    # Step 4: Save the index
    print(f"\n[4/4] Saving index to: {INDEX_SAVE_PATH}")
    indexer.save(INDEX_SAVE_PATH)
    
    # ========== Interactive Search Demo ==========
    print("\n" + "=" * 70)
    print("Interactive Search Demo")
    print("=" * 70)
    
    # Example queries
    queries = [
        {
            "query": "database connection timeout",
            "description": "Find database connection issues",
            "filters": {"filter_errors_only": True}
        },
        {
            "query": "authentication failed",
            "description": "Find authentication problems",
            "filters": {"top_k": 3}
        },
        {
            "query": "performance degradation",
            "description": "Find performance issues in last hour",
            "filters": {
                "time_range": (
                    datetime(2024, 10, 22, 9, 0, 0),
                    datetime(2024, 10, 22, 10, 0, 0)
                )
            }
        }
    ]
    
    for i, example in enumerate(queries, 1):
        print(f"\n--- Query {i}: {example['description']} ---")
        print(f"Search: '{example['query']}'")
        print(f"Filters: {example['filters']}")
        
        results = indexer.search(example['query'], **example['filters'])
        
        if not results:
            print("  No results found")
            continue
        
        for j, result in enumerate(results, 1):
            print(f"\n  Result {j}:")
            print(f"    Chunk ID: {result['chunk_id']}")
            print(f"    Similarity: {result['score']:.4f}")
            print(f"    Has Error: {result['metadata']['has_error']}")
            print(f"    Log Levels: {result['metadata']['log_levels']}")
            print(f"    Timestamp: {result['metadata']['start_timestamp']}")
            print(f"    Preview: {result['text'][:150]}...")
    
    # ========== Reload Demo ==========
    print("\n" + "=" * 70)
    print("Reload Demo - Loading saved index")
    print("=" * 70)
    
    # Create fresh indexer and load
    embedder_new = Embedder(model_name="all-MiniLM-L6-v2")
    indexer_new = InMemoryIndexer(embedder=embedder_new, use_faiss=True)
    indexer_new.load(INDEX_SAVE_PATH)
    
    print("\nTesting loaded index with search...")
    results = indexer_new.search("error", top_k=3, filter_errors_only=True)
    print(f"Found {len(results)} error chunks")
    
    for result in results:
        print(f"  - {result['chunk_id']}: score={result['score']:.4f}")
    
    print("\n" + "=" * 70)
    print("Complete! Your log analysis system is ready.")
    print("=" * 70)


if __name__ == "__main__":
    main()