#!/usr/bin/env python3
"""
Script to search and retrieve scraping results from the organized structure.

This script provides powerful search capabilities across all organization methods
with filtering options by date, domain, content type, and keywords.
"""

import os
import sys
import json
import argparse
import re
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple, Set
from collections import defaultdict

# Add the current directory to the path to import result_manager
sys.path.insert(0, os.path.dirname(__file__))

try:
    from result_manager import ResultManager
except ImportError:
    print("Error: Could not import result_manager. Make sure it's in the same directory.")
    sys.exit(1)


class ResultSearcher:
    """Searches and retrieves scraping results from the organized structure."""

    def __init__(self, base_dir: str = "/Users/tachongrak/Projects/Optus/apps/output/scraping"):
        """Initialize the searcher.

        Args:
            base_dir: Base directory for scraping outputs
        """
        self.base_dir = Path(base_dir)
        self.manager = ResultManager(str(base_dir))

    def search_results(
        self,
        query: str = None,
        domains: List[str] = None,
        content_types: List[str] = None,
        date_from: datetime = None,
        date_to: datetime = None,
        organization_methods: List[str] = None,
        max_results: int = None,
        include_content: bool = False
    ) -> List[Dict[str, Any]]:
        """Search for results matching the given criteria.

        Args:
            query: Text query to search for in content
            domains: List of domains to filter by
            content_types: List of content types to filter by
            date_from: Start date for filtering
            date_to: End date for filtering
            organization_methods: Organization methods to search in
            max_results: Maximum number of results to return
            include_content: Whether to include full content in results

        Returns:
            List of matching results
        """
        if organization_methods is None:
            organization_methods = ['by_date', 'by_domain', 'by_type', 'latest']

        all_results = []

        for method in organization_methods:
            method_results = self._search_in_organization_method(
                method, query, domains, content_types, date_from, date_to, include_content
            )
            all_results.extend(method_results)

        # Remove duplicates (same result may appear in multiple methods)
        unique_results = self._deduplicate_results(all_results)

        # Sort by relevance (newer, more matches)
        sorted_results = self._sort_results_by_relevance(unique_results, query, domains, content_types)

        # Limit results if requested
        if max_results:
            sorted_results = sorted_results[:max_results]

        return sorted_results

    def _search_in_organization_method(
        self,
        method: str,
        query: str = None,
        domains: List[str] = None,
        content_types: List[str] = None,
        date_from: datetime = None,
        date_to: datetime = None,
        include_content: bool = False
    ) -> List[Dict[str, Any]]:
        """Search within a specific organization method.

        Args:
            method: Organization method ('by_date', 'by_domain', 'by_type', 'latest')
            query: Text query to search for
            domains: Domains to filter by
            content_types: Content types to filter by
            date_from: Start date
            date_to: End date
            include_content: Whether to include full content

        Returns:
            List of matching results from this method
        """
        method_dir = self.base_dir / method
        if not method_dir.exists():
            return []

        results = []

        # Walk through the directory structure
        for root, dirs, files in os.walk(method_dir):
            root_path = Path(root)

            # Skip if this looks like a subdirectory of a result (raw/, processed/, etc.)
            if any(part in root_path.parts for part in ['raw', 'processed', 'summary', 'assets']):
                continue

            # Check for result indicators
            if self._is_result_directory(root_path):
                result_info = self._analyze_result_directory(root_path, include_content, query)
                if result_info and self._matches_filters(
                    result_info, domains, content_types, date_from, date_to, query
                ):
                    results.append(result_info)

        return results

    def _is_result_directory(self, dir_path: Path) -> bool:
        """Check if a directory contains scraping results.

        Args:
            dir_path: Directory path to check

        Returns:
            True if this is a result directory
        """
        # Check for standard subdirectories
        subdirs = ['raw', 'processed', 'summary', 'assets']
        has_subdirs = any((dir_path / d).exists() for d in subdirs)

        # Check for result files
        result_files = [
            "cc_raw_output.json",
            "cc_raw_output.jsonl",
            "scrape_results.json",
            "metadata.json"
        ]
        has_files = any((dir_path / f).exists() for f in result_files)

        return has_subdirs or has_files

    def _analyze_result_directory(self, dir_path: Path, include_content: bool = False, query: str = None) -> Optional[Dict[str, Any]]:
        """Analyze a result directory and extract information.

        Args:
            dir_path: Directory path to analyze
            include_content: Whether to include full content
            query: Search query for highlighting matches

        Returns:
            Result information or None
        """
        try:
            result_info = {
                "path": str(dir_path),
                "name": dir_path.name,
                "relative_path": str(dir_path.relative_to(self.base_dir)),
                "size_bytes": self._get_directory_size(dir_path),
                "created": self._get_directory_created_time(dir_path),
                "modified": self._get_directory_modified_time(dir_path),
                "domains": [],
                "content_types": [],
                "urls": [],
                "file_count": 0,
                "metadata": {}
            }

            # Extract metadata
            metadata = self._extract_metadata(dir_path)
            result_info["metadata"] = metadata

            # Extract URLs and domains
            urls = metadata.get('urls', [])
            if not urls:
                urls = self._extract_urls_from_files(dir_path)
            result_info["urls"] = urls[:10]  # Limit to first 10 URLs

            # Extract domains from URLs
            domains = set()
            for url in urls:
                try:
                    domain = self.manager.get_domain_from_url(url)
                    domains.add(domain)
                except:
                    continue
            result_info["domains"] = list(domains)

            # Detect content type
            if urls:
                primary_url = urls[0]
                content = self._extract_content_from_files(dir_path) if include_content else None
                content_type = self.manager.detect_content_type(primary_url, content, metadata)
                result_info["content_types"] = [content_type]

            # Count files
            result_info["file_count"] = len(list(dir_path.rglob("*")))

            # Include content if requested
            if include_content:
                content = self._extract_content_from_files(dir_path)
                if content and query:
                    # Highlight query matches
                    highlighted_content = self._highlight_matches(content, query)
                    result_info["content_preview"] = highlighted_content[:1000] + "..." if len(highlighted_content) > 1000 else highlighted_content
                elif content:
                    result_info["content_preview"] = content[:1000] + "..." if len(content) > 1000 else content

            return result_info

        except Exception as e:
            print(f"Error analyzing directory {dir_path}: {e}")
            return None

    def _extract_metadata(self, dir_path: Path) -> Dict[str, Any]:
        """Extract metadata from result files.

        Args:
            dir_path: Directory to extract metadata from

        Returns:
            Extracted metadata
        """
        metadata = {}

        # Try various metadata files
        metadata_files = [
            "metadata.json",
            "custom_summary_output.json",
            "cc_final_object.json"
        ]

        for metadata_file in metadata_files:
            metadata_path = dir_path / metadata_file
            if metadata_path.exists():
                try:
                    with open(metadata_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if isinstance(data, dict):
                            metadata.update(data)
                            break
                except Exception:
                    continue

        return metadata

    def _extract_urls_from_files(self, dir_path: Path) -> List[str]:
        """Extract URLs from result files.

        Args:
            dir_path: Directory to search for URLs

        Returns:
            List of found URLs
        """
        urls = []

        # Search in common output files
        output_files = [
            "cc_raw_output.json",
            "cc_raw_output.jsonl",
            "scrape_results.json"
        ]

        for output_file in output_files:
            file_path = dir_path / output_file
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        if output_file.endswith('.jsonl'):
                            # JSONL format
                            for line in f:
                                if line.strip():
                                    try:
                                        data = json.loads(line)
                                        if isinstance(data, dict) and 'url' in data and data['url']:
                                            urls.append(data['url'])
                                    except:
                                        continue
                        else:
                            # JSON format
                            data = json.load(f)
                            if isinstance(data, list):
                                for item in data:
                                    if isinstance(item, dict) and 'url' in item and item['url']:
                                        urls.append(item['url'])
                            elif isinstance(data, dict):
                                if 'results' in data and isinstance(data['results'], list):
                                    for item in data['results']:
                                        if isinstance(item, dict) and 'url' in item and item['url']:
                                            urls.append(item['url'])
                                elif 'url' in data and data['url']:
                                    urls.append(data['url'])
                except Exception:
                    continue

        return list(set(urls))  # Remove duplicates

    def _extract_content_from_files(self, dir_path: Path) -> Optional[str]:
        """Extract content from result files.

        Args:
            dir_path: Directory to extract content from

        Returns:
            Extracted content or None
        """
        # Look for content in processed files first
        content_files = [
            "raw/cc_raw_output.json",
            "processed/scrape_results.json",
            "cc_raw_output.json"
        ]

        for content_file in content_files:
            file_path = dir_path / content_file
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                        # Extract content from various structures
                        if isinstance(data, list) and data:
                            first_item = data[0]
                            if isinstance(first_item, dict):
                                content = first_item.get('content') or first_item.get('markdown')
                                if content and len(content.strip()) > 100:
                                    return content
                        elif isinstance(data, dict):
                            if 'results' in data and isinstance(data['results'], list) and data['results']:
                                first_result = data['results'][0]
                                if isinstance(first_result, dict):
                                    content = first_result.get('content') or first_result.get('markdown')
                                    if content and len(content.strip()) > 100:
                                        return content
                            else:
                                content = data.get('content') or data.get('markdown')
                                if content and len(content.strip()) > 100:
                                    return content
                except Exception:
                    continue

        return None

    def _highlight_matches(self, text: str, query: str) -> str:
        """Highlight query matches in text.

        Args:
            text: Text to highlight
            query: Query string

        Returns:
            Text with highlighted matches
        """
        if not query:
            return text

        # Simple case-insensitive highlighting
        pattern = re.compile(re.escape(query), re.IGNORECASE)
        return pattern.sub(f"**{query.upper()}**", text)

    def _matches_filters(
        self,
        result_info: Dict[str, Any],
        domains: List[str] = None,
        content_types: List[str] = None,
        date_from: datetime = None,
        date_to: datetime = None,
        query: str = None
    ) -> bool:
        """Check if a result matches the given filters.

        Args:
            result_info: Result information
            domains: Domains to filter by
            content_types: Content types to filter by
            date_from: Start date
            date_to: End date
            query: Text query

        Returns:
            True if result matches all filters
        """
        # Domain filter
        if domains:
            result_domains = set(domain.lower() for domain in result_info["domains"])
            filter_domains = set(domain.lower() for domain in domains)
            if not result_domains.intersection(filter_domains):
                return False

        # Content type filter
        if content_types:
            result_types = set(t.lower() for t in result_info["content_types"])
            filter_types = set(t.lower() for t in content_types)
            if not result_types.intersection(filter_types):
                return False

        # Date filter
        if date_from and result_info["created"] < date_from:
            return False
        if date_to and result_info["created"] > date_to:
            return False

        # Text query filter
        if query:
            content = result_info.get("content_preview", "")
            metadata_text = json.dumps(result_info.get("metadata", {})).lower()
            urls_text = " ".join(result_info["urls"]).lower()

            query_lower = query.lower()
            if (query_lower not in content.lower() and
                query_lower not in metadata_text and
                query_lower not in urls_text):
                return False

        return True

    def _deduplicate_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate results based on path or content.

        Args:
            results: List of results to deduplicate

        Returns:
            Deduplicated results
        """
        seen_paths = set()
        seen_names = set()
        unique_results = []

        for result in results:
            path = result["path"]
            name = result["name"]

            # Check if we've seen this path or a directory with the same name
            if path not in seen_paths and name not in seen_names:
                seen_paths.add(path)
                seen_names.add(name)
                unique_results.append(result)

        return unique_results

    def _sort_results_by_relevance(
        self,
        results: List[Dict[str, Any]],
        query: str = None,
        domains: List[str] = None,
        content_types: List[str] = None
    ) -> List[Dict[str, Any]]:
        """Sort results by relevance (newer, matching filters, etc.).

        Args:
            results: Results to sort
            query: Search query
            domains: Filtered domains
            content_types: Filtered content types

        Returns:
            Sorted results
        """
        def relevance_score(result):
            score = 0

            # Prefer newer results
            days_old = (datetime.now() - result["created"]).days
            score += max(0, 100 - days_old)  # Newer = higher score

            # Prefer results matching explicit filters
            if domains and any(domain in result["domains"] for domain in domains):
                score += 50

            if content_types and any(ct in result["content_types"] for ct in content_types):
                score += 30

            # Prefer larger results (likely more content)
            if result["size_bytes"] > 0:
                score += min(20, result["size_bytes"] / 100000)  # Cap at 20 points

            # Prefer results with more URLs
            score += min(10, len(result["urls"]))

            return score

        return sorted(results, key=relevance_score, reverse=True)

    def _get_directory_size(self, dir_path: Path) -> int:
        """Get total size of a directory in bytes.

        Args:
            dir_path: Directory path

        Returns:
            Size in bytes
        """
        total_size = 0
        try:
            for item in dir_path.rglob("*"):
                if item.is_file():
                    total_size += item.stat().st_size
        except Exception:
            pass
        return total_size

    def _get_directory_created_time(self, dir_path: Path) -> datetime:
        """Get the creation time of a directory.

        Args:
            dir_path: Directory path

        Returns:
            Creation datetime
        """
        try:
            stat = dir_path.stat()
            return datetime.fromtimestamp(stat.st_ctime)
        except Exception:
            return datetime.now()

    def _get_directory_modified_time(self, dir_path: Path) -> datetime:
        """Get the modification time of a directory.

        Args:
            dir_path: Directory path

        Returns:
            Modification datetime
        """
        try:
            stat = dir_path.stat()
            return datetime.fromtimestamp(stat.st_mtime)
        except Exception:
            return datetime.now()

    def copy_or_move_results(self, results: List[Dict[str, Any]], destination: str, move: bool = False) -> List[str]:
        """Copy or move found results to a destination.

        Args:
            results: Results to copy/move
            destination: Destination directory
            move: Whether to move (True) or copy (False)

        Returns:
            List of destination paths
        """
        dest_path = Path(destination)
        dest_path.mkdir(parents=True, exist_ok=True)

        destination_paths = []

        for result in results:
            source_path = Path(result["path"])
            result_dest_path = dest_path / result["name"]

            try:
                if move:
                    if result_dest_path.exists():
                        shutil.rmtree(str(result_dest_path))
                    shutil.move(str(source_path), str(result_dest_path))
                    action = "Moved"
                else:
                    if result_dest_path.exists():
                        shutil.rmtree(str(result_dest_path))
                    shutil.copytree(str(source_path), str(result_dest_path))
                    action = "Copied"

                destination_paths.append(str(result_dest_path))
                print(f"{action}: {result['name']} -> {result_dest_path}")

            except Exception as e:
                print(f"Error {action.lower()}ing {result['name']}: {e}")

        return destination_paths

    def list_available_domains(self) -> List[str]:
        """List all available domains in the organized results.

        Returns:
            List of unique domains
        """
        domains = set()

        # Search in by_domain structure
        domain_dir = self.base_dir / 'by_domain'
        if domain_dir.exists():
            for item in domain_dir.iterdir():
                if item.is_dir() and item.name != '.gitkeep':
                    domains.add(item.name)

        return sorted(list(domains))

    def list_available_content_types(self) -> List[str]:
        """List all available content types in the organized results.

        Returns:
            List of unique content types
        """
        content_types = set()

        # Search in by_type structure
        type_dir = self.base_dir / 'by_type'
        if type_dir.exists():
            for item in type_dir.iterdir():
                if item.is_dir() and item.name != '.gitkeep':
                    content_types.add(item.name)

        return sorted(list(content_types))

    def get_date_range(self) -> Tuple[datetime, datetime]:
        """Get the date range of available results.

        Returns:
            Tuple of (earliest_date, latest_date)
        """
        earliest = None
        latest = None

        # Search in by_date structure
        date_dir = self.base_dir / 'by_date'
        if date_dir.exists():
            for item in date_dir.iterdir():
                if item.is_dir() and item.name != '.gitkeep':
                    try:
                        date = datetime.strptime(item.name, "%Y-%m-%d")
                        if earliest is None or date < earliest:
                            earliest = date
                        if latest is None or date > latest:
                            latest = date
                    except ValueError:
                        continue

        return earliest, latest


def format_results_table(results: List[Dict[str, Any]], show_content: bool = False) -> str:
    """Format results as a readable table.

    Args:
        results: Results to format
        show_content: Whether to show content preview

    Returns:
        Formatted table string
    """
    if not results:
        return "No results found."

    lines = [
        f"Found {len(results)} results:",
        "=" * 100,
        f"{'Name':<25} {'Path':<40} {'Size':<10} {'Date':<12} {'Domains'}",
        "-" * 100
    ]

    for result in results:
        name = result["name"][:24]
        path = result["relative_path"][:39]
        size = f"{result['size_bytes']//1024}KB"[:9]
        date = result["created"].strftime("%Y-%m-%d")[:11]
        domains = ", ".join(result["domains"][:2])[:20]

        lines.append(f"{name:<25} {path:<40} {size:<10} {date:<12} {domains}")

        if show_content and "content_preview" in result:
            content_preview = result["content_preview"][:150] + "..." if len(result["content_preview"]) > 150 else result["content_preview"]
            lines.append(f"  Content: {content_preview}")
            lines.append("")

    return "\n".join(lines)


def interactive_search(searcher: ResultSearcher):
    """Run an interactive search session.

    Args:
        searcher: ResultSearcher instance
    """
    print("🔍 Interactive Scraping Results Search")
    print("=" * 40)

    while True:
        print("\nSearch options:")
        print("1. Search by text query")
        print("2. Filter by domain")
        print("3. Filter by content type")
        print("4. Filter by date range")
        print("5. List available domains")
        print("6. List available content types")
        print("7. Advanced search (combine filters)")
        print("8. Quit")

        choice = input("\nEnter your choice (1-8): ").strip()

        if choice == '1':
            query = input("Enter search query: ").strip()
            if query:
                results = searcher.search_results(query=query, include_content=True)
                print("\n" + format_results_table(results, show_content=True))

        elif choice == '2':
            domains = searcher.list_available_domains()
            if domains:
                print(f"\nAvailable domains: {', '.join(domains)}")
                domain_input = input("Enter domain(s) to search (comma-separated): ").strip()
                if domain_input:
                    selected_domains = [d.strip() for d in domain_input.split(',')]
                    results = searcher.search_results(domains=selected_domains)
                    print("\n" + format_results_table(results))
            else:
                print("No domains found.")

        elif choice == '3':
            content_types = searcher.list_available_content_types()
            if content_types:
                print(f"\nAvailable content types: {', '.join(content_types)}")
                type_input = input("Enter content type(s) to search (comma-separated): ").strip()
                if type_input:
                    selected_types = [t.strip() for t in type_input.split(',')]
                    results = searcher.search_results(content_types=selected_types)
                    print("\n" + format_results_table(results))
            else:
                print("No content types found.")

        elif choice == '4':
            try:
                days_input = input("Search results from last N days (or enter 'all'): ").strip()
                if days_input.lower() == 'all':
                    results = searcher.search_results()
                else:
                    days = int(days_input)
                    date_from = datetime.now() - timedelta(days=days)
                    results = searcher.search_results(date_from=date_from)
                print("\n" + format_results_table(results))
            except ValueError:
                print("Invalid number. Please enter a valid number of days.")

        elif choice == '5':
            domains = searcher.list_available_domains()
            if domains:
                print(f"\nAvailable domains:")
                for domain in domains:
                    print(f"  - {domain}")
            else:
                print("No domains found.")

        elif choice == '6':
            content_types = searcher.list_available_content_types()
            if content_types:
                print(f"\nAvailable content types:")
                for ct in content_types:
                    print(f"  - {ct}")
            else:
                print("No content types found.")

        elif choice == '7':
            print("\nAdvanced search - leave fields empty to skip")
            query = input("Text query: ").strip() or None
            domain_input = input("Domains (comma-separated): ").strip()
            domains = [d.strip() for d in domain_input.split(',')] if domain_input else None
            type_input = input("Content types (comma-separated): ").strip()
            content_types = [t.strip() for t in type_input.split(',')] if type_input else None
            max_input = input("Maximum results: ").strip()
            max_results = int(max_input) if max_input else None

            results = searcher.search_results(
                query=query,
                domains=domains,
                content_types=content_types,
                max_results=max_results,
                include_content=True
            )
            print("\n" + format_results_table(results, show_content=True))

            if results:
                copy_input = input("\nCopy results to directory? (path or 'no'): ").strip()
                if copy_input.lower() != 'no':
                    searcher.copy_or_move_results(results, copy_input, move=False)

        elif choice == '8':
            print("Goodbye!")
            break

        else:
            print("Invalid choice. Please enter 1-8.")


def main():
    """Main function for the find_results script."""
    parser = argparse.ArgumentParser(
        description="Search and retrieve scraping results from the organized structure"
    )
    parser.add_argument(
        "--query",
        help="Text query to search for in content"
    )
    parser.add_argument(
        "--domains",
        nargs="+",
        help="Filter by domains"
    )
    parser.add_argument(
        "--content-types",
        nargs="+",
        help="Filter by content types"
    )
    parser.add_argument(
        "--date-from",
        help="Filter results from this date (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--date-to",
        help="Filter results until this date (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--methods",
        nargs="+",
        choices=["by_date", "by_domain", "by_type", "latest"],
        default=["by_date", "by_domain", "by_type"],
        help="Organization methods to search in"
    )
    parser.add_argument(
        "--max-results",
        type=int,
        help="Maximum number of results to return"
    )
    parser.add_argument(
        "--include-content",
        action="store_true",
        help="Include full content preview in results"
    )
    parser.add_argument(
        "--copy-to",
        help="Copy matching results to this directory"
    )
    parser.add_argument(
        "--move-to",
        help="Move matching results to this directory"
    )
    parser.add_argument(
        "--list-domains",
        action="store_true",
        help="List all available domains"
    )
    parser.add_argument(
        "--list-types",
        action="store_true",
        help="List all available content types"
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Run in interactive mode"
    )
    parser.add_argument(
        "--base-dir",
        default="/Users/tachongrak/Projects/Optus/apps/output/scraping",
        help="Base directory for organized outputs"
    )

    args = parser.parse_args()

    # Initialize searcher
    searcher = ResultSearcher(args.base_dir)

    # Handle list operations
    if args.list_domains:
        domains = searcher.list_available_domains()
        if domains:
            print("Available domains:")
            for domain in domains:
                print(f"  - {domain}")
        else:
            print("No domains found.")
        return

    if args.list_types:
        content_types = searcher.list_available_content_types()
        if content_types:
            print("Available content types:")
            for ct in content_types:
                print(f"  - {ct}")
        else:
            print("No content types found.")
        return

    # Handle interactive mode
    if args.interactive:
        interactive_search(searcher)
        return

    # Parse date filters
    date_from = None
    date_to = None
    if args.date_from:
        try:
            date_from = datetime.strptime(args.date_from, "%Y-%m-%d")
        except ValueError:
            print("Invalid date-from format. Use YYYY-MM-DD")
            return

    if args.date_to:
        try:
            date_to = datetime.strptime(args.date_to, "%Y-%m-%d")
        except ValueError:
            print("Invalid date-to format. Use YYYY-MM-DD")
            return

    # Perform search
    print("🔍 Searching for results...")
    results = searcher.search_results(
        query=args.query,
        domains=args.domains,
        content_types=args.content_types,
        date_from=date_from,
        date_to=date_to,
        organization_methods=args.methods,
        max_results=args.max_results,
        include_content=args.include_content
    )

    # Display results
    print(f"\nFound {len(results)} results:")
    print(format_results_table(results, show_content=args.include_content))

    # Handle copy/move operations
    if results and (args.copy_to or args.move_to):
        destination = args.copy_to or args.move_to
        move = bool(args.move_to)

        print(f"\n{'Moving' if move else 'Copying'} {len(results)} results to: {destination}")
        destination_paths = searcher.copy_or_move_results(results, destination, move)

        if destination_paths:
            print(f"Successfully {'moved' if move else 'copied'} {len(destination_paths)} results")


if __name__ == "__main__":
    main()