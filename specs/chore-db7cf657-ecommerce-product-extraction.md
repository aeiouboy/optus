# Chore: Create E-commerce Product Data Extraction Workflow

## Metadata
adw_id: `db7cf657`
prompt: `Create a new scraping workflow that extracts product data from e-commerce websites and outputs the specific JSON format with fields: name, retailer, url, current_price, original_price, product_key, brand, model, sku, category, volume, dimensions, material, color, images, description, scraped_at, has_discount, discount_percent, discount_amount. The workflow should integrate with the existing crawl4ai system and include proper data extraction and transformation logic.`

## Chore Description
Create a specialized e-commerce product data extraction workflow that extends the existing crawl4ai system to extract structured product information from e-commerce websites. The workflow must output data in a specific JSON format with comprehensive product fields including pricing, discount calculations, and physical attributes. This requires integrating with the existing crawl4ai wrapper and adding product-specific extraction logic.

## Relevant Files
Use these files to complete the chore:

### Existing Files
- `adws/adw_modules/crawl4ai_wrapper.py` - Core crawl4ai integration module
- `adws/adw_crawl4ai_scraper.py` - Main scraper ADW script
- `adws/adw_modules/utils.py` - Utility functions for formatting and status
- `.claude/commands/crawl4ai_scrape.md` - Existing command template
- `specs/chore-976192b6-crawl4ai-scraping-system.md` - Reference implementation

### New Files

#### `adws/adw_modules/product_extractor.py`
Product-specific data extraction module with e-commerce field mappings and transformation logic.

#### `adws/adw_ecommerce_product_scraper.py`
Main ADW script specialized for e-commerce product data extraction.

#### `.claude/commands/ecommerce_product_scrape.md`
Command template for e-commerce product scraping operations.

#### `adws/adw_modules/product_schemas.py`
JSON schemas and validation for product data extraction.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Create Product Data Schema Module
- Create `adws/adw_modules/product_schemas.py` with:
  - Product data class/model with all required fields
  - JSON schema for validation and extraction
  - Field mapping functions for different e-commerce sites
  - Price and discount calculation utilities
  - Data validation and normalization functions

### 2. Create Product Extractor Module
- Create `adws/adw_modules/product_extractor.py` with:
  - E-commerce specific extraction strategies for crawl4ai
  - CSS selectors and XPath patterns for common product page elements
  - Brand, SKU, and product identifier detection logic
  - Image URL extraction and filtering
  - Price parsing and currency handling
  - Discount calculation algorithms
  - Retailer identification from domain patterns
  - Fallback extraction methods for different site structures

### 3. Create Main E-commerce Scraper ADW
- Create `adws/adw_ecommerce_product_scraper.py` that:
  - Extends the existing crawl4ai scraper pattern
  - Integrates with crawl4ai_wrapper for basic scraping
  - Adds product-specific extraction using product_extractor module
  - Validates output against product schemas
  - Handles batch processing of product URLs
  - Outputs data in the required JSON format
  - Includes rich status panels and progress tracking
  - Follows ADW patterns for file organization and output

### 4. Implement Data Transformation Logic
- Add comprehensive data transformation:
  - Price parsing from various formats (currency symbols, decimals, ranges)
  - Discount percentage and amount calculations
  - Dimension and volume parsing and normalization
  - Color, material, and category standardization
  - Image URL validation and filtering
  - Product key generation (unique identifiers)
  - Missing field handling and default values

### 5. Add Multi-Retailer Support
- Implement retailer-specific extraction rules:
  - Amazon, eBay, Shopify, and major marketplace patterns
  - Custom field mappings for different retailers
  - Retailer identification from URL patterns
  - Adaptive extraction based on detected retailer
  - Configuration system for new retailer support

### 6. Create Command Template
- Create `.claude/commands/ecommerce_product_scrape.md` with:
  - Support for single product URLs and batch files
  - Output format options (JSON required, with CSV/CSV support)
  - Retailer-specific configuration options
  - Field validation and filtering options
  - Integration with existing crawl4ai options

### 7. Update Documentation and Integration
- Update existing documentation:
  - Add e-commerce scraper to `adws/README.md`
  - Document all 18 required output fields
  - Provide usage examples and configuration guides
  - Integration notes with existing crawl4ai system

### 8. Add Testing and Validation
- Implement comprehensive validation:
  - Product schema validation checks
  - Test cases for different e-commerce sites
  - Price and discount calculation verification
  - Field completeness and data quality checks
  - Error handling for malformed product pages

## Validation Commands
Execute these commands to validate the chore is complete:

- `uv run python -m py_compile adws/adw_ecommerce_product_scraper.py` - Test main script compilation
- `uv run python -m py_compile adws/adw_modules/product_extractor.py` - Test extractor module
- `uv run python -m py_compile adws/adw_modules/product_schemas.py` - Test schema module
- `./adws/adw_ecommerce_product_scraper.py --help` - Verify CLI interface
- `./adws/adw_ecommerce_product_scraper.py --url https://example.com/product --test` - Test product extraction
- Verify JSON output contains all required fields: `jq '.[] | keys' output.json | grep -E "(name|retailer|url|current_price|original_price|product_key|brand|model|sku|category|volume|dimensions|material|color|images|description|scraped_at|has_discount|discount_percent|discount_amount)"`
- Test discount calculations: `jq '.[] | select(.has_discount == true) | {original_price, current_price, discount_percent, discount_amount}' output.json`

## Notes
- The workflow must integrate seamlessly with the existing crawl4ai system while adding product-specific capabilities
- All 18 required JSON fields must be present in the output, with appropriate handling for missing data
- Price parsing should handle international currencies and various number formats
- Discount calculations must be mathematically accurate: discount_percent = ((original_price - current_price) / original_price) * 100
- Image URLs should be validated and filtered for product-relevant images only
- The system should be extensible to support new e-commerce retailers and product page structures
- Data validation should ensure output consistency across different retailers and product types