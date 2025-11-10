#!/usr/bin/env python3
"""Import products from Best Buy API into Pinecone items_index."""
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import List, Optional

import httpx

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.embedding_service import embedding_service
from app.services.pinecone_service import pinecone_service
from app.config import settings


BESTBUY_API_BASE = "https://api.bestbuy.com/v1"


def fetch_products_from_bestbuy(
    category: str = "Televisions",
    limit: int = 100,
    brand: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
) -> List[dict]:
    """Fetch products from Best Buy API."""
    api_key = os.getenv("BESTBUY_API_KEY")
    if not api_key:
        raise ValueError("BESTBUY_API_KEY not found in environment variables")
    
    # Build search query
    query_parts = [f"categoryPath.id=abcat0101000"]  # TVs category
    
    if brand:
        query_parts.append(f"manufacturer={brand}")
    
    if min_price:
        query_parts.append(f"regularPrice>={min_price}")
    
    if max_price:
        query_parts.append(f"regularPrice<={max_price}")
    
    query = "&".join(query_parts)
    
    url = f"{BESTBUY_API_BASE}/products({query})"
    params = {
        "apiKey": api_key,
        "format": "json",
        "show": "sku,name,salePrice,regularPrice,shortDescription,longDescription,manufacturer,modelNumber,image,features.feature",
        "pageSize": min(limit, 100),  # Best Buy max is 100 per page
        "sort": "salePrice.asc"
    }
    
    products = []
    page = 1
    
    print(f"Fetching products from Best Buy API...")
    print(f"  Category: {category}")
    if brand:
        print(f"  Brand: {brand}")
    if min_price or max_price:
        print(f"  Price range: ${min_price or 0:.2f} - ${max_price or '∞'}")
    print(f"  Limit: {limit}")
    print()
    
    with httpx.Client() as client:
        while len(products) < limit:
            params["page"] = page
            response = client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            page_products = data.get("products", [])
            if not page_products:
                break
            
            products.extend(page_products)
            print(f"  Fetched page {page}: {len(page_products)} products (total: {len(products)})")
            
            if len(page_products) < params["pageSize"]:
                break
            
            page += 1
            
            # Rate limiting
            import time
            time.sleep(0.5)
    
    return products[:limit]


def transform_bestbuy_product(product: dict) -> dict:
    """Transform Best Buy product to our format."""
    # Extract features
    features = []
    if "features" in product:
        for feature_obj in product["features"]:
            if isinstance(feature_obj, dict) and "feature" in feature_obj:
                features.append(feature_obj["feature"])
    
    # Build description
    description_parts = []
    
    if product.get("shortDescription"):
        description_parts.append(product["shortDescription"])
    
    if product.get("longDescription"):
        description_parts.append(product["longDescription"])
    
    # Add features to description
    if features:
        description_parts.append(f"Features: {', '.join(features[:5])}")  # Limit to 5 features
    
    description = " ".join(description_parts)
    
    # Extract size from name or description
    size = None
    name = product.get("name", "")
    for size_str in ["32\"", "43\"", "50\"", "55\"", "65\"", "75\"", "85\"", "98\""]:
        if size_str in name or size_str in description:
            size = size_str.replace('"', '')
            break
    
    # Use sale price if available, otherwise regular price
    price = product.get("salePrice") or product.get("regularPrice", 0)
    
    # Generate item_id
    sku = str(product.get("sku", ""))
    item_id = f"item_bb_{sku}"
    
    return {
        "item_id": item_id,
        "name": name,
        "category": "televisions",
        "price": float(price),
        "description": description,
        "brand": product.get("manufacturer", ""),
        "features": features,
        "size": size,
        "model": product.get("modelNumber", ""),
    }


async def import_products(
    category: str = "Televisions",
    limit: int = 100,
    brand: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
):
    """Import products from Best Buy API to Pinecone."""
    try:
        # Fetch products
        bestbuy_products = fetch_products_from_bestbuy(
            category=category,
            limit=limit,
            brand=brand,
            min_price=min_price,
            max_price=max_price,
        )
        
        if not bestbuy_products:
            print("No products found")
            return
        
        print(f"\nTransforming {len(bestbuy_products)} products...")
        
        # Transform to our format
        items = [transform_bestbuy_product(p) for p in bestbuy_products]
        
        # Initialize Pinecone
        print("\nInitializing Pinecone...")
        await pinecone_service.initialize()
        print("✓ Pinecone initialized\n")
        
        # Process in batches
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
                    vector_id = item["item_id"]
                    
                    # Prepare metadata
                    metadata = {
                        "name": item["name"],
                        "category": item["category"],
                        "price": float(item["price"]),
                        "description": item["description"],
                        "brand": item.get("brand", ""),
                        "features": ",".join(item.get("features", [])),
                    }
                    
                    # Add optional fields if present
                    if item.get("size"):
                        metadata["size"] = item["size"]
                    if item.get("model"):
                        metadata["model"] = item["model"]
                    
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
                
                # Print sample items
                for item in batch[:3]:  # Show first 3
                    print(f"    - {item['name']} (${item['price']:.2f})")
                if len(batch) > 3:
                    print(f"    ... and {len(batch) - 3} more")
                
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
        print(f"{'='*60}\n")
        
    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await pinecone_service.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Import products from Best Buy API")
    parser.add_argument("--category", default="Televisions", help="Product category")
    parser.add_argument("--limit", type=int, default=100, help="Maximum number of products to import")
    parser.add_argument("--brand", help="Filter by brand (e.g., Samsung, LG)")
    parser.add_argument("--min-price", type=float, help="Minimum price filter")
    parser.add_argument("--max-price", type=float, help="Maximum price filter")
    
    args = parser.parse_args()
    
    # Check for API key
    if not os.getenv("BESTBUY_API_KEY"):
        print("Error: BESTBUY_API_KEY not found in environment variables")
        print("Get your API key from: https://developer.bestbuy.com/")
        print("Add it to your .env file: BESTBUY_API_KEY=your_key_here")
        sys.exit(1)
    
    asyncio.run(import_products(
        category=args.category,
        limit=args.limit,
        brand=args.brand,
        min_price=args.min_price,
        max_price=args.max_price,
    ))

