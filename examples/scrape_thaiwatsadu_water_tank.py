#!/usr/bin/env python3

import json
import re
from crawl4ai import AsyncWebCrawler

async def scrape_thaiwatsadu_detailed():
    url = "https://www.thaiwatsadu.com/th/sku/60363373"

    async with AsyncWebCrawler(
        headless=True,
        browser_type="chromium",
        verbose=True
    ) as crawler:
        result = await crawler.arun(
            url=url,
            js_code="""
            // Wait for any dynamic content to load
            await new Promise(resolve => setTimeout(resolve, 3000));

            // Look for product data in window objects
            window.productData = {
                price: document.querySelector('[data-price]')?.getAttribute('data-price'),
                originalPrice: document.querySelector('[data-original-price]')?.getAttribute('data-original-price'),
                brand: document.querySelector('[data-brand]')?.getAttribute('data-brand'),
                sku: document.querySelector('[data-sku]')?.getAttribute('data-sku'),
            };

            // Extract price information from common selectors
            const priceSelectors = [
                '.price',
                '.current-price',
                '[data-price]',
                '.product-price',
                '.special-price'
            ];

            const originalPriceSelectors = [
                '.original-price',
                '.old-price',
                '[data-original-price]',
                '.regular-price'
            ];

            for (let selector of priceSelectors) {
                const element = document.querySelector(selector);
                if (element) {
                    window.extractedPrice = element.textContent.trim();
                    break;
                }
            }

            for (let selector of originalPriceSelectors) {
                const element = document.querySelector(selector);
                if (element) {
                    window.extractedOriginalPrice = element.textContent.trim();
                    break;
                }
            }
            """,
            wait_for="css:.product-detail",
            delay_before_return_html=3.0,
            magic=True
        )

        print(f"Success: {result.success}")
        print(f"Status: {result.status_code}")
        print(f"HTML length: {len(result.html)}")

        # Save raw HTML for analysis
        with open('/tmp/water_tank_raw.html', 'w', encoding='utf-8') as f:
            f.write(result.html)

        # Extract specific patterns
        html_content = result.html

        patterns = [
            # Price patterns
            (r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(?:฿|THB|baht)', 'price_thai'),
            (r'"price"[^:]*:\s*"?([\d,\.]+)"?', 'price_json'),
            (r'"current_price"[^:]*:\s*"?([\d,\.]+)"?', 'current_price_json'),
            (r'"original_price"[^:]*:\s*"?([\d,\.]+)"?', 'original_price_json'),

            # SKU patterns
            (r'รหัส\s*สินค้า[:\s]*([A-Z0-9-]+)', 'sku_thai'),
            (r'"sku"[^:]*:\s*"?([^"]+)"?', 'sku_json'),
            (r'"productCode"[^:]*:\s*"?([^"]+)"?', 'product_code_json'),

            # Brand patterns
            (r'ยี่ห้อ[:\s]*([^,\n<]+)', 'brand_thai'),
            (r'"brand"[^:]*:\s*"?([^"]+)"?', 'brand_json'),

            # Model patterns
            (r'รุ่น[:\s]*([^,\n<]+)', 'model_thai'),
            (r'"model"[^:]*:\s*"?([^"]+)"?', 'model_json'),
        ]

        extracted_data = {}
        for pattern, name in patterns:
            try:
                matches = re.findall(pattern, html_content, re.IGNORECASE | re.DOTALL)
                if matches:
                    extracted_data[name] = matches
                    print(f"{name}: {matches[:3]}")
            except Exception as e:
                print(f"Error with pattern {name}: {e}")

        # Look for JSON-LD structured data
        script_data = re.findall(r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html_content, re.DOTALL)
        if script_data:
            print(f"\nFound {len(script_data)} JSON-LD script blocks")
            for i, block in enumerate(script_data):
                try:
                    json_obj = json.loads(block.strip())
                    if isinstance(json_obj, dict):
                        print(f"JSON-LD Block {i+1}:")
                        print(json.dumps(json_obj, indent=2, ensure_ascii=False))
                        break  # Just show the first relevant block
                except:
                    pass

        return result

if __name__ == "__main__":
    import asyncio
    asyncio.run(scrape_thaiwatsadu_detailed())