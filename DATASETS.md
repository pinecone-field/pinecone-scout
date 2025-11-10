# Product Datasets for Pinecone Scout

This guide covers datasets you can use to populate the items index with a larger, more diverse product catalog.

## Recommended Datasets

### 1. Amazon Product Dataset (Kaggle) ⭐ **BEST OPTION**

**Dataset**: [Amazon Product Dataset](https://www.kaggle.com/datasets/karkavelrajaj/amazon-products-dataset) or similar

**Why it's good:**

- Contains product descriptions, prices, categories
- Large variety of products
- Includes metadata like brand, features
- CSV/JSON format, easy to import

**How to use:**

1. Download from Kaggle (requires account)
2. Filter for electronics/TVs category
3. Use `scripts/import_from_csv.py` to import

### 2. Best Buy API (Official)

**Source**: [Best Buy Developer API](https://developer.bestbuy.com/)

**Why it's good:**

- Official API with real product data
- Free tier available (5,000 calls/day)
- Includes descriptions, prices, features
- JSON format

**Setup:**

1. Sign up at <https://developer.bestbuy.com/>
2. Get API key
3. Use `scripts/import_from_bestbuy_api.py` to fetch products

### 3. Amazon Product Reviews Dataset

**Dataset**: [Amazon Product Reviews](https://www.kaggle.com/datasets/arhamrumi/amazon-product-reviews) or similar

**Why it's good:**

- Includes product metadata
- Large dataset
- Real product descriptions

### 4. Synthetic Data Generation

**Option**: Generate synthetic product data programmatically

**Why it's good:**

- No external dependencies
- Full control over product attributes
- Can generate specific sizes, price ranges

**Use**: `scripts/generate_synthetic_products.py`

## Quick Start: Best Buy API

The easiest way to get real product data is via the Best Buy API:

### Step 1: Get API Key

1. Go to <https://developer.bestbuy.com/>
2. Sign up for free account
3. Create an app to get API key
4. Add to `.env`:

   ```bash
   BESTBUY_API_KEY=your_api_key_here
   ```

### Step 2: Import Products

```bash
python scripts/import_from_bestbuy_api.py --category "Televisions" --limit 100
```

This will:

- Fetch TV products from Best Buy API
- Generate embeddings from descriptions
- Upsert to Pinecone items_index
- Create proper item_ids and metadata

## Dataset Format Requirements

For any dataset you use, ensure it has (or can be mapped to):

```json
{
  "item_id": "unique_id",
  "name": "Product Name",
  "category": "televisions",
  "price": 999.99,
  "description": "Detailed product description for embedding",
  "brand": "Brand Name",
  "features": ["feature1", "feature2"]
}
```

### Required Fields

- `name`: Product name
- `description`: Rich text description (used for embeddings)
- `price`: Numeric price
- `category`: Product category

### Optional Fields

- `brand`: Brand name
- `features`: Array of features
- `size`: Screen size (for TVs)
- `resolution`: Resolution (4K, 8K, etc.)

## Import Scripts

### CSV Import

If you have a CSV file with products:

```bash
python scripts/import_from_csv.py --file products.csv \
  --name-col "Product Name" \
  --desc-col "Description" \
  --price-col "Price" \
  --category "televisions"
```

### JSON Import

If you have a JSON file:

```bash
python scripts/import_from_json.py --file products.json
```

### Best Buy API Import

```bash
# Import TVs
python scripts/import_from_bestbuy_api.py --category "Televisions" --limit 200

# Import specific brands
python scripts/import_from_bestbuy_api.py --category "Televisions" --brand "Samsung" --limit 50

# Import by price range
python scripts/import_from_bestbuy_api.py --category "Televisions" --min-price 500 --max-price 2000 --limit 100
```

## Synthetic Data Generation

Generate synthetic products for testing:

```bash
python scripts/generate_synthetic_products.py \
  --category "televisions" \
  --count 100 \
  --price-range 200 2000 \
  --sizes "50,55,65,75,85"
```

This creates realistic product descriptions with:

- Various brands (Samsung, LG, Sony, TCL, etc.)
- Different sizes
- Price ranges
- Feature combinations
- Rich descriptions for embeddings

## Recommended Product Count

For good recommendation quality:

- **Minimum**: 50-100 products per category
- **Recommended**: 200-500 products per category
- **Optimal**: 1000+ products per category

## Size Distribution

For TVs specifically, ensure you have:

- Multiple sizes: 32", 43", 50", 55", 65", 75", 85"
- Multiple price points: Budget ($200-500), Mid ($500-1000), Premium ($1000-2000), Luxury ($2000+)
- Multiple brands: Samsung, LG, Sony, TCL, Hisense, Vizio, etc.
- Multiple technologies: LED, QLED, OLED, Mini-LED

## Quality Checklist

Before importing, verify:

- [ ] Descriptions are detailed (at least 50-100 words)
- [ ] Prices are realistic and current
- [ ] Categories are consistent
- [ ] No duplicate items
- [ ] All required fields present
- [ ] item_ids are unique

## Next Steps

1. **Start with Best Buy API** (easiest, real data)
2. **Add synthetic data** for edge cases
3. **Expand to other categories** (laptops, phones, etc.)
4. **Regular updates** to keep prices current
