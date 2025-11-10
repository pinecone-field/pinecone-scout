# MCP Inspector Testing Guide

Quick reference for testing and validating recommendations using the MCP Inspector.

## Starting the Inspector

```bash
source .venv/bin/activate
npx @modelcontextprotocol/inspector python -m app.mcp_server
```

The inspector will open a web UI (usually `http://localhost:5173`).

## Testing Recommendations

### Step 1: List Available Tools

In the inspector, you should see 4 tools:

- `recommend`
- `submit_feedback`
- `get_user_profile`
- `predictive_suggest`

### Step 2: Test with Different Personas

#### Test 1: Premium Professional (user_001)

```json
{
  "user_id": "user_001",
  "query": "I'm looking for a 50-inch TV for my apartment"
}
```

**What to check:**

- ✅ Recommendations are $800+ (premium user)
- ✅ Modern, sleek designs (SF professional)
- ✅ QLED/OLED technology (quality-focused)

#### Test 2: Budget Family (user_014)

```json
{
  "user_id": "user_014",
  "query": "I need a TV for my family"
}
```

**What to check:**

- ✅ Recommendations are $200-600 (budget-conscious)
- ✅ Family-friendly features
- ✅ Good value options

#### Test 3: Luxury User (user_006)

```json
{
  "user_id": "user_006",
  "query": "Show me the best TV available"
}
```

**What to check:**

- ✅ Top-tier models ($1000+)
- ✅ Premium brands (Samsung, LG, Sony)
- ✅ Latest technology

#### Test 4: Art Collector (user_001 or user_002)

```json
{
  "user_id": "user_001",
  "query": "I want a TV that looks like art when not in use"
}
```

**What to check:**

- ✅ Samsung Frame TV should appear
- ✅ Art-focused features mentioned
- ✅ Design-oriented options

### Step 3: Verify User Profiles

Before testing recommendations, verify the user profile:

```json
{
  "user_id": "user_001"
}
```

**Check:**

- Age range matches persona
- City is correct
- Price sensitivity is set
- Interests are listed

### Step 4: Test Collaborative Filtering

1. **Have one user like an item:**

    ```json
    {
    "user_id": "user_001",
    "item_id": "item_bb_001",
    "feedback_type": "like"
    }
    ```

2. **Query with a similar user:**

    ```json
    {
    "user_id": "user_007",
    "query": "I'm looking for a TV"
    }
    ```

3. **Check for "🔥 Popular with similar users"** flag on the liked item

## Validation Checklist

For each recommendation set, verify:

### Price Alignment

- [ ] Premium users get $800+ items
- [ ] Budget users get $200-600 items
- [ ] Luxury users get $1000+ items
- [ ] Mid-range users get $400-800 items

### Interest Match

- [ ] Art collectors see Frame TV or design-focused options
- [ ] Gamers see Game Mode features
- [ ] Entertainment-focused see Smart TV features

### Similarity Scores

- [ ] Scores are reasonable (typically 0.7-0.95 for good matches)
- [ ] Scores vary appropriately
- [ ] Top recommendation has highest score

### User Context

- [ ] Memory recall appears when user has liked items
- [ ] Similar user signals appear when collaborative filtering finds matches

## Quick Test Matrix

| User ID | Persona | Expected Price Range | Key Interests |
|---------|---------|---------------------|---------------|
| user_001 | SF Premium Professional | $800-1500 | Art, travel, tech |
| user_006 | NY Luxury Trust Fund | $1000+ | Luxury, exclusivity |
| user_014 | Budget Family | $200-600 | Value, durability |
| user_010 | Affluent Couple | $800-1500 | Wine, entertaining |
| user_005 | Retired Couple | $400-800 | Value, comfort |

## Debugging in Inspector

### Check Tool Response

- Look at the raw JSON response
- Verify similarity scores
- Check metadata fields

### Compare Results

- Run same query with different users
- Compare price ranges
- Check if recommendations differ appropriately

### Test Edge Cases

- New user (no profile)
- User with many liked items
- User with disliked items
- Very specific queries vs. general queries

## Common Patterns to Verify

1. **Price Sensitivity Works:**
   - user_006 (luxury) should never see $300 TVs
   - user_014 (budget) should rarely see $1500 TVs

2. **Interests Matter:**
   - Art collectors should see Frame TV
   - Tech enthusiasts should see latest features

3. **Collaborative Filtering:**
   - Similar users should influence recommendations
   - "Popular with similar users" should appear

4. **Memory Works:**
   - Users with liked items should see memory recall
   - Previously liked items shouldn't appear again (unless requested)

## Tips for Effective Testing

1. **Test systematically**: Go through each persona type
2. **Compare side-by-side**: Same query, different users
3. **Check scores**: Higher scores = better matches
4. **Verify metadata**: Use `get_user_profile` to confirm persona data
5. **Test feedback loop**: Like items, then query again

## Expected Behaviors

✅ **Good Signs:**

- Different users get different recommendations
- Price ranges match user sensitivity
- Similarity scores are reasonable (0.7+)
- Memory recall appears for users with history
- Collaborative filtering flags appear

❌ **Red Flags:**

- All users get identical recommendations
- Price ranges don't match personas
- Very low similarity scores (<0.5)
- No personalization evident
- Collaborative filtering never triggers
