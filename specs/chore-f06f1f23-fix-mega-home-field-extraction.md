# Chore: Fix Mega Home Field Extraction Sanitization Integration

## Metadata
adw_id: `f06f1f23`
prompt: `The field extraction fixes are not working as expected. After testing with the same Mega Home URL (https://www.megahome.co.th/p/18964), we still see: 1) Product name extracted as 'MegaHome' (store name instead of product name), 2) Model field contains 'html' (invalid data), 3) Color field contains 'var(--black)' (CSS variable), 4) Dimensions contains '16' (CSS value). The sanitization methods need to be properly integrated into the extraction workflow. Please investigate and fix the integration issue.`

## Chore Description
The field extraction sanitization methods are not properly integrated for Mega Home retailer extraction. When testing with Mega Home URL (https://www.megahome.co.th/p/18964), the extraction still returns contaminated data:

1. **Product name**: Shows 'MegaHome' (store name) instead of actual product name
2. **Model field**: Contains 'html' (HTML element contamination)
3. **Color field**: Contains 'var(--black)' (CSS variable contamination)
4. **Dimensions field**: Contains '16' (CSS value contamination)

The root cause is that Mega Home uses the generic `ProductExtractor` class instead of a specialized extractor with enhanced sanitization methods applied. While sanitization methods exist in the base class, they are not being systematically applied to all fields during extraction.

## Relevant Files
Use these files to complete the chore:

- `/Users/tachongrak/Projects/Optus/adws/adw_modules/product_extractor.py` - Main extraction logic with sanitization methods
- `/Users/tachongrak/Projects/Optus/adws/adw_ecommerce_product_scraper.py` - Main scraper orchestration
- `/Users/tachongrak/Projects/Optus/tests/test_field_extraction.py` - Comprehensive test suite for validation

### Key Issues Found:
1. **Mega Home Implementation**: Uses generic `ProductExtractor` without field-specific sanitization (line 1085-1088)
2. **Sanitization Methods Exist**: `_sanitize_color_field()`, `_sanitize_dimensions_field()`, etc. are implemented but not applied
3. **ThaiWatsaduExtractor Model**: Shows proper sanitization integration example (lines 883-890)
4. **Base ProductExtractor**: Has sanitization methods but needs systematic application in `extract_from_html()`

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Create MegaHomeExtractor Class
- Create specialized `MegaHomeExtractor` class inheriting from `ProductExtractor`
- Override `extract_from_html()` method to apply field-specific sanitization
- Follow the pattern established in `ThaiWatsaduExtractor` (lines 883-890)
- Apply sanitization methods for: color, dimensions, material, brand, model fields

### 2. Enhance Base ProductExtractor Sanitization Integration
- Modify base `ProductExtractor.extract_from_html()` to apply sanitization methods systematically
- Apply `_sanitize_color_field()` to prevent CSS variables like `var(--black)`
- Apply `_sanitize_dimensions_field()` to extract proper dimension patterns
- Apply `_sanitize_text_field()` to prevent HTML contamination in model field
- Ensure retailer name doesn't contaminate product name extraction

### 3. Update Extractor Factory Function
- Modify `get_extractor()` function to return `MegaHomeExtractor` for Mega Home URLs
- Ensure proper retailer assignment: `extractor.retailer = "Mega Home"`

### 4. Fix Product Name Extraction Logic
- Enhance `_extract_product_name()` to avoid extracting store/retailer names
- Add logic to filter out common retailer names from product title
- Improve HTML parsing to target actual product name elements vs site branding

### 5. Update CSS Variable Sanitization
- Add `var(--[^)]+)` pattern to CSS color patterns in `_sanitize_color_field()`
- Ensure CSS custom properties are filtered out from color fields
- Test with Mega Home's specific CSS variable patterns

### 6. Validate Model Field Extraction
- Fix `_extract_model()` to prevent HTML element names as model values
- Add validation to reject 'html', 'body', 'div', 'span' as model values
- Apply enhanced text sanitization to model field extraction

### 7. Test and Validate Integration
- Run comprehensive tests using existing test suite
- Test specifically with Mega Home URL to verify all issues are resolved
- Verify output fields contain clean, valid data without contamination
- Ensure field extraction works consistently across all retailers

## Validation Commands
Execute these commands to validate the chore is complete:

- `python -m pytest tests/test_field_extraction.py -v` - Run comprehensive field extraction tests
- `python -c "
from adws.adw_modules.product_extractor import get_extractor
extractor = get_extractor('https://www.megahome.co.th/p/18964')
print(f'Extractor type: {type(extractor).__name__}')
print(f'Retailer: {getattr(extractor, \"retailer\", \"Not set\")}')
"` - Verify Mega Home extractor instantiation
- `python -c "
from adws.adw_modules.product_extractor import MegaHomeExtractor
extractor = MegaHomeExtractor()
# Test CSS variable sanitization
result = extractor._sanitize_color_field('var(--black)')
print(f'CSS variable sanitized: {result}')
# Test dimension sanitization
result = extractor._sanitize_dimensions_field('16')
print(f'Dimension sanitized: {result}')
"` - Test specific sanitization methods
- `uv run python -m py_compile adws/adw_modules/product_extractor.py` - Ensure code compiles without syntax errors

## Notes
- The sanitization methods already exist and work correctly - they just need to be properly integrated
- Follow the established pattern from `ThaiWatsaduExtractor` for consistent implementation
- Focus on systematic application of sanitization methods rather than rewriting existing logic
- Mega Home has specific contamination patterns (CSS variables) that need to be addressed
- Test with the actual failing URL to ensure all reported issues are resolved