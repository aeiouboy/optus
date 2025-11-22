# Chore: Add file input and output folder functionality to adw_crawl4ai_scraper.py

## Metadata
adw_id: `d365a3ef`
prompt: `Add file input and output folder functionality to adw_crawl4ai_scraper.py. Add --input-folder option to read URLs from multiple files in a directory, and --output-folder option to organize results in separate folders by date or job ID.`

## Chore Description
Add enhanced file handling capabilities to the crawl4ai scraper script:
1. Implement `--input-folder` option to read URLs from multiple files in a directory
2. Implement `--output-folder` option to organize results in separate folders by date or job ID
3. Support flexible file name patterns for input files (e.g., *.txt, *.urls)
4. Maintain backward compatibility with existing `--urls-file` option
5. Update output structure to create organized directory structures for results

## Relevant Files
Use these files to complete the chore:

### Existing Files
- `adws/adw_crawl4ai_scraper.py` - Main scraper script that needs modification
- `adws/adw_modules/crawl4ai_wrapper.py` - Wrapper module for crawl4ai functionality
- `specs/chore-976192b6-crawl4ai-scraping-system.md` - Previous chore specification for reference

### New Files
- No new files needed - modifications to existing script only

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Analyze Current Implementation
- Review existing CLI argument structure and URL loading functionality
- Examine current output directory structure and file naming conventions
- Understand the existing file reading patterns and error handling

### 2. Add --input-folder CLI Option
- Add new Click option for `--input-folder` with path validation
- Create function to scan directory for URL files (*.txt, *.urls, *.list extensions)
- Implement `load_urls_from_folder()` function to aggregate URLs from multiple files
- Add file type filtering and validation for input files

### 3. Add --output-folder CLI Option
- Add new Click option for `--output-folder` with path validation
- Create function to generate organized output directory structures
- Support organization by date (YYYY-MM-DD) or job ID
- Update output path handling to use folder structure when specified

### 4. Update Argument Validation Logic
- Modify existing argument validation to handle new folder options
- Ensure mutual exclusivity between --url, --urls-file, and --input-folder
- Add validation for folder existence and permissions
- Update help text and error messages for clarity

### 5. Enhance Output Organization
- Modify output directory creation to support folder-based organization
- Update file saving logic to create subdirectories as needed
- Implement date-based and job-ID based folder naming schemes
- Ensure all output files (JSON, JSONL, summary) follow new folder structure

### 6. Update Rich Console Output
- Add configuration display for new folder options
- Update status panels to show folder processing information
- Display file discovery progress when reading from input folders
- Show output directory structure information

### 7. Test and Validate Changes
- Test with single URL (existing functionality)
- Test with single URLs file (existing functionality)
- Test with input folder containing multiple URL files
- Test output folder organization with date-based naming
- Test output folder organization with job-ID based naming
- Verify backward compatibility is maintained

## Validation Commands
Execute these commands to validate the chore is complete:

```bash
# Test basic functionality is preserved
./adws/adw_crawl4ai_scraper.py --url https://example.com --test

# Test existing file input still works
echo -e "https://example.com\nhttps://httpbin.org/html" > test_urls.txt
./adws/adw_crawl4ai_scraper.py --urls-file test_urls.txt --output-format json --test

# Test new input folder functionality
mkdir -p test_input
echo -e "https://example.com" > test_input/urls1.txt
echo -e "https://httpbin.org/html" > test_input/urls2.urls
./adws/adw_crawl4ai_scraper.py --input-folder test_input --output-format json --test

# Test output folder functionality
./adws/adw_crawl4ai_scraper.py --url https://example.com --output-folder organized_results --test

# Test combined input and output folders
./adws/adw_crawl4ai_scraper.py --input-folder test_input --output-folder organized_results --output-format json --test

# Verify compilation
python -m py_compile adws/adw_crawl4ai_scraper.py

# Check help output includes new options
./adws/adw_crawl4ai_scraper.py --help | grep -E "(input-folder|output-folder)"
```

## Notes
- Maintain backward compatibility with existing CLI options
- Use appropriate file extensions for URL files (*.txt, *.urls, *.list)
- Implement proper error handling for folder permissions and invalid paths
- Consider adding recursive folder scanning option for future enhancement
- Ensure output folder structure is intuitive and easy to navigate
- Add proper logging for file discovery and processing steps