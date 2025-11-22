# Chore: Fix E-commerce Product Scraper Issues

## Metadata
adw_id: `abb2b520`
prompt: `Fix the e-commerce product scraper issues: 1) Clean up the brand field extraction to avoid JSON data contamination from the HTML, 2) Improve output folder structure to follow proper ADW patterns with organized subdirectories (raw/, processed/, logs/, assets/) like the crawl4ai_scraper.py does, 3) Ensure all output files are properly organized in the agents/{adw_id}/ structure`

## Chore Description
Fix three critical issues in the e-commerce product scraper:
1. Brand field extraction is contaminated with JSON data from HTML, causing data quality issues
2. Output folder structure lacks proper ADW organization patterns (missing raw/, processed/, logs/, assets/ subdirectories)
3. Output files need consistent organization under agents/{adw_id}/ structure matching other ADWs

## Relevant Files

### Current Files
- `adws/adw_ecommerce_product_scraper.py` - Main scraper with output structure issues (lines 342-344, 479-532)
- `adws/adw_modules/product_extractor.py` - Brand extraction logic causing JSON contamination (lines 48-50)
- `adws/adw_crawl4ai_scraper.py` - Reference implementation for proper ADW output patterns (lines 328-370, 780-793)

### New Files
None - modifications to existing files only

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Fix Brand Field Extraction Logic
- Locate brand extraction methods in `product_extractor.py`
- Clean extraction logic to avoid JSON data contamination from HTML
- Add proper sanitization and validation for brand field data
- Ensure brand extraction returns clean text strings only

### 2. Implement Proper ADW Output Folder Structure
- Add `create_output_directory_structure()` function to `adw_ecommerce_product_scraper.py`
- Implement organized subdirectories: raw/, processed/, logs/, assets/
- Follow the pattern established in `crawl4ai_scraper.py` (lines 328-370)
- Support both legacy (agents/{adw_id}/) and organized output structures

### 3. Update File Output Organization
- Modify output file paths to use proper subdirectory organization
- Place raw data files (JSONL, JSON) in `raw/` subdirectory
- Place processed results in `processed/` subdirectory
- Place summary and log files in `logs/` subdirectory
- Update all references to output paths in the main scraper logic

### 4. Ensure Consistent agents/{adw_id}/ Structure
- Verify all output files respect the agents/{adw_id}/ base structure
- Update path resolution logic to handle both absolute and relative paths
- Ensure backward compatibility with existing output expectations
- Test output structure matches ADW patterns consistently

### 5. Validate Output Structure and Data Quality
- Test brand field extraction produces clean data without JSON contamination
- Verify output folder structure matches crawl4ai_scraper.py patterns
- Confirm all files are properly organized in agents/{adw_id}/ structure
- Run test scraping to validate complete implementation

## Validation Commands
Execute these commands to validate the chore is complete:

```bash
# Test brand field extraction for data quality
uv run adws/adw_ecommerce_product_scraper.py --url https://www.thaiwatsadu.com/th/sku/60363373 --test --adw-id test-brand-fix

# Verify output folder structure
ls -la agents/test-brand-fix/ecommerce_scraper/
ls -la agents/test-brand-fix/ecommerce_scraper/raw/
ls -la agents/test-brand-fix/ecommerce_scraper/processed/
ls -la agents/test-brand-fix/ecommerce_scraper/logs/

# Test full workflow with organized output
uv run adws/adw_ecommerce_product_scraper.py --url https://www.thaiwatsadu.com/th/sku/60363373 --output-folder ./test_output --adw-id test-structure

# Compare structure with crawl4ai_scraper.py
diff -r agents/test-brand-fix/ agents/test-crawl4ai/ || true
```

## Notes
- Key focus on data quality: brand field must be clean text without JSON contamination
- Output structure must match crawl4ai_scraper.py patterns for consistency
- Maintain backward compatibility with existing agents/{adw_id}/ expectations
- Test with real e-commerce URLs to validate fixes work in production