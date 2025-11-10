#!/usr/bin/env python3
"""Generate synthetic product data for furniture, cruises, and experiences."""
import asyncio
import json
import random
import sys
from pathlib import Path
from typing import List, Dict

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.embedding_service import embedding_service
from app.services.pinecone_service import pinecone_service
from app.config import settings


# Furniture data templates
FURNITURE_CATEGORIES = {
    "living_room": ["Sofa", "Coffee Table", "TV Stand", "Bookshelf", "Armchair", "Side Table", "Media Console", "Ottoman", "Sectional", "Entertainment Center"],
    "bedroom": ["Bed Frame", "Dresser", "Nightstand", "Wardrobe", "Desk", "Chair", "Mirror", "Storage Bench", "Headboard", "Chest of Drawers"],
    "kitchen": ["Dining Table", "Dining Chairs", "Kitchen Island", "Bar Stools", "Pantry Cabinet", "Kitchen Cart", "Wall Shelf", "Cutting Board", "Utensil Holder", "Spice Rack"],
    "bathroom": ["Vanity", "Medicine Cabinet", "Bathroom Shelf", "Towel Rack", "Shower Caddy", "Toilet Paper Holder", "Bathroom Mirror", "Storage Basket", "Soap Dispenser", "Toothbrush Holder"]
}

FURNITURE_MATERIALS = ["Wood", "Metal", "Glass", "Plastic", "Fabric", "Leather", "Rattan", "Bamboo", "Particle Board", "MDF"]
FURNITURE_STYLES = ["Modern", "Scandinavian", "Minimalist", "Industrial", "Rustic", "Traditional", "Mid-Century", "Contemporary", "Bohemian", "Farmhouse"]

FURNITURE_PRICE_RANGES = {
    "living_room": {"budget": (50, 200), "mid": (200, 600), "premium": (600, 1500), "luxury": (1500, 4000)},
    "bedroom": {"budget": (30, 150), "mid": (150, 500), "premium": (500, 1200), "luxury": (1200, 3000)},
    "kitchen": {"budget": (40, 180), "mid": (180, 550), "premium": (550, 1400), "luxury": (1400, 3500)},
    "bathroom": {"budget": (20, 100), "mid": (100, 300), "premium": (300, 800), "luxury": (800, 2000)}
}


# Cruise data templates
CRUISE_DESTINATIONS = {
    "Europe": ["Mediterranean", "Baltic Sea", "Norwegian Fjords", "Greek Islands", "British Isles", "Iberian Peninsula"],
    "Asia": ["Japan", "Southeast Asia", "China", "India", "Indonesia", "Philippines"],
    "Americas": ["Alaska", "Caribbean", "Panama Canal", "New England", "Pacific Coast", "Hawaii"],
    "Other": ["Antarctica", "Australia/New Zealand", "Middle East", "Africa", "Arctic", "Transatlantic"]
}

CRUISE_DURATIONS = [7, 10, 14, 21, 28]
CRUISE_THEMES = ["Cultural", "Adventure", "Relaxation", "Culinary", "History", "Nature", "Art", "Music", "Wellness"]

CRUISE_PRICE_RANGES = {
    "budget": (2000, 5000),
    "mid": (5000, 10000),
    "premium": (10000, 20000),
    "luxury": (20000, 50000)
}


# Experience data templates
EXPERIENCE_CATEGORIES = {
    "outdoor": ["Hiking Tour", "Kayaking Adventure", "Bike Tour", "Rock Climbing", "Surfing Lesson", "Snorkeling", "Zip Lining", "Camping Experience"],
    "cultural": ["Cooking Class", "Art Workshop", "Music Performance", "Historical Tour", "Museum Visit", "Local Market Tour", "Photography Walk", "Language Exchange"],
    "food": ["Food Tour", "Wine Tasting", "Farm Visit", "Chef's Table", "Street Food Tour", "Brewery Tour", "Cooking Experience", "Dining Experience"],
    "wellness": ["Yoga Retreat", "Spa Day", "Meditation Session", "Wellness Workshop", "Hot Springs", "Massage Experience", "Fitness Class", "Mindfulness Walk"],
    "entertainment": ["Concert", "Theater Show", "Comedy Night", "Dance Class", "Live Music", "Karaoke", "Game Night", "Trivia Night"]
}

EXPERIENCE_LOCATIONS = {
    "urban": ["Downtown", "Historic District", "Arts Quarter", "Waterfront", "Market Area", "Cultural Center"],
    "nature": ["Mountain", "Beach", "Forest", "Park", "Lake", "Desert", "Valley", "Coastline"],
    "rural": ["Countryside", "Vineyard", "Farm", "Village", "Ranch", "Countryside Estate"]
}

EXPERIENCE_DURATIONS = [1, 2, 3, 4, 6, 8]  # hours
EXPERIENCE_PRICE_RANGES = {
    "budget": (20, 75),
    "mid": (75, 200),
    "premium": (200, 500),
    "luxury": (500, 1500)
}


def generate_furniture_description(category: str, item_type: str, material: str, style: str, price: float) -> str:
    """Generate a realistic furniture description."""
    room_context = {
        "living_room": "Perfect for your living space",
        "bedroom": "Ideal for bedroom organization and comfort",
        "kitchen": "Great for kitchen functionality and style",
        "bathroom": "Perfect for bathroom storage and organization"
    }
    
    description_parts = [
        f"{style} {material} {item_type}",
        room_context.get(category, "Functional and stylish"),
        f"Designed with {style.lower()} aesthetics in mind",
        f"Made from quality {material.lower()} materials",
        "Easy to assemble and maintain"
    ]
    
    if price < 100:
        description_parts.append("Budget-friendly option")
    elif price < 500:
        description_parts.append("Great value for money")
    elif price < 1500:
        description_parts.append("Premium quality construction")
    else:
        description_parts.append("Luxury design and craftsmanship")
    
    return ". ".join(description_parts) + "."


def generate_cruise_description(destination: str, region: str, duration: int, theme: str, price: float) -> str:
    """Generate a realistic cruise description."""
    description_parts = [
        f"{duration}-day {theme.lower()} cruise",
        f"Exploring {destination} in {region}",
        "All-inclusive luxury experience",
        "Fine dining and world-class entertainment",
        "Expert guides and cultural enrichment"
    ]
    
    if "Mediterranean" in destination or "Greek" in destination:
        description_parts.append("Visit historic ports and ancient sites")
    elif "Alaska" in destination:
        description_parts.append("Wildlife viewing and glacier experiences")
    elif "Caribbean" in destination:
        description_parts.append("Tropical beaches and crystal-clear waters")
    elif "Norwegian" in destination or "Fjords" in destination:
        description_parts.append("Stunning natural landscapes and scenic views")
    
    if price > 20000:
        description_parts.append("Premium accommodations and exclusive amenities")
    elif price > 10000:
        description_parts.append("Comfortable staterooms and excellent service")
    else:
        description_parts.append("Great value with comfortable accommodations")
    
    return ". ".join(description_parts) + "."


def generate_experience_description(category: str, experience_type: str, location_type: str, location: str, duration: int, price: float) -> str:
    """Generate a realistic experience description."""
    description_parts = [
        f"{duration}-hour {experience_type}",
        f"Located in {location} ({location_type} setting)",
        "Led by local experts",
        "Small group experience for personalized attention"
    ]
    
    if category == "outdoor":
        description_parts.append("Adventure and nature-focused activity")
    elif category == "cultural":
        description_parts.append("Immerse yourself in local culture and traditions")
    elif category == "food":
        description_parts.append("Culinary journey through local flavors")
    elif category == "wellness":
        description_parts.append("Relaxation and wellness-focused experience")
    elif category == "entertainment":
        description_parts.append("Fun and engaging entertainment experience")
    
    if price < 100:
        description_parts.append("Affordable and accessible")
    elif price < 300:
        description_parts.append("Great value experience")
    else:
        description_parts.append("Premium experience with exclusive access")
    
    return ". ".join(description_parts) + "."


def generate_furniture_products(count_per_category: int = 5) -> List[Dict]:
    """Generate furniture products across all categories."""
    products = []
    item_counter = 1
    
    for category in FURNITURE_CATEGORIES.keys():
        for _ in range(count_per_category):
            item_type = random.choice(FURNITURE_CATEGORIES[category])
            material = random.choice(FURNITURE_MATERIALS)
            style = random.choice(FURNITURE_STYLES)
            
            # Price based on category and tier
            tier = random.choice(["budget", "mid", "premium", "luxury"])
            price_range = FURNITURE_PRICE_RANGES[category][tier]
            price = round(random.uniform(*price_range), 2)
            
            description = generate_furniture_description(category, item_type, material, style, price)
            
            item_id = f"item_furn_{category[:3]}_{item_counter:04d}"
            name = f"{style} {material} {item_type} - {category.replace('_', ' ').title()}"
            
            # Generate URL
            url = f"https://www.example-furniture.com/products/{item_id}"
            
            products.append({
                "item_id": item_id,
                "name": name,
                "category": f"furniture_{category}",
                "price": price,
                "description": description,
                "brand": "IKEA Style",
                "features": [style, material, item_type, category.replace("_", " ").title()],
                "url": url
            })
            
            item_counter += 1
    
    return products


def generate_cruise_products(count: int = 25) -> List[Dict]:
    """Generate cruise vacation packages."""
    products = []
    item_counter = 1
    
    for _ in range(count):
        region = random.choice(list(CRUISE_DESTINATIONS.keys()))
        destination = random.choice(CRUISE_DESTINATIONS[region])
        duration = random.choice(CRUISE_DURATIONS)
        theme = random.choice(CRUISE_THEMES)
        
        # Price based on duration and tier
        tier = random.choice(["budget", "mid", "premium", "luxury"])
        base_price_range = CRUISE_PRICE_RANGES[tier]
        duration_multiplier = duration / 7  # Scale with duration
        price = round(random.uniform(*base_price_range) * duration_multiplier, 2)
        
        description = generate_cruise_description(destination, region, duration, theme, price)
        
        item_id = f"item_cruise_{item_counter:04d}"
        name = f"{duration}-Day {theme} Cruise to {destination}"
        
        # Generate URL
        url = f"https://www.vikingcruises.com/cruises/{item_id}"
        
        products.append({
            "item_id": item_id,
            "name": name,
            "category": "cruises",
            "price": price,
            "description": description,
            "brand": "Viking Cruises",
            "features": [theme, destination, f"{duration} days", region],
            "url": url
        })
        
        item_counter += 1
    
    return products


def generate_experience_products(count_per_category: int = 5) -> List[Dict]:
    """Generate Airbnb-style experience products."""
    products = []
    item_counter = 1
    
    for category in EXPERIENCE_CATEGORIES.keys():
        for _ in range(count_per_category):
            experience_type = random.choice(EXPERIENCE_CATEGORIES[category])
            location_type = random.choice(list(EXPERIENCE_LOCATIONS.keys()))
            location = random.choice(EXPERIENCE_LOCATIONS[location_type])
            duration = random.choice(EXPERIENCE_DURATIONS)
            
            # Price based on duration and tier
            tier = random.choice(["budget", "mid", "premium", "luxury"])
            base_price_range = EXPERIENCE_PRICE_RANGES[tier]
            duration_multiplier = duration / 4  # Scale with duration
            price = round(random.uniform(*base_price_range) * duration_multiplier, 2)
            
            description = generate_experience_description(category, experience_type, location_type, location, duration, price)
            
            item_id = f"item_exp_{category[:3]}_{item_counter:04d}"
            name = f"{duration}-Hour {experience_type} in {location}"
            
            # Generate URL
            url = f"https://www.example-experiences.com/experiences/{item_id}"
            
            products.append({
                "item_id": item_id,
                "name": name,
                "category": f"experiences_{category}",
                "price": price,
                "description": description,
                "brand": "Local Experience",
                "features": [category, experience_type, location, f"{duration} hours"],
                "url": url
            })
            
            item_counter += 1
    
    return products


async def populate_extended_products():
    """Populate Pinecone with furniture, cruises, and experiences."""
    try:
        print("=" * 60)
        print("Generating Extended Product Catalog")
        print("=" * 60)
        
        # Generate products
        print("\nGenerating furniture products...")
        furniture_products = generate_furniture_products(count_per_category=5)  # 5 per category = 20 total
        print(f"✓ Generated {len(furniture_products)} furniture items")
        
        print("\nGenerating cruise packages...")
        cruise_products = generate_cruise_products(count=25)
        print(f"✓ Generated {len(cruise_products)} cruise packages")
        
        print("\nGenerating experience products...")
        experience_products = generate_experience_products(count_per_category=5)  # 5 per category = 25 total
        print(f"✓ Generated {len(experience_products)} experience items")
        
        all_products = furniture_products + cruise_products + experience_products
        print(f"\nTotal products to process: {len(all_products)}")
        
        # Initialize Pinecone
        print("\nInitializing Pinecone...")
        await pinecone_service.initialize()
        print("✓ Pinecone initialized\n")
        
        # Process items in batches
        batch_size = 10
        total_items = len(all_products)
        successful = 0
        failed = 0
        
        for i in range(0, total_items, batch_size):
            batch = all_products[i:i + batch_size]
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
    asyncio.run(populate_extended_products())

