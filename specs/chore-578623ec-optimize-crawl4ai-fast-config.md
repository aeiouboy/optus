# Chore: Optimize crawl4ai wrapper with fast configuration settings

## Metadata
adw_id: `578623ec`
prompt: `Optimize crawl4ai wrapper with fast configuration settings while preserving image extraction. Apply these optimizations to adws/adw_modules/crawl4ai_wrapper.py:

1. Import CrawlerRunConfig and CacheMode from crawl4ai at the top
2. Create a new method create_run_config() that returns CrawlerRunConfig with:
   - cache_mode=CacheMode.BYPASS for fresh data (configurable)
   - stream=True for immediate processing
   - only_text=False to preserve image extraction capability
   - wait_for=None for faster loading when not needed
3. Update scrape_url() method to use the new CrawlerRunConfig when calling crawler.arun()
4. Update scrape_urls() method to use crawler.arun_many() instead of individual arun() calls for better batch concurrency handling
5. Make the optimization configurable via ScrapingConfig dataclass with new fields:
   - use_cache: bool = False (controls CacheMode.BYPASS vs ENABLED)
   - stream_results: bool = True (enables streaming for faster processing)

Reference implementation:
python
# Import at top
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

# Create run config method
def create_run_config(self) -> CrawlerRunConfig:
    return CrawlerRunConfig(
        cache_mode=CacheMode.ENABLED if self.config.use_cache else CacheMode.BYPASS,
        stream=self.config.stream_results,
        only_text=False,  # Keep images
        wait_for=None
    )

# Use arun_many for batch processing
async with AsyncWebCrawler(config=browser_cfg) as crawler:
    results = await crawler.arun_many(urls, config=run_cfg)
    async for result in results:
        # Process each result as it arrives


Ensure backward compatibility and update both adw_crawl4ai_scraper.py and adw_ecommerce_product_scraper.py to support the new config options.`

## Chore Description
This chore optimizes the crawl4ai wrapper module (`adws/adw_modules/crawl4ai_wrapper.py`) to use crawl4ai's fast configuration settings for improved scraping performance while preserving image extraction capabilities.

The key optimizations include:
1. **Import CrawlerRunConfig and CacheMode** - These crawl4ai classes enable fine-grained control over crawler behavior
2. **Create `create_run_config()` method** - A new method that generates CrawlerRunConfig instances with optimal settings
3. **Update `scrape_url()` method** - Use the new CrawlerRunConfig when calling `crawler.arun()` for single URL scraping
4. **Update `scrape_urls()` method** - Use `crawler.arun_many()` instead of individual `arun()` calls for better batch processing with streaming support
5. **Add configurable options to ScrapingConfig** - New fields `use_cache` and `stream_results` to control optimization behavior

The changes must maintain backward compatibility with existing scrapers (`adw_crawl4ai_scraper.py` and `adw_ecommerce_product_scraper.py`).

## Relevant Files
Use these files to complete the chore:

- **`adws/adw_modules/crawl4ai_wrapper.py`** - Primary file to modify. Contains `Crawl4AIWrapper` class with `ScrapingConfig` dataclass, `scrape_url()`, and `scrape_urls()` methods that need to be updated with fast configuration settings.

- **`adws/adw_crawl4ai_scraper.py`** - Consumer of crawl4ai_wrapper. Uses `ScrapingConfig`, `Crawl4AIWrapper`, and calls `scrape_url()` and `scrape_urls()` methods. Needs to be updated to support and optionally expose new config options via CLI.

- **`adws/adw_ecommerce_product_scraper.py`** - Consumer of crawl4ai_wrapper. Uses `ScrapingConfig` via `create_simple_config()` and `Crawl4AIWrapper`. Needs to be updated to support new config options.

### New Files
None required - all changes are modifications to existing files.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Update imports in crawl4ai_wrapper.py
- Add `CrawlerRunConfig` and `CacheMode` to the imports from crawl4ai
- Add these to the try/except block for graceful handling if not available
- Set `CrawlerRunConfig = None` and `CacheMode = None` in the except block

### 2. Add new configuration fields to ScrapingConfig dataclass
- Add `use_cache: bool = False` field (controls CacheMode.BYPASS vs ENABLED)
- Add `stream_results: bool = True` field (enables streaming for faster processing)
- Ensure default values maintain backward compatibility (False for cache means BYPASS which is fresh data)

### 3. Create create_run_config() method in Crawl4AIWrapper class
- Add new method `create_run_config(self, wait_for: Optional[str] = None) -> CrawlerRunConfig`
- Configure cache_mode based on `self.config.use_cache`
- Set `stream=self.config.stream_results`
- Set `only_text=False` to preserve image extraction
- Accept optional `wait_for` parameter to allow caller override
- Handle case where CrawlerRunConfig is not available (return None)

### 4. Update scrape_url() method to use CrawlerRunConfig
- Create run config using `create_run_config()` at the start of the method
- Pass the run_config to `crawler.arun()` via the `config` parameter
- Keep existing wait_for and css_selector parameters as optional overrides
- Maintain backward compatibility by checking if CrawlerRunConfig is available

### 5. Update scrape_urls() method to use arun_many() with streaming
- Replace the existing batch processing logic with `crawler.arun_many()`
- Create run config using `create_run_config()` for the batch
- Use async iteration over results for streaming processing
- Process each result as it arrives instead of waiting for all
- Maintain error handling and result collection
- Fall back to original logic if arun_many is not available

### 6. Update adw_crawl4ai_scraper.py to support new config options
- Add `--use-cache/--no-cache` CLI option (default: no-cache for fresh data)
- Add `--stream/--no-stream` CLI option (default: stream enabled)
- Update `create_scraping_config()` function to accept and pass through new parameters
- Pass new config options to ScrapingConfig when creating it

### 7. Update adw_ecommerce_product_scraper.py to support new config options
- Add same CLI options as adw_crawl4ai_scraper.py for consistency
- Update `create_simple_config()` call to pass new parameters if provided
- Maintain backward compatibility with existing usage

### 8. Validate the implementation
- Run Python syntax check on all modified files
- Verify imports are correct by importing the modules
- Test with a simple scraping command to ensure functionality works

## Validation Commands
Execute these commands to validate the chore is complete:

- `uv run python -m py_compile adws/adw_modules/crawl4ai_wrapper.py` - Verify crawl4ai_wrapper.py compiles without syntax errors
- `uv run python -m py_compile adws/adw_crawl4ai_scraper.py` - Verify adw_crawl4ai_scraper.py compiles without syntax errors
- `uv run python -m py_compile adws/adw_ecommerce_product_scraper.py` - Verify adw_ecommerce_product_scraper.py compiles without syntax errors
- `uv run python -c "from adws.adw_modules.crawl4ai_wrapper import ScrapingConfig; c = ScrapingConfig(); print(f'use_cache={c.use_cache}, stream_results={c.stream_results}')"` - Verify new ScrapingConfig fields exist and have correct defaults
- `uv run python -c "from adws.adw_modules.crawl4ai_wrapper import Crawl4AIWrapper, ScrapingConfig; w = Crawl4AIWrapper(ScrapingConfig()); print('create_run_config' in dir(w))"` - Verify create_run_config method exists

## Notes
- The `CrawlerRunConfig` and `CacheMode` imports are wrapped in try/except to handle cases where the crawl4ai library version doesn't support these classes
- Default `use_cache=False` means fresh data is fetched by default (BYPASS mode), which is the safer default for scraping
- Default `stream_results=True` enables streaming by default for better performance
- The `only_text=False` setting is hardcoded to always preserve image extraction capability as per requirements
- The `arun_many()` method provides better concurrency handling than manual batching with individual `arun()` calls
- Backward compatibility is critical - existing scripts should work without modification unless they want to use new features
