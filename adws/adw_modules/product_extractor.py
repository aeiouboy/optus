"""
Product data extraction module for e-commerce websites.

This module provides extraction strategies and utilities for extracting
product information from various e-commerce website structures.
"""

import re
import json
from typing import Dict, List, Any, Optional, Union
from urllib.parse import urljoin, urlparse

from .product_schemas import ProductData, PriceParser, normalize_product_data


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

        # Apply systematic field sanitization
        if raw_data['brand']:
            raw_data['brand'] = self._sanitize_brand_field(raw_data['brand'])

        if raw_data['model']:
            # Prevent HTML element names as model values
            clean_model = self._sanitize_text_field(raw_data['model'], max_length=50)
            # Reject common HTML element names
            html_elements = ['html', 'body', 'div', 'span', 'section', 'article', 'header', 'footer']
            if clean_model and clean_model.lower() not in html_elements:
                raw_data['model'] = clean_model
            else:
                raw_data['model'] = None

        if raw_data['sku']:
            raw_data['sku'] = self._sanitize_sku_field(raw_data['sku'])

        if raw_data['color']:
            raw_data['color'] = self._sanitize_color_field(raw_data['color'])

        if raw_data['dimensions']:
            raw_data['dimensions'] = self._sanitize_dimensions_field(raw_data['dimensions'])

        if raw_data['material']:
            raw_data['material'] = self._sanitize_material_field(raw_data['material'])

        if raw_data['volume']:
            raw_data['volume'] = self._sanitize_text_field(raw_data['volume'], max_length=50)

        if raw_data['category']:
            raw_data['category'] = self._sanitize_text_field(raw_data['category'], max_length=100)

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
                # Use group 1 if available, otherwise group 0
                val = match.group(1) if match.re.groups > 0 else match.group(0)
                name = self._clean_text(val)

                # Filter out retailer names and site branding
                if name:
                    # Common retailer names and site branding to filter out
                    retailer_names = [
                        'megahome', 'mega home', 'homepro', 'home pro', 'boonthavorn', 'dohome', 'do home',
                        'global house', 'thai watsadu', 'watsadu', 'power buy', 'powerbuy',
                        'lazada', 'shopee', 'central', 'jaymart', 'Vivin', 'banner'
                    ]

                    # Check if the name is just a retailer name (case insensitive)
                    name_lower = name.lower().strip()
                    if name_lower in retailer_names:
                        continue  # Skip this pattern and try the next one

                    # Check if the name starts with a retailer name and clean it
                    for retailer in retailer_names:
                        if name_lower.startswith(retailer + ' '):
                            # Remove retailer prefix
                            name = name[len(retailer):].strip()
                            if not name or len(name) < 3:
                                continue  # Skip if name becomes too short after cleaning
                            break

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
                # Use group 1 if available, otherwise group 0
                val = match.group(1) if match.re.groups > 0 else match.group(0)
                desc = self._clean_text(val)
                if desc and len(desc) > 10:
                    return desc

        return None

    def _extract_brand(self, html_content: str) -> Optional[str]:
        """Extract product brand from HTML with enhanced patterns and JSON-LD support."""
        # First try JSON-LD extraction
        json_ld_data = self.extract_from_json_ld(html_content)
        if json_ld_data.get('brand'):
            brand_value = json_ld_data['brand']
            if isinstance(brand_value, dict):
                brand_value = brand_value.get('name')
            if brand_value:
                clean_brand = self._sanitize_brand_field(str(brand_value))
                if clean_brand:
                    return clean_brand

        # HTML patterns for brand extraction
        patterns = [
            r'<meta[^>]*property=["\']og:brand["\'][^>]*content=["\']([^"\']+)["\']',
            r'<meta[^>]*name=["\']brand["\'][^>]*content=["\']([^"\']+)["\']',
            r'<span[^>]*class="[^"]*brand[^"]*"[^>]*>(.*?)</span>',
            r'<div[^>]*class="[^"]*brand[^"]*"[^>]*>(.*?)</div>',
            r'<a[^>]*class="[^"]*brand[^"]*"[^>]*>(.*?)</a>',
            r'ยี่ห้อ[:\s]*([^\n<]+)',
            r'แบรนด์[:\s]*([^\n<]+)',
            r'Brand[:\s]*([^\n<]+)',
            r'Manufacturer[:\s]*([^\n<]+)',
            # Thai variations
            r'ผู้ผลิต[:\s]*([^\n<]+)',
            r'เครื่องหมาย[:\s]*([^\n<]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                # Use group 1 if available, otherwise group 0
                val = match.group(1) if match.re.groups > 0 else match.group(0)
                brand = self._clean_text(val)
                if brand and len(brand) > 1:
                    # Additional sanitization to prevent contamination
                    clean_brand = self._sanitize_brand_field(brand)
                    if clean_brand:
                        return clean_brand

        # Try to extract from title (first word is often brand)
        title_patterns = [
            r'<title[^>]*>(.*?)</title>',
            r'<h1[^>]*class="[^"]*product-title[^"]*"[^>]*>(.*?)</h1>',
            r'<h1[^>]*>(.*?)</h1>',
        ]

        for pattern in title_patterns:
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                title_text = self._clean_text(match.group(1))
                if title_text:
                    # First word or phrase might be brand
                    words = title_text.split()
                    if len(words) >= 2:
                        potential_brand = ' '.join(words[:2])  # Try first two words
                        clean_brand = self._sanitize_brand_field(potential_brand)
                        if clean_brand and len(clean_brand) >= 3:
                            # Validate it looks like a brand (starts with capital)
                            if clean_brand[0].isupper():
                                return clean_brand

        return None

    def _extract_model(self, html_content: str) -> Optional[str]:
        """Extract product model from HTML with enhanced patterns and contamination prevention."""
        # First try JSON-LD extraction
        json_ld_data = self.extract_from_json_ld(html_content)
        if json_ld_data.get('model'):
            model_value = json_ld_data['model']
            if model_value:
                clean_model = self._sanitize_text_field(str(model_value), max_length=200)
                if clean_model:
                    return clean_model

        # HTML patterns for model extraction
        patterns = [
            r'<span[^>]*class="[^"]*model[^"]*"[^>]*>(.*?)</span>',
            r'<div[^>]*class="[^"]*model[^"]*"[^>]*>(.*?)</div>',
            r'<meta[^>]*property=["\']product:model["\'][^>]*content=["\']([^"\']+)["\']',
            r'<meta[^>]*name=["\']model["\'][^>]*content=["\']([^"\']+)["\']',
            r'รุ่น[:\s]*([^\n<]+)',
            r'โมเดล[:\s]*([^\n<]+)',
            r'Model[:\s]*([^\n<]+)',
            r'Model No[:\s]*([^\n<]+)',
            r'Model Number[:\s]*([^\n<]+)',
            r'Type[:\s]*([^\n<]+)',
            r'แบบ[:\s]*([^\n<]+)',
            r'รหัสแบบ[:\s]*([^\n<]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                # Use group 1 if available, otherwise group 0
                val = match.group(1) if match.re.groups > 0 else match.group(0)
                model = self._clean_text(val)
                if model and len(model) > 1:
                    # Additional sanitization to prevent contamination
                    clean_model = self._sanitize_text_field(model, max_length=200)
                    if clean_model:
                        return clean_model

        # Try to extract model from title and description using regex patterns
        text_sources = []

        # Add title to sources
        title_match = re.search(r'<title[^>]*>(.*?)</title>', html_content, re.IGNORECASE)
        if title_match:
            text_sources.append(self._clean_text(title_match.group(1)))

        h1_match = re.search(r'<h1[^>]*>(.*?)</h1>', html_content, re.IGNORECASE)
        if h1_match:
            text_sources.append(self._clean_text(h1_match.group(1)))

        # Add description to sources
        desc_match = re.search(r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']+)["\']', html_content, re.IGNORECASE)
        if desc_match:
            text_sources.append(self._clean_text(desc_match.group(1)))

        # Model extraction patterns from text
        model_patterns = [
            r'รุ่น\s+([A-Za-z0-9\-\_]+)',
            r'โมเดล\s+([A-Za-z0-9\-\_]+)',
            r'Model[:\s]+([A-Za-z0-9\-\_]+)',
            r'Type[:\s]+([A-Za-z0-9\-\_]+)',
            r'([A-Z]{2,4}-?\d{3,6})',  # Common model pattern like "ABC-1234"
            r'([A-Z][a-z]*-\d+[A-Za-z]*)',  # Pattern like "Product-123X"
        ]

        for text_source in text_sources:
            if text_source:
                for pattern in model_patterns:
                    match = re.search(pattern, text_source, re.IGNORECASE)
                    if match:
                        potential_model = match.group(1).strip()
                        clean_model = self._sanitize_text_field(potential_model, max_length=200)
                        if clean_model and len(clean_model) >= 2:
                            return clean_model

        return None

    def _extract_sku(self, html_content: str) -> Optional[str]:
        """Extract product SKU from HTML with enhanced validation to prevent URL contamination."""
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
                # Use group 1 if available, otherwise group 0
                val = match.group(1) if match.re.groups > 0 else match.group(0)
                sku = self._clean_text(val)
                if sku and len(sku) > 1:
                    # Apply enhanced sanitization
                    clean_sku = self._sanitize_sku_field(sku)
                    if clean_sku:
                        return clean_sku

        # Try to extract from URL (enhanced to extract meaningful product codes)
        if self.base_url:
            url_patterns = [
                r'/product/([^/]+?)(?:/|$)',
                r'/item/([^/]+?)(?:/|$)',
                r'/p/([^/]+?)(?:/|$)',
                r'sku[=/]([^/&]+)',
                r'/(\d{6,})',  # Extract numeric product codes
                r'-([A-Z0-9]{4,})',  # Extract alphanumeric codes at end
            ]
            for pattern in url_patterns:
                match = re.search(pattern, self.base_url, re.IGNORECASE)
                if match:
                    potential_sku = match.group(1).strip()
                    # Validate the extracted URL component is a meaningful SKU
                    if self._is_valid_sku(potential_sku):
                        return potential_sku

        return None

    def _sanitize_sku_field(self, sku: str) -> Optional[str]:
        """Specialized sanitization for SKU field to prevent URL contamination."""
        if not sku:
            return None

        # Apply general sanitization first
        sku = self._sanitize_text_field(sku, max_length=50)
        if not sku:
            return None

        # Additional SKU-specific validation
        if self._is_valid_sku(sku):
            return sku

        return None

    def _is_valid_sku(self, sku: str) -> bool:
        """Validate that SKU is actually a SKU and not a URL or other invalid data."""
        if not sku:
            return False

        # Must be alphanumeric with reasonable length
        if len(sku) < 2 or len(sku) > 50:
            return False

        # Must not contain URLs or domains (more specific patterns)
        sku_lower = sku.lower()
        if (sku_lower.startswith(('http', 'https', 'www')) or
            any(domain in sku_lower for domain in ['.com', '.co.th', '.net', '.org']) or
            '/product/' in sku_lower or
            '/item/' in sku_lower or
            '/category/' in sku_lower or
            '/search/' in sku_lower or
            '/page/' in sku_lower):
            return False

        # Must not contain path separators (except valid SKU patterns with hyphens)
        if '/' in sku or '\\' in sku:
            return False

        # Must not be just numeric dates
        if re.match(r'^\d{4}[-/]\d{2}[-/]\d{2}$', sku):
            return False

        # Allow alphanumeric, hyphens, and underscores
        if re.match(r'^[A-Za-z0-9\-_]+$', sku):
            return True

        return False

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
                # Use group 1 if available, otherwise group 0
                val = match.group(1) if match.re.groups > 0 else match.group(0)
                category = self._clean_text(val)
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
        """Extract product dimensions from HTML with enhanced sanitization."""
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
                    # Apply specialized dimensions sanitization
                    clean_dimensions = self._sanitize_dimensions_field(dimensions)
                    if clean_dimensions:
                        return clean_dimensions

        return None

    def _extract_material(self, html_content: str) -> Optional[str]:
        """Extract product material from HTML with enhanced sanitization."""
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
                    # Apply specialized material sanitization
                    clean_material = self._sanitize_material_field(material)
                    if clean_material:
                        return clean_material

        return None

    def _extract_color(self, html_content: str) -> Optional[str]:
        """Extract product color from HTML with enhanced sanitization."""
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
                    # Apply specialized color sanitization
                    clean_color = self._sanitize_color_field(color)
                    if clean_color:
                        return clean_color

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
                'advice.co.th': 'Advice',
                'banana-it': 'Banana IT',
                'dohome.co.th': 'DoHome',
                'globalhouse.co.th': 'Global House',
                'homepro.co.th': 'HomePro',
                'jaymart.co.th': 'Jaymart',
                'lazada.co.th': 'Lazada',
                'megahome.co.th': 'Mega Home',
                'powerbuy.co.th': 'Power Buy',
                'shopee.co.th': 'Shopee',
                'thaiwatsadu.com': 'Thai Watsadu',
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
        """Enhanced field sanitization to prevent HTML/CSS/JSON contamination and ensure clean data."""
        if not text:
            return None

        # Remove HTML/CSS class names and attributes patterns
        css_patterns = [
            r'class="[^"]*"',
            r'quickInfo-infoLabel-[^"\s]*',
            r'quickInfo-infoValue-[^"\s]*',
            r'style="[^"]*"',
            r'id="[^"]*"',
            r'<label[^>]*>',
            r'</label>',
            r'<span[^>]*>',
            r'</span>',
            r'<div[^>]*>',
            r'</div>',
        ]

        for pattern in css_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)

        # Remove URLs and domain names from text fields
        url_patterns = [
            r'https?://[^\s<>"\']+',
            r'www\.[^\s<>"\']+',
            r'[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?:/[^\s<>"\']*)?',
        ]

        for pattern in url_patterns:
            text = re.sub(pattern, '', text)

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
        text = re.sub(r'[{}[\]"\',:;\\<>]', '', text)

        # Handle trailing comma truncation by removing trailing commas
        text = text.rstrip(',;')

        # Clean whitespace again
        text = ' '.join(text.split())

        # Validate the cleaned text
        if (text and
            len(text) > 1 and
            len(text) <= max_length and
            not text.lower().startswith(('http', 'www', 'data:', 'class=', 'style=')) and
            not any(char in text for char in ['{', '}', '[', ']', '"', "'", '\\', '<', '>', '='])):
            return text.strip()

        return None

    def _sanitize_dimensions_field(self, dimensions: str) -> Optional[str]:
        """Specialized sanitization for dimensions field."""
        if not dimensions:
            return None

        # Remove CSS variables first
        css_variable_patterns = [
            r'var\([^)]+\)',
        ]

        for pattern in css_variable_patterns:
            dimensions = re.sub(pattern, '', dimensions, flags=re.IGNORECASE)

        # Extract dimension patterns more precisely before general sanitization
        dim_patterns = [
            r'(\d+(?:\.\d+)?\s*[x×]\s*\d+(?:\.\d+)?\s*[x×]\s*\d+(?:\.\d+)?)',
            r'(\d+(?:\.\d+)?\s*[x×]\s*\d+(?:\.\d+)?)',
            r'(\d+(?:\.\d+)?)',
        ]

        # First try to extract dimension pattern
        for pattern in dim_patterns:
            match = re.search(pattern, dimensions)
            if match:
                clean_dim = match.group(1).strip()
                if clean_dim and len(clean_dim) <= 200:
                    return clean_dim

        # If no pattern found, apply general sanitization
        dimensions = self._sanitize_text_field(dimensions, max_length=200)
        if dimensions and len(dimensions) <= 200:
            return dimensions

        return None

    def _sanitize_color_field(self, color: str) -> Optional[str]:
        """Specialized sanitization for color field to prevent CSS color codes."""
        if not color:
            return None

        # Remove CSS color codes and patterns first
        css_color_patterns = [
            r'#[0-9a-fA-F]{3,6}',
            r'rgb\([^)]+\)',
            r'rgba\([^)]+\)',
            r'hsl\([^)]+\)',
            r'hsla\([^)]+\)',
            r'color:\s*[^;\\]+',
            r'background:\s*[^;\\]+',
            r'var\([^)]+\)',
        ]

        for pattern in css_color_patterns:
            color = re.sub(pattern, '', color, flags=re.IGNORECASE)

        # Final cleanup and validation
        color = ' '.join(color.split()).strip()

        # Apply general sanitization
        color = self._sanitize_text_field(color, max_length=50)
        if not color:
            return None

        # Validate color is not a code
        if (color and
            len(color) >= 2 and
            len(color) <= 50 and
            not color.startswith(('#', 'rgb', 'hsl')) and
            not re.match(r'^[0-9a-fA-F]{3,6}$', color)):
            return color

        return None

    def _sanitize_material_field(self, material: str) -> Optional[str]:
        """Specialized sanitization for material field."""
        if not material:
            return None

        # Remove common prefixes first
        material = re.sub(r'วัสดุ\s*[:\s]*|Material\s*[:\s]*|ผลิตจาก\s*[:\s]*|เนื้อวัสดุ\s*[:\s]*', '', material, flags=re.IGNORECASE)
        material = ' '.join(material.split()).strip()

        # Apply general sanitization
        material = self._sanitize_text_field(material, max_length=100)
        if not material:
            return None

        if material and len(material) >= 2 and len(material) <= 100:
            return material

        return None

    def _sanitize_brand_field(self, brand: str) -> Optional[str]:
        """Sanitize brand field to prevent JSON contamination and ensure clean data."""
        return self._sanitize_text_field(brand, max_length=100)


# Retailer-specific extractors
class ThaiWatsaduExtractor(ProductExtractor):
    """Specialized extractor for Thai Watsadu website with enhanced sanitization."""

    def extract_from_html(self, html_content: str, url: str = None) -> Optional[ProductData]:
        """Extract product data specifically from Thai Watsadu with enhanced sanitization."""
        # First try the general extraction
        product = super().extract_from_html(html_content, url)

        if product:
            # Thai Watsadu specific enhancements with enhanced SKU validation
            if url:
                sku_match = re.search(r'/sku/(\d+)', url)
                if sku_match:
                    potential_sku = sku_match.group(1).strip()
                    # Enhanced SKU validation
                    if self._is_valid_sku(potential_sku):
                        product.sku = potential_sku

            # Additional Thai Watsadu-specific field cleaning
            if product.dimensions:
                product.dimensions = self._sanitize_dimensions_field(product.dimensions)

            if product.color:
                product.color = self._sanitize_color_field(product.color)

            if product.material:
                product.material = self._sanitize_material_field(product.material)

        return product


class HomeProExtractor(ProductExtractor):
    """Specialized extractor for HomePro website."""

    def extract_from_html(self, html_content: str, url: str = None) -> Optional[ProductData]:
        """Extract product data specifically from HomePro."""
        # First try the general extraction
        product = super().extract_from_html(html_content, url)

        # Add HomePro-specific logic here if needed
        return product


class BoonthavornExtractor(ProductExtractor):
    """Specialized extractor for Boonthavorn website using JSON-LD with enhanced sanitization."""

    def extract_from_html(self, html_content: str, url: str = None) -> Optional[ProductData]:
        """Extract product data specifically from Boonthavorn using JSON-LD and HTML parsing with enhanced sanitization."""
        product = ProductData(url=url)

        # 1. Try to extract from JSON-LD (Structured Data) - Most reliable for basic info
        json_ld_data = self._extract_json_ld(html_content)

        if json_ld_data:
            product.name = json_ld_data.get('name')
            product.description = json_ld_data.get('description')

            # Enhanced brand extraction with sanitization
            brand_value = json_ld_data.get('brand')
            if brand_value:
                if isinstance(brand_value, dict):
                    brand_value = brand_value.get('name')
                if brand_value:
                    clean_brand = self._sanitize_brand_field(str(brand_value))
                    product.brand = clean_brand

            # Enhanced SKU extraction with validation
            sku_value = json_ld_data.get('sku')
            if sku_value:
                clean_sku = self._sanitize_sku_field(str(sku_value))
                product.sku = clean_sku

            offers = json_ld_data.get('offers', {})
            if isinstance(offers, dict):
                price = offers.get('price')
                if price:
                    product.current_price = float(price)
                    product.currency = offers.get('priceCurrency', 'THB')

            image = json_ld_data.get('image')
            if image:
                if isinstance(image, list):
                    product.images = image
                elif isinstance(image, str):
                    product.images = [image]

        # 2. Extract attributes from "Quick Info" section (HTML) with enhanced sanitization
        # Pattern: <label class="quickInfo-infoLabel-WkG">Label</label><label class="quickInfo-infoValue-NpP">Value</label>
        quick_info_pattern = r'class="quickInfo-infoLabel-[^"]+">([^<]+)</label><label class="quickInfo-infoValue-[^"]+">([^<]+)</label>'
        attributes = dict(re.findall(quick_info_pattern, html_content))

        if attributes:
            # Enhanced color extraction with CSS prevention
            if 'สี' in attributes and not product.color:
                color_value = attributes['สี'].strip()
                clean_color = self._sanitize_color_field(color_value)
                product.color = clean_color

            # Enhanced dimensions extraction
            if 'ขนาดสินค้า' in attributes:
                dimensions_value = attributes['ขนาดสินค้า'].strip()
                clean_dimensions = self._sanitize_dimensions_field(dimensions_value)
                product.dimensions = clean_dimensions

            # Enhanced volume extraction
            if 'หน่วยนับ' in attributes:
                volume_value = attributes['หน่วยนับ'].strip()
                clean_volume = self._sanitize_text_field(volume_value, max_length=50)
                product.volume = clean_volume

            # Enhanced brand extraction
            if 'ยี่ห้อ' in attributes and not product.brand:
                brand_value = attributes['ยี่ห้อ'].strip()
                clean_brand = self._sanitize_brand_field(brand_value)
                if clean_brand:
                    product.brand = clean_brand

            # Enhanced SKU extraction with validation
            if 'รหัสสินค้า' in attributes and (not product.sku or product.sku == 'None'):
                sku_value = attributes['รหัสสินค้า'].strip()
                clean_sku = self._sanitize_sku_field(sku_value)
                if clean_sku:
                    product.sku = clean_sku

        # 3. Extract Original Price (if exists) with enhanced cleaning
        if not product.original_price:
            old_price_match = re.search(r'productPrice-oldPrice.*?price-currency-[^>]+>บาท</span>((?:<span>[^<]+</span>)+)', html_content)
            if old_price_match:
                raw_price = old_price_match.group(1)
                # Remove tags and commas with enhanced cleaning
                clean_price = re.sub(r'<[^>]+>|,', '', raw_price)
                clean_price = ' '.join(clean_price.split()).strip()
                try:
                    product.original_price = float(clean_price)
                except ValueError:
                    pass

        # 4. Fallback/Supplement with base HTML extraction
        html_product = super().extract_from_html(html_content, url)
        if html_product:
            if not product.name: product.name = html_product.name
            if not product.description: product.description = html_product.description
            if not product.images: product.images = html_product.images

            # Use base extraction for material if not found yet
            if html_product.material and not product.material:
                product.material = html_product.material

        # 5. Extract Model from Name or Description with enhanced pattern matching
        if product.name and 'รุ่น' in product.name:
            model_match = re.search(r'รุ่น\s+([A-Za-z0-9\-_\s]+)', product.name)
            if model_match:
                model_value = model_match.group(1).strip()
                clean_model = self._sanitize_text_field(model_value, max_length=200)
                if clean_model:
                    product.model = clean_model
        elif product.description and 'รุ่น' in product.description:
            model_match = re.search(r'รุ่น\s+([A-Za-z0-9\-_\s]+)', product.description)
            if model_match:
                model_value = model_match.group(1).strip()
                clean_model = self._sanitize_text_field(model_value, max_length=200)
                if clean_model:
                    product.model = clean_model

        # 6. Enhanced URL-based SKU fallback with validation
        if url and (not product.sku or product.sku == 'None'):
            url_patterns = [
                r'-(\d+)$',
                r'/product/([^/]+)',
                r'/item/([^/]+)'
            ]
            for pattern in url_patterns:
                match = re.search(pattern, url)
                if match:
                    potential_sku = match.group(1).strip()
                    if self._is_valid_sku(potential_sku):
                        product.sku = potential_sku
                        break

        product.retailer = "Boonthavorn"
        return product

    def _extract_json_ld(self, html_content: str) -> Optional[Dict[str, Any]]:
        """Extract and parse JSON-LD data from HTML."""
        try:
            # Regex to find the script tag content
            pattern = r'<script type="application/ld\+json">(.*?)</script>'
            matches = re.finditer(pattern, html_content, re.DOTALL)
            
            for match in matches:
                try:
                    data = json.loads(match.group(1))
                    # We are looking for @type Product
                    if isinstance(data, dict) and data.get('@type') == 'Product':
                        return data
                    # Sometimes it's a list of objects
                    elif isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict) and item.get('@type') == 'Product':
                                return item
                except json.JSONDecodeError:
                    continue
        except Exception:
            pass
        return None


class MegaHomeExtractor(ProductExtractor):
    """Specialized extractor for Mega Home website with enhanced sanitization."""

    def extract_from_html(self, html_content: str, url: str = None) -> Optional[ProductData]:
        """Extract product data specifically from Mega Home with enhanced sanitization."""
        # First try the general extraction
        product = super().extract_from_html(html_content, url)

        if product:
            # Mega Home specific enhancements with comprehensive field sanitization

            # Apply comprehensive sanitization to all fields to prevent CSS/HTML contamination
            if product.name:
                # Ensure product name doesn't contain retailer name
                if product.name == "MegaHome" or "megahome" in product.name.lower():
                    # Try to extract a better product name from HTML
                    better_name = self._extract_product_name(html_content)
                    if better_name and better_name != "MegaHome":
                        product.name = better_name
                    else:
                        product.name = None  # Clear invalid product name

            if product.model:
                # Prevent HTML element names as model values
                clean_model = self._sanitize_text_field(product.model, max_length=50)
                # Reject common HTML element names
                html_elements = ['html', 'body', 'div', 'span', 'section', 'article', 'header', 'footer']
                if clean_model and clean_model.lower() not in html_elements:
                    product.model = clean_model
                else:
                    product.model = None

            if product.color:
                product.color = self._sanitize_color_field(product.color)

            if product.dimensions:
                product.dimensions = self._sanitize_dimensions_field(product.dimensions)

            if product.material:
                product.material = self._sanitize_material_field(product.material)

            if product.brand:
                product.brand = self._sanitize_brand_field(product.brand)

            # Extract SKU from URL if available
            if url and not product.sku:
                url_match = re.search(r'/p/(\d+)', url)
                if url_match:
                    potential_sku = url_match.group(1).strip()
                    if self._is_valid_sku(potential_sku):
                        product.sku = potential_sku

        return product


def get_extractor(url: str) -> ProductExtractor:
    """Get the appropriate extractor for the given URL."""
    domain = urlparse(url).netloc.lower()

    if 'thaiwatsadu.com' in domain:
        return ThaiWatsaduExtractor(url)
    elif 'homepro.co.th' in domain:
        return HomeProExtractor(url)
    elif 'boonthavorn.com' in domain:
        return BoonthavornExtractor(url)
    elif 'dohome.co.th' in domain:
        extractor = ProductExtractor(url)
        extractor.retailer = "DoHome"
        return extractor
    elif 'megahome.co.th' in domain:
        return MegaHomeExtractor(url)
    elif 'globalhouse.co.th' in domain:
        extractor = ProductExtractor(url)
        extractor.retailer = "Global House"
        return extractor
    else:
        return ProductExtractor(url)

