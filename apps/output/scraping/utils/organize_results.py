#!/usr/bin/env python3
"""
Script to organize existing scraping results into the standardized structure.

This script scans for existing scraping results and organizes them by date,
domain, and content type according to the new structure.
"""

import os
import sys
import json
import argparse
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

# Add the current directory to the path to import result_manager
sys.path.insert(0, os.path.dirname(__file__))

try:
    from result_manager import ResultManager
except ImportError:
    print("Error: Could not import result_manager. Make sure it's in the same directory.")
    sys.exit(1)


class ResultOrganizer:
    """Organizes existing scraping results into the standard structure."""

    def __init__(self, base_dir: str = "/Users/tachongrak/Projects/Optus/apps/output/scraping"):
        """Initialize the organizer.

        Args:
            base_dir: Base directory for scraping outputs
        """
        self.base_dir = Path(base_dir)
        self.manager = ResultManager(str(base_dir))
        self.report = {
            "scanned_directories": 0,
            "organized_results": 0,
            "errors": [],
            "organization_summary": {}
        }

    def find_existing_results(self, search_paths: List[str] = None) -> List[Dict[str, Any]]:
        """Find existing scraping results.

        Args:
            search_paths: List of paths to search (defaults to common locations)

        Returns:
            List of found results with metadata
        """
        if search_paths is None:
            # Default search paths
            search_paths = [
                str(self.base_dir.parent),  # apps/output
                str(Path.cwd() / "agents"),  # agents directory
                str(Path.cwd()),  # current directory
            ]

        found_results = []

        for search_path in search_paths:
            if not Path(search_path).exists():
                continue

            print(f"Searching in: {search_path}")
            results = self._scan_directory_for_results(Path(search_path))
            found_results.extend(results)

        print(f"Found {len(found_results)} potential result directories")
        return found_results

    def _scan_directory_for_results(self, scan_path: Path) -> List[Dict[str, Any]]:
        """Scan a directory for scraping results.

        Args:
            scan_path: Directory path to scan

        Returns:
            List of found results
        """
        results = []
        self.report["scanned_directories"] += 1

        # Look for common scraping result patterns
        patterns = [
            "**/crawler/",
            "**/scraping_results/",
            "**/crawl_results/",
            "*crawler*",
            "*scrape*",
            "*crawl*"
        ]

        for pattern in patterns:
            try:
                matching_paths = list(scan_path.glob(pattern))
                for match_path in matching_paths:
                    if match_path.is_dir():
                        result_info = self._analyze_result_directory(match_path)
                        if result_info:
                            results.append(result_info)
            except Exception as e:
                self.report["errors"].append(f"Error scanning {scan_path} with pattern {pattern}: {e}")

        # Also look for directories with typical result files
        try:
            for item in scan_path.rglob("*"):
                if item.is_file() and item.name in [
                    "cc_raw_output.json",
                    "cc_raw_output.jsonl",
                    "scrape_results.json",
                    "crawl_results.json"
                ]:
                    result_info = self._analyze_result_directory(item.parent)
                    if result_info and not any(r["path"] == str(item.parent) for r in results):
                        results.append(result_info)
        except Exception as e:
            self.report["errors"].append(f"Error scanning for result files in {scan_path}: {e}")

        return results

    def _analyze_result_directory(self, dir_path: Path) -> Optional[Dict[str, Any]]:
        """Analyze a directory to determine if it contains scraping results.

        Args:
            dir_path: Directory path to analyze

        Returns:
            Result information or None if not a result directory
        """
        # Check for typical result files
        result_files = [
            "cc_raw_output.json",
            "cc_raw_output.jsonl",
            "scrape_results.json",
            "crawl_results.json",
            "custom_summary_output.json"
        ]

        has_result_files = any((dir_path / f).exists() for f in result_files)

        if not has_result_files:
            # Check for subdirectories with typical names
            subdirs = ["raw", "processed", "logs", "assets"]
            has_typical_subdirs = any((dir_path / d).exists() and (dir_path / d).is_dir() for d in subdirs)

            if not has_typical_subdirs:
                return None

        # Extract metadata
        metadata = self._extract_result_metadata(dir_path)

        return {
            "path": str(dir_path),
            "name": dir_path.name,
            "has_result_files": has_result_files,
            "metadata": metadata,
            "size_bytes": self._get_directory_size(dir_path),
            "created": self._get_directory_created_time(dir_path)
        }

    def _extract_result_metadata(self, dir_path: Path) -> Dict[str, Any]:
        """Extract metadata from a result directory.

        Args:
            dir_path: Directory path to analyze

        Returns:
            Extracted metadata
        """
        metadata = {}

        # Try to read summary files
        summary_files = [
            "custom_summary_output.json",
            "cc_final_object.json",
            "summary.json"
        ]

        for summary_file in summary_files:
            summary_path = dir_path / summary_file
            if summary_path.exists():
                try:
                    with open(summary_path, 'r', encoding='utf-8') as f:
                        summary_data = json.load(f)
                        metadata.update(summary_data)
                        break  # Use the first readable summary file
                except Exception:
                    continue

        # Extract URLs from raw output files
        for output_file in ["cc_raw_output.json", "cc_raw_output.jsonl", "scrape_results.json"]:
            output_path = dir_path / output_file
            if output_path.exists():
                try:
                    with open(output_path, 'r', encoding='utf-8') as f:
                        if output_file.endswith('.jsonl'):
                            # JSONL format
                            urls = []
                            for line in f:
                                if line.strip():
                                    data = json.loads(line)
                                    if isinstance(data, dict) and 'url' in data:
                                        urls.append(data['url'])
                            metadata['urls'] = urls[:5]  # First 5 URLs
                        else:
                            # JSON format
                            data = json.load(f)
                            if isinstance(data, list):
                                metadata['urls'] = [item.get('url', '') for item in data[:5] if isinstance(item, dict)]
                            elif isinstance(data, dict):
                                if 'results' in data and isinstance(data['results'], list):
                                    metadata['urls'] = [item.get('url', '') for item in data['results'][:5] if isinstance(item, dict)]
                                elif 'url' in data:
                                    metadata['urls'] = [data['url']]
                    break
                except Exception:
                    continue

        return metadata

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

    def organize_results(self, results: List[Dict[str, Any]],
                        organization_methods: List[str] = None,
                        move_results: bool = False,
                        dry_run: bool = False) -> Dict[str, Any]:
        """Organize found results.

        Args:
            results: List of results to organize
            organization_methods: Methods to use for organization
            move_results: Whether to move (True) or copy (False) results
            dry_run: Whether to perform a dry run (no actual changes)

        Returns:
            Organization report
        """
        if organization_methods is None:
            organization_methods = ['by_date', 'by_domain', 'by_type']

        organization_report = {
            "total_processed": len(results),
            "organized_by_method": {method: 0 for method in organization_methods},
            "errors": [],
            "dry_run": dry_run
        }

        print(f"\n{'DRY RUN - ' if dry_run else ''}Organizing {len(results)} results...")

        for i, result in enumerate(results):
            print(f"\n[{i+1}/{len(results)}] Processing: {result['name']}")

            try:
                result_path = result["path"]
                metadata = result.get("metadata", {})

                # Get date from result
                date = self._extract_date_from_result(result)

                # Get URLs from metadata
                urls = metadata.get('urls', [])
                primary_url = urls[0] if urls else None

                # Get content for type detection
                content = self._extract_content_from_result(result)

                # Organize by each method
                for method in organization_methods:
                    if method == 'by_date':
                        organized_path = self.manager.organize_by_date(result_path, date)
                    elif method == 'by_domain':
                        if not primary_url:
                            print(f"  Skipping {method}: No URL found")
                            continue
                        organized_path = self.manager.organize_by_domain(result_path, primary_url, date)
                    elif method == 'by_type':
                        if not primary_url:
                            print(f"  Skipping {method}: No URL found")
                            continue
                        organized_path = self.manager.organize_by_type(
                            result_path, primary_url, content, metadata, date
                        )
                    else:
                        print(f"  Unknown organization method: {method}")
                        continue

                    if not dry_run:
                        # Move or copy the actual data
                        if move_results:
                            print(f"  Moving to: {organized_path}")
                        else:
                            print(f"  Copying to: {organized_path}")

                    organization_report["organized_by_method"][method] += 1

                # Update latest
                if not dry_run:
                    self.manager.update_latest(result_path, result['name'])
                    print(f"  Updated latest: {result['name']}")

                self.report["organized_results"] += 1

            except Exception as e:
                error_msg = f"Error organizing {result['name']}: {e}"
                print(f"  ERROR: {error_msg}")
                organization_report["errors"].append(error_msg)
                self.report["errors"].append(error_msg)

        return organization_report

    def _extract_date_from_result(self, result: Dict[str, Any]) -> datetime:
        """Extract date from result metadata or file system.

        Args:
            result: Result information

        Returns:
            Date for organization
        """
        # Try to get date from metadata
        metadata = result.get("metadata", {})

        # Check for various date fields
        date_fields = ["timestamp", "created_at", "processing_time", "date"]
        for field in date_fields:
            if field in metadata:
                try:
                    if isinstance(metadata[field], (int, float)):
                        return datetime.fromtimestamp(metadata[field])
                    elif isinstance(metadata[field], str):
                        # Try ISO format first
                        try:
                            return datetime.fromisoformat(metadata[field].replace('Z', '+00:00'))
                        except ValueError:
                            # Try other common formats
                            for fmt in ["%Y-%m-%d", "%Y-%m-%d %H:%M:%S"]:
                                try:
                                    return datetime.strptime(metadata[field], fmt)
                                except ValueError:
                                    continue
                except Exception:
                    continue

        # Fall back to filesystem creation time
        return result.get("created", datetime.now())

    def _extract_content_from_result(self, result: Dict[str, Any]) -> Optional[str]:
        """Extract content from result for type detection.

        Args:
            result: Result information

        Returns:
            Content string or None
        """
        result_path = Path(result["path"])

        # Look for content files
        content_files = ["cc_raw_output.json", "scrape_results.json"]

        for content_file in content_files:
            content_path = result_path / content_file
            if content_path.exists():
                try:
                    with open(content_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                        # Extract content from different structures
                        if isinstance(data, list) and data:
                            first_item = data[0]
                            if isinstance(first_item, dict):
                                return first_item.get('content') or first_item.get('markdown')
                        elif isinstance(data, dict):
                            if 'results' in data and isinstance(data['results'], list) and data['results']:
                                first_result = data['results'][0]
                                if isinstance(first_result, dict):
                                    return first_result.get('content') or first_result.get('markdown')
                            else:
                                return data.get('content') or data.get('markdown')
                except Exception:
                    continue

        return None

    def generate_report(self) -> str:
        """Generate a text report of the organization process.

        Returns:
            Formatted report string
        """
        report_lines = [
            "Scraping Results Organization Report",
            "=" * 40,
            f"Scanned directories: {self.report['scanned_directories']}",
            f"Organized results: {self.report['organized_results']}",
            f"Errors encountered: {len(self.report['errors'])}",
        ]

        if self.report['errors']:
            report_lines.extend([
                "\nErrors:",
                "-" * 10
            ])
            for error in self.report['errors'][:10]:  # Show first 10 errors
                report_lines.append(f"- {error}")

        report_lines.extend([
            "\nOrganization Summary:",
            "-" * 20
        ])

        for method, count in self.report.get('organization_summary', {}).items():
            report_lines.append(f"- {method}: {count} results")

        report_lines.append(f"\nReport generated at: {datetime.now().isoformat()}")

        return "\n".join(report_lines)


def main():
    """Main function for the organize_results script."""
    parser = argparse.ArgumentParser(
        description="Organize existing scraping results into the standardized structure"
    )
    parser.add_argument(
        "--search-paths",
        nargs="+",
        help="Paths to search for existing results (default: common locations)"
    )
    parser.add_argument(
        "--methods",
        nargs="+",
        choices=["by_date", "by_domain", "by_type"],
        default=["by_date", "by_domain", "by_type"],
        help="Organization methods to use (default: all methods)"
    )
    parser.add_argument(
        "--move",
        action="store_true",
        help="Move results instead of copying them"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes"
    )
    parser.add_argument(
        "--base-dir",
        default="/Users/tachongrak/Projects/Optus/apps/output/scraping",
        help="Base directory for organized outputs"
    )
    parser.add_argument(
        "--report-file",
        help="File to save the organization report"
    )

    args = parser.parse_args()

    # Initialize organizer
    organizer = ResultOrganizer(args.base_dir)

    print("🔍 Scanning for existing scraping results...")
    results = organizer.find_existing_results(args.search_paths)

    if not results:
        print("❌ No scraping results found to organize.")
        return

    print(f"✅ Found {len(results)} result directories to process")

    # Organize results
    organization_report = organizer.organize_results(
        results,
        args.methods,
        args.move,
        args.dry_run
    )

    # Update report
    organizer.report["organization_summary"] = organization_report["organized_by_method"]

    # Generate and display report
    report_text = organizer.generate_report()
    print("\n" + report_text)

    # Save report to file if requested
    if args.report_file:
        try:
            with open(args.report_file, 'w', encoding='utf-8') as f:
                f.write(report_text)
            print(f"\n📄 Report saved to: {args.report_file}")
        except Exception as e:
            print(f"\n❌ Error saving report: {e}")

    if not args.dry_run:
        print(f"\n✅ Organization complete! {organization_report['total_processed']} results processed.")
    else:
        print(f"\n🔍 Dry run complete! {organization_report['total_processed']} results would be processed.")


if __name__ == "__main__":
    main()