#!/usr/bin/env python3
"""Test script for predictive suggestions."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.services.predictive_module import predictive_module

async def test():
    """Test predictive suggestion with debug output."""
    context = "I just moved into a new place and need to get some furniture. It's a pain because I want it to look clean and modern but my old TV just looks like, well, a TV."
    user_id = "user_001"
    
    print("=" * 80)
    print("TESTING PREDICTIVE SUGGESTION")
    print("=" * 80)
    print(f"\nContext: {context}")
    print(f"User ID: {user_id}\n")
    
    # Test topic detection
    print("1. Testing topic detection...")
    try:
        topic = await predictive_module._detect_topic_advanced(context)
        print(f"   ✓ Topic detected: {topic}")
    except Exception as e:
        print(f"   ✗ Topic detection failed: {e}")
        import traceback
        traceback.print_exc()
        topic = None
    
    # Test should_suggest
    print(f"\n2. Testing should_suggest (topic: {topic})...")
    try:
        should = predictive_module._should_suggest(context, topic)
        print(f"   ✓ Should suggest: {should}")
    except Exception as e:
        print(f"   ✗ Should suggest check failed: {e}")
        import traceback
        traceback.print_exc()
        should = False
    
    if not should:
        print("\n   ⚠️  Suggestion blocked by _should_suggest()")
        return
    
    # Test full suggestion
    print(f"\n3. Testing full suggestion generation...")
    try:
        response = await predictive_module.generate_suggestion(
            user_id=user_id,
            conversation_context=context,
            detected_topic=topic
        )
        
        print(f"   ✓ Response received")
        print(f"   - Has suggestion: {response.suggestion is not None}")
        if response.suggestion:
            print(f"   - Suggestion text: {response.suggestion.text[:100]}...")
            print(f"   - Item ID: {response.suggestion.item_id}")
            print(f"   - Item name: {response.suggestion.item_name}")
        else:
            print(f"   - No suggestion returned")
    except Exception as e:
        print(f"   ✗ Suggestion generation failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    asyncio.run(test())

