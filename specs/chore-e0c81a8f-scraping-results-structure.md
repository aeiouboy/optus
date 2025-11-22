# Chore: Create Comprehensive Scraping Results Output Structure

## Metadata
adw_id: `e0c81a8f`
prompt: `Create a well-organized output structure for scraping results in /Users/tachongrak/Projects/Optus/apps/output with the following requirements:

1. Create a main structure:
   - /apps/output/scraping/
     - by_date/ (organized by YYYY-MM-DD)
     - by_domain/ (organized by website domain)
     - by_type/ (organized by content type like products, articles, etc.)
     - latest/ (most recent results)

2. Each result should include:
   - raw/ (original HTML/JSON)
   - processed/ (cleaned data)
   - summary/ (key information extracted)
   - assets/ (images, files downloaded)

3. Create utility scripts:
   - organize_results.py (to move existing results)
   - find_results.py (to search and retrieve results)
   - cleanup_old.py (to remove old results)

4. Create an index.html dashboard to browse results easily

5. Update the crawl4ai scraper to save results to this new structure by default

Make the structure user-friendly and accessible for easy browsing and analysis of scraped data.`

## Chore Description
This chore creates a comprehensive, well-organized output structure for web scraping results in the Optus project. The goal is to establish a standardized directory hierarchy that makes scraping results easy to browse, search, and analyze. The structure includes multiple organization methods (by date, domain, and content type), standardized subdirectories for different data types, utility scripts for result management, a web dashboard for browsing, and integration with the existing crawl4ai scraper to use this new structure by default.

## Relevant Files
Use these files to complete the chore:

### Existing Files to Modify:
- `adws/adw_crawl4ai_scraper.py` - Main scraper that needs to be updated to use the new output structure
- `adws/adw_modules/crawl4ai_wrapper.py` - Wrapper module that may need updates for new organization options

### New Files to Create:

#### Directory Structure:
- `apps/output/scraping/` - Main scraping output directory
  - `by_date/` - Date-organized results (YYYY-MM-DD/domain/job-id/)
  - `by_domain/` - Domain-organized results (domain/YYYY-MM-DD/job-id/)
  - `by_type/` - Content type organized results (type/domain/YYYY-MM-DD/job-id/)
  - `latest/` - Symbolic links or copies to most recent results
  - `index.html` - Dashboard for browsing results

#### Utility Scripts:
- `apps/output/scraping/utils/organize_results.py` - Script to organize and move existing results
- `apps/output/scraping/utils/find_results.py` - Script to search and retrieve specific results
- `apps/output/scraping/utils/cleanup_old.py` - Script to clean up old results based on criteria
- `apps/output/scraping/utils/result_manager.py` - Core utilities shared by other scripts

#### Configuration and Documentation:
- `apps/output/scraping/config.json` - Configuration file for output organization
- `apps/output/scraping/README.md` - Documentation for the structure and usage

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Create the Main Directory Structure
- Create the base `/apps/output/scraping/` directory
- Create the main organization subdirectories: `by_date/`, `by_domain/`, `by_type/`, `latest/`
- Create the `utils/` directory for management scripts
- Set appropriate permissions and create placeholder `.gitkeep` files

### 2. Create Standardized Result Subdirectory Structure
- Define the standard result structure with: `raw/`, `processed/`, `summary/`, `assets/` subdirectories
- Create a template function that generates this structure for any result
- Ensure each subdirectory has appropriate README files explaining its purpose

### 3. Implement Core Result Management Utilities
- Create `result_manager.py` with core functions:
  - `create_result_structure()` - Creates the standard directory structure
  - `organize_by_date()` - Organizes results by date
  - `organize_by_domain()` - Organizes results by domain
  - `organize_by_type()` - Organizes results by content type
  - `get_domain_from_url()` - Extracts domain from URLs
  - `detect_content_type()` - Analyzes content to determine type

### 4. Create the Organization Script (organize_results.py)
- Implement functionality to scan existing result directories
- Add logic to categorize existing results by date, domain, and content type
- Create the organized directory structure
- Move/copy existing results to appropriate locations
- Generate a report of organization actions taken

### 5. Create the Search and Retrieval Script (find_results.py)
- Implement search functionality across all organization methods
- Add filtering options by date, domain, content type, keywords
- Support both interactive and command-line usage
- Include options to display, copy, or move found results

### 6. Create the Cleanup Script (cleanup_old.py)
- Implement age-based cleanup (remove results older than X days)
- Add size-based cleanup (remove results when total size exceeds threshold)
- Include content type filtering for selective cleanup
- Add dry-run mode to preview what would be deleted
- Implement backup/confirmation mechanisms

### 7. Create the Web Dashboard (index.html)
- Design a responsive, user-friendly interface
- Include navigation for all organization methods
- Add search and filtering capabilities
- Display result metadata and statistics
- Include preview functionality for text-based results
- Add management links (cleanup, organize, etc.)

### 8. Create Configuration System
- Design `config.json` with default settings for organization
- Include options for default organization method, retention policies, etc.
- Make configuration easily extensible
- Add validation for configuration values

### 9. Update the Crawl4AI Scraper Integration
- Modify `adw_crawl4ai_scraper.py` to use the new output structure
- Add new CLI options for organization preferences
- Integrate with the result manager utilities
- Maintain backward compatibility with existing output options
- Update help documentation and examples

### 10. Update the Crawl4AI Wrapper
- Extend `crawl4ai_wrapper.py` with content type detection
- Add domain extraction utilities
- Include result organization metadata in ScrapingResult
- Ensure compatibility with the new output structure

### 11. Create Comprehensive Documentation
- Write detailed README.md explaining the structure and usage
- Include examples of common workflows
- Document all utility scripts with usage examples
- Add troubleshooting guide for common issues

### 12. Testing and Validation
- Test the complete structure with sample scraping results
- Validate all utility scripts work correctly
- Test the web dashboard functionality
- Ensure integration with crawl4ai scraper works properly
- Test edge cases and error conditions

## Validation Commands
Execute these commands to validate the chore is complete:

### Structure Validation:
- `ls -la /Users/tachongrak/Projects/Optus/apps/output/scraping/` - Verify main structure exists
- `find /Users/tachongrak/Projects/Optus/apps/output/scraping/ -name "*.py" | wc -l` - Should show 4+ utility scripts
- `test -f /Users/tachongrak/Projects/Optus/apps/output/scraping/index.html` - Dashboard exists

### Script Validation:
- `python apps/output/scraping/utils/organize_results.py --help` - Organization script working
- `python apps/output/scraping/utils/find_results.py --help` - Search script working
- `python apps/output/scraping/utils/cleanup_old.py --help` - Cleanup script working

### Integration Validation:
- `python adws/adw_crawl4ai_scraper.py --help | grep "output-folder"` - Verify new options exist
- Test run with new output structure: `python adws/adw_crawl4ai_scraper.py --url https://example.com --output-folder apps/output/scraping --test`
- `ls -la apps/output/scraping/by_date/$(date +%Y-%m-%d)/` - Verify results are organized

### Content Validation:
- `test -f apps/output/scraping/config.json` - Configuration exists
- `test -f apps/output/scraping/README.md` - Documentation exists
- `python -m json.tool apps/output/scraping/config.json > /dev/null` - Valid JSON configuration

## Notes
- Maintain backward compatibility with existing crawl4ai scraper workflows
- Ensure all utility scripts have proper error handling and logging
- Make the web dashboard responsive and accessible
- Consider future extensibility when designing the structure
- Include proper security measures for the web dashboard (no sensitive data exposure)
- Ensure the structure works well with both small and large numbers of results
- Test with various content types and domains to ensure robust organization