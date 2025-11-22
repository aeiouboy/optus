# Chore: Fix Retailer Domain Mappings

## Metadata
adw_id: `66cc0750`
prompt: `Fix the retailer mapping in product_extractor.py by adding missing domain mappings for DoHome (dohome.co.th), Global House (globalhouse.co.th), and Mega Home (megahome.co.th) to the _extract_retailer_from_url method`

## Chore Description
The chore involves fixing a bug in the `product_extractor.py` file where the `_extract_retailer_from_url` method is missing domain mappings for three supported retailers: DoHome, Global House, and Mega Home. While these retailers are properly supported in the `get_extractor` function (lines 759-770), they are missing from the `retailer_mappings` dictionary in the `_extract_retailer_from_url` method (lines 499-509). This inconsistency causes the retailer extraction to fall back to generic domain-based naming instead of using the proper retailer names.

## Relevant Files
Use these files to complete the chore:

- `/Users/tachongrak/Projects/Optus/adws/adw_modules/product_extractor.py` - Main file containing the retailer mapping bug that needs to be fixed

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Locate the retailer_mappings dictionary
- Find the `_extract_retailer_from_url` method in product_extractor.py (around line 486)
- Locate the `retailer_mappings` dictionary within this method (around line 499)

### 2. Add missing domain mappings
- Add `'dohome.co.th': 'DoHome'` to the retailer_mappings dictionary
- Add `'globalhouse.co.th': 'Global House'` to the retailer_mappings dictionary
- Add `'megahome.co.th': 'Mega Home'` to the retailer_mappings dictionary

### 3. Verify consistency with get_extractor function
- Ensure the retailer names in the mappings match exactly with those used in the `get_extractor` function (lines 759-770)
- Confirm that the domain patterns match those used in the extractor selection logic

### 4. Test the fix
- Run a syntax check to ensure the code is valid Python
- Test the method with sample URLs from each retailer domain to verify correct retailer name extraction

## Validation Commands
Execute these commands to validate the chore is complete:

- `python -m py_compile /Users/tachongrak/Projects/Optus/adws/adw_modules/product_extractor.py` - Test to ensure the code compiles without syntax errors
- `cd /Users/tachongrak/Projects/Optus && python3 -c "
import sys
sys.path.append('adws/adw_modules')
from product_extractor import ProductExtractor
extractor = ProductExtractor()
test_urls = [
    'https://www.dohome.co.th/product/123',
    'https://globalhouse.co.th/item/456',
    'https://megahome.co.th/p/789'
]
for url in test_urls:
    print(f'{url} -> {extractor._extract_retailer_from_url(url)}')
"` - Test the retailer extraction for the three domains

## Notes
- The retailer mappings should be placed in alphabetical order within the dictionary for maintainability
- Ensure the retailer names exactly match those used in the `get_extractor` function to maintain consistency
- The domain patterns should match the existing patterns used in the extractor selection logic