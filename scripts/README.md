# Scripts

Utility scripts for managing Pinecone Scout.

## populate_items.py

Populates the Pinecone `items_index` with television products from `ITEM_POPULATE.txt`.

### Usage

```bash
# Make sure your virtual environment is activated
source .venv/bin/activate

# Make sure your .env file is configured with API keys
# PINECONE_API_KEY and OPENAI_API_KEY must be set

# Run the script
python scripts/populate_items.py
```

### What it does

1. Reads items from `ITEM_POPULATE.txt` (JSON format)
2. Generates embeddings for each item's description using OpenAI
3. Formats data with:
   - `item_id` as the vector ID
   - Embedding vector from description
   - Metadata: name, category, price, description, brand, features
4. Upserts items to Pinecone `items_index` in batches of 10

### Output

The script will:

- Show progress for each batch
- Display item names and prices as they're processed
- Report success/failure counts
- Clean up connections when done

### Requirements

- `.env` file with `PINECONE_API_KEY` and `OPENAI_API_KEY`
- Pinecone indexes must exist (created automatically on first run)
- `ITEM_POPULATE.txt` must exist in project root

## populate_users.py

Populates the Pinecone `users_index` with diverse user personas from `USER_POPULATE.txt`.

### Usage

```bash
# Make sure your virtual environment is activated
source .venv/bin/activate

# Make sure your .env file is configured with API keys
# PINECONE_API_KEY and OPENAI_API_KEY must be set

# Run the script
python scripts/populate_users.py
```

### What it does

1. Reads user personas from `USER_POPULATE.txt` (JSON format)
2. Generates embeddings from comprehensive persona descriptions
3. Formats data with:
   - `user_id` as the vector ID
   - Embedding vector from persona description
   - Metadata: age_range, household_size, city, style_preference, interests, lifestyle, price_sensitivity, shopping_style
4. Upserts users to Pinecone `users_index`

### Persona Details

Each persona includes:

- **Demographics**: age_range, household_size, city
- **Style**: style_preference (e.g., "modern minimalist", "family-friendly modern")
- **Interests**: array of hobbies and interests
- **Lifestyle**: urban/suburban/rural, professional/family/retired
- **Price Sensitivity**: budget, mid-range, premium, luxury
- **Shopping Style**: researcher, impulse buyer, brand loyal, value seeker, etc.
- **Rich Description**: comprehensive text combining all attributes for embedding

### Output

The script will:

- Show progress for each user
- Display user location, age, and household info
- Report success/failure counts
- Clean up connections when done

### Requirements

- `.env` file with `PINECONE_API_KEY` and `OPENAI_API_KEY`
- Pinecone indexes must exist (created automatically on first run)
- `USER_POPULATE.txt` must exist in project root

## import_from_bestbuy_api.py

Imports real product data from the Best Buy API into the Pinecone `items_index`.

### Usage

```bash
# Make sure your virtual environment is activated
source .venv/bin/activate

# Add BESTBUY_API_KEY to your .env file
# Get your free API key from: https://developer.bestbuy.com/

# Import 100 TVs
python scripts/import_from_bestbuy_api.py --category "Televisions" --limit 100

# Import specific brand
python scripts/import_from_bestbuy_api.py --category "Televisions" --brand "Samsung" --limit 50

# Import by price range
python scripts/import_from_bestbuy_api.py --category "Televisions" --min-price 500 --max-price 2000 --limit 100
```

### What it does

1. Fetches products from Best Buy API
2. Transforms to our format with proper metadata
3. Generates embeddings from product descriptions
4. Upserts to Pinecone `items_index`

### Requirements

- `.env` file with `PINECONE_API_KEY`, `OPENAI_API_KEY`, and `BESTBUY_API_KEY`
- Best Buy API key (free tier: 5,000 calls/day)
- Pinecone indexes must exist (created automatically on first run)

## generate_synthetic_products.py

Generates synthetic product data for testing when you need more items but don't have API access.

### Usage

```bash
# Make sure your virtual environment is activated
source .venv/bin/activate

# Generate 100 synthetic TVs
python scripts/generate_synthetic_products.py --category "televisions" --count 100

# Generate with specific price range
python scripts/generate_synthetic_products.py --category "televisions" --count 50 --min-price 500 --max-price 1500

# Generate specific sizes
python scripts/generate_synthetic_products.py --category "televisions" --count 100 --sizes "50,55,65,75"
```

### What it does

1. Generates realistic product descriptions
2. Creates diverse products across price tiers (budget, mid, premium, luxury)
3. Includes various brands, sizes, technologies, and features
4. Generates embeddings and upserts to Pinecone

### Requirements

- `.env` file with `PINECONE_API_KEY` and `OPENAI_API_KEY`
- Pinecone indexes must exist (created automatically on first run)

## generate_extended_products.py

Generates synthetic products for furniture (IKEA-style), cruise packages (Viking Cruises), and experiences (Airbnb-style).

### Usage

```bash
# Make sure your virtual environment is activated
source .venv/bin/activate

# Generate all extended products (furniture, cruises, experiences)
python scripts/generate_extended_products.py
```

### What it does

1. Generates **20 furniture items** (5 each for living room, bedroom, kitchen, bathroom)
2. Generates **25 cruise packages** (various destinations, durations, themes)
3. Generates **25 experience items** (5 each for outdoor, cultural, food, wellness, entertainment)
4. Creates realistic descriptions, pricing, and URLs
5. Generates embeddings and upserts all products to Pinecone

### Product Categories

- **Furniture**: IKEA-style furnishings with various materials (wood, metal, glass, etc.) and styles (modern, Scandinavian, minimalist, etc.)
- **Cruises**: Viking Cruises packages with destinations (Mediterranean, Alaska, Caribbean, etc.), durations (7-28 days), and themes (cultural, adventure, culinary, etc.)
- **Experiences**: Airbnb-style experiences including outdoor adventures, cultural activities, food tours, wellness retreats, and entertainment

### Requirements

- `.env` file with `PINECONE_API_KEY` and `OPENAI_API_KEY`
- Pinecone indexes must exist (created automatically on first run)
