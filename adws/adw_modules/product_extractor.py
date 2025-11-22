"""
Product data extraction module for e-commerce websites.

This module provides extraction strategies and utilities for extracting
product information from various e-commerce website structures.
"""

import re
import json
from typing import Dict, List, Any, Optional, Union
from urllib.parse import urljoin, urlparse

from product_schemas import ProductData, PriceParser, normalize_product_data


class ProductExtractor:
    """Extracts product data from e-commerce web pages."""

    def __init__(self, base_url: str = None):
        """Initialize the extractor with base URL for resolving relative URLs."""
        self.base_url = base_url

    def extract_from_html(self, html_content: str, url: str = None) -> Optional[ProductData]:
        """Extract product data from HTML content.

        Args:
            html_content: HTML content of the product page
            url: URL of the product page (for context)

        Returns:
            ProductData object or None if extraction failed
        """
        if not html_content:
            return None

        # Set base URL if provided
        if url:
            self.base_url = url

        # Extract all product information
        raw_data = {}

        # Extract basic product information
        # Extract retailer from URL
        raw_data['retailer'] = self._extract_retailer_from_url(url)
        raw_data['name'] = self._extract_product_name(html_content)
        raw_data['description'] = self._extract_description(html_content)
        raw_data['brand'] = self._extract_brand(html_content)
        raw_data['model'] = self._extract_model(html_content)
        raw_data['sku'] = self._extract_sku(html_content)
        raw_data['category'] = self._extract_category(html_content)

        # Extract pricing information
        current_price, original_price = self._extract_prices(html_content)
        raw_data['current_price'] = current_price
        raw_data['original_price'] = original_price

        # Extract product specifications
        raw_data['volume'] = self._extract_volume(html_content)
        raw_data['dimensions'] = self._extract_dimensions(html_content)
        raw_data['material'] = self._extract_material(html_content)
        raw_data['color'] = self._extract_color(html_content)

        # Extract images
        raw_data['images'] = self._extract_images(html_content)

        # Add URL
        raw_data['url'] = url or self.base_url

        # Normalize and validate data
        normalized_data = normalize_product_data(raw_data)

        # Create ProductData object
        try:
            return ProductData(**normalized_data)
        except Exception as e:
            print(f"Error creating ProductData: {e}")
            return None

    def extract_from_json_ld(self, html_content: str) -> Dict[str, Any]:
        """Extract product data from JSON-LD structured data.

        Args:
            html_content: HTML content containing JSON-LD

        Returns:
            Dictionary with extracted product data
        """
        json_ld_data = {}

        # Find JSON-LD scripts
        json_ld_pattern = r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>'
        matches = re.findall(json_ld_pattern, html_content, re.DOTALL | re.IGNORECASE)

        for match in matches:
            try:
                data = json.loads(match.strip())
                if isinstance(data, dict):
                    # Handle single object
                    if data.get('@type') in ['Product', 'ProductModel']:
                        json_ld_data.update(self._parse_json_ld_product(data))
                    # Handle array of objects
                    elif isinstance(data.get('@graph'), list):
                        for item in data['@graph']:
                            if item.get('@type') in ['Product', 'ProductModel']:
                                json_ld_data.update(self._parse_json_ld_product(item))
            except json.JSONDecodeError:
                continue

        return json_ld_data

    def _parse_json_ld_product(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse product data from JSON-LD structure."""
        parsed = {}

        # Basic fields
        parsed['name'] = data.get('name')
        parsed['description'] = data.get('description')
        parsed['brand'] = data.get('brand', {}).get('name') if isinstance(data.get('brand'), dict) else data.get('brand')
        parsed['model'] = data.get('model')
        parsed['sku'] = data.get('sku')
        parsed['category'] = data.get('category', [None])[0] if isinstance(data.get('category'), list) else data.get('category')

        # Pricing
        offers = data.get('offers')
        if isinstance(offers, dict):
            parsed['current_price'] = offers.get('price')
            parsed['original_price'] = offers.get('highPrice') or offers.get('price') if offers.get('priceSpecification', {}).get('highPrice') else None
        elif isinstance(offers, list) and offers:
            offer = offers[0]  # Take first offer
            parsed['current_price'] = offer.get('price')
            parsed['original_price'] = offer.get('highPrice')

        # Images
        images = data.get('image')
        if isinstance(images, list):
            parsed['images'] = images
        elif isinstance(images, str):
            parsed['images'] = [images]

        return parsed

    def _extract_product_name(self, html_content: str) -> Optional[str]:
        """Extract product name from HTML."""
        # Common selectors for product name
        patterns = [
            r'<h1[^>]*class="[^"]*product[^"]*"[^>]*>(.*?)</h1>',
            r'<h1[^>]*>(.*?)</h1>',
            r'<title[^>]*>(.*?)</title>',
            r'<meta[^>]*property=["\']og:title["\'][^>]*content=["\']([^"\']+)["\']',
            r'<div[^>]*class="[^"]*product-title[^"]*"[^>]*>(.*?)</div>',
            r'<span[^>]*class="[^"]*product-name[^"]*"[^>]*>(.*?)</span>',
        ]

        for pattern in patterns:
            match = re.search(pattern, html_content, re.DOTALL | re.IGNORECASE)
            if match:
                name = self._clean_text(match.group(1))
                if name and len(name) > 3:  # Minimum length check
                    return name

        return None

    def _extract_description(self, html_content: str) -> Optional[str]:
        """Extract product description from HTML."""
        patterns = [
            r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']+)["\']',
            r'<meta[^>]*property=["\']og:description["\'][^>]*content=["\']([^"\']+)["\']',
            r'<div[^>]*class="[^"]*description[^"]*"[^>]*>(.*?)</div>',
            r'<div[^>]*class="[^"]*product-description[^"]*"[^>]*>(.*?)</div>',
            r'<p[^>]*class="[^"]*description[^"]*"[^>]*>(.*?)</p>',
        ]

        for pattern in patterns:
            match = re.search(pattern, html_content, re.DOTALL | re.IGNORECASE)
            if match:
                desc = self._clean_text(match.group(1))
                if desc and len(desc) > 10:
                    return desc

        return None

    def _extract_brand(self, html_content: str) -> Optional[str]:
        """Extract product brand from HTML with JSON contamination prevention."""
        patterns = [
            r'<meta[^>]*property=["\']og:brand["\'][^>]*content=["\']([^"\']+)["\']',
            r'<span[^>]*class="[^"]*brand[^"]*"[^>]*>(.*?)</span>',
            r'<div[^>]*class="[^"]*brand[^"]*"[^>]*>(.*?)</div>',
            r'ยี่ห้อ[:\s]*([^\n<]+)',
            r'แบรนด์[:\s]*([^\n<]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                brand = self._clean_text(match.group(1))
                if brand and len(brand) > 1:
                    # Additional sanitization to prevent JSON contamination
                    brand = self._sanitize_brand_field(brand)
                    if brand:
                        return brand

        return None

    def _extract_model(self, html_content: str) -> Optional[str]:
        """Extract product model from HTML with contamination prevention."""
        patterns = [
            r'<span[^>]*class="[^"]*model[^"]*"[^>]*>(.*?)</span>',
            r'รุ่น[:\s]*([^\n<]+)',
            r'โมเดล[:\s]*([^\n<]+)',
            r'Model[:\s]*([^\n<]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                model = self._clean_text(match.group(1))
                if model and len(model) > 1:
                    # Additional sanitization to prevent JSON contamination
                    model = self._sanitize_text_field(model, max_length=200)
                    if model:
                        return model

        return None

    def _extract_sku(self, html_content: str) -> Optional[str]:
        """Extract product SKU from HTML."""
        patterns = [
            r'<span[^>]*class="[^"]*sku[^"]*"[^>]*>(.*?)</span>',
            r'<meta[^>]*property=["\']product:retailer_item_id["\'][^>]*content=["\']([^"\']+)["\']',
            r'รหัสสินค้า[:\s]*([^\n<]+)',
            r'SKU[:\s]*([^\n<]+)',
            r'Article No[:\s]*([^\n<]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                sku = self._clean_text(match.group(1))
                if sku and len(sku) > 1:
                    # Additional sanitization to prevent JSON contamination
                    sku = self._sanitize_text_field(sku)
                    if sku:
                        return sku

        # Try to extract from URL
        if self.base_url:
            url_patterns = [
                r'/product/([^/]+)',
                r'/item/([^/]+)',
                r'/p/([^/]+)',
                r'sku[=/]([^/&]+)',
            ]
            for pattern in url_patterns:
                match = re.search(pattern, self.base_url, re.IGNORECASE)
                if match:
                    return match.group(1)

        return None

    def _extract_category(self, html_content: str) -> Optional[str]:
        """Extract product category from HTML."""
        patterns = [
            r'<nav[^>]*class="[^"]*breadcrumb[^"]*"[^>]*>.*?</nav>',
            r'<div[^>]*class="[^"]*breadcrumb[^"]*"[^>]*>.*?</div>',
            r'หมวดหมู่[:\s]*([^\n<]+)',
            r'Category[:\s]*([^\n<]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, html_content, re.DOTALL | re.IGNORECASE)
            if match:
                category = self._clean_text(match.group(1))
                if category and len(category) > 1:
                    # If it's breadcrumb, take the last part
                    if '>' in category:
                        parts = [p.strip() for p in category.split('>')]
                        category = parts[-1] if parts else category
                    return category

        return None

    def _extract_prices(self, html_content: str) -> tuple[Optional[float], Optional[float]]:
        """Extract current and original prices from HTML."""
        # Extract price information
        price_patterns = [
            r'<span[^>]*class="[^"]*price[^"]*"[^>]*>(.*?)</span>',
            r'<div[^>]*class="[^"]*price[^"]*"[^>]*>(.*?)</div>',
            r'<meta[^>]*property=["\']product:price:amount["\'][^>]*content=["\']([^"\']+)["\']',
            r'<meta[^>]*property=["\']og:price:amount["\'][^>]*content=["\']([^"\']+)["\']',
        ]

        all_price_text = []
        for pattern in price_patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            all_price_text.extend(matches)

        # Also look for prices in text content
        price_text_patterns = [
            r'ราคา[:\s]*([฿$]?[\d,]+\.?\d*)',
            r'Price[:\s]*([฿$]?[\d,]+\.?\d*)',
            r'([฿$]?[\d,]+\.?\d*)\s*บาท',
        ]

        for pattern in price_text_patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            all_price_text.extend(matches)

        # Original price patterns
        original_price_patterns = [
            r'<span[^>]*class="[^"]*original[^"]*price[^"]*"[^>]*>(.*?)</span>',
            r'<span[^>]*class="[^"]*was[^"]*"[^>]*>(.*?)</span>',
            r'<div[^>]*class="[^"]*original-price[^"]*"[^>]*>(.*?)</div>',
            r'ราคาปกติ[:\s]*([฿$]?[\d,]+\.?\d*)',
            r'ปกติ[:\s]*([฿$]?[\d,]+\.?\d*)',
        ]

        original_prices = []
        for pattern in original_price_patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            original_prices.extend(matches)

        # Parse all found prices
        all_prices = [PriceParser.parse_price(price) for price in all_price_text]
        all_prices = [p for p in all_prices if p is not None]

        orig_prices = [PriceParser.parse_price(price) for price in original_prices]
        orig_prices = [p for p in orig_prices if p is not None]

        current_price = None
        original_price = None

        if orig_prices:
            original_price = max(orig_prices)  # Highest price is likely original price
            # Current price is the lowest price that's not the original
            other_prices = [p for p in all_prices if p != original_price]
            current_price = min(other_prices) if other_prices else None
        elif all_prices:
            # If no clear original price, use min/max logic
            if len(all_prices) >= 2:
                original_price = max(all_prices)
                current_price = min(all_prices)
            else:
                current_price = all_prices[0]

        return current_price, original_price

    def _extract_volume(self, html_content: str) -> Optional[str]:
        """Extract product volume/capacity from HTML."""
        patterns = [
            r'(\d+(?:\.\d+)?)\s*(?:ลิตร|L|l)(?:\s*ตัน)?',
            r'(\d+(?:\.\d+)?)\s*(?:มล|ml|ML)',
            r'(\d+(?:\.\d+)?)\s*(?:แกลลอน|gallon)',
            r'ความจุ[:\s]*([^\n<]+)',
            r'Volume[:\s]*([^\n<]+)',
            r'Capacity[:\s]*([^\n<]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                volume = self._clean_text(match.group(1) if match.groups() else match.group(0))
                if volume:
                    return volume

        return None

    def _extract_dimensions(self, html_content: str) -> Optional[str]:
        """Extract product dimensions from HTML."""
        patterns = [
            r'(\d+(?:\.\d+)?\s*[x×]\s*\d+(?:\.\d+)?\s*[x×]\s*\d+(?:\.\d+)?)\s*(?:ซม|cm|mm|m)',
            r'ขนาด[:\s]*([^\n<]+)',
            r'Dimension[:\s]*([^\n<]+)',
            r'Size[:\s]*([^\n<]+)',
            r'(\d+(?:\.\d+)?)\s*ซม',
        ]

        for pattern in patterns:
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                dimensions = self._clean_text(match.group(1) if match.groups() else match.group(0))
                if dimensions:
                    return dimensions

        return None

    def _extract_material(self, html_content: str) -> Optional[str]:
        """Extract product material from HTML."""
        patterns = [
            r'วัสดุ[:\s]*([^\n<]+)',
            r'Material[:\s]*([^\n<]+)',
            r'ผลิตจาก[:\s]*([^\n<]+)',
            r'เนื้อวัสดุ[:\s]*([^\n<]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                material = self._clean_text(match.group(1))
                if material and len(material) > 1:
                    return material

        return None

    def _extract_color(self, html_content: str) -> Optional[str]:
        """Extract product color from HTML."""
        patterns = [
            r'สี[:\s]*([^\n<]+)',
            r'Color[:\s]*([^\n<]+)',
            r'สีแบบ[:\s]*([^\n<]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                color = self._clean_text(match.group(1))
                if color and len(color) > 1:
                    return color

        return None

    def _extract_images(self, html_content: str) -> List[str]:
        """Extract product image URLs from HTML."""
        images = []

        # Product image patterns
        patterns = [
            r'<img[^>]*class="[^"]*product[^"]*image[^"]*"[^>]*src=["\']([^"\']+)["\']',
            r'<img[^>]*class="[^"]*product-image[^"]*"[^>]*src=["\']([^"\']+)["\']',
            r'<meta[^>]*property=["\']og:image["\'][^>]*content=["\']([^"\']+)["\']',
            r'<meta[^>]*property=["\']product:image["\'][^>]*content=["\']([^"\']+)["\']',
            r'<img[^>]*src=["\']([^"\']*product[^"\']*)["\']',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            for match in matches:
                img_url = self._resolve_url(match.strip())
                if img_url and img_url not in images:
                    images.append(img_url)

        # Also check JSON-LD for images
        json_ld_data = self.extract_from_json_ld(html_content)
        if 'images' in json_ld_data:
            for img_url in json_ld_data['images']:
                resolved_url = self._resolve_url(img_url)
                if resolved_url and resolved_url not in images:
                    images.append(resolved_url)

        return images[:10]  # Limit to 10 images

    def _resolve_url(self, url: str) -> Optional[str]:
        """Resolve relative URL to absolute URL."""
        if not url:
            return None

        # Skip data URLs and invalid URLs
        if url.startswith(('data:', 'mailto:', 'tel:', 'javascript:')):
            return None

        # If already absolute, return as is
        if url.startswith(('http://', 'https://')):
            return url

        # Resolve relative URL
        if self.base_url:
            try:
                return urljoin(self.base_url, url)
            except Exception:
                pass

        return url

    def _extract_retailer_from_url(self, url: str) -> str:
        """Extract retailer name from URL domain."""
        if not url:
            return "Unknown Retailer"

        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()

            # Remove www. prefix
            domain = domain.replace('www.', '')

            # Known retailer mappings
            retailer_mappings = {
                'thaiwatsadu.com': 'Thai Watsadu',
                'homepro.co.th': 'HomePro',
                'lazada.co.th': 'Lazada',
                'shopee.co.th': 'Shopee',
                'central.co.th': 'Central',
                'powerbuy.co.th': 'Power Buy',
                'jaymart.co.th': 'Jaymart',
                'banana-it': 'Banana IT',
                'advice.co.th': 'Advice',
            }

            for domain_pattern, retailer in retailer_mappings.items():
                if domain_pattern in domain:
                    return retailer

            # Extract domain name as fallback
            domain_parts = domain.split('.')
            if len(domain_parts) >= 2:
                return domain_parts[-2].title()

            return domain.title()

        except Exception:
            return "Unknown Retailer"

    def _clean_text(self, text: str) -> str:
        """Clean extracted text by removing HTML tags and extra whitespace."""
        if not text:
            return ""

        # Remove HTML tags
        text = re.sub(r'<[^>]+>', ' ', text)

        # Replace HTML entities
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')

        # Clean whitespace
        text = ' '.join(text.split())

        return text.strip()

    def _sanitize_text_field(self, text: str, max_length: int = 100) -> Optional[str]:
        """Generic field sanitization to prevent JSON contamination and ensure clean data."""
        if not text:
            return None

        # Remove JSON-like structures and objects
        text = re.sub(r'\{[^}]*\}', '', text)
        text = re.sub(r'\[[^\]]*\]', '', text)

        # Remove common JSON keys and values
        json_patterns = [
            r'"name"\s*:\s*"[^"]*"',
            r'"type"\s*:\s*"[^"]*"',
            r'"@[^"]*"\s*:\s*"[^"]*"',
            r'"[^"]*"\s*:\s*"[^"]*"',
            r'true|false|null',
            r'\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}',  # ISO dates
        ]

        for pattern in json_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)

        # Remove excessive punctuation and special characters
        text = re.sub(r'[{}[\]"\',:;\\]', '', text)

        # Clean whitespace again
        text = ' '.join(text.split())

        # Validate the cleaned text
        if (text and
            len(text) > 1 and
            len(text) <= max_length and
            not text.lower().startswith(('http', 'www', 'data:')) and
            not any(char in text for char in ['{', '}', '[', ']', '"', "'", '\\'])):
            return text.strip()

        return None

    def _sanitize_brand_field(self, brand: str) -> Optional[str]:
        """Sanitize brand field to prevent JSON contamination and ensure clean data."""
        return self._sanitize_text_field(brand, max_length=100)


# Retailer-specific extractors
class ThaiWatsaduExtractor(ProductExtractor):
    """Specialized extractor for Thai Watsadu website."""

    def extract_from_html(self, html_content: str, url: str = None) -> Optional[ProductData]:
        """Extract product data specifically from Thai Watsadu."""
        # First try the general extraction
        product = super().extract_from_html(html_content, url)

        if product:
            # Thai Watsadu specific enhancements
            # Extract SKU from URL pattern (prioritize URL extraction over HTML extraction)
            if url:
                sku_match = re.search(r'/sku/(\d+)', url)
                if sku_match:
                    # Clean and validate the SKU from URL
                    url_sku = self._sanitize_text_field(sku_match.group(1), max_length=50)
                    if url_sku and url_sku.isdigit():
                        product.sku = url_sku

        return product


class HomeProExtractor(ProductExtractor):
    """Specialized extractor for HomePro website."""

    def extract_from_html(self, html_content: str, url: str = None) -> Optional[ProductData]:
        """Extract product data specifically from HomePro."""
        # First try the general extraction
        product = super().extract_from_html(html_content, url)

        # Add HomePro-specific logic here if needed
        return product


def get_extractor(url: str) -> ProductExtractor:
    """Get the appropriate extractor for the given URL."""
    domain = urlparse(url).netloc.lower()

    if 'thaiwatsadu.com' in domain:
        return ThaiWatsaduExtractor(url)
    elif 'homepro.co.th' in domain:
        return HomeProExtractor(url)
    else:
        return ProductExtractor(url)

    def _extract_retailer_from_url(self, url: str) -> str:
        """Extract retailer name from URL domain."""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = parsed.netloc.lower()

            # Remove www. prefix
            domain = domain.replace('www.', '')

            # Known retailer mappings
            retailer_mappings = {
                'thaiwatsadu.com': 'Thai Watsadu',
                'homepro.co.th': 'HomePro',
                'lazada.co.th': 'Lazada',
                'shopee.co.th': 'Shopee',
                'central.co.th': 'Central',
                'powerbuy.co.th': 'Power Buy',
                'jaymart.co.th': 'Jaymart',
                'banana-it': 'Banana IT',
                'advice.co.th': 'Advice',
            }

            for domain_pattern, retailer in retailer_mappings.items():
                if domain_pattern in domain:
                    return retailer

            # Extract domain name as fallback
            domain_parts = domain.split('.')
            if len(domain_parts) >= 2:
                return domain_parts[-2].title()

            return domain.title()

        except Exception:
            return "Unknown Retailer"
