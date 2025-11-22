# Chore: Fix Relative Import Error in product_extractor.py

## Metadata
adw_id: `30e650f6`
prompt: `Import error occurred after implementing MegaHomeExtractor. The error is: 'ImportError: attempted relative import with no known parent package' in product_extractor.py line 13. The import statement 'from .product_schemas import ProductData, PriceParser, normalize_product_data' needs to be fixed to work with the current module structure. Please fix the import issue.`

## Chore Description
The import error occurs because the `product_extractor.py` module is using relative imports (`from .product_schemas import ...`) but the `adw_modules` directory lacks an `__init__.py` file, making it unable to be recognized as a Python package. This prevents the MegaHomeExtractor and other classes in product_extractor.py from being imported properly when the module is executed as part of the e-commerce scraping workflow.

The issue manifests when the ADW e-commerce scraper tries to import and use the MegaHomeExtractor class, resulting in an ImportError that blocks the scraping functionality for Mega Home retailer URLs.

## Relevant Files
Use these files to complete the chore:

- `/Users/tachongrak/Projects/Optus/adws/adw_modules/product_extractor.py` - Contains the problematic relative import on line 13
- `/Users/tachongrak/Projects/Optus/adws/adw_modules/product_schemas.py` - Contains the classes being imported (ProductData, PriceParser, normalize_product_data)
- `/Users/tachongrak/Projects/Optus/adws/adw_ecommerce_product_scraper.py` - Main script that uses the extractor classes
- `/Users/tachongrak/Projects/Optus/adws/adw_modules/__init__.py` - Missing file that needs to be created

### New Files
- `/Users/tachongrak/Projects/Optus/adws/adw_modules/__init__.py` - Empty init file to make adw_modules a proper Python package

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Create __init__.py file in adw_modules directory
- Create an empty `__init__.py` file in `/Users/tachongrak/Projects/Optus/adws/adw_modules/`
- This file will make `adw_modules` a proper Python package, allowing relative imports to work correctly

### 2. Test the import fix
- Test importing the product_extractor module from the project root directory
- Verify that MegaHomeExtractor can be imported without errors
- Ensure the relative import works properly with the new package structure

### 3. Validate the e-commerce scraper functionality
- Test that the e-commerce product scraper can use all retailer extractors including MegaHomeExtractor
- Run a quick test with a Mega Home URL to ensure the extraction workflow functions correctly

## Validation Commands
Execute these commands to validate the chore is complete:

- `python3 -c "from adws.adw_modules.product_extractor import MegaHomeExtractor; print('✅ MegaHomeExtractor imported successfully')"` - Test that MegaHomeExtractor imports correctly
- `python3 -c "from adws.adw_modules.product_extractor import ProductExtractor; print('✅ ProductExtractor imported successfully')"` - Test that ProductExtractor still works
- `python3 -c "from adws.adw_modules.product_extractor import ThaiWatsaduExtractor, HomeProExtractor, BoonthavornExtractor; print('✅ All retailer extractors imported successfully')"` - Test all existing extractors
- `ls -la /Users/tachongrak/Projects/Optus/adws/adw_modules/__init__.py` - Verify the __init__.py file exists

## Notes
The relative import pattern (`from .module import ...`) is the correct approach for intra-package imports in Python. The issue is not with the import syntax itself, but with the missing package structure. By adding the `__init__.py` file, we make `adw_modules` a proper Python package, which allows Python's import system to resolve relative imports correctly.

This fix will ensure that:
- All retailer-specific extractors (ThaiWatsaduExtractor, HomeProExtractor, BoonthavornExtractor, MegaHomeExtractor) can be imported properly
- The e-commerce scraping workflow can use the appropriate extractor based on URL domain
- The existing code structure and import patterns remain unchanged
- No modifications to the actual import statements are needed, preserving the intended package architecture