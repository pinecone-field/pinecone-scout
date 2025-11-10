#!/usr/bin/env python3
"""Script to validate recommendations against user personas."""
import asyncio
import json
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.recommendation_engine import recommendation_engine
from app.services.user_profile_manager import user_profile_manager
from app.config import settings


async def validate_recommendations():
    """Test recommendations for different personas and validate they make sense."""
    
    # Load user personas
    users_file = Path(__file__).parent.parent / "USER_POPULATE.txt"
    if not users_file.exists():
        print(f"Error: {users_file} not found")
        return
    
    with open(users_file, 'r') as f:
        users = json.load(f)
    
    # Test queries that should produce different results
    test_queries = [
        "I'm looking for a 50-inch TV for my apartment",
        "I need a premium TV with great picture quality",
        "What's a good budget TV option?",
        "Show me TVs that look good as art when not in use",
        "I want a TV for gaming",
        "Looking for a family-friendly TV that's durable"
    ]
    
    print("=" * 80)
    print("RECOMMENDATION VALIDATION TEST")
    print("=" * 80)
    print()
    
    # Test a few representative users
    test_users = [
        users[0],   # SF professional - premium, modern
        users[3],   # Budget-conscious family
        users[5],   # Luxury trust fund user
        users[10],  # Retired couple - value conscious
    ]
    
    for user in test_users:
        user_id = user["user_id"]
        print(f"\n{'='*80}")
        print(f"Testing User: {user_id}")
        print(f"  Location: {user.get('city', 'unknown')}")
        print(f"  Age: {user.get('age_range', 'unknown')}")
        print(f"  Household: {user.get('household_size', 'unknown')}")
        print(f"  Price Sensitivity: {user.get('price_sensitivity', 'unknown')}")
        print(f"  Style: {user.get('style_preference', 'unknown')}")
        print(f"  Interests: {', '.join(user.get('interests', []))}")
        print(f"{'='*80}\n")
        
        # Test with a relevant query
        query = "I'm looking for a 50-inch TV"
        print(f"Query: \"{query}\"")
        print()
        
        try:
            response = await recommendation_engine.get_recommendations(
                user_id=user_id,
                query=query,
                top_k=3
            )
            
            print("Recommendations:")
            for i, rec in enumerate(response.recommendations, 1):
                print(f"\n  {i}. {rec.name}")
                print(f"     Price: ${rec.price:.2f}")
                print(f"     Similarity: {rec.similarity_score:.3f}")
                print(f"     Rationale: {rec.rationale}")
                if rec.similar_user_signal:
                    print(f"     🔥 Popular with similar users")
                
                # Validation checks
                checks = []
                
                # Price sensitivity check
                price_sens = user.get("price_sensitivity", "")
                if price_sens == "luxury" and rec.price < 1000:
                    checks.append("⚠️  Price seems low for luxury user")
                elif price_sens == "budget" and rec.price > 800:
                    checks.append("⚠️  Price seems high for budget user")
                elif price_sens == "premium" and rec.price < 500:
                    checks.append("⚠️  Price seems low for premium user")
                else:
                    checks.append("✓ Price matches sensitivity")
                
                # Style check (basic - would need item style metadata)
                # Interest check (would need item interest mapping)
                
                if checks:
                    print(f"     Validation: {', '.join(checks)}")
            
            if response.user_context.memory_recall:
                print(f"\n  Memory: {response.user_context.memory_recall}")
            
            print()
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
            import traceback
            traceback.print_exc()
            print()
    
    print("\n" + "=" * 80)
    print("VALIDATION COMPLETE")
    print("=" * 80)
    print("\nManual Checks:")
    print("  - Do premium users get higher-priced items?")
    print("  - Do budget users get lower-priced items?")
    print("  - Do recommendations match user interests?")
    print("  - Are similar users being found correctly?")
    print()


async def compare_users():
    """Compare recommendations for different users with the same query."""
    print("\n" + "=" * 80)
    print("COMPARING RECOMMENDATIONS ACROSS USERS")
    print("=" * 80)
    print()
    
    # Load users
    users_file = Path(__file__).parent.parent / "USER_POPULATE.txt"
    with open(users_file, 'r') as f:
        users = json.load(f)
    
    # Same query for different users
    query = "I'm looking for a 65-inch TV"
    
    test_user_ids = ["user_001", "user_006", "user_010"]  # Premium, Luxury, Value-conscious
    
    print(f"Query: \"{query}\"\n")
    
    for user_id in test_user_ids:
        user = next((u for u in users if u["user_id"] == user_id), None)
        if not user:
            continue
        
        print(f"User: {user_id} ({user.get('city', 'unknown')}, {user.get('price_sensitivity', 'unknown')})")
        
        try:
            response = await recommendation_engine.get_recommendations(
                user_id=user_id,
                query=query,
                top_k=3
            )
            
            for rec in response.recommendations:
                print(f"  - {rec.name}: ${rec.price:.2f} (score: {rec.similarity_score:.3f})")
            
            print()
        except Exception as e:
            print(f"  ✗ Error: {e}\n")


if __name__ == "__main__":
    asyncio.run(validate_recommendations())
    asyncio.run(compare_users())

