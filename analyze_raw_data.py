#!/usr/bin/env python3

import json
import glob
import re

def find_latest_raw_file():
    """Find the most recent raw output file."""
    files = glob.glob('/Users/tachongrak/Projects/Optus/apps/output/scraping/2025-11-22/*/raw/cc_raw_output.json')
    files.sort(key=lambda x: x.split('/')[-3], reverse=True)
    return files[0] if files else None

def analyze_thaiwatsadu_data():
    """Analyze raw ThaiWatsadu data to find price and product info."""
    raw_file = find_latest_raw_file()
    if not raw_file:
        print("No raw files found")
        return

    print(f"Analyzing: {raw_file}")

    with open(raw_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"Data type: {type(data)}")

    if isinstance(data, list) and data:
        first_item = data[0]
        print(f"Keys in first item: {list(first_item.keys())}")

        if 'html' in first_item:
            html_content = first_item['html']
            print(f"HTML content length: {len(html_content)}")

            # Look for structured data patterns in ThaiWatsadu pages
            patterns = [
                # JSON-LD structured data
                (r'"@type"\s*:\s*"Product"[^}]*?"name"\s*:\s*"([^"]+)"', 'product_name'),
                (r'"@type"\s*:\s*"Product"[^}]*?"brand"\s*:\s*"([^"]+)"', 'brand'),
                (r'"@type"\s*:\s*"Product"[^}]*?"sku"\s*:\s*"([^"]+)"', 'sku'),
                (r'"@type"\s*:\s*"Product"[^}]*?"offers"[^}]*?"price"\s*:\s*"?([\d,\.]+)"?', 'current_price'),
                (r'"@type"\s*:\s*"Product"[^}]*?"price"\s*:\s*"?([\d,\.]+)"?', 'current_price_alt'),

                # ThaiWatsadu specific patterns
                (r'current_price[^:]*:\s*"?([\d,\.]+)"?', 'current_price_var'),
                (r'original_price[^:]*:\s*"?([\d,\.]+)"?', 'original_price_var'),
                (r'"brand"[^:]*:\s*"?([^"]+)"?', 'brand_var'),
                (r'"sku"[^:]*:\s*"?([^"]+)"?', 'sku_var'),

                # General Thai price patterns
                (r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(?:฿|THB|baht)', 'price_thai'),
                (r'ราคา[^0-9]*([0-9,]+)', 'price_thai_text'),

                # SKU patterns
                (r'รหัส\s*สินค้า[:\s]*([A-Z0-9-]+)', 'sku_thai'),
                (r'sku[:\s]*([A-Z0-9-]+)', 'sku_en'),

                # Brand patterns
                (r'ยี่ห้อ[:\s]*([^,\n]+)', 'brand_thai'),
                (r'brand[:\s]*([^,\n]+)', 'brand_en'),

                # Model patterns
                (r'รุ่น[:\s]*([^,\n]+)', 'model_thai'),
                (r'model[:\s]*([^,\n]+)', 'model_en'),
            ]

            print("\n=== Pattern Matches ===")
            for pattern, name in patterns:
                try:
                    matches = re.findall(pattern, html_content, re.IGNORECASE | re.DOTALL)
                    if matches:
                        print(f"{name}: {matches[:3]}")
                except Exception as e:
                    print(f"Error with pattern {name}: {e}")

            # Look for specific data structures
            print("\n=== Looking for data structures ===")

            # Look for JSON data in script tags
            script_data = re.findall(r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html_content, re.DOTALL)
            if script_data:
                print(f"Found {len(script_data)} JSON-LD script blocks")
                for i, block in enumerate(script_data[:2]):  # Check first 2 blocks
                    try:
                        json_obj = json.loads(block.strip())
                        if isinstance(json_obj, dict):
                            print(f"Block {i+1} keys: {list(json_obj.keys())}")
                            if 'offers' in json_obj:
                                print(f"  Offers: {json_obj['offers']}")
                    except:
                        pass

            # Look for JavaScript variables
            js_vars = re.findall(r'var\s+(\w+)\s*=\s*({.*?});', html_content, re.DOTALL)
            if js_vars:
                print(f"Found {len(js_vars)} JavaScript variables")
                for var_name, var_content in js_vars[:5]:
                    print(f"  {var_name}: {var_content[:100]}...")

if __name__ == "__main__":
    analyze_thaiwatsadu_data()