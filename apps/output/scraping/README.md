# Scraping Results Management System

A comprehensive, well-organized output structure for web scraping results in the Optus project. This system provides standardized directory hierarchies, utility scripts for management, and a web dashboard for easy browsing and analysis of scraped data.

## Overview

The Scraping Results Management System creates a standardized structure for organizing web scraping results with multiple organization methods, automatic content type detection, and powerful management tools.

## Directory Structure

```
apps/output/scraping/
├── by_date/              # Results organized by date (YYYY-MM-DD/domain/job-id/)
├── by_domain/            # Results organized by domain (domain/YYYY-MM-DD/job-id/)
├── by_type/              # Results organized by content type (type/domain/YYYY-MM-DD/job-id/)
├── latest/               # Symbolic links to most recent results
├── utils/                # Management utility scripts
│   ├── result_manager.py # Core result management utilities
│   ├── organize_results.py # Script to organize existing results
│   ├── find_results.py   # Script to search and retrieve results
│   └── cleanup_old.py    # Script to clean up old results
├── config.json           # Configuration file
├── index.html            # Web dashboard for browsing results
└── README.md             # This documentation
```

## Standard Result Structure

Each result directory contains a standardized subdirectory structure:

```
job-id/
├── raw/                  # Original, unmodified scraping data
│   ├── cc_raw_output.jsonl    # Results in JSONL format
│   ├── cc_raw_output.json     # Results in JSON array format
│   └── screenshots/           # Original screenshots (if any)
├── processed/            # Cleaned, processed, and transformed data
│   └── cc_final_object.json   # Processed results with metadata
├── summary/              # High-level summaries and metadata
│   └── summary.json           # Summary statistics and information
├── assets/               # Downloaded assets and resources
│   ├── images/                # Downloaded images
│   ├── documents/             # PDFs, Word docs, etc.
│   └── media/                 # Other media files
├── metadata.json         # Result metadata
└── README.md             # Index and quick access information
```

## Features

### Multiple Organization Methods

- **By Date**: `YYYY-MM-DD/domain/job-id/` - Chronological organization
- **By Domain**: `domain/YYYY-MM-DD/job-id/` - Domain-based organization
- **By Content Type**: `type/domain/YYYY-MM-DD/job-id/` - Content categorization
- **Latest**: Symbolic links to the most recent results

### Automatic Content Type Detection

The system automatically detects content types based on:
- URL patterns (`/product`, `/article`, `/documentation`, etc.)
- Page content analysis
- Metadata examination
- Domain heuristics

Supported content types:
- `products` - E-commerce pages, product listings
- `articles` - Blog posts, news articles, stories
- `documentation` - Help docs, guides, wikis
- `api` - API endpoints and responses
- `forum` - Discussion forums and threads
- `video` - Video pages and streaming
- `general` - Default fallback

### Enhanced Metadata

Each result includes comprehensive metadata:
- Domain information
- Content type classification
- Scraping timestamp
- Word count and statistics
- Links and images count
- Success/failure status
- Extraction method used

## Usage

### Using with Crawl4AI Scraper

#### New Standard Structure (Recommended)

```bash
# Use the new standardized structure
python adws/adw_crawl4ai_scraper.py \
  --url https://example.com \
  --scraping-output apps/output/scraping

# Or use explicit flags
python adws/adw_crawl4ai_scraper.py \
  --url https://example.com \
  --use-new-structure \
  --output-folder apps/output/scraping \
  --organization-methods by_date by_domain by_type
```

#### Legacy Structure (Backward Compatible)

```bash
# Use the legacy organized structure
python adws/adw_crawl4ai_scraper.py \
  --url https://example.com \
  --output-folder apps/output/scraping \
  --organization date

# Use legacy ADW structure
python adws/adw_crawl4ai_scraper.py \
  --url https://example.com
```

### Utility Scripts

#### Organize Existing Results

```bash
# Organize existing results into the new structure
python apps/output/scraping/utils/organize_results.py \
  --search-paths ./agents ./output \
  --dry-run  # Preview changes

# Execute organization
python apps/output/scraping/utils/organize_results.py \
  --search-paths ./agents ./output \
  --methods by_date by_domain by_type \
  --move  # Move instead of copy
```

#### Search and Retrieve Results

```bash
# Interactive search mode
python apps/output/scraping/utils/find_results.py --interactive

# Command-line search
python apps/output/scraping/utils/find_results.py \
  --query "product review" \
  --domains example.com test.org \
  --content-types products articles \
  --date-from 2024-01-01 \
  --max-results 50

# Copy found results
python apps/output/scraping/utils/find_results.py \
  --domains example.com \
  --copy-to ./selected_results
```

#### Cleanup Old Results

```bash
# Show cleanup statistics
python apps/output/scraping/utils/cleanup_old.py --statistics

# Dry run cleanup
python apps/output/scraping/utils/cleanup_old.py \
  --age-days 365 \
  --dry-run

# Execute cleanup with backup
python apps/output/scraping/utils/cleanup_old.py \
  --age-days 365 \
  --backup-dir ./backup \
  --total-size-threshold 10  # Keep under 10GB
```

### Web Dashboard

Open `apps/output/scraping/index.html` in your web browser to access the interactive dashboard:

- **Search Tab**: Advanced search and filtering capabilities
- **Browse Tab**: Navigate by organization method
- **Manage Tab**: Cleanup and organization tools
- **Analytics Tab**: Statistics and insights

## Configuration

The system behavior can be customized through `config.json`:

### Key Configuration Options

```json
{
  "organization": {
    "default_method": "by_date",
    "supported_methods": ["by_date", "by_domain", "by_type"],
    "create_latest_links": true
  },
  "retention": {
    "default_retention_days": 365,
    "max_total_size_gb": 50,
    "cleanup_policies": {
      "by_age": {
        "enabled": true,
        "default_age_days": 365,
        "critical_age_days": 730
      }
    }
  },
  "content_detection": {
    "url_patterns": {
      "products": ["/product", "/item", "/shop"],
      "articles": ["/article", "/blog", "/news"],
      "documentation": ["/doc", "/guide", "/help"]
    }
  }
}
```

## API Integration

### ResultManager Class

```python
from apps.output.scraping.utils.result_manager import ResultManager

# Initialize the result manager
manager = ResultManager("/path/to/scraping/output")

# Create standard result structure
subdirs = manager.create_result_structure("/path/to/result")

# Organize results by different methods
date_path = manager.organize_by_date(result_path)
domain_path = manager.organize_by_domain(result_path, url)
type_path = manager.organize_by_type(result_path, url, content, metadata)

# Extract domain and detect content type
domain = manager.get_domain_from_url(url)
content_type = manager.detect_content_type(url, content, metadata)
```

### Enhanced Crawl4AI Wrapper

```python
from adw_modules.crawl4ai_wrapper import Crawl4AIWrapper

# Initialize with enhanced metadata
wrapper = Crawl4AIWrapper()

# Extract domain information
domain = wrapper.get_domain_from_url(url)

# Detect content type
content_type = wrapper.detect_content_type(url, content, metadata)

# Enhance result with organization metadata
result = wrapper.enhance_result_for_organization(result)
```

## File Formats

### Raw Data (`raw/`)

- **cc_raw_output.jsonl**: JSON Lines format - one JSON object per line
- **cc_raw_output.json**: JSON array format - all results in one file

Each result contains:
```json
{
  "url": "https://example.com",
  "success": true,
  "content": "Page content...",
  "markdown": "Markdown content...",
  "html": "Original HTML...",
  "links": ["https://example.com/page1", "..."],
  "images": ["https://example.com/image1.jpg", "..."],
  "metadata": {
    "title": "Page Title",
    "description": "Page description",
    "domain": "example.com",
    "content_type": "articles",
    "word_count": 1500,
    "status_code": 200
  },
  "timestamp": 1640995200.0,
  "status_code": 200
}
```

### Processed Data (`processed/`)

- **cc_final_object.json**: Consolidated results with summary and metadata

```json
{
  "type": "scraping_results",
  "adw_id": "abc12345",
  "timestamp": "2024-01-01T12:00:00Z",
  "primary_url": "https://example.com",
  "content_type": "articles",
  "summary": {
    "total_urls": 1,
    "successful_scrapes": 1,
    "failed_scrapes": 0,
    "success_rate": 100.0,
    "total_content_length": 15000,
    "total_links_found": 25,
    "total_images_found": 5
  },
  "results": [...],
  "url_count": 1,
  "successful_scrapes": 1
}
```

### Summary Data (`summary/`)

- **summary.json**: High-level summary and processing information

## Best Practices

### Directory Organization

1. **Use the new standardized structure** for all new scraping jobs
2. **Specify organization methods** based on your use case:
   - `by_date` for chronological analysis
   - `by_domain` for domain-specific research
   - `by_type` for content categorization

### Content Type Detection

1. **Provide informative URLs** - the system uses URL patterns for classification
2. **Enable metadata extraction** - titles and descriptions improve accuracy
3. **Review classifications** - verify automatic detection for critical applications

### Storage Management

1. **Set appropriate retention policies** in `config.json`
2. **Regular cleanup** - use `cleanup_old.py` to manage disk usage
3. **Backup important results** before cleanup operations

### Performance Optimization

1. **Batch processing** - use multiple URLs in single jobs
2. **Concurrent limits** - adjust based on target website tolerance
3. **Caching strategies** - leverage crawl4ai's built-in caching

## Troubleshooting

### Common Issues

#### Permission Errors
```bash
# Ensure write permissions
chmod -R 755 /Users/tachongrak/Projects/Optus/apps/output/scraping
```

#### Import Errors
```bash
# Ensure Python path includes utils directory
export PYTHONPATH="/Users/tachongrak/Projects/Optus/apps/output/scraping/utils:$PYTHONPATH"
```

#### Missing Dependencies
```bash
# Install required Python packages
pip install click rich pathlib
```

### Debug Mode

Enable verbose output for troubleshooting:

```bash
python adws/adw_crawl4ai_scraper.py \
  --url https://example.com \
  --use-new-structure \
  --verbose
```

### Log Files

Check utility script logs:
- `cleanup_old.py` generates detailed operation logs
- `organize_results.py` logs organization actions
- Scraper logs include structure creation details

## Migration Guide

### From Legacy Structure

1. **Backup existing results** before migration
2. **Use organize_results.py** to migrate existing data:
   ```bash
   python apps/output/scraping/utils/organize_results.py \
     --search-paths ./agents \
     --methods by_date by_domain by_type \
     --backup-dir ./migration_backup
   ```
3. **Update scraping scripts** to use `--scraping-output` or `--use-new-structure`
4. **Verify migration** by checking new structure and running test searches

### Integration with Existing Workflows

1. **Update CI/CD pipelines** to use new output structure
2. **Modify result processing scripts** to work with new directory layout
3. **Update monitoring** to track new structure metrics
4. **Train team members** on new management tools

## Contributing

### Adding New Content Types

1. Update `config.json` with new patterns:
   ```json
   "content_detection": {
     "url_patterns": {
       "new_type": ["/pattern1", "/pattern2"]
     },
     "content_keywords": {
       "new_type": ["keyword1", "keyword2"]
     }
   }
   ```

2. Add detection logic to `result_manager.py` and `crawl4ai_wrapper.py`

### Extending Utility Scripts

1. Follow existing patterns in utility scripts
2. Add comprehensive error handling
3. Include dry-run modes for destructive operations
4. Update this documentation

## Security Considerations

- **File Access**: Restrict access to sensitive scraped data
- **Input Validation**: Validate URLs and file paths in utility scripts
- **Backup Security**: Secure backup directories with appropriate permissions
- **Content Filtering**: Consider content filtering for inappropriate material

## Support

For issues and questions:

1. Check this documentation first
2. Review script help messages (`--help`)
3. Enable verbose logging for detailed error information
4. Check configuration file syntax

## Version History

- **v1.0**: Initial implementation with core structure and utilities
- Support for multiple organization methods
- Content type detection and metadata enhancement
- Web dashboard for result browsing
- Comprehensive management utilities

---

*This system is designed to scale with your scraping needs while maintaining organization and accessibility of results.*