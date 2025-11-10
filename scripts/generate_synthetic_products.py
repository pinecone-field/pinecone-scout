#!/usr/bin/env python3
"""Generate synthetic product data for testing."""
import asyncio
import json
import random
import sys
from pathlib import Path
from typing import List

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.embedding_service import embedding_service
from app.services.pinecone_service import pinecone_service
from app.config import settings


# Product data templates
BRANDS = {
    "televisions": ["Samsung", "LG", "Sony", "TCL", "Hisense", "Vizio", "Insignia", "Roku", "Sharp", "Panasonic"]
}

TECHNOLOGIES = {
    "televisions": ["LED", "QLED", "OLED", "Mini-LED", "MicroLED"]
}

RESOLUTIONS = ["4K UHD", "8K UHD", "1080p Full HD"]

FEATURES = {
    "televisions": [
        "Smart TV", "HDR10", "HDR10+", "Dolby Vision", "Game Mode", "Voice Control",
        "Alexa Built-in", "Google Assistant", "Apple AirPlay", "Wi-Fi", "Bluetooth",
        "HDMI 2.1", "USB Ports", "Ethernet", "Screen Mirroring", "App Store",
        "4K Upscaling", "Local Dimming", "Quantum Dot", "Perfect Blacks",
        "Object Tracking Sound", "Acoustic Surface Audio", "IMAX Enhanced"
    ]
}

SIZES = {
    "televisions": ["32", "43", "50", "55", "65", "75", "85", "98"]
}

PRICE_RANGES = {
    "televisions": {
        "budget": (200, 500),
        "mid": (500, 1000),
        "premium": (1000, 2000),
        "luxury": (2000, 5000)
    }
}


def generate_tv_description(brand: str, size: str, tech: str, resolution: str, features: List[str], price: float) -> str:
    """Generate a realistic TV description."""
    price_tier = "budget" if price < 500 else "mid" if price < 1000 else "premium" if price < 2000 else "luxury"
    
    description_parts = [
        f"{brand} {size}-inch {tech} {resolution} Smart TV"
    ]
    
    # Add technology-specific details
    if tech == "OLED":
        description_parts.append("with perfect blacks and infinite contrast ratio")
    elif tech == "QLED":
        description_parts.append("with Quantum Dot technology for vibrant colors")
    elif tech == "Mini-LED":
        description_parts.append("with advanced local dimming for superior contrast")
    
    # Add resolution details
    if resolution == "8K UHD":
        description_parts.append("delivering stunning 8K picture quality")
    elif resolution == "4K UHD":
        description_parts.append("featuring 4K Ultra HD resolution")
    
    # Add key features
    key_features = random.sample(features, min(5, len(features)))
    if "Smart TV" in key_features:
        description_parts.append("with built-in smart TV platform")
    if "Game Mode" in key_features:
        description_parts.append("optimized for gaming with low input lag")
    if "HDR10+" in key_features or "Dolby Vision" in key_features:
        description_parts.append("supporting advanced HDR formats")
    
    # Add price context
    if price_tier == "luxury":
        description_parts.append("Premium flagship model with cutting-edge technology")
    elif price_tier == "premium":
        description_parts.append("High-end model with advanced features")
    elif price_tier == "mid":
        description_parts.append("Great value with essential smart TV features")
    else:
        description_parts.append("Budget-friendly option with solid performance")
    
    # Add use case
    if size in ["32", "43"]:
        description_parts.append("Perfect for bedrooms or small spaces")
    elif size in ["50", "55"]:
        description_parts.append("Ideal for living rooms and apartments")
    elif size in ["65", "75"]:
        description_parts.append("Great for large living rooms and home theaters")
    else:
        description_parts.append("Immersive viewing experience for large spaces")
    
    return ". ".join(description_parts) + "."


def generate_synthetic_products(category: str, count: int, price_range: tuple = None, sizes: List[str] = None) -> List[dict]:
    """Generate synthetic products."""
    if category != "televisions":
        raise ValueError(f"Category '{category}' not yet supported")
    
    products = []
    brands = BRANDS[category]
    technologies = TECHNOLOGIES[category]
    features = FEATURES[category]
    available_sizes = sizes or SIZES[category]
    price_ranges = PRICE_RANGES[category]
    
    # Distribute across price tiers
    tier_counts = {
        "budget": count // 4,
        "mid": count // 2,
        "premium": count // 4,
        "luxury": count // 8
    }
    tier_counts["budget"] += count - sum(tier_counts.values())  # Adjust for rounding
    
    item_counter = 1
    
    for tier, tier_count in tier_counts.items():
        if tier_count == 0:
            continue
        
        tier_price_range = price_ranges[tier]
        if price_range:
            # Override with provided range, but still respect tier distribution
            tier_price_range = (
                max(price_range[0], tier_price_range[0]),
                min(price_range[1], tier_price_range[1])
            )
        
        for _ in range(tier_count):
            brand = random.choice(brands)
            size = random.choice(available_sizes)
            tech = random.choice(technologies)
            resolution = random.choice(RESOLUTIONS)
            
            # Price based on tier and size
            base_price = random.uniform(*tier_price_range)
            size_multiplier = {"32": 0.5, "43": 0.7, "50": 0.85, "55": 1.0, "65": 1.3, "75": 1.7, "85": 2.2, "98": 3.0}.get(size, 1.0)
            tech_multiplier = {"LED": 1.0, "QLED": 1.3, "OLED": 1.5, "Mini-LED": 1.4, "MicroLED": 2.0}.get(tech, 1.0)
            price = base_price * size_multiplier * tech_multiplier
            
            # Select features
            num_features = random.randint(5, 10)
            selected_features = random.sample(features, min(num_features, len(features)))
            
            # Generate description
            description = generate_tv_description(brand, size, tech, resolution, selected_features, price)
            
            # Generate item_id
            item_id = f"item_synth_{category[:3]}_{item_counter:04d}"
            
            # Generate URL - use a placeholder format that could be replaced with real URLs
            # For synthetic products, we'll use a generic format
            url = f"https://www.example-store.com/products/{item_id}"
            
            products.append({
                "item_id": item_id,
                "name": f"{brand} {size}-inch Class {tech} {resolution} Smart TV",
                "category": category,
                "price": round(price, 2),
                "description": description,
                "brand": brand,
                "features": selected_features,
                "size": size,
                "technology": tech,
                "resolution": resolution,
                "url": url
            })
            
            item_counter += 1
    
    return products


async def populate_synthetic_products(
    category: str = "televisions",
    count: int = 100,
    price_range: tuple = None,
    sizes: List[str] = None
):
    """Generate and populate synthetic products."""
    try:
        print(f"Generating {count} synthetic {category}...")
        items = generate_synthetic_products(category, count, price_range, sizes)
        print(f"✓ Generated {len(items)} products\n")
        
        # Initialize Pinecone
        print("Initializing Pinecone...")
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
                        "url": item.get("url", "")
                    }
                    
                    # Add optional fields
                    if item.get("size"):
                        metadata["size"] = item["size"]
                    if item.get("technology"):
                        metadata["technology"] = item["technology"]
                    if item.get("resolution"):
                        metadata["resolution"] = item["resolution"]
                    
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
                for item in batch[:3]:
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
    
    parser = argparse.ArgumentParser(description="Generate synthetic products")
    parser.add_argument("--category", default="televisions", help="Product category")
    parser.add_argument("--count", type=int, default=100, help="Number of products to generate")
    parser.add_argument("--min-price", type=float, help="Minimum price")
    parser.add_argument("--max-price", type=float, help="Maximum price")
    parser.add_argument("--sizes", help="Comma-separated list of sizes (e.g., '50,55,65,75')")
    
    args = parser.parse_args()
    
    price_range = None
    if args.min_price or args.max_price:
        price_range = (args.min_price or 0, args.max_price or 10000)
    
    sizes = None
    if args.sizes:
        sizes = [s.strip() for s in args.sizes.split(",")]
    
    asyncio.run(populate_synthetic_products(
        category=args.category,
        count=args.count,
        price_range=price_range,
        sizes=sizes
    ))

