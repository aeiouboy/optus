# E-commerce Product Scraper User Manual

## Overview

The **E-commerce Product Scraper** is a powerful AI Developer Workflow (ADW) designed to extract structured product data from e-commerce websites. It outputs data in a standardized JSON format with comprehensive product fields including pricing, specifications, and metadata.

> **🔧 Environment Requirement**: This project uses **uv** as the exclusive package manager and execution environment. All commands must use `uv run adws/adw_ecommerce_product_scraper.py`. Direct script execution without uv is not supported.

## Features

- ✅ **All 18 Required Fields**: name, retailer, url, current_price, original_price, product_key, brand, model, sku, category, volume, dimensions, material, color, images, description, scraped_at, has_discount, discount_percent, discount_amount
- ✅ **Multi-retailer Support**: Thai Watsadu, HomePro, Lazada, Shopee, and generic e-commerce sites
- ✅ **Smart Price Processing**: Automatic discount calculations and currency parsing
- ✅ **Data Quality**: Built-in sanitization to prevent JSON contamination
- ✅ **Organized Output**: Professional folder structure with raw/processed/logs/assets subdirectories
- ✅ **Batch Processing**: Handle multiple URLs efficiently
- ✅ **Progress Tracking**: Rich console output with success/failure reporting

## Quick Start

### Basic Usage
```bash
# Single product scraping
uv run adws/adw_ecommerce_product_scraper.py \
  --url "https://www.thaiwatsadu.com/th/sku/60363373"

# Batch scraping from file
uv run adws/adw_ecommerce_product_scraper.py \
  --urls-file product-urls.txt \
  --output-file results.json
```

### Advanced Usage with Organized Output
```bash
# Create organized structure with date-based folders
uv run adws/adw_ecommerce_product_scraper.py \
  --url "https://www.thaiwatsadu.com/th/sku/60363373" \
  --output-folder ./results/2025-11-22 \
  --organization date \
  --output-file thai-products.json

# Job-ID based organization for batch processing
uv run adws/adw_ecommerce_product_scraper.py \
  --urls-file large-batch.txt \
  --output-folder ./results/ \
  --organization job-id
```

## Installation

### Prerequisites
- Python 3.10+ (managed by uv)
- uv package manager (required for execution)
- crawl4ai with browser support (installed via uv)

### Environment Setup with uv

#### Install uv (if not already installed)
```bash
# Install uv using the official installer
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or install via pip
pip install uv

# Verify installation
uv --version
```

#### Project Setup
```bash
# Clone or navigate to the project directory
cd /path/to/project

# Install project dependencies and create virtual environment
uv sync

# Verify the scraper is working
uv run adws/adw_ecommerce_product_scraper.py --help
```

#### Benefits of Using uv
- **Consistent Environments**: Ensures the same Python version and dependencies across all systems
- **Dependency Management**: Automatically handles package installation and version conflicts
- **Fast Execution**: No need to activate virtual environments manually
- **Reproducible Results**: Guarantees the same runtime environment for every execution

**Important**: Always use `uv run adws/adw_ecommerce_product_scraper.py` to execute the scraper. Direct script execution without uv is not supported.

## Command Line Options

### Input Options
- `--url`: Single product URL to scrape
- `--urls-file`: File containing product URLs (one per line)
- `--test`: Run in test mode with minimal output

### Output Options
- `--output-file`: Output file path (default: products.json)
- `--output-folder`: Base folder for organized results
- `--organization`: Organization type (`date` or `job-id`)

### Configuration
- `--adw-id`: Custom ADW ID for tracking
- `--max-concurrent`: Maximum concurrent requests (default: 3)
- `delay`: Delay between requests in seconds (default: 1.0)
- `--timeout`: Request timeout in seconds (default: 30)
- `--headless/--no-headless`: Browser mode (default: --headless)
- `--use-browser/--no-browser`: Use browser for JavaScript handling (default: --use-browser)
- `--retry-attempts`: Number of retry attempts (default: 3)
- `retry-delay`: Delay between retries (default: 2.0)

## Output Format

### Required JSON Fields (All 18 Fields)
```json
{
  "name": "Product Name",
  "retailer": "Store Name",
  "url": "Product URL",
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
    "https://example.com/image1.jpg",
    "https://example.com/image2.jpg"
  ],
  "description": "Product description text",
  "scraped_at": "2025-11-06T12:52:18.376125",
  "has_discount": true,
  "discount_percent": 15.19756838905775,
  "discount_amount": 500
}
```

### Output Structure

#### Organized Output (`--output-folder`)
```
output-folder/
└── date_YYYY-MM-DD/
    └── adw_id/
        ├── raw/
        │   ├── cc_raw_output.jsonl
        │   └── cc_raw_output.json
        ├── processed/
        │   └── cc_final_object.json
        ├── logs/
        │   └── custom_summary_output.json
        ├── assets/
        │   └── (downloaded media files)
        └── products.json (main results)
```

#### Legacy Output (Default)
```
agents/{adw_id}/ecommerce_scraper/
├── cc_raw_output.jsonl
├── cc_raw_output.json
├── cc_final_object.json
├── custom_summary_output.json
```

## URL File Format

Create a text file with one URL per line:

```bash
# product-urls.txt
https://www.thaiwatsadu.com/th/sku/60363373
https://www.homepro.co.th/p/product-12345
https://www.lazada.co.th/product-67890

# Add comments for organization
https://www.shopee.co.th/product-12345  # Electronics
```

## Examples

### Example 1: Single Product Scraping
```bash
uv run adws/adw_ecommerce_product_scraper.py \
  --url "https://www.thaiwatsadu.com/th/sku/60363373" \
  --output-folder ./results/single-products \
  --organization date \
  --output-file water-tank.json
```

### Example 2: Batch Processing
```bash
# Create URL file
cat > electronics-products.txt << EOF
https://www.lazada.co.th/product-12345
https://www.shopee.co.th/product-67890
https://www.powerbuy.co.th/product-13579
EOF

# Run batch scraping
uv run adws/adw_ecommerce_product_scraper.py \
  --urls-file electronics-products.txt \
  --output-folder ./results/electronics \
  --organization date \
  --output-file electronics-products.json \
  --max-concurrent 5 \
  --delay 2.0
```

### Example 3: Daily Monitoring
```bash
# Create daily URL file
cat > daily-monitor.txt << EOF
https://www.thaiwatsadu.com/th/sku/60363373
https://www.homepro.co.th/p/product-12345
https://www.lazada.co.th/product-67890
EOF

# Set up daily cron job
echo "0 9 * * * cd /path/to/project && uv run adws/adw_ecommerce_product_scraper.py --urls-file daily-monitor.txt --output-folder ./monitoring/\$(date +\%Y-%m-%d) --organization date --output-file daily-products.json" | crontab -
```

### Example 4: Price Monitoring
```bash
# Monitor specific products for price changes
uv run adws/adw_ecommerce_product_scraper.py \
  --url "https://www.thaiwatsadu.com/th/sku/60363373" \
  --output-folder ./price-monitoring \
  --organization job-id \
  --adw-id price-check \
  --retry-attempts 5
```

## Output Directory Examples

### Single Product - Date Organization
```
results/
└── 2025-11-22/
    └── water-tanks/
        ├── raw/
        │   ├── cc_raw_output.jsonl
        │   ├── cc_raw_output.json
        ├── processed/
        │   └── cc_final_object.json
        ├── logs/
        │   └── custom_summary_output.json
        └── water-tank.json
```

### Batch Processing - Job-ID Organization
```
results/
└── test-structure/
    ├── raw/
    │   ├── cc_raw_output.jsonl
    │   ├── cc_raw_output.json
    ├── processed/
    │   └── cc_final_object.json
    ├── logs/
    │   └── custom_summary_output.json
    └── batch-products.json
```

## Data Quality Features

### Automatic Data Cleaning
- **Brand Field Sanitization**: Removes JSON contamination and cleans HTML artifacts
- **Price Parsing**: Handles various currency formats (฿, $, €, etc.)
- **Image Validation**: Filters invalid or broken image URLs
- **Text Normalization**: Removes excessive whitespace and special characters

### Price Processing
- **Automatic Discount Calculation**: `discount_percent = ((original_price - current_price) / original_price) * 100`
- **Multiple Price Detection**: Finds current and original prices from various page patterns
- **Currency Support**: Handles Thai Baht (฿), USD ($), EUR (€), etc.

### Field Validation
- **Required Fields**: Ensures name, retailer, and URL are always present
- **Type Validation**: Validates numeric fields for prices and percentages
- **URL Validation**: Checks for valid URL format
- **Length Constraints**: Enforces reasonable field length limits

## Supported Retailers

### Pre-configured Retailers
- **Thai Watsadu** (`thaiwatsadu.com`)
- **HomePro** (`homepro.co.th`)
- **Lazada Thailand** (`lazada.co.th`)
- **Shopee Thailand** (`shopee.co.th`)
- **Power Buy** (`powerbuy.co.th`)

### Generic Fallback
- Works with any e-commerce website
- Automatic retailer detection from URL domain
- Adaptive extraction patterns for various site structures

## Troubleshooting

### Common Issues

#### Brand Field Issues
**Problem**: Brand field contains JSON data contamination
**Solution**: The `_sanitize_brand_field()` function automatically cleans the brand field. If brand still shows contamination, report the URL for investigation.

#### Output Structure Issues
**Problem**: Files not appearing in expected directories
**Solution**:
- Check permissions on output directory
- Verify `--output-folder` or default agents structure
- Check if disk space is available

#### Price Extraction Issues
**Problem**: Prices showing as `null` or incorrect
**Solution**:
- Try with `--headless` vs `--no-browser`
- Increase `--timeout` for slow-loading pages
- Verify site doesn't require JavaScript for price display

#### Extraction Fails
**Problem**: "Failed to extract product data" errors
**Solutions**:
- Test with `--test` flag first
- Check if URL is accessible in browser
- Verify retailer is supported
- Try increasing `--retry-attempts`

### Debugging Mode
```bash
# Test mode with detailed output
uv run adws/adw_ecommerce_product_scraper.py \
  --url "https://example.com/product" \
  --test \
  --adw-id debug-test \
  --verbose
```

### Performance Optimization

#### For Large Scale Scraping
```bash
# Increase concurrency for faster processing
uv run adws/adw_ecommerce_product_scraper.py \
  --urls-file large-batch.txt \
  --max-concurrent 10 \
  --delay 0.5 \
  --retry-attempts 1
```

#### For Rate-Limited Sites
```bash
# Be respectful of server resources
uv run adws/adw_ecommerce_product_scraper.py \
  --urls-file sensitive-sites.txt \
  --max-concurrent 1 \
  --delay 5.0 \
  --timeout 60
```

## Best Practices

### URL Management
1. **Organize URLs by retailer** and product category
2. **Validate URLs** before running batch jobs
3. **Use date-based organization** for regular scraping jobs
4. **Archive old results** after successful completion

### Data Quality
1. **Test with single URLs first** before batch processing
2. **Use `--test` mode** for quick validation
3. **Monitor success rates** and adjust retry parameters
4. **Validate output JSON** to ensure all 18 fields are present

### Resource Management
1. **Set appropriate concurrency** based on site limitations
2. **Use delays** between requests to avoid rate limiting
3. **Monitor disk space** for large scraping jobs
4. **Clean up temporary files** and outdated results

### uv Environment Management
1. **Always use `uv run`** for consistent execution environments
2. **Run `uv sync`** after pulling updates to ensure dependencies are current
3. **Use `uv run python`** for any additional Python scripts in data pipelines
4. **Check uv version compatibility** when upgrading to newer versions
5. **Leverage uv's caching** for faster consecutive runs

### Error Handling
1. **Use appropriate retry attempts** for transient failures
2. **Monitor for patterns** in failed extractions
3. **Log and investigate** persistent issues
4. **Implement fallback strategies** for unreliable sites

## Advanced Usage

### Custom Extraction Rules
For retailer-specific extraction, modify the `product_extractor.py`:

```python
class CustomRetailerExtractor(ProductExtractor):
    def _extract_brand(self, html_content: str) -> Optional[str]:
        # Custom brand extraction logic
        custom_patterns = [
            r'<div class="brand-name">(.*?)</div>',
            r'<span itemprop="brand">(.*?)</span>',
        ]
        for pattern in custom_patterns:
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                brand = self._clean_text(match.group(1))
                return brand
        return super()._extract_brand(html_content)
```

### Output Filtering
```python
# Filter products with discounts only
products_with_discounts = [p for p in products if p['has_discount']]

# Filter by price range
affordable_products = [p for p in products if p['current_price'] < 5000]
```

### Data Enrichment
Post-process the extracted data for additional analysis:

```python
# Add additional computed fields
for product in products:
    product['price_per_liter'] = (
        product['current_price'] /
        float(product['volume'].replace(',', '') if product['volume'] else 1.0)
        if product['volume'] else None
    )
```

## Integration Examples

### With Python Applications
```python
from adw_modules.product_schemas import ProductData
from adws.adw_ecommerce_product_scraper import main

# Direct integration
results = main(url, output_file='output.json')
for product_data in results:
    product = ProductData(**product_data)
    print(f"Extracted: {product.name} - {product.current_price}")
```

### With Data Pipelines
```bash
# Stage 1: Extract data
uv run adws/adw_ecommerce_product_scraper.py \
  --urls-file products-to-scrape.txt \
  --output-folder ./stage1/raw

# Stage 2: Process and validate
uv run python scripts/validate_products.py \
  --input ./stage1/raw/processed/cc_final_object.json \
  --output ./stage2/validated/

# Stage 3: Analytics and reporting
uv run python scripts/analyze_products.py \
  --input ./stage2/validated/
```

## Summary

The E-commerce Product Scraper provides a robust, production-ready solution for extracting structured product data from e-commerce websites with:

- ✅ **Complete field coverage** (all 18 required fields)
- ✅ **Data quality assurance** (sanitization and validation)
- ✅ **Professional output organization** (multiple formats)
- ✅ **Scalable architecture** (batch processing and optimization)
- ✅ **Error resilience** (retry logic and fallback handling)
- ✅ **Multi-retailer support** (pre-configured and generic)

The scraper successfully extracts product data in your exact specified JSON format while maintaining data quality and professional file organization!