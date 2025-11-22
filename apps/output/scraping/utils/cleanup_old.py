#!/usr/bin/env python3
"""
Script to clean up old scraping results based on various criteria.

This script provides safe cleanup functionality with dry-run mode,
backup mechanisms, and flexible filtering options.
"""

import os
import sys
import json
import argparse
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Set, Tuple
import time

# Add the current directory to the path to import result_manager
sys.path.insert(0, os.path.dirname(__file__))

try:
    from result_manager import ResultManager
except ImportError:
    print("Error: Could not import result_manager. Make sure it's in the same directory.")
    sys.exit(1)


class ResultCleaner:
    """Cleans up old scraping results with safety mechanisms."""

    def __init__(self, base_dir: str = "/Users/tachongrak/Projects/Optus/apps/output/scraping"):
        """Initialize the cleaner.

        Args:
            base_dir: Base directory for scraping outputs
        """
        self.base_dir = Path(base_dir)
        self.manager = ResultManager(str(base_dir))
        self.cleanup_log = []

    def scan_for_cleanup(
        self,
        age_days: int = None,
        size_threshold_mb: int = None,
        content_types: List[str] = None,
        domains: List[str] = None,
        exclude_patterns: List[str] = None,
        organization_methods: List[str] = None
    ) -> List[Dict[str, Any]]:
        """Scan for results that match cleanup criteria.

        Args:
            age_days: Remove results older than this many days
            size_threshold_mb: Remove if total size exceeds this threshold
            content_types: Content types to include in cleanup
            domains: Domains to include in cleanup
            exclude_patterns: Path patterns to exclude from cleanup
            organization_methods: Organization methods to scan

        Returns:
            List of cleanup candidates with metadata
        """
        if organization_methods is None:
            organization_methods = ['by_date', 'by_domain', 'by_type']

        candidates = []

        for method in organization_methods:
            method_candidates = self._scan_organization_method(
                method, age_days, size_threshold_mb, content_types, domains, exclude_patterns
            )
            candidates.extend(method_candidates)

        # Sort candidates by age (oldest first) and size
        candidates.sort(key=lambda x: (x["age_days"], -x["size_mb"]))

        return candidates

    def _scan_organization_method(
        self,
        method: str,
        age_days: int = None,
        size_threshold_mb: int = None,
        content_types: List[str] = None,
        domains: List[str] = None,
        exclude_patterns: List[str] = None
    ) -> List[Dict[str, Any]]:
        """Scan a specific organization method for cleanup candidates.

        Args:
            method: Organization method
            age_days: Age threshold in days
            size_threshold_mb: Size threshold in MB
            content_types: Content types to include
            domains: Domains to include
            exclude_patterns: Path patterns to exclude

        Returns:
            List of cleanup candidates from this method
        """
        method_dir = self.base_dir / method
        if not method_dir.exists():
            return []

        candidates = []

        for root, dirs, files in os.walk(method_dir):
            root_path = Path(root)

            # Skip if this looks like a subdirectory of a result
            if any(part in root_path.parts for part in ['raw', 'processed', 'summary', 'assets']):
                continue

            # Check exclude patterns
            if exclude_patterns and self._matches_exclude_patterns(root_path, exclude_patterns):
                continue

            # Check if this is a result directory
            if self._is_result_directory(root_path):
                candidate_info = self._analyze_cleanup_candidate(root_path)
                if candidate_info and self._matches_cleanup_criteria(
                    candidate_info, age_days, size_threshold_mb, content_types, domains
                ):
                    candidate_info["organization_method"] = method
                    candidates.append(candidate_info)

        return candidates

    def _matches_exclude_patterns(self, path: Path, patterns: List[str]) -> bool:
        """Check if a path matches any exclude patterns.

        Args:
            path: Path to check
            patterns: List of patterns to match against

        Returns:
            True if path should be excluded
        """
        path_str = str(path)
        path_relative = str(path.relative_to(self.base_dir))

        for pattern in patterns:
            if pattern in path_str or pattern in path_relative:
                return True

        return False

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

    def _analyze_cleanup_candidate(self, dir_path: Path) -> Optional[Dict[str, Any]]:
        """Analyze a directory for cleanup consideration.

        Args:
            dir_path: Directory to analyze

        Returns:
            Candidate information or None
        """
        try:
            stat = dir_path.stat()
            created_time = datetime.fromtimestamp(stat.st_ctime)
            modified_time = datetime.fromtimestamp(stat.st_mtime)
            age_days = (datetime.now() - created_time).days

            # Calculate size
            size_bytes = self._get_directory_size(dir_path)
            size_mb = size_bytes / (1024 * 1024)

            # Extract metadata
            metadata = self._extract_metadata(dir_path)

            # Extract URLs and domains
            urls = self._extract_urls_from_files(dir_path)
            domains = set()
            for url in urls:
                try:
                    domain = self.manager.get_domain_from_url(url)
                    domains.add(domain)
                except:
                    continue

            # Detect content type
            content_type = None
            if urls:
                content = self._extract_content_from_files(dir_path)
                content_type = self.manager.detect_content_type(urls[0], content, metadata)

            return {
                "path": str(dir_path),
                "name": dir_path.name,
                "relative_path": str(dir_path.relative_to(self.base_dir)),
                "size_bytes": size_bytes,
                "size_mb": size_mb,
                "created": created_time,
                "modified": modified_time,
                "age_days": age_days,
                "domains": list(domains),
                "content_type": content_type,
                "url_count": len(urls),
                "file_count": len(list(dir_path.rglob("*"))),
                "metadata": metadata
            }

        except Exception as e:
            self.cleanup_log.append(f"Error analyzing {dir_path}: {e}")
            return None

    def _matches_cleanup_criteria(
        self,
        candidate: Dict[str, Any],
        age_days: int = None,
        size_threshold_mb: int = None,
        content_types: List[str] = None,
        domains: List[str] = None
    ) -> bool:
        """Check if a candidate matches cleanup criteria.

        Args:
            candidate: Candidate information
            age_days: Age threshold in days
            size_threshold_mb: Size threshold in MB
            content_types: Content types to include
            domains: Domains to include

        Returns:
            True if candidate matches criteria
        """
        # Age filter
        if age_days is not None and candidate["age_days"] < age_days:
            return False

        # Size filter
        if size_threshold_mb is not None and candidate["size_mb"] < size_threshold_mb:
            return False

        # Content type filter
        if content_types and candidate["content_type"]:
            if candidate["content_type"] not in content_types:
                return False

        # Domain filter
        if domains:
            candidate_domains = set(d.lower() for d in candidate["domains"])
            filter_domains = set(d.lower() for d in domains)
            if not candidate_domains.intersection(filter_domains):
                return False

        return True

    def _extract_metadata(self, dir_path: Path) -> Dict[str, Any]:
        """Extract metadata from result directory.

        Args:
            dir_path: Directory to extract metadata from

        Returns:
            Extracted metadata
        """
        metadata = {}

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
            dir_path: Directory to extract URLs from

        Returns:
            List of found URLs
        """
        urls = []

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
                            for line in f:
                                if line.strip():
                                    try:
                                        data = json.loads(line)
                                        if isinstance(data, dict) and 'url' in data and data['url']:
                                            urls.append(data['url'])
                                    except:
                                        continue
                        else:
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

        return list(set(urls))

    def _extract_content_from_files(self, dir_path: Path) -> Optional[str]:
        """Extract content from result files.

        Args:
            dir_path: Directory to extract content from

        Returns:
            Extracted content or None
        """
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

    def execute_cleanup(
        self,
        candidates: List[Dict[str, Any]],
        backup_dir: str = None,
        dry_run: bool = False,
        confirm: bool = True,
        batch_size: int = 10
    ) -> Dict[str, Any]:
        """Execute cleanup on the given candidates.

        Args:
            candidates: List of cleanup candidates
            backup_dir: Directory to backup deleted content
            dry_run: Whether to perform a dry run
            confirm: Whether to require confirmation for each batch
            batch_size: Number of items to process in each batch

        Returns:
            Cleanup execution report
        """
        report = {
            "total_candidates": len(candidates),
            "processed": 0,
            "deleted": 0,
            "backed_up": 0,
            "errors": [],
            "space_freed_mb": 0,
            "dry_run": dry_run
        }

        if not candidates:
            print("No candidates to clean up.")
            return report

        # Prepare backup directory
        if backup_dir and not dry_run:
            backup_path = Path(backup_dir)
            backup_path.mkdir(parents=True, exist_ok=True)
            print(f"Backup directory: {backup_path}")

        print(f"\n{'DRY RUN - ' if dry_run else ''}Processing {len(candidates)} cleanup candidates...")

        # Process in batches
        for i in range(0, len(candidates), batch_size):
            batch = candidates[i:i + batch_size]

            if confirm and not dry_run:
                print(f"\nBatch {i//batch_size + 1}/{(len(candidates) + batch_size - 1)//batch_size}:")
                for candidate in batch:
                    print(f"  - {candidate['name']} ({candidate['size_mb']:.1f}MB, {candidate['age_days']} days old)")

                response = input(f"\nDelete this batch? (y/n/a for all, q to quit): ").strip().lower()
                if response == 'q':
                    break
                elif response == 'a':
                    confirm = False
                elif response != 'y':
                    continue

            # Process batch
            for candidate in batch:
                try:
                    candidate_path = Path(candidate["path"])

                    # Backup if requested
                    if backup_dir and not dry_run:
                        backup_dest = Path(backup_dir) / candidate["name"]
                        if backup_dest.exists():
                            shutil.rmtree(str(backup_dest))
                        shutil.copytree(str(candidate_path), str(backup_dest))
                        report["backed_up"] += 1

                    # Get size before deletion
                    size_mb = candidate["size_mb"]

                    # Delete the directory
                    if not dry_run:
                        if candidate_path.exists():
                            shutil.rmtree(str(candidate_path))
                            report["deleted"] += 1
                            report["space_freed_mb"] += size_mb
                    else:
                        report["deleted"] += 1
                        report["space_freed_mb"] += size_mb

                    report["processed"] += 1
                    self.cleanup_log.append(f"{'Would delete' if dry_run else 'Deleted'}: {candidate['name']}")

                except Exception as e:
                    error_msg = f"Error processing {candidate['name']}: {e}"
                    report["errors"].append(error_msg)
                    self.cleanup_log.append(error_msg)

        return report

    def create_backup(self, candidates: List[Dict[str, Any]], backup_dir: str) -> Dict[str, Any]:
        """Create backup of candidates before deletion.

        Args:
            candidates: List of candidates to backup
            backup_dir: Backup directory path

        Returns:
            Backup report
        """
        backup_path = Path(backup_dir)
        backup_path.mkdir(parents=True, exist_ok=True)

        backup_report = {
            "total_candidates": len(candidates),
            "backed_up": 0,
            "errors": [],
            "backup_dir": str(backup_path)
        }

        print(f"Creating backup in: {backup_path}")

        for candidate in candidates:
            try:
                candidate_path = Path(candidate["path"])
                backup_dest = backup_path / candidate["name"]

                if backup_dest.exists():
                    shutil.rmtree(str(backup_dest))

                shutil.copytree(str(candidate_path), str(backup_dest))
                backup_report["backed_up"] += 1
                print(f"Backed up: {candidate['name']}")

            except Exception as e:
                error_msg = f"Error backing up {candidate['name']}: {e}"
                backup_report["errors"].append(error_msg)
                print(f"Error: {error_msg}")

        return backup_report

    def get_cleanup_statistics(self) -> Dict[str, Any]:
        """Get statistics about the current state for cleanup planning.

        Returns:
            Cleanup statistics
        """
        stats = {
            "total_size_mb": 0,
            "total_results": 0,
            "by_age": {},
            "by_domain": {},
            "by_content_type": {},
            "oldest_result": None,
            "newest_result": None
        }

        # Scan all organization methods
        for method in ['by_date', 'by_domain', 'by_type']:
            method_dir = self.base_dir / method
            if method_dir.exists():
                for root, dirs, files in os.walk(method_dir):
                    root_path = Path(root)

                    # Skip subdirectories of results
                    if any(part in root_path.parts for part in ['raw', 'processed', 'summary', 'assets']):
                        continue

                    if self._is_result_directory(root_path):
                        candidate = self._analyze_cleanup_candidate(root_path)
                        if candidate:
                            stats["total_results"] += 1
                            stats["total_size_mb"] += candidate["size_mb"]

                            # Age statistics
                            age_bucket = self._get_age_bucket(candidate["age_days"])
                            if age_bucket not in stats["by_age"]:
                                stats["by_age"][age_bucket] = {"count": 0, "size_mb": 0}
                            stats["by_age"][age_bucket]["count"] += 1
                            stats["by_age"][age_bucket]["size_mb"] += candidate["size_mb"]

                            # Domain statistics
                            for domain in candidate["domains"]:
                                if domain not in stats["by_domain"]:
                                    stats["by_domain"][domain] = {"count": 0, "size_mb": 0}
                                stats["by_domain"][domain]["count"] += 1
                                stats["by_domain"][domain]["size_mb"] += candidate["size_mb"]

                            # Content type statistics
                            if candidate["content_type"]:
                                ct = candidate["content_type"]
                                if ct not in stats["by_content_type"]:
                                    stats["by_content_type"][ct] = {"count": 0, "size_mb": 0}
                                stats["by_content_type"][ct]["count"] += 1
                                stats["by_content_type"][ct]["size_mb"] += candidate["size_mb"]

                            # Track oldest/newest
                            if (stats["oldest_result"] is None or
                                candidate["created"] < stats["oldest_result"]["created"]):
                                stats["oldest_result"] = candidate

                            if (stats["newest_result"] is None or
                                candidate["created"] > stats["newest_result"]["created"]):
                                stats["newest_result"] = candidate

        return stats

    def _get_age_bucket(self, age_days: int) -> str:
        """Get age bucket label for statistics.

        Args:
            age_days: Age in days

        Returns:
            Age bucket label
        """
        if age_days < 7:
            return "0-7 days"
        elif age_days < 30:
            return "7-30 days"
        elif age_days < 90:
            return "30-90 days"
        elif age_days < 365:
            return "90-365 days"
        else:
            return "365+ days"

    def print_cleanup_candidates(self, candidates: List[Dict[str, Any]], show_details: bool = False):
        """Print cleanup candidates in a readable format.

        Args:
            candidates: List of cleanup candidates
            show_details: Whether to show detailed information
        """
        if not candidates:
            print("No cleanup candidates found.")
            return

        total_size = sum(c["size_mb"] for c in candidates)
        print(f"\nFound {len(candidates)} cleanup candidates ({total_size:.1f}MB total):")
        print("=" * 100)

        for candidate in candidates:
            if show_details:
                print(f"Name: {candidate['name']}")
                print(f"Path: {candidate['relative_path']}")
                print(f"Size: {candidate['size_mb']:.1f}MB")
                print(f"Age: {candidate['age_days']} days")
                print(f"Created: {candidate['created'].strftime('%Y-%m-%d %H:%M:%S')}")
                if candidate["domains"]:
                    print(f"Domains: {', '.join(candidate['domains'])}")
                if candidate["content_type"]:
                    print(f"Content Type: {candidate['content_type']}")
                print(f"URLs: {candidate['url_count']}, Files: {candidate['file_count']}")
                print("-" * 50)
            else:
                domains_preview = ", ".join(candidate["domains"][:2])
                print(f"{candidate['name']:<30} {candidate['size_mb']:>6.1f}MB {candidate['age_days']:>4} days {domains_preview:<20}")

    def print_cleanup_statistics(self, stats: Dict[str, Any]):
        """Print cleanup statistics.

        Args:
            stats: Cleanup statistics
        """
        print("\n📊 Cleanup Statistics")
        print("=" * 40)
        print(f"Total results: {stats['total_results']}")
        print(f"Total size: {stats['total_size_mb']:.1f}MB")

        if stats["oldest_result"]:
            print(f"Oldest result: {stats['oldest_result']['name']} ({stats['oldest_result']['age_days']} days)")
        if stats["newest_result"]:
            print(f"Newest result: {stats['newest_result']['name']} ({stats['newest_result']['age_days']} days)")

        print("\nBy Age:")
        for age_bucket, data in stats["by_age"].items():
            print(f"  {age_bucket}: {data['count']} results, {data['size_mb']:.1f}MB")

        print("\nBy Domain:")
        sorted_domains = sorted(stats["by_domain"].items(), key=lambda x: x[1]["size_mb"], reverse=True)
        for domain, data in sorted_domains[:10]:  # Top 10 domains
            print(f"  {domain}: {data['count']} results, {data['size_mb']:.1f}MB")

        print("\nBy Content Type:")
        sorted_types = sorted(stats["by_content_type"].items(), key=lambda x: x[1]["size_mb"], reverse=True)
        for content_type, data in sorted_types:
            print(f"  {content_type}: {data['count']} results, {data['size_mb']:.1f}MB")

    def generate_cleanup_report(self) -> str:
        """Generate a text report of cleanup operations.

        Returns:
            Formatted report string
        """
        report_lines = [
            "Scraping Results Cleanup Report",
            "=" * 40,
            f"Generated at: {datetime.now().isoformat()}"
        ]

        if self.cleanup_log:
            report_lines.extend([
                "\nOperations Log:",
                "-" * 20
            ])
            for entry in self.cleanup_log[-50]:  # Last 50 entries
                report_lines.append(f"- {entry}")

        return "\n".join(report_lines)


def main():
    """Main function for the cleanup_old script."""
    parser = argparse.ArgumentParser(
        description="Clean up old scraping results with safety mechanisms"
    )
    parser.add_argument(
        "--age-days",
        type=int,
        help="Remove results older than this many days"
    )
    parser.add_argument(
        "--size-mb",
        type=float,
        help="Remove results larger than this many MB (for total size cleanup)"
    )
    parser.add_argument(
        "--total-size-threshold",
        type=float,
        help="Remove oldest results until total size is below this threshold (MB)"
    )
    parser.add_argument(
        "--content-types",
        nargs="+",
        help="Content types to include in cleanup"
    )
    parser.add_argument(
        "--domains",
        nargs="+",
        help="Domains to include in cleanup"
    )
    parser.add_argument(
        "--exclude-patterns",
        nargs="+",
        help="Path patterns to exclude from cleanup"
    )
    parser.add_argument(
        "--methods",
        nargs="+",
        choices=["by_date", "by_domain", "by_type"],
        default=["by_date", "by_domain", "by_type"],
        help="Organization methods to clean up"
    )
    parser.add_argument(
        "--backup-dir",
        help="Directory to backup deleted content"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without making changes"
    )
    parser.add_argument(
        "--no-confirm",
        action="store_true",
        help="Skip confirmation prompts"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="Number of items to process in each batch"
    )
    parser.add_argument(
        "--statistics",
        action="store_true",
        help="Show cleanup statistics without performing cleanup"
    )
    parser.add_argument(
        "--backup-only",
        action="store_true",
        help="Only create backup, don't delete anything"
    )
    parser.add_argument(
        "--base-dir",
        default="/Users/tachongrak/Projects/Optus/apps/output/scraping",
        help="Base directory for organized outputs"
    )
    parser.add_argument(
        "--report-file",
        help="File to save the cleanup report"
    )

    args = parser.parse_args()

    # Initialize cleaner
    cleaner = ResultCleaner(args.base_dir)

    # Show statistics if requested
    if args.statistics:
        stats = cleaner.get_cleanup_statistics()
        cleaner.print_cleanup_statistics(stats)
        return

    print("🔍 Scanning for cleanup candidates...")

    # Determine candidates based on criteria
    if args.total_size_threshold:
        # Calculate total size and find oldest results to remove
        stats = cleaner.get_cleanup_statistics()
        current_size = stats["total_size_mb"]

        if current_size <= args.total_size_threshold:
            print(f"Current size ({current_size:.1f}MB) is already below threshold ({args.total_size_threshold}MB)")
            return

        size_to_free = current_size - args.total_size_threshold
        print(f"Current size: {current_size:.1f}MB, need to free {size_to_free:.1f}MB")

        # Get all candidates sorted by age
        all_candidates = cleaner.scan_for_cleanup(
            organization_methods=args.methods,
            exclude_patterns=args.exclude_patterns
        )

        # Select oldest candidates until we free enough space
        candidates = []
        freed_space = 0
        for candidate in all_candidates:
            candidates.append(candidate)
            freed_space += candidate["size_mb"]
            if freed_space >= size_to_free:
                break

        print(f"Selected {len(candidates)} oldest results to free {freed_space:.1f}MB")
    else:
        # Regular cleanup by criteria
        candidates = cleaner.scan_for_cleanup(
            age_days=args.age_days,
            size_threshold_mb=args.size_mb,
            content_types=args.content_types,
            domains=args.domains,
            exclude_patterns=args.exclude_patterns,
            organization_methods=args.methods
        )

    if not candidates:
        print("No cleanup candidates found matching the criteria.")
        return

    # Show candidates
    cleaner.print_cleanup_candidates(candidates, show_details=True)

    total_size = sum(c["size_mb"] for c in candidates)
    print(f"\nTotal space to be freed: {total_size:.1f}MB")

    # Backup only mode
    if args.backup_only:
        if not args.backup_dir:
            print("Error: --backup-dir is required for --backup-only")
            return

        print("\n📦 Creating backup...")
        backup_report = cleaner.create_backup(candidates, args.backup_dir)
        print(f"Backed up {backup_report['backed_up']}/{backup_report['total_candidates']} items")
        return

    # Confirmation
    if not args.dry_run and not args.no_confirm:
        response = input(f"\nProceed with cleanup of {len(candidates)} items? (y/N): ").strip().lower()
        if response != 'y':
            print("Cleanup cancelled.")
            return

    # Execute cleanup
    print(f"\n{'DRY RUN MODE - ' if args.dry_run else ''}Executing cleanup...")
    cleanup_report = cleaner.execute_cleanup(
        candidates,
        args.backup_dir,
        args.dry_run,
        not args.no_confirm,
        args.batch_size
    )

    # Show results
    print(f"\n{'Dry run ' if args.dry_run else ''}complete!")
    print(f"Processed: {cleanup_report['processed']}")
    print(f"Deleted: {cleanup_report['deleted']}")
    print(f"Space freed: {cleanup_report['space_freed_mb']:.1f}MB")
    print(f"Backed up: {cleanup_report['backed_up']}")

    if cleanup_report['errors']:
        print(f"Errors: {len(cleanup_report['errors'])}")
        for error in cleanup_report['errors'][:5]:  # Show first 5 errors
            print(f"  - {error}")

    # Save report if requested
    if args.report_file:
        try:
            report_text = cleaner.generate_cleanup_report()
            with open(args.report_file, 'w', encoding='utf-8') as f:
                f.write(report_text)
            print(f"\n📄 Report saved to: {args.report_file}")
        except Exception as e:
            print(f"\n❌ Error saving report: {e}")


if __name__ == "__main__":
    main()