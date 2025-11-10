#!/usr/bin/env python3
"""Script to populate Pinecone items_index with television products."""
import asyncio
import json
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.embedding_service import embedding_service
from app.services.pinecone_service import pinecone_service
from app.config import settings


async def populate_items():
    """Read items from ITEM_POPULATE.txt, generate embeddings, and upsert to Pinecone."""
    
    try:
        # Read items from file
        items_file = Path(__file__).parent.parent / "ITEM_POPULATE.txt"
        
        if not items_file.exists():
            print(f"Error: {items_file} not found")
            return
        
        print(f"Reading items from {items_file}...")
        with open(items_file, 'r') as f:
            items = json.load(f)
        
        print(f"Found {len(items)} items to process\n")
        
        # Initialize Pinecone
        print("Initializing Pinecone...")
        await pinecone_service.initialize()
        print("✓ Pinecone initialized\n")
        
        # Process items in batches for efficiency
        batch_size = 10
        total_items = len(items)
        successful = 0
        failed = 0
        
        for i in range(0, total_items, batch_size):
            batch = items[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (total_items + batch_size - 1) // batch_size
            
            print(f"Processing batch {batch_num}/{total_batches} ({len(batch)} items)...")
            
            try:
                # Prepare batch for embedding
                descriptions = [item["description"] for item in batch]
                
                # Generate embeddings
                print("  Generating embeddings...")
                embeddings = await embedding_service.embed_batch(descriptions)
                print(f"  ✓ Generated {len(embeddings)} embeddings")
                
                # Prepare vectors for upsert
                vectors = []
                for item, embedding in zip(batch, embeddings):
                    # Use item_id as the vector ID
                    vector_id = item["item_id"]
                    
                    # Prepare metadata (all fields except item_id)
                    # Note: Pinecone metadata values must be strings, numbers, booleans, or arrays of strings
                    metadata = {
                        "name": item["name"],
                        "category": item["category"],
                        "price": float(item["price"]),  # Ensure price is a float
                        "description": item["description"],  # Include description in metadata for reference
                        "brand": item.get("brand", ""),
                        "features": ",".join(item.get("features", [])),  # Convert list to comma-separated string
                        "url": item.get("url", "")
                    }
                    
                    vectors.append({
                        "id": vector_id,
                        "values": embedding,
                        "metadata": metadata
                    })
                
                # Upsert batch to Pinecone
                print(f"  Upserting {len(vectors)} vectors to Pinecone...")
                await pinecone_service.items_index.upsert(vectors=vectors)
                successful += len(vectors)
                print(f"  ✓ Successfully upserted {len(vectors)} items")
                
                # Print item names for confirmation
                for item in batch:
                    print(f"    - {item['name']} (${item['price']})")
                
            except Exception as e:
                failed += len(batch)
                print(f"  ✗ Error processing batch: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        print(f"\n{'='*60}")
        print(f"✅ Completed!")
        print(f"   Successfully upserted: {successful} items")
        if failed > 0:
            print(f"   Failed: {failed} items")
        print(f"   Items are now available in the '{settings.items_index_name}' index")
        print(f"{'='*60}")
        
    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Clean up
        await pinecone_service.close()


if __name__ == "__main__":
    asyncio.run(populate_items())

