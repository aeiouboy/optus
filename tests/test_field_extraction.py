#!/usr/bin/env python3
"""
Comprehensive test suite for field extraction validation and sanitization.

This module tests all the enhanced field extraction and sanitization methods
to ensure contamination prevention and data quality.
"""

import unittest
import sys
import os

# Add the adws modules to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'adws'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'adws', 'adw_modules'))

from product_extractor import ProductExtractor
from product_schemas import ProductData, normalize_product_data
from output_formatter import OutputFormatter


class TestFieldExtraction(unittest.TestCase):
    """Test cases for field extraction and sanitization."""

    def setUp(self):
        """Set up test fixtures."""
        self.extractor = ProductExtractor()
        self.formatter = OutputFormatter()

    def test_text_sanitization_removes_html_contamination(self):
        """Test that text sanitization removes HTML/CSS contamination."""
        contaminated_text = 'quickInfo-infoLabel-ขนาดสินค้า</label><label class="quickInfo-infoValue-123">10x20x30 cm</label>'
        cleaned = self.extractor._sanitize_text_field(contaminated_text, max_length=100)

        # Should remove HTML/CSS class names and tags
        self.assertIsNotNone(cleaned)
        self.assertNotIn('quickInfo-infoLabel', cleaned)
        self.assertNotIn('class=', cleaned)
        self.assertNotIn('<label', cleaned)
        self.assertNotIn('</label>', cleaned)
        self.assertIn('10x20x30', cleaned)

    def test_text_sanitization_removes_urls(self):
        """Test that text sanitization removes URLs."""
        contaminated_text = 'Brand name https://example.com/product and more text'
        cleaned = self.extractor._sanitize_text_field(contaminated_text, max_length=100)

        self.assertIsNotNone(cleaned)
        self.assertNotIn('https://example.com', cleaned)
        self.assertNotIn('http://', cleaned)

    def test_text_sanitization_removes_json_fragments(self):
        """Test that text sanitization removes JSON fragments."""
        contaminated_text = 'Product name {"name": "test", "type": "product"} more text'
        cleaned = self.extractor._sanitize_text_field(contaminated_text, max_length=100)

        self.assertIsNotNone(cleaned)
        self.assertNotIn('{"name": "test"}', cleaned)
        self.assertNotIn('"type": "product"', cleaned)

    def test_dimensions_sanitization_extracts_patterns(self):
        """Test dimension field sanitization extracts proper patterns."""
        test_cases = [
            '10x20x30 cm',
            'ขนาด 15 x 25 x 35 ซม.',
            'dimensions: 12.5x24.5x36.75mm',
            'class="dim-label</label><span>10x20x30</span>'
        ]

        for test_text in test_cases:
            cleaned = self.extractor._sanitize_dimensions_field(test_text)
            self.assertIsNotNone(cleaned, f"Failed to extract from: {test_text}")
            # Should contain dimension pattern
            self.assertTrue(
                any(char in cleaned for char in ['x', '×']) or cleaned.replace('.', '').isdigit(),
                f"No dimension pattern found in: {cleaned}"
            )

    def test_color_sanitization_prevents_css_codes(self):
        """Test color field sanitization prevents CSS color codes."""
        test_cases = [
            '#FF0000',
            'rgb(255, 0, 0)',
            'rgba(255, 0, 0, 0.5)',
            'hsl(0, 100%, 50%)',
            'color: #FF0000;'
        ]

        for test_color in test_cases:
            cleaned = self.extractor._sanitize_color_field(test_color)
            # Should reject CSS color codes
            self.assertIsNone(cleaned, f"CSS color code should be rejected: {test_color}")

    def test_color_sanitization_accepts_valid_colors(self):
        """Test color field sanitization accepts valid color names."""
        valid_colors = ['Red', 'Blue', 'Green', 'สีแดง', 'สีฟ้า', 'Dark Wood']

        for color in valid_colors:
            cleaned = self.extractor._sanitize_color_field(color)
            self.assertEqual(cleaned, color, f"Valid color should be accepted: {color}")

    def test_material_sanitization_cleans_prefixes(self):
        """Test material field sanitization removes common prefixes."""
        test_cases = [
            ('วัสดุ ไม้', 'ไม้'),
            ('Material: Steel', 'Steel'),
            ('ผลิตจากพลาสติก', 'พลาสติก'),
            ('เนื้อวัสดุ เหล็ก', 'เหล็ก')
        ]

        for input_text, expected in test_cases:
            cleaned = self.extractor._sanitize_material_field(input_text)
            self.assertEqual(cleaned, expected, f"Material prefix not removed: {input_text}")

    def test_sku_validation_rejects_urls(self):
        """Test SKU validation rejects URLs and domains."""
        invalid_skus = [
            'https://example.com/product/123',
            'www.example.com/product/456',
            'example.com/item/789'
        ]

        for invalid_sku in invalid_skus:
            is_valid = self.extractor._is_valid_sku(invalid_sku)
            self.assertFalse(is_valid, f"URL should be rejected as SKU: {invalid_sku}")

    def test_sku_validation_accepts_valid_skus(self):
        """Test SKU validation accepts valid SKU formats."""
        valid_skus = [
            'ABC123',
            'XYZ-456',
            '12345',
            'PROD7890',
            'ITEM-12345'
        ]

        for valid_sku in valid_skus:
            is_valid = self.extractor._is_valid_sku(valid_sku)
            self.assertTrue(is_valid, f"Valid SKU should be accepted: {valid_sku}")

    def test_discount_field_defaults(self):
        """Test discount fields default to 0.0 when no pricing."""
        product = ProductData(name='Test', url='http://test.com', current_price=None, original_price=None)

        # Should default to 0.0, not None
        self.assertEqual(product.discount_amount, 0.0)
        self.assertEqual(product.discount_percent, 0.0)
        self.assertEqual(product.has_discount, False)

    def test_discount_calculation_with_pricing(self):
        """Test discount calculation with valid pricing."""
        product = ProductData(
            name='Test',
            url='http://test.com',
            current_price=80.0,
            original_price=100.0
        )

        self.assertEqual(product.discount_amount, 20.0)
        self.assertEqual(product.discount_percent, 20.0)
        self.assertEqual(product.has_discount, True)

    def test_normalize_product_data_discount_defaults(self):
        """Test normalize_product_data sets discount defaults."""
        raw_data = {
            'name': 'Test Product',
            'url': 'http://test.com',
            'retailer': 'Test Store'
            # No discount fields provided
        }

        normalized = normalize_product_data(raw_data)

        # Should have default discount values
        self.assertEqual(normalized['discount_amount'], 0.0)
        self.assertEqual(normalized['discount_percent'], 0.0)
        self.assertEqual(normalized['has_discount'], False)

    def test_brand_extraction_patterns(self):
        """Test enhanced brand extraction patterns."""
        html_content = '''
        <html>
        <head>
            <meta property="og:brand" content="TestBrand">
            <meta name="brand" content="AnotherBrand">
        </head>
        <body>
            <div class="brand">HTMLBrand</div>
            <span>ยี่ห้อ ThaiBrand</span>
            <h1>ProductName</h1>
        </body>
        </html>
        '''

        brand = self.extractor._extract_brand(html_content)
        self.assertIsNotNone(brand)
        # Should extract one of the brands
        self.assertIn(brand, ['TestBrand', 'AnotherBrand', 'HTMLBrand', 'ThaiBrand'])

    def test_model_extraction_patterns(self):
        """Test enhanced model extraction patterns."""
        html_content = '''
        <html>
        <body>
            <div class="model">ModelX123</div>
            <span>รุ่น ProMax</span>
            <meta property="product:model" content="MetaModel">
            <title>ProductName - ABC-456</title>
        </body>
        </html>
        '''

        model = self.extractor._extract_model(html_content)
        self.assertIsNotNone(model)
        # Should extract one of the models
        self.assertIn(model, ['ModelX123', 'ProMax', 'MetaModel', 'ABC-456'])

    def test_output_formatter_field_validation(self):
        """Test output formatter field validation."""
        contaminated_value = 'Brand Name class="quickInfo-label-123" https://example.com'
        cleaned_value = self.formatter._validate_and_sanitize_field(contaminated_value, 'brand')

        self.assertIsNotNone(cleaned_value)
        self.assertNotIn('class=', cleaned_value)
        self.assertNotIn('https://', cleaned_value)

    def test_output_formatter_dimension_validation(self):
        """Test output formatter dimension field validation."""
        test_value = 'ขนาด 10x20x30 ซม. class="dimension-label"'
        cleaned_value = self.formatter._validate_dimension_field(test_value, 'dimensions')

        self.assertIsNotNone(cleaned_value)
        self.assertIn('10x20x30', cleaned_value)
        self.assertNotIn('class=', cleaned_value)

    def test_output_formatter_color_validation(self):
        """Test output formatter color field validation."""
        # Should reject CSS colors
        css_colors = ['#FF0000', 'rgb(255,0,0)', 'hsl(0,100%,50%)']
        for css_color in css_colors:
            cleaned = self.formatter._validate_color_field(css_color)
            self.assertIsNone(cleaned, f"CSS color should be rejected: {css_color}")

        # Should accept valid color names
        valid_colors = ['Red', 'Blue', 'สีแดง']
        for valid_color in valid_colors:
            cleaned = self.formatter._validate_color_field(valid_color)
            self.assertEqual(cleaned, valid_color, f"Valid color should be accepted: {valid_color}")

    def test_trailing_comma_handling(self):
        """Test handling of trailing commas in text fields."""
        text_with_comma = 'Product Name,'
        cleaned = self.extractor._sanitize_text_field(text_with_comma, max_length=100)

        self.assertIsNotNone(cleaned)
        self.assertEqual(cleaned, 'Product Name')  # Trailing comma should be removed

    def test_field_length_validation(self):
        """Test field length validation prevents excessive values."""
        long_text = 'x' * 1000  # Very long text
        cleaned = self.extractor._sanitize_text_field(long_text, max_length=100)

        self.assertIsNone(cleaned, "Excessively long text should be rejected")

    def test_json_fragment_removal(self):
        """Test removal of JSON fragments from text fields."""
        contaminated_text = 'Product {"name": "test", "@type": "Product", "date": "2023-01-01T00:00:00"} Details'
        cleaned = self.extractor._sanitize_text_field(contaminated_text, max_length=100)

        self.assertIsNotNone(cleaned)
        self.assertNotIn('{"name": "test"}', cleaned)
        self.assertNotIn('@type', cleaned)
        self.assertNotIn('2023-01-01T00:00:00', cleaned)

    def test_css_class_removal(self):
        """Test removal of CSS class patterns."""
        contaminated_text = 'Text quickInfo-infoLabel-123 and quickInfo-infoValue-456 more text'
        cleaned = self.extractor._sanitize_text_field(contaminated_text, max_length=100)

        self.assertIsNotNone(cleaned)
        self.assertNotIn('quickInfo-infoLabel', cleaned)
        self.assertNotIn('quickInfo-infoValue', cleaned)


class TestIntegrationValidation(unittest.TestCase):
    """Integration tests for complete field extraction pipeline."""

    def test_complete_product_extraction(self):
        """Test complete product extraction with contaminated HTML."""
        contaminated_html = '''
        <html>
        <head>
            <title>Test Product - ContaminatedBrand</title>
            <meta property="og:brand" content="CleanBrand">
            <meta name="description" content="A test product with details">
        </head>
        <body>
            <h1>Test Product</h1>
            <div class="brand">class="quickInfo-brand-123"</div>
            <span>รุ่น ModelX-123</span>
            <div>สี #FF0000</div>
            <div>วัสดุ Material: Steel class="mat-info"</div>
            <div>ขนาด 10x20x30 class="dim-info"</div>
            <div>รหัสสินค้า https://example.com/product/123</div>
        </body>
        </html>
        '''

        extractor = ProductExtractor('https://example.com/test')
        product = extractor.extract_from_html(contaminated_html, 'https://example.com/test')

        self.assertIsNotNone(product)

        # Brand should be cleaned
        if product.brand:
            self.assertNotIn('class=', product.brand)
            self.assertNotIn('https://', product.brand)

        # Model should be cleaned
        if product.model:
            self.assertNotIn('class=', product.model)

        # Color should not contain CSS codes
        if product.color:
            self.assertNotIn('#FF0000', product.color)
            self.assertNotIn('#', product.color)

        # Material should be cleaned
        if product.material:
            self.assertNotIn('class=', product.material)

        # Dimensions should be cleaned
        if product.dimensions:
            self.assertNotIn('class=', product.dimensions)

        # SKU should not be a URL
        if product.sku:
            self.assertNotIn('https://', product.sku)
            self.assertNotIn('example.com', product.sku)

    def test_ecommerce_data_detection(self):
        """Test e-commerce data detection in output formatter."""
        formatter = OutputFormatter()

        # Test with e-commerce indicators
        ecommerce_data = [{
            'name': 'Test Product',
            'current_price': 100.0,
            'brand': 'TestBrand',
            'sku': 'TEST123'
        }]

        self.assertTrue(formatter.is_ecommerce_data(ecommerce_data))

        # Test without e-commerce indicators
        non_ecommerce_data = [{
            'title': 'Simple Page',
            'content': 'Some content'
        }]

        self.assertFalse(formatter.is_ecommerce_data(non_ecommerce_data))


if __name__ == '__main__':
    # Run tests with detailed output
    unittest.main(verbosity=2)