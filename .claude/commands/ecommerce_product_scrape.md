# E-commerce Product Data Scraping

Extract structured product data from e-commerce websites and output in the specified JSON format with comprehensive product fields.

## Usage

```bash
# Single product URL scraping
/ecommerce_product_scrape --url https://www.thaiwatsadu.com/th/sku/60363373

# Batch scraping from file
/ecommerce_product_scrape --urls-file products.txt --output-file products.json

# With custom configuration
/ecommerce_product_scrape --url https://example.com/product --max-concurrent 5 --delay 2.0

# Test mode for validation
/ecommerce_product_scrape --url https://example.com/product --test
```

## Required Arguments

One of the following must be provided:

- `--url`: Single product URL to scrape
- `--urls-file`: File containing list of product URLs (one per line)

## Optional Arguments

- `--output-file`: Output file path for scraped product data (default: products.json)
- `--max-concurrent`: Maximum concurrent requests (default: 3)
- `--delay`: Delay between requests in seconds (default: 1.0)
- `--timeout`: Request timeout in seconds (default: 30)
- `--headless/--no-headless`: Run browser in headless mode (default: --headless)
- `--use-browser/--no-browser`: Use browser for scraping (default: --use-browser)
- `--retry-attempts`: Number of retry attempts for failed requests (default: 3)
- `--retry-delay`: Delay between retries in seconds (default: 2.0)
- `--test`: Run in test mode with minimal output

## Output Format

The scraper outputs JSON data with the following fields for each product:

### Basic Information
- `name`: Product name
- `retailer`: Retailer name (extracted from URL or detected)
- `url`: Product URL
- `description`: Product description
- `product_key`: Unique product identifier (auto-generated)

### Pricing Information
- `current_price`: Current selling price
- `original_price`: Original price before discount
- `has_discount`: Boolean indicating if product has discount
- `discount_percent`: Discount percentage (calculated)
- `discount_amount`: Discount amount in currency

### Product Details
- `brand`: Product brand
- `model`: Product model
- `sku`: Product SKU/stock keeping unit
- `category`: Product category
- `volume`: Product volume/capacity
- `dimensions`: Product dimensions
- `material`: Product material
- `color`: Product color

### Media and Metadata
- `images`: Array of product image URLs
- `scraped_at`: Timestamp when data was scraped (ISO format)

## Supported Retailers

The scraper includes specialized extractors for:

- **Thai Watsadu** (thaiwatsadu.com)
- **HomePro** (homepro.co.th)
- **Generic e-commerce sites** (fallback extraction)

## Example Output

```json
[
  {
    "name": "ถังเก็บน้ำบนดิน 1,000 ลิตร ICE DOS รุ่น ECO-14/BL-1000L สีไอซ์บลู",
    "retailer": "Thai Watsadu",
    "url": "https://www.thaiwatsadu.com/th/sku/60363373",
    "current_price": 2790.0,
    "original_price": 3290.0,
    "product_key": "8ccb64f6568f",
    "brand": "DOS",
    "model": "ECO-14/BL-1000L",
    "sku": "60363373",
    "category": "ถังเก็บน้ำ",
    "volume": "1,000 ลิตร",
    "dimensions": "93 x 93 x 185 ซม.",
    "material": "Compound Polymer",
    "color": "สีไอซ์บลู",
    "images": [
      "https://www.thaiwatsadu.com/_next/image?url=https%3A%2F%2Fpim.thaiwatsadu.com%2FTWDPIM%2Fweb%2FThumbnail%2FImage%2F0204%2F60363373.jpg&w=1920&q=75"
    ],
    "description": "ถังเก็บน้ำบนดินคุณภาพดี DOS รุ่น ICE สำหรับใช้สำรองน้ำไว้ใช้ภายในบ้านและสำนักงาน",
    "scraped_at": "2025-11-06T12:52:18.376125",
    "has_discount": true,
    "discount_percent": 15.19756838905775,
    "discount_amount": 500.0
  }
]
```

## Input File Format

When using `--urls-file`, the file should contain one URL per line:

```
https://www.thaiwatsadu.com/th/sku/60363373
https://www.homepro.co.th/p/product-12345
https://example.com/product/abc-123
# Lines starting with # are ignored
```

## Error Handling

The scraper includes robust error handling:

- Automatic retry for failed requests
- Graceful handling of malformed product pages
- Validation of extracted data against schema
- Detailed error reporting and logging

## Output Structure

Results are saved in multiple formats:

- **JSON Array**: `products.json` - Main output file
- **JSONL**: `./agents/{adw_id}/ecommerce_scraper/cc_raw_output.jsonl` - Streaming format
- **JSON**: `./agents/{adw_id}/ecommerce_scraper/cc_raw_output.json` - Complete dataset
- **Summary**: `./agents/{adw_id}/ecommerce_scraper/custom_summary_output.json` - Execution summary

## Performance Tips

1. **Concurrent Requests**: Use `--max-concurrent` to control parallelism (default: 3)
2. **Rate Limiting**: Set `--delay` between requests to avoid being blocked
3. **Browser Settings**: Disable browser (`--no-browser`) for simple HTML pages
4. **Timeout**: Adjust `--timeout` for slow-loading sites

## Data Quality

The scraper includes data validation and normalization:

- Price parsing from multiple formats (฿1,299, $1299.00, etc.)
- Automatic discount calculations
- Image URL validation and filtering
- Text cleaning and normalization
- Field completeness validation

## Integration

This command integrates with the existing crawl4ai infrastructure:

- Uses `crawl4ai_wrapper` for web scraping
- Follows ADW patterns for output and logging
- Compatible with existing multi-agent workflows
- Supports structured data extraction with validation
