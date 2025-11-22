# Chore: Fix critical field extraction issues in e-commerce product scraper

## Metadata
adw_id: `68d27d02`
prompt: `Fix critical field extraction issues in the e-commerce product scraper to ensure all 18 required fields are properly extracted and validated. Address: 1) CSS/HTML contamination in text fields (dimensions, color, material), 2) Data truncation with trailing commas, 3) Default null discount fields to 0.0 when no pricing, 4) Invalid SKU extraction (URLs stored as SKU), 5) Missing brand/model extraction, 6) Proper text cleaning to remove HTML/JSON fragments`

## Chore Description
This chore addresses critical data quality issues in the e-commerce product scraper that are causing contaminated, incomplete, or invalid field extraction. The scraper currently allows HTML/CSS fragments, JSON objects, and URLs to contaminate text fields, fails to properly handle null discount values, extracts URLs instead of proper SKUs, and lacks comprehensive brand/model extraction. These issues compromise data integrity and require systematic fixes across the extraction pipeline.

## Relevant Files
Use these files to complete the chore:

### Primary Files
- `adws/adw_modules/product_extractor.py` - Core extraction logic with contamination prevention methods that need enhancement
- `adws/output_formatter.py` - Output formatting and processing logic that needs improved field validation
- `adws/adw_modules/product_schemas.py` - Data models and validation that need enhanced null handling and discount defaults

### Secondary Files
- `adws/thaiwatsadu_formatter.py` - Retailer-specific formatter that may need contamination fixes
- `adws/adw_ecommerce_product_scraper.py` - Main scraper that coordinates extraction
- `adws/adw_crawl4ai_scraper.py` - General scraper that calls extraction functions

### New Files
- `tests/test_field_extraction.py` - Unit tests for validating field extraction fixes
- `specs/field-extraction-validation-report.md` - Validation report documenting the fixes

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Enhance Text Field Sanitization and Decontamination
- Update `_sanitize_text_field()` in `product_extractor.py` to remove HTML/CSS class names, JSON fragments, and URLs
- Add specific patterns to detect and remove CSS class patterns (e.g., `class="..."`, `quickInfo-infoLabel-...`)
- Implement URL detection and removal from text fields (dimensions, color, material, brand, model)
- Add protection against trailing comma truncation by properly handling comma-separated values
- Create separate sanitization methods for different field types (dimensions vs brand vs color)

### 2. Fix SKU Extraction Logic
- Update `_extract_sku()` to prevent URL extraction as SKU values
- Add validation to ensure extracted SKUs don't contain URLs or domain names
- Implement proper SKU format validation (alphanumeric, reasonable length, no forward slashes)
- Enhance URL-based SKU extraction to extract meaningful product codes, not full URLs
- Add fallback logic for when no valid SKU is found

### 3. Implement Proper Discount Field Defaults
- Update `ProductData.__post_init__()` in `product_schemas.py` to default discount fields to 0.0 instead of null
- Fix `_calculate_discounts()` to properly handle cases with no pricing information
- Ensure `has_discount` is always boolean and `discount_percent/discount_amount` default to 0.0
- Add validation in `normalize_product_data()` to enforce proper discount defaults

### 4. Enhance Brand and Model Extraction
- Improve `_extract_brand()` and `_extract_model()` patterns to catch more variations
- Add brand extraction from JSON-LD structured data when available
- Implement model extraction from product titles and descriptions using regex patterns
- Add fallback logic for brand/model extraction from URL paths and page content
- Create retailer-specific brand extraction patterns for major retailers

### 5. Fix Data Truncation and Field Validation
- Update output formatter to properly handle comma-separated values without truncation
- Add field length validation to prevent excessive values that indicate contamination
- Implement proper text cleaning for dimensions to remove unit contamination (cm, mm, etc.)
- Add validation for color fields to prevent CSS color codes from being stored as color names
- Create field-specific cleaning methods for different data types

### 6. Add Comprehensive Testing and Validation
- Create unit tests in `tests/test_field_extraction.py` to validate all extraction fixes
- Test with contaminated HTML samples to ensure sanitization works
- Add tests for discount field defaulting behavior
- Create validation scripts to test SKU extraction accuracy
- Add regression tests to prevent future contamination issues

### 7. Update Retailer-Specific Extractors
- Update ThaiWatsaduExtractor to use enhanced sanitization methods
- Fix BoonthavornExtractor brand/model extraction using improved patterns
- Ensure all retailer-specific extractors implement the new contamination prevention
- Add retailer-specific SKU validation rules for each major retailer

### 8. Document and Validate Fixes
- Create comprehensive documentation of all field extraction improvements
- Generate before/after examples showing contamination removal
- Update extraction method documentation with new patterns and validation rules
- Create validation report showing improved data quality metrics

## Validation Commands
Execute these commands to validate the chore is complete:

### Field Extraction Validation
```bash
# Test enhanced text sanitization
python3 -c "
from adws.adw_modules.product_extractor import ProductExtractor
extractor = ProductExtractor()
test_text = 'quickInfo-infoLabel-ขนาดสินค้า</label><label class=\"quickInfo-infoValue-123\">10x20x30 cm</label>'
cleaned = extractor._sanitize_text_field(test_text, max_length=100)
print(f'Sanitized: {cleaned}')
"

# Test discount field defaults
python3 -c "
from adws.adw_modules.product_schemas import ProductData
product = ProductData(name='Test', url='http://test.com', current_price=None, original_price=None)
print(f'Discount defaults: has_discount={product.has_discount}, discount_percent={product.discount_percent}, discount_amount={product.discount_amount}')
"

# Test SKU extraction validation
python3 -c "
from adws.adw_modules.product_extractor import ProductExtractor
extractor = ProductExtractor('https://example.com/product/12345')
sku = extractor._extract_sku('<div>Invalid URL: https://example.com/product/12345</div>')
print(f'Extracted SKU: {sku}')
"
```

### Output Validation
```bash
# Run comprehensive extraction test
python3 debug_tools/test_extractor.py --test-sanitization --test-discounts --test-skus

# Validate output formatting
python3 -c "
from adws.output_formatter import OutputFormatter
formatter = OutputFormatter()
test_data = [{'name': 'Test Product with contamination', 'dimensions': 'class=\"dim-label</label><span>10x20x30</span>', 'current_price': None}]
result = formatter.format_results(test_data, 'structured')
print(result)
"
```

### Integration Testing
```bash
# Test with real retailer URLs
python3 adws/adw_ecommerce_product_scraper.py --urls-file tests/retailer_test_urls.csv --test-mode --validate-fields

# Run full extraction pipeline with validation
python3 debug_tools/test_all_retailers.sh --validate-extraction --check-contamination
```

## Notes
- Focus on preventing HTML/CSS class name contamination in text fields
- Ensure all 18 required e-commerce fields are properly validated and cleaned
- Test with real retailer data to validate fixes work in production scenarios
- Pay special attention to discount field null handling to ensure proper 0.0 defaults
- Document all new patterns and validation rules for future maintenance
- Create comprehensive unit tests to prevent regression of these critical data quality issues