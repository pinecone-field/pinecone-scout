#!/usr/bin/env python3
"""Script to populate Pinecone users_index with diverse user personas."""
import asyncio
import json
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.embedding_service import embedding_service
from app.services.pinecone_service import pinecone_service
from app.models import UserProfileMetadata
from app.config import settings


async def populate_users():
    """Read users from USER_POPULATE.txt, generate embeddings, and upsert to Pinecone."""
    
    try:
        # Read users from file
        users_file = Path(__file__).parent.parent / "USER_POPULATE.txt"
        
        if not users_file.exists():
            print(f"Error: {users_file} not found")
            return
        
        print(f"Reading users from {users_file}...")
        with open(users_file, 'r') as f:
            users = json.load(f)
        
        print(f"Found {len(users)} users to process\n")
        
        # Initialize Pinecone
        print("Initializing Pinecone...")
        await pinecone_service.initialize()
        print("✓ Pinecone initialized\n")
        
        # Process users
        successful = 0
        failed = 0
        
        for i, user_data in enumerate(users, 1):
            user_id = user_data["user_id"]
            print(f"Processing user {i}/{len(users)}: {user_id}...")
            
            try:
                # Build comprehensive description for embedding
                # Combine all persona information into a rich text description
                description_parts = [
                    user_data.get("description", ""),
                    f"Age range: {user_data.get('age_range', 'unknown')}",
                    f"Household size: {user_data.get('household_size', 'unknown')}",
                    f"City: {user_data.get('city', 'unknown')}",
                    f"Style preference: {user_data.get('style_preference', 'unknown')}",
                    f"Lifestyle: {user_data.get('lifestyle', 'unknown')}",
                    f"Price sensitivity: {user_data.get('price_sensitivity', 'unknown')}",
                    f"Shopping style: {user_data.get('shopping_style', 'unknown')}",
                ]
                
                if user_data.get("interests"):
                    interests_str = ", ".join(user_data["interests"])
                    description_parts.append(f"Interests: {interests_str}")
                
                full_description = ". ".join(description_parts)
                
                # Generate embedding from comprehensive description
                print(f"  Generating embedding...")
                embedding = await embedding_service.embed_text(full_description)
                print(f"  ✓ Generated embedding ({len(embedding)} dimensions)")
                
                # Create UserProfileMetadata
                metadata = UserProfileMetadata(
                    age_range=user_data.get("age_range"),
                    household_size=user_data.get("household_size"),
                    city=user_data.get("city"),
                    style_preference=user_data.get("style_preference"),
                    liked_items=user_data.get("liked_items", []),
                    disliked_items=user_data.get("disliked_items", [])
                )
                
                # Convert to dict and add additional metadata fields
                metadata_dict = metadata.model_dump()
                
                # Add extended metadata fields (Pinecone supports additional fields)
                if "interests" in user_data:
                    metadata_dict["interests"] = ",".join(user_data["interests"])
                if "lifestyle" in user_data:
                    metadata_dict["lifestyle"] = user_data["lifestyle"]
                if "price_sensitivity" in user_data:
                    metadata_dict["price_sensitivity"] = user_data["price_sensitivity"]
                if "shopping_style" in user_data:
                    metadata_dict["shopping_style"] = user_data["shopping_style"]
                
                # Upsert to Pinecone
                print(f"  Upserting to Pinecone...")
                await pinecone_service.upsert_user(
                    user_id=user_id,
                    vector=embedding,
                    metadata=metadata_dict
                )
                
                successful += 1
                print(f"  ✓ Successfully created user: {user_id}")
                print(f"    Location: {user_data.get('city', 'unknown')}, Age: {user_data.get('age_range', 'unknown')}, Household: {user_data.get('household_size', 'unknown')}")
                print()
                
            except Exception as e:
                failed += 1
                print(f"  ✗ Error processing user {user_id}: {e}")
                import traceback
                traceback.print_exc()
                print()
                continue
        
        print(f"{'='*60}")
        print(f"✅ Completed!")
        print(f"   Successfully created: {successful} users")
        if failed > 0:
            print(f"   Failed: {failed} users")
        print(f"   Users are now available in the '{settings.users_index_name}' index")
        print(f"{'='*60}")
        
    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Clean up
        await pinecone_service.close()


if __name__ == "__main__":
    asyncio.run(populate_users())

