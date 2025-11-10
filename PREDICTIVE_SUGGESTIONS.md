# Predictive Suggestions Guide

The predictive suggestion feature (P2) is the conversational heart of Pinecone Scout. It intelligently detects when users might benefit from product suggestions and offers them naturally within the conversation flow.

## How It Works

### 1. Topic Detection

The system uses a **three-tier approach** to detect conversation topics:

> **LLM-Based Detection (Primary)** ⭐

- Uses GPT-4o-mini to analyze conversation context
- Understands nuance, implicit meaning, and context
- Catches topics that keyword matching might miss
- Returns confidence levels (high/medium/low)
- Falls back gracefully if LLM fails

> **Keyword Matching (Fast Fallback)**

- Detects common topics like "gaming", "entertainment", "art_design", etc.
- Uses predefined keyword lists for instant detection
- Very fast, no API calls needed

> **Embedding-Based Detection (Semantic Fallback)**

- If keywords don't match, uses semantic similarity
- Compares conversation context to topic embeddings
- More accurate for nuanced conversations than keywords alone

### 2. Suggestion Appropriateness

The system only suggests when appropriate:

✅ **Will Suggest When:**

- User uses trigger phrases: "looking for", "need", "want", "interested in", "considering"
- Topic is detected and relevant
- User seems open to suggestions

❌ **Won't Suggest When:**

- User explicitly rejects: "don't need", "not looking", "not interested"
- No relevant topic detected
- No trigger phrases found

### 3. Product Search

When a suggestion is appropriate:

1. **Searches items_index** using conversation context + user profile
2. **Filters by similarity** (minimum 0.60 threshold)
3. **Respects user preferences** (skips disliked items)
4. **Personalizes** based on user profile (price sensitivity, interests, etc.)

### 4. Conversational Generation

Suggestions are generated in natural, contextual language:

- **Context-aware**: Adapts to what user said
- **Size-aware**: Mentions specific sizes if user mentioned them
- **Topic-specific**: Tailored to detected topic (gaming, art, etc.)
- **Non-pushy**: Feels helpful, not salesy

## Example Scenarios

### Scenario 1: User Looking for Gaming TV

**User**: "I'm looking for a TV that's good for gaming"

**System detects:**

- Topic: `gaming`
- Trigger: "looking for"
- Appropriate: ✅ Yes

**Suggestion**:
> "For gaming, you might want to consider the Samsung 65-inch QLED 4K Smart TV ($1,299.99). It has features that work well for gaming."

### Scenario 2: Art Collector

**User**: "I want something that looks like art when not in use"

**System detects:**

- Topic: `art_design`
- Trigger: "want"
- Appropriate: ✅ Yes

**Suggestion**:
> "If aesthetics matter to you, the Samsung Frame TV 55-inch ($1,499.99) has a design-focused approach that might appeal to you."

### Scenario 3: Apartment Dweller

**User**: "I need a TV for my small apartment"

**System detects:**

- Topic: `apartment`
- Trigger: "need"
- Appropriate: ✅ Yes

**Suggestion**:
> "For smaller spaces, the LG 50-inch Class UQ70 Series ($329.99) could work well. It's designed with compact living in mind."

### Scenario 4: User Not Interested

**User**: "I'm just browsing, not looking for anything specific"

**System detects:**

- Topic: None
- Trigger: None
- Appropriate: ❌ No

**Result**: No suggestion (returns empty)

## LLM-Based Topic Detection

The LLM-based detection provides superior understanding:

### Advantages

- **Context Understanding**: Understands implicit meaning
- **Nuance**: Catches subtle references (e.g., "looks like, well, a TV" → art_design)
- **Flexibility**: Works with varied phrasing and natural language
- **Confidence Scoring**: Returns confidence levels for better filtering

### Example

**Input**: "I just moved into a new place and need to get some furniture. It's a pain because I want it to look clean and modern but my old TV just looks like, well, a TV."

**LLM Analysis**:

```json
{
  "topic": "art_design",
  "confidence": "high",
  "reasoning": "User explicitly mentions wanting clean/modern aesthetic and is concerned about TV appearance, indicating design/aesthetic priority"
}
```

### Configuration

LLM detection can be disabled if needed:

```python
predictive_module.use_llm_detection = False  # Falls back to keyword/embedding
```

## Supported Topics

| Topic | Keywords | Use Case |
|-------|----------|----------|
| `gaming` | gaming, game, playstation, xbox, nintendo | Gaming-focused TVs |
| `entertainment` | watching, movie, film, show, streaming | Entertainment viewing |
| `home_theater` | home theater, cinema, immersive | Premium viewing experience |
| `art_design` | art, design, decor, aesthetic, frame | Design-focused TVs |
| `sports` | sports, football, basketball, live | Sports viewing |
| `work` | work, office, presentation, meeting | Professional use |
| `family` | family, kids, children, shared | Family-friendly |
| `apartment` | apartment, small space, compact | Small spaces |
| `budget` | affordable, budget, cheap, value | Budget-conscious |
| `premium` | premium, high-end, luxury, best | Premium options |

## API Usage

### Endpoint

```bash
POST /api/predictive_suggest
```

### Request

```json
{
  "user_id": "user_001",
  "conversation_context": "I'm looking for a TV for gaming",
  "detected_topic": "gaming",  // Optional
  "previous_topics": ["entertainment"]  // Optional
}
```

### Response

```json
{
  "suggestion": {
    "text": "For gaming, you might want to consider the Samsung 65-inch QLED 4K Smart TV ($1,299.99). It has features that work well for gaming.",
    "partner": null,
    "is_sponsored": false,
    "item_id": "item_bb_001",
    "item_name": "Samsung 65-inch Class QLED 4K Q80C Series",
    "item_price": 1299.99
  },
  "opt_in_required": false
}
```

## ChatGPT Integration

In ChatGPT, the `predictive_suggest` tool can be called automatically or manually:

### Automatic Usage

ChatGPT can call this tool when it detects:

- User is looking for something
- Conversation context suggests product interest
- Natural opportunity for suggestion

### Manual Usage

You can also call it explicitly:

```json
{
  "name": "predictive_suggest",
  "arguments": {
    "user_id": "user_001",
    "conversation_context": "I'm thinking about upgrading my TV for better movie watching"
  }
}
```

## Best Practices

### For ChatGPT Integration

1. **Call naturally**: Use the tool when conversation naturally flows to product interest
2. **Don't overuse**: Only suggest when user seems open to it
3. **Be contextual**: Pass full conversation context, not just the last message
4. **Track topics**: Use `previous_topics` to avoid repetitive suggestions

### For Backend Development

1. **Tune thresholds**: Adjust `MIN_SIMILARITY_THRESHOLD` based on your product catalog
2. **Expand topics**: Add more topics to `TOPIC_KEYWORDS` as needed
3. **Refine triggers**: Update `SUGGESTION_TRIGGERS` based on user behavior
4. **Test appropriateness**: Ensure `_should_suggest()` logic prevents pushy behavior
5. **Monitor LLM costs**: LLM detection adds API costs; monitor usage

## Customization

### Adding New Topics

Edit `app/services/predictive_module.py`:

```python
TOPIC_KEYWORDS = {
    "your_topic": ["keyword1", "keyword2", "keyword3"],
    # ...
}
```

Also update the `available_topics` dict in `_detect_topic_with_llm()`.

### Adjusting Suggestion Style

Modify `_generate_conversational_suggestion()` to change how suggestions are phrased.

### Changing Similarity Threshold

```python
MIN_SIMILARITY_THRESHOLD = 0.70  # Higher = more strict
```

### Disabling LLM Detection

```python
predictive_module.use_llm_detection = False
```

## Testing

### Test in MCP Inspector

```json
{
  "user_id": "user_001",
  "conversation_context": "I'm looking for a TV for gaming"
}
```

### Test Different Scenarios

1. **Gaming**: "I need a TV for my PlayStation"
2. **Art**: "I want something that looks like art"
3. **Budget**: "Looking for something affordable"
4. **Rejection**: "I'm not looking for anything right now"
5. **Nuanced**: "My old TV just looks like, well, a TV" (should detect art_design)

## Future Enhancements

- **Conversation history**: Track full conversation for better context
- **A/B testing**: Test different suggestion styles
- **Engagement tracking**: Measure which suggestions work best
- **Multi-product suggestions**: Suggest multiple related products
- **Seasonal/temporal awareness**: Adjust suggestions based on time/season
- **Fine-tuned model**: Train a custom model for topic detection
