# Recommendation Validation Guide

This guide helps you validate that recommendations are accurate and appropriate for each user persona.

## Using MCP Inspector for Testing

The MCP Inspector is perfect for interactive testing. Here's how to use it:

### 1. Start the Inspector

```bash
source .venv/bin/activate
npx @modelcontextprotocol/inspector python -m app.mcp_server
```

### 2. Test Recommendations in Inspector

Once the inspector UI opens, you can test the `recommend` tool with different users:

#### Test Case 1: Premium User (user_001)

```json
{
  "user_id": "user_001",
  "query": "I'm looking for a 50-inch TV for my apartment"
}
```

**Expected**: Should recommend higher-end TVs (QLED, OLED) with premium prices ($1000+)

#### Test Case 2: Budget User (user_014)

```json
{
  "user_id": "user_014",
  "query": "I need a TV for my family"
}
```

**Expected**: Should recommend budget-friendly options ($300-600 range)

#### Test Case 3: Luxury User (user_006)

```json
{
  "user_id": "user_006",
  "query": "Show me the best TV available"
}
```

**Expected**: Should recommend premium/luxury models, price not a concern

#### Test Case 4: Art Collector (user_001, user_002)

```json
{
  "user_id": "user_001",
  "query": "I want a TV that looks like art"
}
```

**Expected**: Should recommend Samsung Frame TV or similar art-focused models

### 3. Validate User Profiles

Use the `get_user_profile` tool to verify persona data:

```json
{
  "user_id": "user_001"
}
```

Check that:

- Demographics match the persona
- Interests are correct
- Price sensitivity is set appropriately

### 4. Test Collaborative Filtering

1. Have user_001 like a specific item using `submit_feedback`
2. Query with user_007 (similar SF professional)
3. Check if the liked item appears with "similar_user_signal"

## Automated Validation Script

Run the validation script for systematic testing:

```bash
python scripts/validate_recommendations.py
```

This script will:

- Test multiple users with the same query
- Compare recommendations across different personas
- Check price sensitivity alignment
- Report validation warnings

## Manual Validation Checklist

For each recommendation, verify:

### ✅ Price Sensitivity Match

- **Luxury users** (user_006, user_012): Should see $1000+ items
- **Premium users** (user_001, user_004): Should see $800+ items
- **Mid-range users** (user_003, user_015): Should see $400-800 items
- **Budget users** (user_014): Should see $200-500 items

### ✅ Interest Alignment

- **Art collectors** (user_001, user_002, user_005): Should see Frame TV or design-focused options
- **Gamers** (user_007): Should see TVs with Game Mode features
- **Entertainment-focused** (user_003, user_009): Should see feature-rich Smart TVs

### ✅ Lifestyle Match

- **Urban professionals**: Compact, modern designs
- **Families**: Durable, family-friendly options
- **Retirees**: Value-conscious, comfortable options

### ✅ Style Preference

- **Modern minimalist**: Clean, sleek designs
- **Family-friendly**: Practical, durable options
- **Luxury contemporary**: High-end, premium brands

## Testing Scenarios

### Scenario 1: Same Query, Different Users

Query: "I need a 65-inch TV"

- **user_001** (SF premium): Should get QLED/OLED options
- **user_014** (Budget family): Should get budget-friendly options
- **user_006** (Luxury): Should get top-tier models

### Scenario 2: Interest-Based Queries

- **Art collector**: "TV that looks like art" → Frame TV
- **Gamer**: "Best TV for gaming" → Game Mode features
- **Entertainment**: "TV for watching movies" → High-quality picture

### Scenario 3: Collaborative Filtering

1. user_001 likes "item_bb_001" (Samsung QLED)
2. user_007 (similar SF professional) searches for TVs
3. Should see "item_bb_001" with "similar_user_signal: true"

## Common Issues to Watch For

### ❌ Price Mismatch

- Budget user getting $1500 TV
- Luxury user getting $300 TV
- **Fix**: Check price_sensitivity metadata and recommendation filtering

### ❌ Interest Mismatch

- Art collector not getting Frame TV
- Gamer not getting Game Mode TVs
- **Fix**: Ensure descriptions include relevant keywords for embedding

### ❌ No Personalization

- All users getting same recommendations
- **Fix**: Verify user profiles exist and embeddings are being used

### ❌ Collaborative Filtering Not Working

- No "similar_user_signal" flags
- **Fix**: Check that similar users have liked items, verify user embeddings

## Debugging Tips

1. **Check User Profile**:

   ```bash
   curl "http://localhost:8000/api/profile?user_id=user_001"
   ```

2. **Check Item Metadata**:

   ```bash
   # Use Pinecone console or API to verify item metadata
   ```

3. **Test Embeddings**:
   - Verify embeddings are being generated
   - Check embedding dimensions match index

4. **Verify Similarity Scores**:
   - Higher scores = better matches
   - Scores should vary by user

## Expected Results Summary

| User Type | Price Range | Key Features | Example Brands |
|-----------|------------|--------------|----------------|
| Luxury | $1000+ | Premium, exclusive | Samsung QLED, LG OLED, Sony |
| Premium | $800-1500 | High quality, modern | Samsung, LG, Sony |
| Mid-range | $400-800 | Good value, features | TCL, Hisense, Vizio |
| Budget | $200-500 | Basic, functional | TCL, Insignia, Hisense |

## Next Steps

After validation:

1. Fine-tune persona descriptions if recommendations don't match
2. Adjust embedding text to emphasize key attributes
3. Add more items to test edge cases
4. Test collaborative filtering with more user interactions
