#!/usr/bin/env python3
"""
Core result management utilities for organizing scraping results.

This module provides the foundational functions for creating and managing
the standardized directory structure for scraping results.
"""

import os
import json
import shutil
import urllib.parse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ResultManager:
    """Manages scraping results with standardized organization."""

    def __init__(self, base_output_dir: str = "/Users/tachongrak/Projects/Optus/apps/output/scraping"):
        """Initialize the result manager.

        Args:
            base_output_dir: Base directory for all scraping outputs
        """
        self.base_output_dir = Path(base_output_dir)
        self.ensure_base_structure()

    def ensure_base_structure(self):
        """Ensure the base directory structure exists."""
        subdirs = ['by_date', 'by_domain', 'by_type', 'latest', 'utils']

        for subdir in subdirs:
            dir_path = self.base_output_dir / subdir
            dir_path.mkdir(parents=True, exist_ok=True)

            # Create .gitkeep if it doesn't exist
            gitkeep_path = dir_path / '.gitkeep'
            if not gitkeep_path.exists():
                gitkeep_path.write_text(f"# {subdir} directory\n")

    def create_result_structure(self, result_path: str) -> Dict[str, str]:
        """Create the standard result subdirectory structure.

        Args:
            result_path: Path where the result should be stored

        Returns:
            Dictionary mapping subdirectory names to their full paths
        """
        result_dir = Path(result_path)
        result_dir.mkdir(parents=True, exist_ok=True)

        # Standard subdirectories
        subdirs = ['raw', 'processed', 'summary', 'assets']
        created_paths = {}

        for subdir in subdirs:
            subdir_path = result_dir / subdir
            subdir_path.mkdir(exist_ok=True)
            created_paths[subdir] = str(subdir_path)

            # Create README file explaining the purpose
            readme_content = self._get_subdir_readme(subdir)
            (subdir_path / 'README.md').write_text(readme_content)

        # Create metadata file
        metadata = {
            "created_at": datetime.now().isoformat(),
            "result_path": str(result_dir),
            "structure_version": "1.0",
            "subdirectories": list(created_paths.keys())
        }

        (result_dir / 'metadata.json').write_text(json.dumps(metadata, indent=2))

        logger.info(f"Created result structure at: {result_path}")
        return created_paths

    def _get_subdir_readme(self, subdir_name: str) -> str:
        """Get README content for a subdirectory.

        Args:
            subdir_name: Name of the subdirectory

        Returns:
            README content as string
        """
        readme_contents = {
            'raw': """# Raw Data

This directory contains the original, unmodified scraping data:

- **HTML**: Original HTML content from web pages
- **JSON**: Raw JSON responses from APIs or crawling tools
- **Screenshots**: Unmodified screenshot files
- **Media**: Original images, videos, and other media files

Files in this directory should be treated as the source of truth
and should not be modified directly.
""",

            'processed': """# Processed Data

This directory contains cleaned, processed, and transformed data:

- **Cleaned Text**: Text content with HTML tags removed
- **Structured Data**: JSON files with extracted information
- **Summaries**: Processed and summarized content
- **Analysis**: Processed analytical results

These files are derived from the raw data and are ready for
consumption by applications or further analysis.
""",

            'summary': """# Summary Information

This directory contains high-level summaries and metadata:

- **Overview**: Quick summaries of scraping results
- **Statistics**: Quantitative information about the scraped data
- **Index**: Index files for easy searching and navigation
- **Reports**: Generated reports and insights

These files provide quick access to the most important information
without needing to process the full datasets.
""",

            'assets': """# Assets and Resources

This directory contains downloaded assets and resources:

- **Images**: Downloaded image files
- **Documents**: PDFs, Word documents, and other files
- **Stylesheets**: CSS files related to the scraped content
- **Scripts**: JavaScript files (when available)

These assets support the main scraped content and provide
additional context or resources.
"""
        }

        return readme_contents.get(subdir_name, f"# {subdir_name.title()}\n\nThis directory contains {subdir_name} data.")

    def get_domain_from_url(self, url: str) -> str:
        """Extract domain name from URL.

        Args:
            url: URL to extract domain from

        Returns:
            Domain name as string
        """
        try:
            parsed = urllib.parse.urlparse(url)
            domain = parsed.netloc.lower()
            # Remove www. prefix if present
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain
        except Exception as e:
            logger.warning(f"Failed to extract domain from {url}: {e}")
            return "unknown_domain"

    def detect_content_type(self, url: str, content: str = None, metadata: Dict = None) -> str:
        """Detect content type based on URL, content, and metadata.

        Args:
            url: URL that was scraped
            content: Raw content (optional)
            metadata: Additional metadata (optional)

        Returns:
            Detected content type as string
        """
        url_lower = url.lower()

        # Check URL patterns first
        if any(pattern in url_lower for pattern in ['/product', '/item', '/shop']):
            return 'products'
        elif any(pattern in url_lower for pattern in ['/article', '/blog', '/news', '/post']):
            return 'articles'
        elif any(pattern in url_lower for pattern in ['/doc', '/documentation', '/guide']):
            return 'documentation'
        elif any(pattern in url_lower for pattern in ['/api', '/endpoint']):
            return 'api'

        # Check metadata if available
        if metadata:
            title = str(metadata.get('title', '')).lower()
            description = str(metadata.get('description', '')).lower()

            if any(keyword in title + description for keyword in ['product', 'buy', 'price', 'shop']):
                return 'products'
            elif any(keyword in title + description for keyword in ['article', 'blog', 'news']):
                return 'articles'

        # Analyze content if available
        if content:
            content_lower = content.lower()
            if any(keyword in content_lower for keyword in ['price', 'cart', 'checkout']):
                return 'products'
            elif any(keyword in content_lower for keyword in ['article', 'published', 'author']):
                return 'articles'

        # Default fallback
        return 'general'

    def organize_by_date(self, result_path: str, date: datetime = None) -> str:
        """Organize results by date.

        Args:
            result_path: Path to the result directory
            date: Date for organization (defaults to current date)

        Returns:
            Organized path
        """
        if date is None:
            date = datetime.now()

        date_str = date.strftime("%Y-%m-%d")

        # Extract job ID from path
        job_id = Path(result_path).name
        if not job_id:
            job_id = f"job_{int(date.timestamp())}"

        organized_path = self.base_output_dir / 'by_date' / date_str / job_id

        # Create the organized structure
        self.create_result_structure(str(organized_path))

        # Move/copy existing content if path exists and is different
        if Path(result_path).exists() and str(Path(result_path).resolve()) != str(organized_path.resolve()):
            if organized_path.exists():
                shutil.rmtree(str(organized_path))
            shutil.move(str(result_path), str(organized_path))

        return str(organized_path)

    def organize_by_domain(self, result_path: str, url: str, date: datetime = None) -> str:
        """Organize results by domain.

        Args:
            result_path: Path to the result directory
            url: URL that was scraped
            date: Date for organization (defaults to current date)

        Returns:
            Organized path
        """
        if date is None:
            date = datetime.now()

        date_str = date.strftime("%Y-%m-%d")
        domain = self.get_domain_from_url(url)

        # Extract job ID from path
        job_id = Path(result_path).name
        if not job_id:
            job_id = f"job_{int(date.timestamp())}"

        organized_path = self.base_output_dir / 'by_domain' / domain / date_str / job_id

        # Create the organized structure
        self.create_result_structure(str(organized_path))

        # Move/copy existing content if path exists and is different
        if Path(result_path).exists() and str(Path(result_path).resolve()) != str(organized_path.resolve()):
            if organized_path.exists():
                shutil.rmtree(str(organized_path))
            shutil.move(str(result_path), str(organized_path))

        return str(organized_path)

    def organize_by_type(self, result_path: str, url: str, content: str = None, metadata: Dict = None, date: datetime = None) -> str:
        """Organize results by content type.

        Args:
            result_path: Path to the result directory
            url: URL that was scraped
            content: Content for type detection
            metadata: Metadata for type detection
            date: Date for organization (defaults to current date)

        Returns:
            Organized path
        """
        if date is None:
            date = datetime.now()

        date_str = date.strftime("%Y-%m-%d")
        content_type = self.detect_content_type(url, content, metadata)
        domain = self.get_domain_from_url(url)

        # Extract job ID from path
        job_id = Path(result_path).name
        if not job_id:
            job_id = f"job_{int(date.timestamp())}"

        organized_path = self.base_output_dir / 'by_type' / content_type / domain / date_str / job_id

        # Create the organized structure
        self.create_result_structure(str(organized_path))

        # Move/copy existing content if path exists and is different
        if Path(result_path).exists() and str(Path(result_path).resolve()) != str(organized_path.resolve()):
            if organized_path.exists():
                shutil.rmtree(str(organized_path))
            shutil.move(str(result_path), str(organized_path))

        return str(organized_path)

    def update_latest(self, result_path: str, result_name: str):
        """Update the latest directory with a reference to this result.

        Args:
            result_path: Path to the result directory
            result_name: Name for the link/copy in latest
        """
        latest_path = self.base_output_dir / 'latest' / result_name

        # Remove existing if present
        if latest_path.exists():
            if latest_path.is_symlink():
                latest_path.unlink()
            else:
                shutil.rmtree(str(latest_path))

        # Try to create symbolic link, fallback to copy
        try:
            latest_path.symlink_to(Path(result_path).resolve())
            logger.info(f"Created symbolic link: {latest_path} -> {result_path}")
        except (OSError, NotImplementedError):
            # Fallback: copy the directory
            shutil.copytree(str(result_path), str(latest_path))
            logger.info(f"Created copy: {latest_path}")

    def get_organization_stats(self) -> Dict[str, Any]:
        """Get statistics about the organized results.

        Returns:
            Dictionary with organization statistics
        """
        stats = {
            "total_results": 0,
            "by_date": {},
            "by_domain": {},
            "by_type": {},
            "latest_count": 0,
            "disk_usage": {}
        }

        # Count by date
        date_dir = self.base_output_dir / 'by_date'
        if date_dir.exists():
            for date_entry in date_dir.iterdir():
                if date_entry.is_dir():
                    date_str = date_entry.name
                    job_count = len([d for d in date_entry.iterdir() if d.is_dir()])
                    stats["by_date"][date_str] = job_count
                    stats["total_results"] += job_count

        # Count by domain
        domain_dir = self.base_output_dir / 'by_domain'
        if domain_dir.exists():
            for domain_entry in domain_dir.iterdir():
                if domain_entry.is_dir():
                    domain = domain_entry.name
                    job_count = len([d for d in domain_entry.rglob('*') if d.is_dir() and d.parent == domain_entry])
                    stats["by_domain"][domain] = job_count

        # Count by type
        type_dir = self.base_output_dir / 'by_type'
        if type_dir.exists():
            for type_entry in type_dir.iterdir():
                if type_entry.is_dir():
                    content_type = type_entry.name
                    job_count = len([d for d in type_entry.rglob('*') if d.is_dir() and d.parent == type_entry])
                    stats["by_type"][content_type] = job_count

        # Count latest
        latest_dir = self.base_output_dir / 'latest'
        if latest_dir.exists():
            stats["latest_count"] = len([d for d in latest_dir.iterdir() if d.is_dir() or d.is_symlink()])

        return stats


# Convenience functions
def create_standard_structure(base_path: str) -> Dict[str, str]:
    """Create a standard result structure at the given path.

    Args:
        base_path: Base path for the result

    Returns:
        Dictionary of created subdirectories
    """
    manager = ResultManager()
    return manager.create_result_structure(base_path)


def get_domain_from_url(url: str) -> str:
    """Extract domain from URL.

    Args:
        url: URL to extract domain from

    Returns:
        Domain name
    """
    manager = ResultManager()
    return manager.get_domain_from_url(url)


def detect_content_type(url: str, content: str = None, metadata: Dict = None) -> str:
    """Detect content type from URL and content.

    Args:
        url: URL that was scraped
        content: Optional content for analysis
        metadata: Optional metadata for analysis

    Returns:
        Detected content type
    """
    manager = ResultManager()
    return manager.detect_content_type(url, content, metadata)