# Chore: Fix the e-commerce product scraper output format issue

## Metadata
adw_id: `a4b1e161`
prompt: `Fix the e-commerce product scraper output format issue - the output should be in JSON format instead of CSV. Check the output formatting logic and ensure all retailer-specific outputs are saved as JSON files, not CSV files.`

## Chore Description
The e-commerce product scraper is currently outputting CSV files instead of the required JSON format. This needs to be fixed by:

1. Ensuring the e-commerce product scraper (`adw_ecommerce_product_scraper.py`) only outputs JSON format
2. Removing or modifying CSV output options in related scrapers
3. Updating any scripts that might be triggering CSV output for e-commerce data
4. Ensuring all retailer-specific outputs are saved as JSON files with proper formatting

## Relevant Files
Use these files to complete the chore:

### Core E-commerce Scraper
- `adws/adw_ecommerce_product_scraper.py` - Main e-commerce scraper (already outputs JSON correctly)
- `adws/adw_modules/product_extractor.py` - Product extraction logic (outputs JSON)

### Related Scrapers to Modify
- `adws/adw_crawl4ai_scraper.py` - General scraper that supports CSV output (needs modification)
- `adws/output_formatter.py` - Contains CSV formatting logic (needs e-commerce specific changes)
- `adws/adw_modules/crawl4ai_wrapper.py` - Wrapper that formats CSV output (needs modification)

### Scripts and Configuration
- `debug_tools/test_all_retailers.sh` - Test script that should ensure JSON output

### New Files to Create
- `specs/chore-a4b1e161-validation-commands.md` - Documentation of validation commands

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Modify adw_crawl4ai_scraper.py to Remove CSV Option for E-commerce
- Check if the crawl4ai scraper is being used for e-commerce products
- Remove or modify the `--output-format` option to exclude CSV for e-commerce URLs
- Add logic to detect e-commerce URLs and force JSON output
- Update default behavior to ensure JSON is used for product scraping

### 2. Update output_formatter.py CSV Handling
- Modify the `_format_csv` method to detect e-commerce product data
- Add logic to redirect e-commerce data to JSON format instead of CSV
- Ensure retailer-specific product data is always formatted as JSON

### 3. Update crawl4ai_wrapper.py Format Results
- Modify the `format_results` method to detect e-commerce content
- Force JSON output for product-related scraping results
- Add URL pattern detection for e-commerce sites

### 4. Clean Up Existing CSV Output Files
- Identify any existing CSV files in the output directories
- Convert them to JSON format or remove if outdated
- Update directory structure to ensure consistent JSON output

### 5. Update Test Scripts to Ensure JSON Output
- Modify `debug_tools/test_all_retailers.sh` to verify JSON output
- Add validation to ensure no CSV files are generated for e-commerce scraping
- Test with all supported retailers to confirm JSON output

### 6. Update Documentation and Help Text
- Update help text in scrapers to clarify JSON-only output for e-commerce
- Update README files to reflect JSON-only output for product scraping
- Add warnings about deprecated CSV format for e-commerce data

## Validation Commands
Execute these commands to validate the chore is complete:

### Test E-commerce Scraper JSON Output
```bash
# Test single URL scraping
./adws/adw_ecommerce_product_scraper.py \
  --url https://www.thaiwatsadu.com/th/sku/60363373 \
  --output-file /tmp/test_single_output.json

# Verify JSON format and content
python3 -c "
import json
with open('/tmp/test_single_output.json', 'r') as f:
    data = json.load(f)
    print(f'Output type: {type(data)}')
    print(f'Product count: {len(data) if isinstance(data, list) else 1}')
    print('✅ JSON format confirmed' if isinstance(data, (dict, list)) else '❌ Not JSON')
"
```

### Test Batch Scraping JSON Output
```bash
# Test batch scraping
head -6 inputs/ecommerce/thaiwatsadu_urls.csv | tail -5 > /tmp/test_batch.csv
./adws/adw_ecommerce_product_scraper.py \
  --urls-file /tmp/test_batch.csv \
  --output-file /tmp/test_batch_output.json

# Verify JSON output
python3 -c "
import json
try:
    with open('/tmp/test_batch_output.json', 'r') as f:
        data = json.load(f)
        print(f'✅ Batch JSON output: {len(data)} products')
except Exception as e:
    print(f'❌ JSON parse error: {e}')
"
```

### Test All Retailers Script
```bash
# Run the test retailers script and verify no CSV output
./debug_tools/test_all_retailers.sh > /tmp/test_output.txt 2>&1

# Check that no CSV files were created during testing
find /tmp -name "*.csv" -newer /tmp/test_output.txt | wc -l
# Should output 0 (no new CSV files)

# Verify JSON outputs were created
find /tmp -name "*_test_results.json" -newer /tmp/test_output.txt | wc -l
# Should output > 0 (JSON files created)
```

### Test Crawl4AI Scraper with E-commerce URLs
```bash
# Test that crawl4ai scraper forces JSON for e-commerce URLs
./adws/adw_crawl4ai_scraper.py \
  --url https://www.thaiwatsadu.com/th/sku/60363373 \
  --output-format csv \
  --output-file /tmp/test_crawl4ai_output

# Check if output is actually JSON despite CSV request
file /tmp/test_crawl4ai_output
python3 -c "
import json
try:
    with open('/tmp/test_crawl4ai_output', 'r') as f:
        if f.read().strip().startswith('{') or f.read().strip().startswith('['):
            print('✅ E-commerce correctly forced to JSON format')
        else:
            print('❌ CSV format detected for e-commerce')
except:
    print('❌ Error reading output file')
"
```

### Check No CSV Files in Output Directories
```bash
# Verify no new CSV files exist in output directories
find apps/output -name "*.csv" -newer specs/chore-a4b1e161-fix-ecommerce-scraper-output-format.md | wc -l
# Should output 0 (no new CSV files since fix)

# Verify JSON files are present and valid
find apps/output -name "*.json" -newer specs/chore-a4b1e161-fix-ecommerce-scraper-output-format.md | head -5 | xargs -I {} python3 -c "
import json, sys
try:
    with open('{}', 'r') as f:
        json.load(f)
    print('✅ {} - Valid JSON')
except Exception as e:
    print(f'❌ {} - Invalid JSON: {e}')
"
```

## Notes
- The `adw_ecommerce_product_scraper.py` already outputs JSON correctly and doesn't need modification
- Focus on preventing CSV output from other scrapers when processing e-commerce URLs
- Ensure retailer detection works correctly to force JSON format for all supported e-commerce sites
- Test thoroughly with all supported retailers: Thai Watsadu, HomePro, DoHome, Boonthavorn, Global House, Mega Home
- The solution should be backward compatible for non-ecommerce scraping while enforcing JSON for e-commerce