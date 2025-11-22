# Separate Output Files Per Retailer - Feature Documentation

## Overview

The e-commerce scraper now automatically saves products to **separate JSON files per retailer**, making it easier to process and analyze results by retailer.

---

## How It Works

### Before (Single File)
```
apps/output/by_list/2025-11-22/23-28-00/
└── products.json  (all 388 products mixed together)
```

### After (Separate Files)
```
apps/output/by_list/2025-11-22/23-28-00/
├── boonthavorn.json      (92 products)
├── thai_watsadu.json     (150 products)
├── homepro.json          (100 products)
└── dohome.json           (46 products)
```

---

## Example

### Input CSV (Mixed Retailers)
```csv
product_name,url
Product 1,https://www.thaiwatsadu.com/th/sku/60375395
Product 2,https://www.homepro.co.th/p/123456
Product 3,https://www.boonthavorn.com/king-1162107
Product 4,https://www.thaiwatsadu.com/th/sku/60281530
```

### Output Files Created
- **thai_watsadu.json** (2 products)
- **homepro.json** (1 product)
- **boonthavorn.json** (1 product)

---

## File Naming

Retailer names are normalized to lowercase with underscores:

| Retailer | File Name |
|----------|-----------|
| Boonthavorn | `boonthavorn.json` |
| Thai Watsadu | `thai_watsadu.json` |
| HomePro | `homepro.json` |
| DoHome | `dohome.json` |
| Global House | `global_house.json` |
| Mega Home | `mega_home.json` |

---

## Benefits

1. **Easier Analysis**: Process one retailer at a time
2. **Parallel Processing**: Multiple retailers can be analyzed simultaneously
3. **Storage Efficiency**: Smaller files load faster
4. **Better Organization**: Clear separation of data sources
5. **Incremental Updates**: Update one retailer without affecting others

---

## Usage

No changes needed! Just run the scraper as before:

```bash
./adws/adw_ecommerce_product_scraper.py \
  --urls-file inputs/ecommerce/mixed_retailers.csv \
  --output-file apps/output/by_list/2025-11-23/00-00-00/products.json
```

The scraper will automatically:
1. Detect retailer from each URL
2. Group products by retailer
3. Save separate files for each retailer
4. Show progress for each file saved

---

## Output Messages

```
🔄 Saving 92 boonthavorn products to boonthavorn.json
🔄 Saving 150 thai_watsadu products to thai_watsadu.json  
🔄 Saving 100 homepro products to homepro.json
✅ Saved 3 retailer files to apps/output/by_list/2025-11-23/00-00-00
```

---

## Technical Details

### Incremental Saving

Products are saved incrementally as they are scraped:
- After each product is extracted
- Grouped by retailer
- Written to appropriate file
- Real-time updates (no waiting for completion)

### Retailer Detection

Retailer is determined by:
1. `BoonthavornExtractor` → sets `retailer = "Boonthavorn"`
2. `ThaiWatsaduExtractor` → sets `retailer = "Thai Watsadu"`
3. `HomeProExtractor` → sets `retailer = "HomePro"`
4. Generic extractor → detects from URL domain

---

## Backward Compatibility

The scraper still creates:
- Combined JSON/JSONL files for all products
- Summary statistics
- ADW-structured outputs (raw/, processed/, logs/)

---

## Example File Content

### boonthavorn.json
```json
[
  {
    "name": "บานซิงค์ PLATINUM โนวา-เดี่ยว เทาเข้ม",
    "retailer": "Boonthavorn",
    "current_price": 1630.0,
    "sku": "1162107"
  }
]
```

### thai_watsadu.json
```json
[
  {
    "name": "ซับวงกบไม้สังเคราะห์ WPC ECO DOOR",
    "retailer": "Thai Watsadu",
    "current_price": 160.0,
    "sku": "60281530"
  },
  {
    "name": "คลิปพลาสติก สำหรับไม้พื้นไทซัน",
    "retailer": "Thai Watsadu",
    "current_price": 45.0,
    "sku": "60375395"
  }
]
```

---

## Future Enhancements

Potential additions:
- Per-retailer summary statistics
- Retailer-specific metadata files
- Validation per retailer
- Per-retailer error logs
