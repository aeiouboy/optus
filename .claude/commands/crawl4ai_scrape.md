# Crawl4AI Web Scraping

Execute web scraping tasks using the crawl4ai library through the ADW scraper script.

## Variables
urls: $1
output_format: $2
options: $3

## Instructions

- If no URLs are provided, stop and ask the user to specify at least one URL
- Execute the crawl4ai scraper ADW with the provided parameters
- Support both single URLs and multiple URLs from files
- Provide appropriate output format and options

## URL Handling

### Single URL
- Use the `--url` parameter for single URL scraping
- Example: `--url https://example.com`

### Multiple URLs
- If multiple URLs are provided (comma-separated), create a temporary file
- Use the `--urls-file` parameter for batch processing
- Example URL list format: `https://example.com,https://test.com,https://demo.com`

### URL Files
- If the provided parameter is an existing file path, use it directly
- File should contain one URL per line
- Skip empty lines and comments (lines starting with #)

## Output Formats

Support the following output formats:
- `json`: Structured JSON with all scraping data
- `csv`: Tabular CSV format with key metrics
- `markdown`: Human-readable markdown format

Default to `json` if no format is specified.

## Common Options

Parse and apply these common options from the $3 parameter:
- `--max-concurrent N`: Maximum concurrent requests
- `--delay N`: Delay between requests in seconds
- `--timeout N`: Request timeout in seconds
- `--test`: Run in test mode
- `--verbose`: Enable verbose output
- `--headless`/`--no-headless`: Browser headless mode
- `--retry-attempts N`: Number of retry attempts

## Command Construction

Build the command based on the input parameters:

```bash
# Single URL
./adws/adw_crawl4ai_scraper.py --url {url} --output-format {format} {options}

# Multiple URLs from file
./adws/adw_crawl4ai_scraper.py --urls-file {temp_file} --output-format {format} {options}
```

## Error Handling

- Validate URLs before processing
- Check if crawl4ai dependencies are available
- Provide clear error messages for common issues
- Suggest installation of required dependencies if missing

## Output

- Return the command that was executed
- Show the output file location
- Display key scraping statistics
- Report any errors or warnings encountered

## Execution

Execute the scraping operation and return the results to the user.