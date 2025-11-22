# Chore: A4B1E161 Validation Commands

## Metadata
adw_id: `a4b1e161`
purpose: `Validation commands for e-commerce scraper JSON output format fix`

## Validation Commands

These commands can be used to validate that the e-commerce scraper output format fix is working correctly.

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
        content = f.read().strip()
        if content.startswith('{') or content.startswith('['):
            print('✅ E-commerce correctly forced to JSON format')
        else:
            print('❌ CSV format detected for e-commerce')
except:
    print('❌ Error reading output file')
"
```

### Test Output Formatter CSV Redirection

```bash
# Test that output formatter redirects e-commerce data to JSON
python3 -c "
from adws.output_formatter import OutputFormatter

# Create sample e-commerce data
ecommerce_data = [{
    'name': 'Test Product',
    'retailer': 'Thai Watsadu',
    'url': 'https://www.thaiwatsadu.com/th/sku/12345',
    'current_price': 1000,
    'original_price': 1500,
    'sku': '12345',
    'brand': 'Test Brand'
}]

formatter = OutputFormatter()
result = formatter._format_csv(ecommerce_data)

# Check if result is JSON (should be redirected)
if result.strip().startswith('{') or result.strip().startswith('['):
    print('✅ E-commerce CSV correctly redirected to JSON')
else:
    print('❌ E-commerce CSV not redirected')
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

### Test URL Detection Function

```bash
# Test the e-commerce URL detection function
python3 -c "
import sys
sys.path.insert(0, 'adws')
from adw_crawl4ai_scraper import is_ecommerce_url

test_urls = [
    ('https://www.thaiwatsadu.com/th/sku/60363373', True),
    ('https://homepro.co.th/product/123', True),
    ('https://dohome.co.th/item/456', True),
    ('https://boonthavorn.com/product/789', True),
    ('https://globalhouse.co.th/item/321', True),
    ('https://megahome.co.th/product/654', True),
    ('https://google.com/search', False),
    ('https://github.com/user/repo', False)
]

print('Testing e-commerce URL detection:')
for url, expected in test_urls:
    result = is_ecommerce_url(url)
    status = '✅' if result == expected else '❌'
    print(f'{status} {url} -> {result} (expected {expected})')
"
```

### Test E-commerce Data Detection

```bash
# Test the e-commerce data detection function
python3 -c "
from adws.output_formatter import OutputFormatter

# Test cases
test_cases = [
    # E-commerce data (should be detected)
    [{'name': 'Product', 'retailer': 'Thai Watsadu', 'current_price': 1000}],
    [{'name': 'Product', 'url': 'https://www.thaiwatsadu.com/th/sku/123', 'sku': '123'}],
    [{'brand': 'Brand', 'model': 'Model', 'sku': 'SKU', 'current_price': 1000}],

    # Non-ecommerce data (should not be detected)
    [{'title': 'Article', 'content': 'Some text content'}],
    [{'url': 'https://google.com', 'title': 'Google'}]
]

formatter = OutputFormatter()
print('Testing e-commerce data detection:')
for i, data in enumerate(test_cases):
    result = formatter.is_ecommerce_data(data)
    print(f'Test {i+1}: {result}')
"
```

## Expected Results

When all validation commands pass, you should see:

1. ✅ JSON format confirmed for single URL scraping
2. ✅ Batch JSON output with correct product count
3. ✅ No CSV files created during retailer testing
4. ✅ JSON files created for all retailers
5. ✅ E-commerce URLs forced to JSON format in crawl4ai scraper
6. ✅ E-commerce CSV data redirected to JSON in output formatter
7. ✅ No new CSV files in output directories
8. ✅ Valid JSON files in output directories
9. ✅ Correct URL detection for all supported retailers
10. ✅ Proper e-commerce data detection

## Clean Up Commands

```bash
# Clean up test files
rm -f /tmp/test_single_output.json
rm -f /tmp/test_batch.csv
rm -f /tmp/test_batch_output.json
rm -f /tmp/test_output.txt
rm -f /tmp/test_crawl4ai_output*
rm -f /tmp/*_test.csv
rm -f /tmp/*_test_results.json
```