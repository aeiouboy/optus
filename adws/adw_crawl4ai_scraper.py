#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "pydantic",
#   "python-dotenv",
#   "click",
#   "rich",
#   "crawl4ai",
# ]
# ///
"""
AI Developer Workflow script for web scraping using crawl4ai library.

This script provides comprehensive web scraping capabilities with:
- Single URL and batch processing
- Multiple input sources (single URL, file, or folder)
- Multiple output formats (JSON, CSV, Markdown)
- Configurable extraction strategies
- Rich console output with status panels
- Error handling and retry logic
- Structured output following ADW patterns
- Default organized output in /apps/output/ (by_url/ or by_list/)

Usage:
    # Single URL scraping (automatically saves to by_url/{domain}/)
    ./adws/adw_crawl4ai_scraper.py --url https://example.com --output-format json

    # Batch scraping from file (automatically saves to by_list/)
    ./adws/adw_crawl4ai_scraper.py --urls-file urls.txt --output-format markdown

    # Batch scraping from folder (supports *.txt, *.urls, *.list, *.csv)
    ./adws/adw_crawl4ai_scraper.py --input-folder ./url_sources --output-format json

    # Custom output folder with date-based subdirectories
    ./adws/adw_crawl4ai_scraper.py --input-folder ./url_sources --output-folder ./scraping_results

    # Custom output folder with job-ID based subdirectories
    ./adws/adw_crawl4ai_scraper.py --input-folder ./url_sources --output-folder ./scraping_results --organization job-id

    # With custom configuration
    ./adws/adw_crawl4ai_scraper.py --url https://example.com --max-concurrent 5 --delay 2.0

    # Crawl with depth
    ./adws/adw_crawl4ai_scraper.py --url https://example.com --crawl-depth 2 --max-pages 10

Input File Formats:
    - Text files: One URL per line, # comments supported
    - CSV files: First column treated as URL
    - Supported extensions: .txt, .urls, .list, .csv
    - Hidden files (.*) also supported

Output Organization (Default):
    - Single URL: /apps/output/by_url/{domain}/scraped_{timestamp}.json
    - Batch scraping: /apps/output/by_list/product_list_{timestamp}.json
    - Custom folder: --output-folder with date/job-id organization
    - Legacy: ./agents/{adw_id}/crawler/ (when using custom output folder)
"""

import os
import sys
import json
import asyncio
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import glob
import shutil
import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.rule import Rule
from rich.progress import Progress, TaskID, BarColumn, TextColumn
from rich.text import Text

# Add the adw_modules directory to the path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "adw_modules"))

from crawl4ai_wrapper import (
    Crawl4AIWrapper,
    ScrapingConfig,
    ScrapingResult,
    create_simple_config,
)
from utils import format_agent_status, format_worktree_status

# Try to import the new result manager
try:
    sys.path.insert(0, "/Users/tachongrak/Projects/Optus/apps/output/scraping/utils")
    from result_manager import ResultManager
    RESULT_MANAGER_AVAILABLE = True
except ImportError:
    RESULT_MANAGER_AVAILABLE = False

# Import the output formatter
try:
    sys.path.insert(0, os.path.dirname(__file__))
    from output_formatter import OutputFormatter, save_to_organized_structure
    OUTPUT_FORMATTER_AVAILABLE = True
except ImportError:
    OUTPUT_FORMATTER_AVAILABLE = False
    OutputFormatter = None

# Output file name constants (matching other ADWs)
OUTPUT_JSONL = "cc_raw_output.jsonl"
OUTPUT_JSON = "cc_raw_output.json"
FINAL_OBJECT_JSON = "cc_final_object.json"
SUMMARY_JSON = "custom_summary_output.json"


def print_status_panel(
    console,
    action: str,
    adw_id: str,
    phase: str = None,
    status: str = "info",
    url: str = None
):
    """Print a status panel with timestamp and context.

    Args:
        console: Rich console instance
        action: The action being performed
        adw_id: ADW ID for tracking
        phase: Optional phase name (scraping, processing, etc)
        status: Status type (info, success, error, warning)
        url: Optional URL being processed
    """
    timestamp = datetime.now().strftime("%H:%M:%S")

    # Choose color based on status
    if status == "success":
        border_style = "green"
        icon = "✅"
    elif status == "error":
        border_style = "red"
        icon = "❌"
    elif status == "warning":
        border_style = "yellow"
        icon = "⚠️"
    else:
        border_style = "cyan"
        icon = "🔄"

    # Build title with context
    title_parts = [f"[{timestamp}]", adw_id[:6]]
    if phase:
        title_parts.append(phase)
    if url and len(url) > 30:
        title_parts.append(url[:30] + "...")
    elif url:
        title_parts.append(url)
    title = " | ".join(title_parts)

    content = f"{icon} {action}"

    console.print(
        Panel(
            content,
            title=f"[bold {border_style}]{title}[/bold {border_style}]",
            border_style=border_style,
            padding=(0, 1),
        )
    )


def create_scraping_config(
    max_concurrent: int = 3,
    delay: float = 1.0,
    timeout: int = 30,
    headless: bool = True,
    verbose: bool = False,
    retry_attempts: int = 3,
    retry_delay: float = 2.0,
    respect_robots: bool = True,
    use_browser: bool = True,
    simulate_user: bool = True,
) -> ScrapingConfig:
    """Create a ScrapingConfig from CLI parameters.

    Args:
        max_concurrent: Maximum concurrent requests
        delay: Delay between requests in seconds
        timeout: Request timeout in seconds
        headless: Run browser in headless mode
        verbose: Enable verbose logging
        retry_attempts: Number of retry attempts
        retry_delay: Delay between retries in seconds
        respect_robots: Respect robots.txt
        use_browser: Use browser for scraping
        simulate_user: Simulate user behavior

    Returns:
        ScrapingConfig instance
    """
    return ScrapingConfig(
        max_concurrent=max_concurrent,
        delay_between_requests=delay,
        timeout=timeout,
        headless=headless,
        verbose=verbose,
        retry_attempts=retry_attempts,
        retry_delay=retry_delay,
        respect_robots_txt=respect_robots,
        use_browser=use_browser,
        simulate_user=simulate_user,
    )


def load_urls_from_file(file_path: str) -> List[str]:
    """Load URLs from a text file or CSV file.

    Args:
        file_path: Path to the file containing URLs

    Returns:
        List of URLs
    """
    try:
        # Validate file path exists and is readable
        if not os.path.exists(file_path):
            raise click.ClickException(f"File not found: {file_path}")

        if not os.access(file_path, os.R_OK):
            raise click.ClickException(f"File not readable: {file_path}")

        # Check file extension to determine format
        file_ext = os.path.splitext(file_path)[1].lower()

        if file_ext == '.csv':
            # Handle CSV files with headers
            import csv
            urls = []
            with open(file_path, 'r', encoding='utf-8-sig') as f:  # Handle BOM
                reader = csv.reader(f)
                # Read first row to check for headers
                try:
                    first_row = next(reader)
                    if len(first_row) >= 2:
                        # Check if first row looks like headers
                        if (first_row[0].lower() in ['product_name', 'name', 'product'] and
                            first_row[1].lower() in ['url', 'link', 'website']):
                            # CSV has headers, extract URLs from second column
                            for row in reader:
                                if len(row) >= 2 and row[1].strip():
                                    url = row[1].strip()
                                    if url and (url.startswith('http://') or url.startswith('https://')):
                                        urls.append(url)
                        elif (first_row[0].lower() in ['url', 'link', 'website']):
                            # CSV has URL in first column
                            for row in reader:
                                if len(row) >= 1 and row[0].strip():
                                    url = row[0].strip()
                                    if url and (url.startswith('http://') or url.startswith('https://')):
                                        urls.append(url)
                        else:
                            # Assume first column has URLs
                            for row in reader:
                                if len(row) >= 1 and row[0].strip():
                                    url = row[0].strip()
                                    if url and (url.startswith('http://') or url.startswith('https://')):
                                        urls.append(url)
                    else:
                        # Single column CSV, treat as URL list
                        urls.append(first_row[0].strip() if first_row[0].strip() and
                                  (first_row[0].strip().startswith('http://') or
                                   first_row[0].strip().startswith('https://')) else '')
                        for row in reader:
                            if len(row) >= 1 and row[0].strip():
                                url = row[0].strip()
                                if url and (url.startswith('http://') or url.startswith('https://')):
                                    urls.append(url)
                except StopIteration:
                    raise click.ClickException(f"CSV file is empty: {file_path}")
        else:
            # Handle plain text files (original logic)
            with open(file_path, 'r', encoding='utf-8') as f:
                urls = []
                line_num = 0
                for line in f:
                    line_num += 1
                    url = line.strip()
                    if url and not url.startswith('#'):  # Skip empty lines and comments
                        # Basic URL validation
                        if not (url.startswith('http://') or url.startswith('https://')):
                            raise click.ClickException(f"Invalid URL at line {line_num} in {file_path}: {url}")
                        urls.append(url)

        if not urls:
            raise click.ClickException(f"No valid URLs found in {file_path}")

        return urls
    except UnicodeDecodeError:
        raise click.ClickException(f"File encoding error in {file_path}. Please use UTF-8 encoding.")
    except Exception as e:
        raise click.ClickException(f"Failed to load URLs from {file_path}: {e}")


def load_urls_from_folder(folder_path: str, console: Console = None) -> List[str]:
    """Load URLs from multiple files in a directory.

    Args:
        folder_path: Path to the directory containing URL files
        console: Optional Rich console for progress display

    Returns:
        List of URLs from all matching files
    """
    try:
        # Validate folder path exists and is accessible
        if not os.path.exists(folder_path):
            raise click.ClickException(f"Directory not found: {folder_path}")

        if not os.path.isdir(folder_path):
            raise click.ClickException(f"Path is not a directory: {folder_path}")

        if not os.access(folder_path, os.R_OK):
            raise click.ClickException(f"Directory not readable: {folder_path}")

        # Supported file patterns for URL files
        patterns = ['*.txt', '*.urls', '*.list', '*.csv']

        # Find all matching files
        all_files = []
        for pattern in patterns:
            files = glob.glob(os.path.join(folder_path, pattern))
            # Also check for hidden files starting with dot
            files.extend(glob.glob(os.path.join(folder_path, f'.{pattern}')))
            all_files.extend(files)

        # Remove duplicates and sort
        unique_files = sorted(list(set(all_files)))

        if not unique_files:
            raise click.ClickException(
                f"No URL files found in {folder_path}. "
                f"Supported patterns: {', '.join(patterns)}"
            )

        all_urls = []
        processed_files = 0

        # Use rich progress if console is provided
        if console:
            with Progress(
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            ) as progress:
                task = progress.add_task(f"[cyan]Scanning {len(unique_files)} files...", total=len(unique_files))

                for file_path in unique_files:
                    progress.update(task, description=f"[cyan]Processing: {os.path.basename(file_path)}")

                    try:
                        file_urls = load_urls_from_file(file_path)
                        all_urls.extend(file_urls)
                        processed_files += 1

                        if console:
                            console.print(f"[dim]  Found {len(file_urls)} URLs in {os.path.basename(file_path)}[/dim]")

                    except click.ClickException as e:
                        console.print(f"[yellow]Warning: {str(e)} - skipping file[/yellow]")

                    progress.advance(task)
        else:
            # Fallback without progress display
            for file_path in unique_files:
                try:
                    file_urls = load_urls_from_file(file_path)
                    all_urls.extend(file_urls)
                    processed_files += 1
                except click.ClickException:
                    # Skip problematic files silently if no console
                    continue

        # Remove duplicate URLs while preserving order
        seen = set()
        unique_urls = []
        for url in all_urls:
            if url not in seen:
                seen.add(url)
                unique_urls.append(url)

        if not unique_urls:
            raise click.ClickException("No valid URLs found in any files")

        return unique_urls

    except Exception as e:
        if isinstance(e, click.ClickException):
            raise
        raise click.ClickException(f"Failed to load URLs from folder {folder_path}: {e}")


def create_output_directory_structure(base_output_folder: str, adw_id: str, organization_type: str = "date") -> str:
    """Create organized output directory structure.

    Args:
        base_output_folder: Base output folder path
        adw_id: ADW ID for tracking
        organization_type: How to organize subdirectories ("date" or "job-id")

    Returns:
        Path to the created output directory
    """
    try:
        # Validate base folder path
        base_path = Path(base_output_folder)

        # Create base directory if it doesn't exist
        base_path.mkdir(parents=True, exist_ok=True)

        # Check write permissions
        if not os.access(base_path, os.W_OK):
            raise click.ClickException(f"Base output folder is not writable: {base_output_folder}")

        # Create organized subdirectory
        if organization_type == "date":
            # Date-based organization: YYYY-MM-DD
            date_str = datetime.now().strftime("%Y-%m-%d")
            output_dir = base_path / date_str / adw_id
        else:
            # Job-ID based organization
            output_dir = base_path / adw_id

        # Create the full directory structure
        output_dir.mkdir(parents=True, exist_ok=True)

        # Create simplified subdirectories - only logs and final result
        subdirs = ['logs']
        for subdir in subdirs:
            (output_dir / subdir).mkdir(exist_ok=True)

        return str(output_dir)

    except Exception as e:
        raise click.ClickException(f"Failed to create output directory structure: {e}")


def create_new_structured_output(base_output_folder: str, adw_id: str, url: str = None,
                              organization_methods: List[str] = None) -> str:
    """Create new structured output using the result manager.

    Args:
        base_output_folder: Base output folder for scraping results
        adw_id: ADW ID for tracking
        url: Primary URL being scraped (for organization)
        organization_methods: List of organization methods to use

    Returns:
        Path to the primary organized result directory
    """
    if not RESULT_MANAGER_AVAILABLE:
        # Fallback to legacy structure
        return create_output_directory_structure(base_output_folder, adw_id, "date")

    try:
        # Initialize result manager
        manager = ResultManager(base_output_folder)

        # Default organization methods
        if organization_methods is None:
            organization_methods = ["by_date", "by_domain", "by_type"]

        # Create temporary result path first
        temp_path = os.path.join(base_output_folder, "temp_" + adw_id)
        organized_paths = manager.create_result_structure(temp_path)

        # Organize by requested methods
        final_paths = {}
        current_time = datetime.now()

        for method in organization_methods:
            if method == "by_date":
                organized_path = manager.organize_by_date(temp_path, current_time)
                final_paths[method] = organized_path
            elif method == "by_domain" and url:
                organized_path = manager.organize_by_domain(temp_path, url, current_time)
                final_paths[method] = organized_path
            elif method == "by_type" and url:
                organized_path = manager.organize_by_type(temp_path, url, None, None, current_time)
                final_paths[method] = organized_path

        # Update latest
        manager.update_latest(temp_path, adw_id)

        # Clean up temporary path if different from final path
        if os.path.exists(temp_path) and temp_path not in final_paths.values():
            shutil.rmtree(temp_path)

        # Return the primary organized path (by_date is preferred)
        return final_paths.get("by_date", list(final_paths.values())[0])

    except Exception as e:
        # Fallback to legacy structure on error
        print(f"Warning: Could not use new structured output ({e}), using legacy structure")
        return create_output_directory_structure(base_output_folder, adw_id, "date")


def save_results_to_new_structure(results: List[ScrapingResult], output_dir: str,
                                url: str = None, adw_id: str = None):
    """Save results to the new structured output format.

    Args:
        results: List of scraping results
        output_dir: Output directory path
        url: Primary URL that was scraped
        adw_id: ADW ID for tracking
    """
    if not RESULT_MANAGER_AVAILABLE:
        return

    try:
        manager = ResultManager()

        # Extract URLs from results for organization
        urls = [result.url for result in results if result.url]
        primary_url = url or (urls[0] if urls else None)

        # Detect content type if URL is available
        content_type = None
        if primary_url:
            content = results[0].content if results and results[0].content else None
            metadata = results[0].metadata if results and results[0].metadata else {}
            content_type = manager.detect_content_type(primary_url, content, metadata)

        # Save to standard subdirectories
        output_path = Path(output_dir)

        # Save raw data
        raw_dir = output_path / "raw"
        if raw_dir.exists():
            # Save JSONL format
            with open(raw_dir / "cc_raw_output.jsonl", 'w', encoding='utf-8') as f:
                for result in results:
                    f.write(json.dumps(vars(result)) + '\n')

            # Save JSON array
            with open(raw_dir / "cc_raw_output.json", 'w', encoding='utf-8') as f:
                json.dump([vars(result) for result in results], f, indent=2)

        # Save processed data
        processed_dir = output_path / "processed"
        if processed_dir.exists():
            final_object = {
                "type": "scraping_results",
                "adw_id": adw_id,
                "timestamp": datetime.now().isoformat(),
                "primary_url": primary_url,
                "content_type": content_type,
                "summary": generate_summary_stats(results),
                "results": [vars(result) for result in results],
                "url_count": len(urls),
                "successful_scrapes": sum(1 for r in results if r.success)
            }

            with open(processed_dir / "cc_final_object.json", 'w', encoding='utf-8') as f:
                json.dump(final_object, f, indent=2)

        # Save summary
        summary_dir = output_path / "summary"
        if summary_dir.exists():
            summary_data = {
                "task": "web_scraping",
                "adw_id": adw_id,
                "tool": "crawl4ai",
                "timestamp": datetime.now().isoformat(),
                "primary_url": primary_url,
                "content_type": content_type,
                "urls_scraped": len(urls),
                "summary_stats": generate_summary_stats(results),
                "output_structure": "new_standardized",
                "organization": "by_date,by_domain,by_type"
            }

            with open(summary_dir / "summary.json", 'w', encoding='utf-8') as f:
                json.dump(summary_data, f, indent=2)

        # Create index file for easy browsing
        index_content = f"""# Scraping Results Index

**ADW ID:** {adw_id or 'Unknown'}
**Timestamp:** {datetime.now().isoformat()}
**Primary URL:** {primary_url or 'Unknown'}
**Content Type:** {content_type or 'Unknown'}

## Results Summary
- Total URLs: {len(urls)}
- Successful scrapes: {sum(1 for r in results if r.success)}
- Failed scrapes: {sum(1 for r in results if not r.success)}

## Files Structure
- `raw/` - Original scraped data
- `processed/` - Processed and cleaned data
- `summary/` - Summary information and metadata
- `assets/` - Downloaded assets and resources

## Quick Access
- [Raw JSON Data](raw/cc_raw_output.json)
- [Processed Results](processed/cc_final_object.json)
- [Summary Information](summary/summary.json)
"""

        with open(output_path / "README.md", 'w', encoding='utf-8') as f:
            f.write(index_content)

    except Exception as e:
        print(f"Warning: Could not save results to new structure ({e})")


def save_results_to_file(
    results: List[ScrapingResult],
    output_path: str,
    format_type: str = "json",
    wrapper: Crawl4AIWrapper = None,
    base_output_folder: str = None,
    use_new_structure: bool = False,
    input_source_type: str = "single"  # "single", "file", "folder"
):
    """Save scraping results to a file.

    Args:
        results: List of scraping results
        output_path: Path to save the results (can be relative or absolute)
        format_type: Output format (json, csv, markdown)
        wrapper: Crawl4AIWrapper instance for formatting
        base_output_folder: Base output folder for relative paths
        use_new_structure: Use the new organized structure
        input_source_type: Type of input source ("single", "file", "folder")
    """
    try:
        # Use the new organized structure if requested
        if use_new_structure and OUTPUT_FORMATTER_AVAILABLE:
            # Determine use case based on input source
            use_case = "by_url" if input_source_type == "single" else "by_list"

            # Convert ScrapingResult objects to dict format
            results_data = [vars(result) for result in results]

            # Save to organized structure
            organized_path = save_to_organized_structure(results_data, use_case, format_type)

            # Still save to original path for backward compatibility
            # Handle output path resolution
            if not os.path.isabs(output_path) and base_output_folder:
                full_output_path = os.path.join(base_output_folder, output_path)
            else:
                full_output_path = output_path

            # Ensure directory exists
            output_dir = os.path.dirname(full_output_path)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)

            # Save the structured format to original path
            formatter = OutputFormatter()
            if format_type == "csv":
                # Use CSV formatting
                formatted_output = formatter._format_csv(
                    [formatter.process_product_page(item) for item in results_data]
                )
                with open(full_output_path, 'w', encoding='utf-8', newline='') as f:
                    f.write(formatted_output)
            else:
                # Use JSON formatting
                formatted_output = formatter.format_results(results_data, "structured")
                with open(full_output_path, 'w', encoding='utf-8') as f:
                    f.write(formatted_output)

            return organized_path  # Return the organized structure path

        # Original logic for backward compatibility
        # Handle output path resolution
        if not os.path.isabs(output_path) and base_output_folder:
            # If output_path is relative and base_output_folder is provided,
            # save in the base output folder
            full_output_path = os.path.join(base_output_folder, output_path)
        else:
            # Use absolute path or create relative path in current directory
            full_output_path = output_path

        # Ensure directory exists
        output_dir = os.path.dirname(full_output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        # Use the new output formatter for clean, structured data
        if OUTPUT_FORMATTER_AVAILABLE:
            formatter = OutputFormatter()
            formatted_output = formatter.format_results(
                [vars(result) for result in results],
                format_type if format_type != "json" else "structured"
            )
        elif wrapper:
            formatted_output = wrapper.format_results(results, format_type)
        else:
            formatted_output = json.dumps(
                [vars(result) for result in results], indent=2
            )

        # Save with proper format handling
        if format_type == "csv":
            with open(full_output_path, 'w', encoding='utf-8', newline='') as f:
                f.write(formatted_output)
        else:
            with open(full_output_path, 'w', encoding='utf-8') as f:
                f.write(formatted_output)

        return full_output_path
    except Exception as e:
        raise click.ClickException(f"Failed to save results to {output_path}: {e}")


def generate_summary_stats(results: List[ScrapingResult]) -> Dict[str, Any]:
    """Generate summary statistics from scraping results.

    Args:
        results: List of scraping results

    Returns:
        Dictionary with summary statistics
    """
    total = len(results)
    successful = sum(1 for r in results if r.success)
    failed = total - successful

    total_content_length = sum(len(r.content) if r.content else 0 for r in results if r.success)
    total_links = sum(len(r.links) for r in results if r.success)
    total_images = sum(len(r.images) for r in results if r.success)

    status_codes = {}
    for result in results:
        if result.status_code:
            status_codes[result.status_code] = status_codes.get(result.status_code, 0) + 1

    return {
        "total_urls": total,
        "successful_scrapes": successful,
        "failed_scrapes": failed,
        "success_rate": (successful / total * 100) if total > 0 else 0,
        "total_content_length": total_content_length,
        "total_links_found": total_links,
        "total_images_found": total_images,
        "status_code_distribution": status_codes,
        "processing_time": datetime.now().isoformat(),
    }


@click.command()
@click.option(
    "--url",
    help="Single URL to scrape"
)
@click.option(
    "--urls-file",
    type=click.Path(exists=True),
    help="File containing list of URLs to scrape (one per line)"
)
@click.option(
    "--input-folder",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Directory containing multiple URL files (*.txt, *.urls, *.list, *.csv)"
)
@click.option(
    "--output-format",
    type=click.Choice(["json", "csv", "markdown"]),
    default="json",
    help="Output format for results"
)
@click.option(
    "--output-file",
    help="Output file path (default: scrape_results.<format>)"
)
@click.option(
    "--output-folder",
    type=click.Path(),
    help="Base output folder for organized results (creates date/job-ID subdirectories)"
)
@click.option(
    "--organization",
    type=click.Choice(["date", "job-id"]),
    default="date",
    help="How to organize output subdirectories when using --output-folder"
)
@click.option(
    "--adw-id",
    help="ADW ID for tracking (auto-generated if not provided)"
)
@click.option(
    "--organization-methods",
    multiple=True,
    type=click.Choice(["by_date", "by_domain", "by_type"]),
    help="Organization methods for new structure (can specify multiple)"
)
@click.option(
    "--scraping-output",
    type=click.Path(),
    help="Use the standardized scraping output structure (alias for --use-new-structure --output-folder)"
)
@click.option(
    "--max-concurrent",
    type=int,
    default=3,
    help="Maximum concurrent requests"
)
@click.option(
    "--delay",
    type=float,
    default=1.0,
    help="Delay between requests in seconds"
)
@click.option(
    "--timeout",
    type=int,
    default=30,
    help="Request timeout in seconds"
)
@click.option(
    "--headless/--no-headless",
    default=True,
    help="Run browser in headless mode"
)
@click.option(
    "--verbose/--no-verbose",
    default=False,
    help="Enable verbose output"
)
@click.option(
    "--retry-attempts",
    type=int,
    default=3,
    help="Number of retry attempts for failed requests"
)
@click.option(
    "--retry-delay",
    type=float,
    default=2.0,
    help="Delay between retries in seconds"
)
@click.option(
    "--respect-robots/--no-respect-robots",
    default=True,
    help="Respect robots.txt files"
)
@click.option(
    "--use-browser/--no-browser",
    default=True,
    help="Use browser for scraping (handles JavaScript)"
)
@click.option(
    "--simulate-user/--no-simulate-user",
    default=True,
    help="Simulate user behavior to avoid detection"
)
@click.option(
    "--test",
    is_flag=True,
    help="Run in test mode with minimal output"
)
@click.option(
    "--crawl-depth",
    type=int,
    default=1,
    help="Depth to crawl from starting URLs (not implemented yet)"
)
@click.option(
    "--max-pages",
    type=int,
    help="Maximum pages to crawl (not implemented yet)"
)
def main(
    url: Optional[str],
    urls_file: Optional[str],
    input_folder: Optional[str],
    output_format: str,
    output_file: Optional[str],
    output_folder: Optional[str],
    organization: str,
    adw_id: Optional[str],
    organization_methods: List[str],
    scraping_output: Optional[str],
    max_concurrent: int,
    delay: float,
    timeout: int,
    headless: bool,
    verbose: bool,
    retry_attempts: int,
    retry_delay: float,
    respect_robots: bool,
    use_browser: bool,
    simulate_user: bool,
    test: bool,
    crawl_depth: int,
    max_pages: Optional[int],
):
    """Web scraping ADW using crawl4ai library."""

    console = Console()

    # Generate ADW ID if not provided
    if not adw_id:
        import uuid
        adw_id = str(uuid.uuid4())[:8]

    # Validate input arguments - ensure mutual exclusivity
    input_sources = [url, urls_file, input_folder]
    active_sources = [source for source in input_sources if source is not None]

    if len(active_sources) == 0:
        raise click.ClickException("One of --url, --urls-file, or --input-folder must be provided")

    if len(active_sources) > 1:
        raise click.ClickException("Cannot specify multiple input sources. Choose one of --url, --urls-file, or --input-folder")

    # Determine URLs to scrape
    if url:
        urls = [url]
        source_description = f"single URL: {url}"
    elif urls_file:
        urls = load_urls_from_file(urls_file)
        source_description = f"URLs file: {urls_file}"
    else:  # input_folder
        console.print(f"[cyan]Loading URLs from input folder: {input_folder}[/cyan]")
        urls = load_urls_from_folder(input_folder, console)
        source_description = f"input folder: {input_folder}"

    if not urls:
        raise click.ClickException("No URLs found to scrape")

    # Set default output file if not provided
    if not output_file:
        output_file = f"scrape_results.{output_format}"

    # Handle output directory structure
    using_new_structure = True  # Always use new standardized structure
    base_scraping_output = scraping_output or output_folder

    # Convert organization methods tuple to list if needed (for all cases)
    org_methods = list(organization_methods) if organization_methods else ["by_date", "by_domain", "by_type"]

    if scraping_output:
        # Use the legacy new standardized structure with custom output folder
        base_output_folder = base_scraping_output or "/Users/tachongrak/Projects/Optus/apps/output/scraping"

        # Create the new structured output
        output_dir = create_new_structured_output(
            base_output_folder, adw_id, url, org_methods
        )
        output_file_full_path = os.path.join(output_dir, output_file)
        base_output_folder = output_dir

        console.print(f"[green]✅ Using new standardized structure: {output_dir}[/green]")

    elif output_folder:
        # Create organized output directory structure (legacy)
        output_dir = create_output_directory_structure(output_folder, adw_id, organization)
        output_file_full_path = os.path.join(output_dir, output_file)
        base_output_folder = output_dir
    else:
        # Use legacy ADW structure
        output_dir = f"./agents/{adw_id}/crawler"
        os.makedirs(output_dir, exist_ok=True)
        output_file_full_path = output_file
        base_output_folder = output_dir

    # Create scraping configuration
    config = create_scraping_config(
        max_concurrent=max_concurrent,
        delay=delay,
        timeout=timeout,
        headless=headless,
        verbose=verbose,
        retry_attempts=retry_attempts,
        retry_delay=retry_delay,
        respect_robots=respect_robots,
        use_browser=use_browser,
        simulate_user=simulate_user,
    )

    # Display configuration
    config_table = Table(show_header=False, box=None, padding=(0, 1))
    config_table.add_column(style="bold cyan")
    config_table.add_column()

    config_table.add_row("ADW ID", adw_id)
    config_table.add_row("URLs to scrape", str(len(urls)))
    config_table.add_row("Input source", source_description)
    config_table.add_row("Output format", output_format)
    config_table.add_row("Output file", output_file_full_path)

    if using_new_structure:
        config_table.add_row("Output structure", "New standardized")
        config_table.add_row("Base output folder", base_output_folder)
        if org_methods:
            config_table.add_row("Organization methods", ", ".join(org_methods))
    elif output_folder:
        config_table.add_row("Base output folder", output_folder)
        config_table.add_row("Organization", organization)

    config_table.add_row("Max concurrent", str(max_concurrent))
    config_table.add_row("Delay (seconds)", str(delay))
    config_table.add_row("Timeout (seconds)", str(timeout))
    config_table.add_row("Use browser", str(use_browser))
    config_table.add_row("Headless", str(headless))

    console.print(
        Panel(
            config_table,
            title=f"[bold blue]🕷️  Crawl4AI Scraper Configuration[/bold blue]",
            border_style="blue",
        )
    )
    console.print()

    # Prepare for scraping
    results = []
    summary_stats = {}
    error_message = None

    try:
        # Initialize the wrapper
        print_status_panel(console, "Initializing crawl4ai wrapper", adw_id, "init")

        wrapper = Crawl4AIWrapper(config)

        async def run_scraping():
            """Run the scraping process."""
            async with wrapper:
                if len(urls) == 1:
                    # Single URL scraping
                    print_status_panel(console, f"Scraping {urls[0]}", adw_id, "scraping", urls[0])
                    result = await wrapper.scrape_url(urls[0])
                    return [result]
                else:
                    # Batch scraping with progress indicator
                    console.print(f"[bold cyan]Scraping {len(urls)} URLs...[/bold cyan]")
                    console.print()

                    with Progress() as progress:
                        task_id = progress.add_task("Scraping URLs...", total=len(urls))

                        results = []

                        # Process URLs in batches
                        batch_size = max_concurrent
                        for i in range(0, len(urls), batch_size):
                            batch = urls[i:i + batch_size]

                            # Scrape batch
                            batch_results = await wrapper.scrape_urls(batch)
                            results.extend(batch_results)

                            # Update progress
                            progress.update(task_id, completed=min(i + batch_size, len(urls)))

                            # Show status for each URL in batch
                            for url, result in zip(batch, batch_results):
                                if result.success:
                                    print_status_panel(
                                        console,
                                        f"Successfully scraped {len(result.content)} characters",
                                        adw_id,
                                        "scraping",
                                        url,
                                        "success"
                                    )
                                else:
                                    print_status_panel(
                                        console,
                                        f"Failed to scrape: {result.error_message}",
                                        adw_id,
                                        "scraping",
                                        url,
                                        "error"
                                    )

                    return results

        # Run the scraping
        print_status_panel(console, "Starting scraping process", adw_id, "scraping")
        results = asyncio.run(run_scraping())

        print_status_panel(console, "Completed scraping process", adw_id, "scraping", "success")

        # Generate summary statistics
        summary_stats = generate_summary_stats(results)

        # Display results summary
        console.print()
        console.print(Rule("[bold yellow]Scraping Results Summary[/bold yellow]"))
        console.print()

        summary_table = Table()
        summary_table.add_column("Metric", style="bold cyan")
        summary_table.add_column("Value", style="bold")

        summary_table.add_row("Total URLs", str(summary_stats["total_urls"]))
        summary_table.add_row("Successful", str(summary_stats["successful_scrapes"]))
        summary_table.add_row("Failed", str(summary_stats["failed_scrapes"]))
        summary_table.add_row("Success Rate", f"{summary_stats['success_rate']:.1f}%")
        summary_table.add_row("Total Content Length", f"{summary_stats['total_content_length']:,} chars")

        if summary_stats["total_links_found"] > 0:
            summary_table.add_row("Total Links Found", str(summary_stats["total_links_found"]))

        if summary_stats["total_images_found"] > 0:
            summary_table.add_row("Total Images Found", str(summary_stats["total_images_found"]))

        console.print(summary_table)

        # Determine input source type for organized structure
        if url:
            input_source_type = "single"  # Single URL -> by_url
        elif urls_file:
            input_source_type = "file"    # URLs file -> by_list
        elif input_folder:
            input_source_type = "folder"  # Input folder -> by_list
        else:
            input_source_type = "single"  # Default fallback

        # Save results to file (always use new organized structure)
        print_status_panel(console, f"Saving results to {output_file_full_path}", adw_id, "output")
        saved_file_path = save_results_to_file(
            results,
            output_file,
            output_format,
            wrapper,
            base_output_folder,
            True,  # Always use new organized structure
            input_source_type
        )

        # Show new organized structure info
        if saved_file_path != output_file_full_path:
            console.print(f"[bold cyan]📁 Also saved to organized structure:[/bold cyan] {saved_file_path}")
            console.print(f"[dim]   Use case: {input_source_type} -> {'by_url' if input_source_type == 'single' else 'by_list'}[/dim]")

        # Save structured outputs following ADW patterns
        if scraping_output:
            # Use the legacy new standardized structure
            save_results_to_new_structure(results, base_output_folder, url, adw_id)

            # Set paths for the new structure
            jsonl_path = os.path.join(base_output_folder, "raw", OUTPUT_JSONL)
            json_path = os.path.join(base_output_folder, "raw", OUTPUT_JSON)
            final_path = os.path.join(base_output_folder, "processed", FINAL_OBJECT_JSON)
            summary_path = os.path.join(base_output_folder, "summary", SUMMARY_JSON)
        elif output_folder:
            # Use organized structure: raw/, processed/, logs/, assets/
            jsonl_path = os.path.join(base_output_folder, "raw", OUTPUT_JSONL)
            json_path = os.path.join(base_output_folder, "raw", OUTPUT_JSON)
            final_path = os.path.join(base_output_folder, "processed", FINAL_OBJECT_JSON)
            summary_path = os.path.join(base_output_folder, "logs", SUMMARY_JSON)
        else:
            # Use legacy structure
            jsonl_path = os.path.join(output_dir, OUTPUT_JSONL)
            json_path = os.path.join(output_dir, OUTPUT_JSON)
            final_path = os.path.join(output_dir, FINAL_OBJECT_JSON)
            summary_path = os.path.join(output_dir, SUMMARY_JSON)

        # Save raw JSONL
        os.makedirs(os.path.dirname(jsonl_path), exist_ok=True)
        with open(jsonl_path, 'w', encoding='utf-8') as f:
            for result in results:
                f.write(json.dumps(vars(result)) + '\n')

        # Save JSON array
        os.makedirs(os.path.dirname(json_path), exist_ok=True)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump([vars(result) for result in results], f, indent=2)

        # Save final object (last result or summary)
        os.makedirs(os.path.dirname(final_path), exist_ok=True)
        final_object = {
            "type": "scraping_results",
            "adw_id": adw_id,
            "timestamp": datetime.now().isoformat(),
            "summary": summary_stats,
            "results": [vars(result) for result in results],
            "input_source": source_description,
            "output_organization": "new_organized_structure" if saved_file_path != output_file_full_path else (organization if output_folder else "legacy"),
        }

        with open(final_path, 'w', encoding='utf-8') as f:
            json.dump(final_object, f, indent=2)

        # Save summary
        os.makedirs(os.path.dirname(summary_path), exist_ok=True)
        summary_data = {
            "task": "web_scraping",
            "adw_id": adw_id,
            "tool": "crawl4ai",
            "config": vars(config),
            "urls_scraped": len(urls),
            "input_source": source_description,
            "summary_stats": summary_stats,
            "output_file": saved_file_path,
            "output_structure": {
                "base_folder": base_scraping_output if base_scraping_output else output_dir,
                "organization": "new_organized_structure" if saved_file_path != output_file_full_path else (organization if output_folder else "legacy"),
                "organization_methods": list(organization_methods) if saved_file_path != output_file_full_path else None,
                "structured_outputs": {
                    "raw_jsonl": jsonl_path,
                    "raw_json": json_path,
                    "final_object": final_path,
                    "summary": summary_path,
                }
            },
            "success": summary_stats["successful_scrapes"] > 0,
        }

        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, indent=2)

        print_status_panel(console, f"Results saved to {saved_file_path}", adw_id, "output", "success")

        # Display output directory info
        console.print()
        if saved_file_path != output_file_full_path:
            # Display new organized structure
            output_info = (
                f"[bold cyan]Output Structure:[/bold cyan] New Organized Structure\n"
                f"[bold cyan]Base Directory:[/bold cyan] /Users/tachongrak/Projects/Optus/apps/output\n"
                f"[bold cyan]Organization:[/bold cyan] {'by_url' if input_source_type == 'single' else 'by_list'}\n"
                f"[bold cyan]Organized Path:[/bold cyan] {saved_file_path}\n"
                f"[bold cyan]Original Path:[/bold cyan] {output_file_full_path}\n"
                f"[bold cyan]Success Rate:[/bold cyan] {summary_stats['success_rate']:.1f}%"
            )
        elif output_folder:
            # Display organized output structure
            output_info = (
                f"[bold cyan]Base Output Folder:[/bold cyan] {output_folder}\n"
                f"[bold cyan]Organization:[/bold cyan] {organization}\n"
                f"[bold cyan]Job Directory:[/bold cyan] {base_output_folder}\n"
                f"[bold cyan]Results File:[/bold cyan] {saved_file_path}\n"
                f"[bold cyan]Success Rate:[/bold cyan] {summary_stats['success_rate']:.1f}%"
            )
        else:
            # Display legacy structure
            output_info = (
                f"[bold cyan]ADW Output Directory:[/bold cyan] {output_dir}\n"
                f"[bold cyan]Results File:[/bold cyan] {saved_file_path}\n"
                f"[bold cyan]Success Rate:[/bold cyan] {summary_stats['success_rate']:.1f}%"
            )

        console.print(
            Panel(
                output_info,
                title="[bold green]✅ Scraping Complete[/bold green]",
                border_style="green",
            )
        )

        # Exit with appropriate code
        if summary_stats["successful_scrapes"] == 0:
            sys.exit(1)  # All scrapes failed
        elif summary_stats["failed_scrapes"] > 0:
            sys.exit(2)  # Some scrapes failed
        else:
            sys.exit(0)  # All scrapes succeeded

    except KeyboardInterrupt:
        print_status_panel(console, "Scraping interrupted by user", adw_id, "scraping", "warning")
        sys.exit(130)

    except Exception as e:
        error_message = str(e)
        print_status_panel(console, f"Scraping failed: {error_message}", adw_id, "scraping", "error")

        # Save error summary
        try:
            summary_path = os.path.join(output_dir, SUMMARY_JSON)
            with open(summary_path, 'w') as f:
                json.dump({
                    "task": "web_scraping",
                    "adw_id": adw_id,
                    "tool": "crawl4ai",
                    "success": False,
                    "error_message": error_message,
                    "urls_attempted": len(urls),
                    "urls_completed": len(results),
                }, f, indent=2)
        except:
            pass

        sys.exit(1)


if __name__ == "__main__":
    main()