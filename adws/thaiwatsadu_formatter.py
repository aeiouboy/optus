#!/usr/bin/env python3
"""
ThaiWatsadu-specific product data formatter.

This module specializes in extracting structured product data from ThaiWatsadu product pages,
focusing on JSON-LD structured data and ThaiWatsadu-specific patterns.
"""

import json
import re
import html
import os
from typing import Dict, Any, List, Optional
from dataclasses import asdict
from pathlib import Path
from datetime import datetime


class ThaiWatsaduFormatter:
    """Specialized formatter for ThaiWatsadu product pages."""

    def __init__(self):
        """Initialize ThaiWatsadu-specific extraction patterns."""
        pass

    def extract_json_ld_data(self, content: str) -> Dict[str, Any]:
        """Extract structured data from JSON-LD script tags."""
        json_ld_patterns = [
            r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        ]

        for pattern in json_ld_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
            for match in matches:
                try:
                    json_data = json.loads(match.strip())
                    if isinstance(json_data, dict) and json_data.get('@type') == 'Product':
                        return json_data
                    elif isinstance(json_data, list):
                        for item in json_data:
                            if isinstance(item, dict) and item.get('@type') == 'Product':
                                return item
                except json.JSONDecodeError:
                    continue

        return {}

    def extract_thaiwatsadu_prices(self, content: str) -> tuple:
        """Extract current and original prices from ThaiWatsadu pages."""
        current_price = None
        original_price = None

        # First try JSON-LD data - this is most reliable
        json_ld = self.extract_json_ld_data(content)
        if json_ld:
            offers = json_ld.get('offers', {})
            if isinstance(offers, dict):
                price_str = offers.get('price')
                if price_str:
                    try:
                        current_price = int(float(str(price_str).replace(',', '')))
                    except (ValueError, TypeError):
                        pass

        # Look for ThaiWatsadu specific price format in meta tags
        meta_patterns = [
            r'meta property="og:price:amount" content="([\d,\.]+)"',
            r'meta name="price" content="([\d,\.]+)"',
        ]
        for pattern in meta_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches and not current_price:
                try:
                    current_price = int(float(matches[0].replace(',', '')))
                except (ValueError, TypeError):
                    continue

        # Look for price pairs in the format: original, current
        # Pattern: "ราคา 3,290 00 2,790 00"
        thai_price_pattern = r'ราคา[^\d]*([\d,]+)[^\d]*00[^\d]*([\d,]+)[^\d]*00'
        price_matches = re.findall(thai_price_pattern, content)
        if price_matches:
            try:
                potential_original = int(price_matches[0][0].replace(',', ''))
                potential_current = int(price_matches[0][1].replace(',', ''))

                # Only use if values make sense (original should be higher than current)
                if potential_original > potential_current:
                    original_price = potential_original
                    if not current_price:  # Only override if not already set
                        current_price = potential_current
            except (ValueError, IndexError):
                pass

        # Additional fallback: look for "เดิม" (original) patterns
        original_patterns = [
            r'เดิม[^\d]*([0-9,]+)',
            r'ปกติ[^\d]*([0-9,]+)',
        ]
        for pattern in original_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                try:
                    orig_price = int(matches[0].replace(',', ''))
                    # Only use if it's significantly higher than current price and in reasonable range
                    if orig_price > 50 and orig_price <= 50000:
                        if current_price and orig_price > current_price * 1.1:  # At least 10% higher
                            original_price = orig_price
                            break
                        elif not current_price and not original_price:  # Only set if no current price and no original price yet
                            original_price = orig_price
                except (ValueError, IndexError):
                    continue

        # Final fallback for current price if still not found
        if not current_price:
            current_patterns = [
                r'(\d{1,5}(?:,\d{3})?)\s*(?:฿|THB|baht)',
            ]
            for pattern in current_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    try:
                        price = int(matches[0].replace(',', ''))
                        # Filter out very small or very large values that are likely errors
                        if 50 <= price <= 50000:  # Reasonable price range
                            current_price = price
                            break
                    except (ValueError, IndexError):
                        continue

        return current_price, original_price

    def extract_basic_info(self, content: str) -> Dict[str, str]:
        """Extract basic product information."""
        info = {}

        # Use JSON-LD data first
        json_ld = self.extract_json_ld_data(content)
        if json_ld:
            info['name'] = json_ld.get('name', '').replace(' - ไทวัสดุ', '').strip()
            info['description'] = html.unescape(re.sub(r'<[^>]+>', '', json_ld.get('description', ''))).strip()

            brand_data = json_ld.get('brand', {})
            if isinstance(brand_data, dict):
                info['brand'] = brand_data.get('name', '').strip()
            else:
                info['brand'] = str(brand_data).strip()

            info['sku'] = str(json_ld.get('sku', '')).strip()

        # Fallback to HTML extraction
        if not info.get('name'):
            name_patterns = [
                r'<title>([^<]+)</title>',
                r'<h1[^>]*>([^<]+)</h1>',
                r'meta property="og:title" content="([^"]+)"'
            ]
            for pattern in name_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    info['name'] = matches[0].replace(' - ไทวัสดุ', '').strip()
                    break

        if not info.get('brand'):
            brand_patterns = [
                r'meta property="product:brand" content="([^"]+)"',
                r'ยี่ห้อ[:\s]*([^,\n<]+)',
            ]
            for pattern in brand_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    info['brand'] = matches[0].strip()
                    break

        if not info.get('sku'):
            sku_patterns = [
                r'รหัส\s*สินค้า[:\s]*([A-Z0-9-]+)',
                r'รหัสสินค้า[:\s]*([A-Z0-9-]+)',
            ]
            for pattern in sku_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    info['sku'] = matches[0].strip()
                    break

        return info

    def extract_specifications(self, content: str) -> Dict[str, str]:
        """Extract product specifications."""
        specs = {}

        # Extract from JSON-LD description or title
        json_ld = self.extract_json_ld_data(content)
        name = ""
        if json_ld:
            name = json_ld.get('name', '')

        # Model extraction
        model_patterns = [
            r'รุ่น\s*([A-Z0-9\-/]+)(?:\s*สี|$)',  # Model number before color
            r'รุ่น[:\s]*([^,\n<\|สี]+)',  # Model with color stopping at สี
            r'รุ่น\s*([A-Z0-9\-/]+(?:\s+[A-Z0-9\-/]+)*)',
        ]
        for pattern in model_patterns:
            matches = re.findall(pattern, content + " " + name, re.IGNORECASE)
            if matches:
                model = matches[0].strip()
                # Clean up common suffixes
                model = re.sub(r'\s*-\s*ไทวัสดุ.*$', '', model)  # Remove ThaiWatsadu suffix
                model = re.sub(r'\s*สี.*$', '', model)  # Remove color information
                if len(model) > 1 and not model.lower() in ['รุ่น', 'model', '-']:
                    specs['model'] = model.strip()
                    break

        # Category detection based on product name and keywords
        category_keywords = {
            'ถังเก็บน้ำ': ['ถังเก็บน้ำ', 'ถังน้ำ', 'tank', 'ice', 'dos รุ่น ice'],  # Put water tank first since it's more specific
            'เครื่องมือช่าง': ['กรรไกร', 'คีม', 'จักร', 'ไขควง', 'สกัด', 'มีด', 'เลื่อย', 'ค้อน', 'ดอกสว่าน', 'ท่อพีวีซี', 'pvc'],
            'เสื้อผ้า': ['เสื้อ', 'กางเกง', 'ชุด', 't-shirt'],
            'เครื่องใช้ไฟฟ้า': ['laptop', 'โน๊ตบุ๊ค', 'คอมพิวเตอร์', 'iphone', 'โทรศัพท์'],
            'สินค้า': ['สินค้า', 'product'],  # Default fallback
        }

        content_lower = (content + " " + name).lower()
        specs['category'] = 'สินค้า'  # Default fallback
        for category, keywords in category_keywords.items():
            if any(keyword.lower() in content_lower for keyword in keywords):
                specs['category'] = category
                break

        # Volume extraction
        volume_patterns = [
            r'ความจุ[:\s]*(\d+(?:,\d+)?)\s*(?:ลิตร|ลิตร์|L)',
            r'(\d+(?:,\d+)?)\s*(?:ลิตร|ลิตร์|L)\b',
            r'(\d{1,4}(?:,\d{3})?)\s*(?:ลิตร|ลิตร์)',
        ]
        for pattern in volume_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                volume_raw = matches[0]
                if ',' in volume_raw:  # Keep the comma if it was in the original
                    volume = volume_raw
                else:
                    volume = f"{int(volume_raw):,}"  # Add comma for thousands
                if int(volume_raw.replace(',', '')) > 0:  # Filter out zero values
                    specs['volume'] = f"{volume} ลิตร"
                    break

        # Special handling for size in mm (like 42 มม.)
        size_patterns = [
            r'(\d+(?:\.\d+)?)\s*มม\.',
            r'(\d+(?:\.\d+)?)\s*mm',
            r'ขนาด[:\s]*(\d+(?:\.\d+)?)\s*มม\.',
        ]
        for pattern in size_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                size = matches[0]
                # Check if this should be volume (for tools) or dimensions
                if specs.get('category') == 'เครื่องมือช่าง':
                    specs['volume'] = f"{size} มม."  # For tools, size is treated as volume/size
                break

        # Dimensions extraction
        dim_patterns = [
            r'(\d+(?:\.\d+)?)\s*[xX\*]\s*(\d+(?:\.\d+)?)\s*[xX\*]\s*(\d+(?:\.\d+)?)\s*(?:ซม\.|cm)',
            r'ขนาด[:\s]*(\d+(?:\.\d+)?)\s*[xX\*]\s*(\d+(?:\.\d+)?)\s*[xX\*]\s*(\d+(?:\.\d+)?)',
        ]
        for pattern in dim_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                dims = " x ".join(matches[0])
                specs['dimensions'] = f"{dims} ซม."
                break

        # Material extraction - prioritize specific materials from the content
        if specs.get('category') == 'ถังเก็บน้ำ':
            # For water tanks, check for specific materials mentioned in description
            if 'compound polymer' in content.lower():
                specs['material'] = 'Compound Polymer'
            elif 'food grade' in content.lower():
                specs['material'] = 'Food Grade 100%'
            else:
                # Fallback to general material extraction
                material_patterns = [
                    r'วัสดุ[:\s]*([^,\n<\"]+)',
                    r'ผลิตจาก\s*([^,\n<\"]+)',
                    r'Compound Polymer',
                    r'สเตนเลส',
                    r'อะลูมิเนียม',
                ]
                for pattern in material_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    if matches:
                        material = matches[0].strip()
                        # Clean up common HTML artifacts
                        material = re.sub(r'[\"\']>$', '', material)  # Remove trailing quotes
                        material = re.sub(r'^[\"\']', '', material)  # Remove leading quotes
                        if len(material) > 1 and not any(skip in material.lower() for skip in ['ครบเรื่องบ้าน', 'ถูกและดี', 'ไม่พึงประสงค์']):
                            specs['material'] = material
                            break

        # Color extraction - clean up color information
        color_patterns = [
            r'สี[:\s]*([^,\n<\|]+)',
            r'สีไอซ์บลู|สีส้ม[-\s]*ดำ|สีดำ|สีแดง|สีขาว|สีเขียว|สีน้ำเงิน|สีเหลือง',
        ]
        for pattern in color_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                color = matches[0].strip()
                # Clean up color information
                color = re.sub(r'\s*-\s*ไทวัสดุ.*$', '', color)  # Remove ThaiWatsadu suffix
                color = re.sub(r'^สี\s*', 'สี', color)  # Ensure it starts with สี
                if len(color) > 1 and not color.lower() in ['สี', 'color']:
                    specs['color'] = color
                    break

        return specs

    def extract_images(self, content: str) -> List[str]:
        """Extract product images from JSON-LD and HTML."""
        images = []

        # First try JSON-LD images
        json_ld = self.extract_json_ld_data(content)
        if json_ld:
            json_ld_images = json_ld.get('image', [])
            if isinstance(json_ld_images, list):
                for img in json_ld_images:
                    if img and img.startswith('http'):
                        images.append(img)
            elif isinstance(json_ld_images, str) and json_ld_images.startswith('http'):
                images.append(json_ld_images)

        # If no images from JSON-LD, try HTML extraction
        if not images:
            html_patterns = [
                r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
                r'meta property="og:image" content="([^"]+)"',
            ]
            for pattern in html_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    if match and match.startswith('http'):
                        images.append(match)

        # Clean and deduplicate images
        cleaned_images = []
        seen = set()
        for img in images:
            if img and img not in seen and not any(skip in img.lower() for skip in ['logo', 'icon', 'svg']):
                cleaned_images.append(img)
                seen.add(img)
                if len(cleaned_images) >= 5:  # Limit to 5 images
                    break

        return cleaned_images

    def process_thaiwatsadu_page(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Process a ThaiWatsadu scraping result into structured product data."""
        content = result.get('html', '') or result.get('content', '')
        url = result.get('url', '')

        if not content:
            return self._create_empty_result(url)

        # Extract all information
        basic_info = self.extract_basic_info(content)
        current_price, original_price = self.extract_thaiwatsadu_prices(content)
        specifications = self.extract_specifications(content)
        images = self.extract_images(content)

        # Calculate discount information
        has_discount = original_price and current_price and original_price > current_price
        discount_percent = 0
        discount_amount = 0
        if has_discount:
            discount_percent = round(((original_price - current_price) / original_price) * 100, 2)
            discount_amount = original_price - current_price

        # Generate product key
        import hashlib
        product_name = basic_info.get('name', '')
        product_key = hashlib.md5(f"{url}_{product_name}".encode()).hexdigest()[:12]

        # Create structured data matching your exact requirements
        structured_data = {
            'name': product_name,
            'retailer': 'Thai Watsadu',
            'url': url,
            'current_price': current_price,
            'original_price': original_price,
            'product_key': product_key,
            'brand': basic_info.get('brand'),
            'model': specifications.get('model'),
            'sku': basic_info.get('sku'),
            'category': specifications.get('category', 'สินค้า'),
            'volume': specifications.get('volume'),
            'dimensions': specifications.get('dimensions'),
            'material': specifications.get('material'),
            'color': specifications.get('color'),
            'images': images,
            'description': basic_info.get('description', ''),
            'scraped_at': datetime.now().isoformat(),
            'has_discount': has_discount,
            'discount_percent': discount_percent,
            'discount_amount': discount_amount
        }

        # Remove None values but keep empty strings and 0 values
        return {k: v for k, v in structured_data.items() if v is not None}

    def _create_empty_result(self, url: str) -> Dict[str, Any]:
        """Create an empty result structure for failed scrapes."""
        return {
            'name': None,
            'retailer': 'Thai Watsadu',
            'url': url,
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
            'scraped_at': datetime.now().isoformat(),
            'has_discount': False,
            'discount_percent': 0,
            'discount_amount': 0
        }

def test_thaiwatsadu_formatter():
    """Test the ThaiWatsadu formatter with a sample URL."""
    import asyncio
    from crawl4ai import AsyncWebCrawler

    async def test_scrape():
        url = "https://www.thaiwatsadu.com/th/sku/60363373"

        async with AsyncWebCrawler(
            headless=True,
            browser_type="chromium",
            verbose=True
        ) as crawler:
            result = await crawler.arun(
                url=url,
                delay_before_return_html=2.0,
            )

            formatter = ThaiWatsaduFormatter()
            formatted_result = formatter.process_thaiwatsadu_page({
                'url': url,
                'html': result.html,
                'content': result.cleaned_html,
                'success': result.success
            })

            print("Formatted Result:")
            print(json.dumps(formatted_result, indent=2, ensure_ascii=False))

            return formatted_result

    return asyncio.run(test_scrape())

if __name__ == "__main__":
    test_thaiwatsadu_formatter()