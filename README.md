# Optus - Multi-Agent E-commerce Scraping Platform

A sophisticated multi-agent task delegation system for automated e-commerce data extraction workflows.

---

## 📁 Project Structure

```
optus/
├── adws/                      # AI Developer Workflows (scraping scripts)
│   ├── adw_modules/          # Shared modules (extractors, wrappers)
│   └── *.py                  # Individual workflow scripts
├── inputs/                    # Input data (URLs, CSVs)
│   └── ecommerce/            # E-commerce retailer URLs
├── apps/output/              # Scraping results
│   ├── by_list/              # Organized by date/time
│   ├── by_url/               # Organized by domain
│   └── scraping/             # General scraping outputs
├── docs/                      # Documentation
│   ├── reports/              # Analysis reports
│   └── tasks.md              # Task tracking
├── debug_tools/              # Debugging & analysis scripts
├── tests/                     # Test data & utilities
│   └── samples/              # HTML samples for testing
├── scripts/                   # Utility scripts
├── examples/                  # Example/one-off scrapers
└── specs/                     # Schema specifications

Config Files:
├── .env.sample               # Environment variables template
├── .gitignore               # Git ignore rules
├── .mcp.json                # MCP configuration
├── .python-version          # Python version
├── pyproject.toml           # Project dependencies
└── uv.lock                  # UV lock file
```

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
uv sync
```

### 2. Run E-commerce Scraper
```bash
./adws/adw_ecommerce_product_scraper.py \
  --urls-file inputs/ecommerce/thaiwatsadu_urls.csv \
  --output-file output/products.json
```

### 3. Test All Retailers
```bash
./debug_tools/test_all_retailers.sh
```

---

## 📊 Supported Retailers

| Retailer | Status | Success Rate | Notes |
|----------|--------|--------------|-------|
| Thai Watsadu | ✅ Production | 100% | Perfect extraction |
| HomePro | ✅ Production | 100% | Perfect extraction |
| DoHome | ✅ Production | 100% | Perfect extraction |
| Boonthavorn | ⚠️ Review CSV | 24% | 76% invalid URLs |
| Global House | ⚠️ Review CSV | 70% | Some 404s |
| Mega Home | ⚠️ Review CSV | 40% | URL quality issues |

---

## 🛠️ Key Features

- **JSON-LD Extraction**: Structured data parsing for accuracy
- **Multi-Retailer Support**: Specialized extractors per retailer
- **Incremental Saving**: Real-time results during scraping
- **Progress Tracking**: Rich console output with ETAs
- **Error Handling**: Retry logic and detailed error reporting
- **Discount Calculation**: Auto-calculates discount % and amount

---

## 📖 Documentation

- **[Extraction Report](docs/reports/EXTRACTION_REPORT.md)**: Detailed analysis of Boonthavorn extraction
- **[Multi-Retailer Test](docs/reports/MULTI_RETAILER_TEST_RESULTS.md)**: Cross-retailer validation results
- **[ADW README](adws/README.md)**: AI Developer Workflows documentation
- **[Debug Tools](debug_tools/README.md)**: Testing utilities guide

---

## 🔧 Development

### Run Tests
```bash
# Test specific retailer
python3 debug_tools/test_extractor.py

# Analyze results
python3 debug_tools/analyze_results.py
```

### Debug Failing URLs
```bash
python3 debug_tools/test_failed_url.py
```

---

## 📝 Recent Updates

### 2025-11-22: Enhanced Boonthavorn Extraction
- ✅ Implemented JSON-LD structured data parsing
- ✅ Added Quick Info section extraction
- ✅ CSS selector-based page load waiting
- ✅ Auto-discount calculation
- ✅ Multi-field extraction (color, dimensions, volume, etc.)
- ✅ 100% accuracy on valid product URLs

---

## 🤝 Contributing

1. Create feature branch
2. Make changes
3. Test with `debug_tools/test_all_retailers.sh`
4. Submit PR

---

## 📄 License

Private project - All rights reserved
