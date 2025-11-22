#!/usr/bin/env python3
"""
Fixed output formatter for scraping results.

This module processes raw scraping results and converts them to clean,
structured formats suitable for different use cases.
"""

import json
import re
import html
import os
from typing import Dict, Any, List, Optional
from dataclasses import asdict
from pathlib import Path

# Try to import ThaiWatsadu specialist formatter
try:
    from thaiwatsadu_formatter import ThaiWatsaduFormatter
    THAIWATSADU_FORMATTER_AVAILABLE = True
except ImportError:
    THAIWATSADU_FORMATTER_AVAILABLE = False


class OutputFormatter:
    """Formats scraping results into clean, structured outputs."""

    def __init__(self):
        # Initialize ThaiWatsadu specialist formatter if available
        if THAIWATSADU_FORMATTER_AVAILABLE:
            self.thaiwatsadu_formatter = ThaiWatsaduFormatter()
        else:
            self.thaiwatsadu_formatter = None

        self.product_extractors = {
            'name': [
                r'<title>([^<]+)</title>',
                r'<h1[^>]*>([^<]+)</h1>',
                r'meta property="og:title" content="([^"]+)"'
            ],
            'description': [
                r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']+)["\']',
                r'<meta[^>]+property=["\']og:description["\'][^>]+content=["\']([^"\']+)["\']',
                r'<div[^>]+class="[^"]*description[^"]*"[^>]*>([^<]+)</div>'
            ],
            'current_price': [
                r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(?:฿|THB|baht)',
                r'["\']price["\']\s*:\s*["\']?(\d+(?:,\d{3})*(?:\.\d{2})?)["\']?',
                r'<span[^>]+class="[^"]*price[^"]*"[^>]*>([^<]+)</span>'
            ],
            'original_price': [
                r'["\']original_price["\']\s*:\s*["\']?(\d+(?:,\d{3})*(?:\.\d{2})?)["\']?',
                r'["\']list_price["\']\s*:\s*["\']?(\d+(?:,\d{3})*(?:\.\d{2})?)["\']?',
                r'<span[^>]+class="[^"]*original[^"]*price[^"]*"[^>]*>([^<]+)</span>',
                r'<span[^>]+class="[^"]*list[^"]*price[^"]*"[^>]*>([^<]+)</span>'
            ],
            'brand': [
                r'<meta[^>]+property=["\']og:brand["\'][^>]+content=["\']([^"\']+)["\']',
                r'<div[^>]+class="[^"]*brand[^"]*"[^>]*>([^<]+)</div>',
                r'brand["\']\s*:\s*["\']([^"\']+)["\']?'
            ],
            'model': [
                r'["\']model["\']\s*:\s*["\']([^"\']+)["\']?',
                r'รุ่น\s*([^\s<]+)',
                r'Model\s*[:\s]*([^\s<]+)'
            ],
            'sku': [
                r'["\']sku["\']\s*:\s*["\']([^"\']+)["\']?',
                r'<div[^>]+class="[^"]*sku[^"]*"[^>]*>([^<]+)</div>',
                r'รหัสสินค้า[^:]*:\s*([^\s<]+)'
            ],
            'category': [
                r'["\']category["\']\s*:\s*["\']([^"\']+)["\']?',
                r'<div[^>]+class="[^"]*category[^"]*"[^>]*>([^<]+)</div>',
                r'หมวดหมู่[:\s]*([^\s<]+)'
            ],
            'volume': [
                r'(\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:ลิตร|ลิตร|L)',
                r'volume["\']\s*:\s*["\']?(\d+(?:,\d{3})*(?:\.\d+)?)["\']?'
            ],
            'dimensions': [
                r'(\d+\s*[x×X]\s*\d+\s*[x×X]\s*\d+)\s*(?:ซม\.|มม\.|cm|mm)',
                r'ขนาด\s*[:\s]*(\d+\s*[x×X]\s*\d+\s*[x×X]\s*\d+)\s*(?:ซม\.|มม\.|cm|mm)',
                r'dimensions["\']\s*:\s*["\']?(\d+\s*[x×X]\s*\d+\s*[x×X]\s*\d+)["\']?'
            ],
            'material': [
                r'วัสดุ\s*[:\s]*([^\s<]+)',
                r'material["\']\s*:\s*["\']([^"\']+)["\']?',
                r'<div[^>]+class="[^"]*material[^"]*"[^>]*>([^<]+)</div>'
            ],
            'color': [
                r'สี[:\s]*([^\s<]+)',
                r'color["\']\s*:\s*["\']([^"\']+)["\']?',
                r'<div[^>]+class="[^"]*color[^"]*"[^>]*>([^<]+)</div>'
            ],
            'images': [
                r'<img[^>]+src=["\']([^"\']+)["\']',
                r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']'
            ],
            'specifications': [
                r'<li[^>]*>([^<]+)</li>',
                r'<div[^>]+class="[^"]*spec[^"]*"[^>]*>([^<]+)</div>'
            ]
        }

    def extract_field(self, content: str, field_name: str) -> Optional[str]:
        """Extract a specific field from content using multiple patterns."""
        patterns = self.product_extractors.get(field_name, [])

        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
            if matches:
                # Clean and decode HTML entities
                value = matches[0].strip()
                value = html.unescape(value)

                # Additional cleaning
                value = re.sub(r'\s+', ' ', value)  # Normalize whitespace
                value = value.strip()

                if value and len(value) > 0:
                    return value

        return None

    def extract_multiple_fields(self, content: str, field_name: str) -> List[str]:
        """Extract multiple values for a field (e.g., specifications, images)."""
        patterns = self.product_extractors.get(field_name, [])
        results = []

        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                value = match.strip()
                value = html.unescape(value)
                value = re.sub(r'\s+', ' ', value)
                value = value.strip()

                if value and len(value) > 0 and value not in results:
                    results.append(value)

        return results

    def process_product_page(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Process a raw scraping result into structured product data."""
        content = result.get('html', '') or result.get('content', '')
        url = result.get('url', '')

        # Check if we should use ThaiWatsadu specialist formatter
        if self.thaiwatsadu_formatter and url and 'thaiwatsadu.com' in url.lower():
            try:
                thai_result = self.thaiwatsadu_formatter.process_thaiwatsadu_page(result)
                return thai_result
            except Exception as e:
                print(f"ThaiWatsadu formatter failed, falling back to generic: {e}")

        # Fallback to generic extraction
        if not content:
            return self._create_empty_result(url)

        # Extract product information
        current_price = self._extract_price(self.extract_field(content, 'current_price'))
        original_price = self._extract_price(self.extract_field(content, 'original_price'))

        # Calculate discount information
        has_discount = original_price and current_price and original_price > current_price
        discount_percent = 0
        discount_amount = 0
        if has_discount:
            discount_percent = round(((original_price - current_price) / original_price) * 100, 2)
            discount_amount = original_price - current_price

        # Generate product key (simple hash based on URL and name)
        import hashlib
        from datetime import datetime
        product_name = self.extract_field(content, 'name') or ''
        url = result.get('url', '')
        product_key = hashlib.md5(f"{url}_{product_name}".encode()).hexdigest()[:12]

        # Format scraped_at as ISO datetime string
        scraped_at_timestamp = result.get('timestamp', result.get('scraped_at', 0))
        if isinstance(scraped_at_timestamp, (int, float)):
            # Convert Unix timestamp to ISO datetime
            try:
                scraped_at_iso = datetime.fromtimestamp(scraped_at_timestamp).isoformat()
            except (ValueError, OSError):
                scraped_at_iso = datetime.now().isoformat()
        else:
            scraped_at_iso = scraped_at_iso = datetime.now().isoformat()

        # Clean and filter images
        raw_images = self.extract_multiple_fields(content, 'images')
        images = self._clean_images(raw_images, self._extract_domain(result.get('url', '')))

        # Generate description from specifications if no explicit description
        description = self.extract_field(content, 'description')
        if not description:
            specifications = self.extract_multiple_fields(content, 'specifications')
            description = self._generate_description_from_specs(specifications)

        # Determine retailer from domain
        retailer = self._extract_retailer(self._extract_domain(result.get('url', '')))

        structured_data = {
            'name': product_name.replace(' - ไทวัสดุ', '').strip(),
            'retailer': retailer,
            'url': result.get('url', ''),
            'current_price': current_price,
            'original_price': original_price,
            'product_key': product_key,
            'brand': self.extract_field(content, 'brand'),
            'model': self.extract_field(content, 'model'),
            'sku': self.extract_field(content, 'sku'),
            'category': self.extract_field(content, 'category'),
            'volume': self.extract_field(content, 'volume'),
            'dimensions': self.extract_field(content, 'dimensions'),
            'material': self.extract_field(content, 'material'),
            'color': self.extract_field(content, 'color'),
            'images': images,
            'description': description,
            'scraped_at': scraped_at_iso,
            'has_discount': has_discount,
            'discount_percent': discount_percent,
            'discount_amount': discount_amount
        }

        # Clean up empty values
        return self._remove_empty_values(structured_data)

    def _create_empty_result(self, url: str) -> Dict[str, Any]:
        """Create an empty result structure for failed scrapes."""
        return {
            'url': url,
            'success': False,
            'name': None,
            'retailer': None,
            'current_price': None,
            'original_price': None,
            'product_key': None,
            'brand': None,
            'model': None,
            'sku': None,
            'category': None,
            'volume': None,
            'dimensions': None,
            'material': None,
            'color': None,
            'images': [],
            'description': None,
            'scraped_at': 0,
            'has_discount': False,
            'discount_percent': 0,
            'discount_amount': 0
        }

    def _extract_price(self, price_str: Optional[str]) -> Optional[int]:
        """Extract price as integer from string."""
        if not price_str:
            return None

        # Remove currency symbols, commas, and whitespace
        price_clean = re.sub(r'[฿THBbaht,\s]', '', price_str)
        price_clean = re.sub(r'[^\d.]', '', price_clean)

        try:
            return int(float(price_clean)) if price_clean else None
        except (ValueError, TypeError):
            return None

    def _clean_images(self, raw_images: List[str], domain: str) -> List[str]:
        """Clean and filter image URLs."""
        if not raw_images:
            return []

        cleaned_images = []
        for img in raw_images:
            if not img or len(img) < 5:
                continue

            # Skip UI icons, logos, and small images
            skip_patterns = [
                r'svg', r'logo', r'icon', r'header', r'footer',
                r'chat', r'social', r'clear', r'search', r'location',
                r'profile', r'cart', r'menu', r'banner'
            ]

            if any(re.search(pattern, img.lower()) for pattern in skip_patterns):
                continue

            # Convert relative URLs to absolute
            if img.startswith('/'):
                img = f"https://{domain}{img}"
            elif not img.startswith(('http://', 'https://')):
                continue

            # Keep only the first 5 relevant images
            if len(cleaned_images) >= 5:
                break

            cleaned_images.append(img)

        return cleaned_images

    def _generate_description_from_specs(self, specifications: List[str]) -> str:
        """Generate a concise description from specifications."""
        if not specifications:
            return ""

        # Filter for meaningful specs that can form a description
        meaningful_specs = []
        for spec in specifications[:10]:  # Limit to first 10 specs
            if len(spec) > 20 and not spec.startswith('http'):
                clean_spec = re.sub(r'\s+', ' ', spec).strip()
                if clean_spec:
                    meaningful_specs.append(clean_spec)

        # Create a concise description (max 300 characters)
        if meaningful_specs:
            description = ' '.join(meaningful_specs[:3])
            return description[:300] + "..." if len(description) > 300 else description

        return ""

    def _extract_retailer(self, domain: str) -> str:
        """Extract retailer name from domain."""
        domain_mapping = {
            'thaiwatsadu.com': 'Thai Watsadu',
            'scrapeme.live': 'ScrapeMe',
            'powerbuy.co.th': 'Power Buy',
            'homepro.co.th': 'HomePro',
            'central.co.th': 'Central',
            'robinson.co.th': 'Robinson'
        }

        for domain_pattern, retailer in domain_mapping.items():
            if domain_pattern in domain:
                return retailer

        # Default: extract from domain name
        if '.' in domain:
            return domain.split('.')[0].title()

        return domain

    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc
        except:
            return ''

    def _calculate_confidence(self, content: str) -> float:
        """Calculate confidence score for the extraction."""
        if not content:
            return 0.0

        score = 0.0
        total_checks = 0

        # Check for product indicators
        checks = [
            (r'<title>', 0.1),
            (r'<h1', 0.1),
            (r'price|ราคา|฿', 0.2),
            (r'product|สินค้า|สินค้า', 0.2),
            (r'add to cart|เพิ่มในตะกร้า|ซื้อ', 0.2),
            (r'sku|รหัสสินค้า|model', 0.1),
            (r'brand|แบรนด์|ยี่ห้อ', 0.1)
        ]

        for pattern, weight in checks:
            total_checks += weight
            if re.search(pattern, content, re.IGNORECASE):
                score += weight

        return min(score / total_checks if total_checks > 0 else 0.0, 1.0)

    def _remove_empty_values(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove empty or None values from nested dictionary."""
        if isinstance(data, dict):
            return {
                k: self._remove_empty_values(v)
                for k, v in data.items()
                if v is not None and v != '' and v != []
            }
        elif isinstance(data, list):
            return [self._remove_empty_values(item) for item in data if item is not None and item != '']
        else:
            return data

    def format_results(self, results: List[Dict[str, Any]], format_type: str = "structured") -> str:
        """Format results in the specified format."""
        processed_results = [self.process_product_page(result) for result in results]

        if format_type == "structured":
            return json.dumps(processed_results, indent=2, ensure_ascii=False)
        elif format_type == "summary":
            return self._format_summary(processed_results)
        elif format_type == "csv":
            return self._format_csv(processed_results)
        else:
            return json.dumps(processed_results, indent=2, ensure_ascii=False)

    def _format_summary(self, results: List[Dict[str, Any]]) -> str:
        """Format results as a summary."""
        summary = {
            'total_urls': len(results),
            'successful': sum(1 for r in results if r.get('success', False)),
            'failed': sum(1 for r in results if not r.get('success', False)),
            'products_found': len([r for r in results if r.get('product', {}).get('name')]),
            'results': results
        }
        return json.dumps(summary, indent=2, ensure_ascii=False)

    def _format_csv(self, results: List[Dict[str, Any]]) -> str:
        """Format results as CSV matching the exact data structure."""
        import csv
        import io

        output = io.StringIO()

        # CSV headers matching your exact structure
        headers = [
            'name', 'retailer', 'url', 'current_price', 'original_price',
            'product_key', 'brand', 'model', 'sku', 'category', 'volume',
            'dimensions', 'material', 'color', 'images', 'description',
            'scraped_at', 'has_discount', 'discount_percent', 'discount_amount'
        ]

        writer = csv.DictWriter(output, fieldnames=headers)
        writer.writeheader()

        for result in results:
            # Convert images list to string
            images_str = '; '.join(result.get('images', [])) if result.get('images') else ''

            writer.writerow({
                'name': result.get('name', ''),
                'retailer': result.get('retailer', ''),
                'url': result.get('url', ''),
                'current_price': result.get('current_price', ''),
                'original_price': result.get('original_price', ''),
                'product_key': result.get('product_key', ''),
                'brand': result.get('brand', ''),
                'model': result.get('model', ''),
                'sku': result.get('sku', ''),
                'category': result.get('category', ''),
                'volume': result.get('volume', ''),
                'dimensions': result.get('dimensions', ''),
                'material': result.get('material', ''),
                'color': result.get('color', ''),
                'images': images_str,
                'description': result.get('description', ''),
                'scraped_at': result.get('scraped_at', ''),
                'has_discount': result.get('has_discount', False),
                'discount_percent': result.get('discount_percent', ''),
                'discount_amount': result.get('discount_amount', '')
            })

        return output.getvalue()

def fix_output_file(input_file: str, output_file: str = None) -> str:
    """Fix an existing output file by reformatting it."""
    if output_file is None:
        output_file = input_file.replace('.json', '_fixed.json')

    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    formatter = OutputFormatter()
    formatted_data = formatter.format_results(data if isinstance(data, list) else [data], "structured")

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(formatted_data)

    return output_file

def save_to_organized_structure(data: List[Dict[str, Any]], use_case: str = "by_url", format_type: str = "json") -> str:
    """Save formatted data to organized output structure.

    Args:
        data: List of formatted product data
        use_case: Type of organization ("by_url" or "by_list")
        format_type: Output format ("json" or "csv")

    Returns:
        Path to saved file
    """
    from datetime import datetime

    formatter = OutputFormatter()
    formatted_data = [formatter.process_product_page(item) for item in data] if isinstance(data[0], dict) and 'content' in data[0] else data

    # Create output directory
    base_output_dir = "/Users/tachongrak/Projects/Optus/apps/output"
    output_dir = f"{base_output_dir}/{use_case}"
    os.makedirs(output_dir, exist_ok=True)

    # Generate filename based on use case
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_ext = "csv" if format_type == "csv" else "json"

    if use_case == "by_url":
        # Organize by domain
        domains = set()
        for item in formatted_data:
            if item.get('url'):
                from urllib.parse import urlparse
                domain = urlparse(item['url']).netloc
                domains.add(domain)

        if len(domains) == 1:
            # Single domain - organize by domain
            domain = list(domains)[0].replace('.', '_')
            domain_dir = f"{output_dir}/{domain}"
            os.makedirs(domain_dir, exist_ok=True)
            output_file = f"{domain_dir}/scraped_{timestamp}.{file_ext}"
        else:
            # Multiple domains - save in by_url root
            output_file = f"{output_dir}/multiple_domains_{timestamp}.{file_ext}"

    elif use_case == "by_list":
        # Organize by list/date
        output_file = f"{output_dir}/product_list_{timestamp}.{file_ext}"

    else:
        # Default organization
        output_file = f"{output_dir}/scraped_data_{timestamp}.{file_ext}"

    # Save the data
    if format_type == "csv":
        # Use CSV formatting
        csv_data = formatter._format_csv(formatted_data)
        with open(output_file, 'w', encoding='utf-8', newline='') as f:
            f.write(csv_data)
    else:
        # Use JSON formatting (default)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(formatted_data, f, indent=2, ensure_ascii=False)

    return output_file

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python output_formatter.py <input_file> [output_file]")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    try:
        result_file = fix_output_file(input_file, output_file)
        print(f"Fixed output saved to: {result_file}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)