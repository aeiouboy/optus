# Chore: Create Scraping System Using Crawl4AI Library

## Metadata
adw_id: `976192b6`
prompt: `Create adws script that builds a scraping system using crawl4ai library`

## Chore Description
Create an AI Developer Workflow (ADW) script that implements a web scraping system using the crawl4ai library. The script should be capable of scraping websites, extracting structured data, and handling various content types while following the existing ADW patterns in the codebase.

## Relevant Files
Use these files to complete the chore:

### Existing Files
- `adws/adw_build_update_task.py` - Reference implementation pattern for ADW scripts
- `adws/adw_slash_command.py` - Command execution pattern
- `adws/adw_modules/agent.py` - Core agent execution module
- `adws/README.md` - Documentation patterns for ADWs
- `adws/adw_modules/utils.py` - Utility functions for status panels and formatting
- `.claude/commands/` - Directory for slash command templates (if needed)

### New Files

#### `adws/adw_crawl4ai_scraper.py`
The main ADW script that provides web scraping capabilities using crawl4ai library.

#### `adws/adw_modules/crawl4ai_wrapper.py`
A wrapper module around crawl4ai to provide consistent interface and error handling.

#### `requirements.txt` (or update existing)
Add crawl4ai dependency specification.

#### `adws/README.md` (update)
Add documentation for the new crawl4ai ADW script.

#### `.claude/commands/crawl4ai_scrape.md` (if needed)
Template command for scraping operations.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Research crawl4ai Library and Define Requirements
- Research crawl4ai library documentation and API patterns
- Define the core scraping functionality required (URL collection, data extraction, output formats)
- Determine error handling and retry patterns needed for web scraping
- Review existing ADW patterns to ensure consistency

### 2. Create crawl4ai Wrapper Module
- Create `adws/adw_modules/crawl4ai_wrapper.py` with:
  - Scraping configuration management (headers, delays, concurrency limits)
  - URL validation and preprocessing
  - Content extraction methods (text, links, images, structured data)
  - Error handling for network issues and anti-bot measures
  - Output formatting functions (JSON, CSV, markdown)

### 3. Create Main ADW Script Structure
- Create `adws/adw_crawl4ai_scraper.py` with the standard ADW pattern:
  - CLI interface with click for argument parsing
  - Rich console output with status panels
  - Error handling and logging
  - Support for different scraping modes (single URL, batch, sitemap-based)

### 4. Implement Scraping Functionality
- Add support for:
  - Single URL scraping with configurable output formats
  - Batch URL processing from files or lists
  - Depth-limited crawling from starting URLs
  - Content filtering and extraction rules
  - Rate limiting and respectful scraping practices

### 5. Add Output Management
- Implement structured output to `agents/` directory following existing patterns:
  - `cc_raw_output.jsonl` for streaming results
  - `cc_final_object.json` for final scraped data
  - `custom_summary_output.json` for scraping statistics
  - Support for exporting to CSV, JSON, or other formats

### 6. Update Dependencies and Documentation
- Add crawl4ai to project dependencies
- Update `adws/README.md` with usage examples and patterns
- Create comprehensive docstrings and help text
- Add error handling documentation

### 7. Create Command Template (Optional)
- Create `.claude/commands/crawl4ai_scrape.md` if slash command integration is needed
- Define template arguments and usage patterns
- Integrate with existing slash command system

## Validation Commands
Execute these commands to validate the chore is complete:

- `uv run python -m py_compile adws/adw_crawl4ai_scraper.py` - Test script compilation
- `uv run python -m py_compile adws/adw_modules/crawl4ai_wrapper.py` - Test wrapper module compilation
- `./adws/adw_crawl4ai_scraper.py --help` - Verify CLI interface works
- `./adws/adw_crawl4ai_scraper.py --url https://example.com --test` - Test basic scraping functionality
- `grep -r "crawl4ai" adws/README.md` - Verify documentation was updated
- Check that crawl4ai is added to dependencies: `grep crawl4ai requirements.txt` or pyproject.toml

## Notes
- Ensure the scraping system respects robots.txt and implements rate limiting
- Follow existing ADW patterns for CLI arguments, status panels, and output structure
- Consider adding configuration options for custom headers, user agents, and proxy support
- Make the system extensible for future scraping needs and different content types
- Test with various websites to ensure robustness against different HTML structures