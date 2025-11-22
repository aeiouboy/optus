# Chore: Create comprehensive user manual for e-commerce product scraper

## Metadata
adw_id: `944dda17`
prompt: `Create a comprehensive user manual for the e-commerce product scraper. Include: 1) Installation and setup instructions, 2) Command-line usage examples for all retailers, 3) Input file format specifications, 4) Output structure and field descriptions, 5) Troubleshooting guide, 6) Best practices for large-scale scraping, 7) Performance tuning recommendations. Save the manual as a markdown document in the docs directory.`

## Chore Description
Enhance the existing e-commerce product scraper manual to create a comprehensive user guide covering installation, usage for all supported retailers, detailed specifications, troubleshooting, and performance optimization. The manual should be production-ready and suitable for users at all skill levels.

## Relevant Files
Use these files to complete the chore:

### Existing Manual
- `docs/ecommerce_product_scraper_manual.md` - Current manual to enhance and expand

### Core Scraper Files
- `adws/adw_ecommerce_product_scraper.py` - Main scraper script with command-line options
- `adws/adw_modules/product_schemas.py` - Product data models and field definitions
- `adws/adw_modules/product_extractor.py` - Retailer-specific extraction logic
- `adws/adw_modules/crawl4ai_wrapper.py` - Web scraping wrapper and configuration

### Input Data Files
- `inputs/ecommerce/thaiwatsadu_urls.csv` - Sample Thai Watsadu URLs for examples
- `inputs/ecommerce/home_pro_urls.csv` - Sample HomePro URLs
- `inputs/ecommerce/dohome_urls.csv` - Sample DoHome URLs
- `inputs/ecommerce/global_house_urls.csv` - Sample Global House URLs
- `inputs/ecommerce/mega_home_urls.csv` - Sample Mega Home URLs
- `inputs/ecommerce/boonthavorn_urls.csv` - Sample Boonthavorn URLs

### Configuration Files
- `pyproject.toml` - Dependencies and project configuration
- `.env.sample` - Environment variables template

### Testing and Validation
- `debug_tools/test_all_retailers.sh` - Retailer testing script for examples
- `README.md` - Project overview and quick start guide
- `adws/README.md` - ADW-specific documentation

### New Files
- `docs/USER_MANUAL.md` - Enhanced comprehensive user manual

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Analyze Existing Manual and Gaps
- Review current `docs/ecommerce_product_scraper_manual.md`
- Identify missing sections from requirements
- Analyze retailer-specific usage gaps
- Check for incomplete installation instructions
- Note missing advanced troubleshooting scenarios

### 2. Enhance Installation and Setup Section
- Expand prerequisites with version requirements
- Add environment setup instructions
- Include browser dependencies installation
- Add permission and executable setup steps
- Provide Docker/container installation options
- Add Windows/Mac/Linux specific instructions
- Include dependency verification commands

### 3. Add Comprehensive Retailer-Specific Examples
- Create dedicated sections for each supported retailer:
  - Thai Watsadu
  - HomePro
  - DoHome
  - Global House
  - Mega Home
  - Boonthavorn
- Provide working example URLs for each retailer
- Include retailer-specific configuration recommendations
- Add batch processing examples for each retailer
- Include success rates and known limitations

### 4. Expand Input File Format Specifications
- Document CSV format with headers
- Add plain text URL file format
- Include mixed retailer input files
- Provide input validation examples
- Add URL filtering and preprocessing examples
- Include sample input files for each format

### 5. Enhance Output Structure Documentation
- Add detailed field descriptions for all 18 required fields
- Include data types and validation rules
- Provide output file structure explanations
- Add agent output directory mapping
- Include JSON schema reference
- Add output validation examples

### 6. Create Comprehensive Troubleshooting Guide
- Add common error scenarios and solutions
- Include browser/JavaScript issues
- Add network connectivity troubleshooting
- Include memory/resource issues
- Add permission and file system errors
- Provide debugging commands and tools
- Include log analysis instructions

### 7. Add Large-Scale Scraping Best Practices
- Include batch processing strategies
- Add rate limiting and respectful scraping
- Provide memory management techniques
- Include error recovery strategies
- Add progress monitoring approaches
- Provide data quality assurance methods
- Include backup and recovery procedures

### 8. Include Performance Tuning Recommendations
- Add concurrency optimization guidelines
- Include timeout and retry configuration
- Provide browser vs. HTTP recommendations
- Add memory usage optimization
- Include network performance tips
- Provide caching strategies
- Add monitoring and profiling tools

### 9. Add Advanced Usage Patterns
- Include automation and scheduling examples
- Add integration with data pipelines
- Provide custom extraction examples
- Include output filtering and processing
- Add API integration patterns
- Provide monitoring and alerting setup

### 10. Create Reference Materials
- Add complete command-line options reference
- Include field extraction mappings
- Provide retailer configuration reference
- Add output format specifications
- Include error code reference
- Provide performance benchmarks

### 11. Validate and Test Manual
- Test all command examples
- Validate all URL examples
- Check formatting and consistency
- Verify all sections are complete
- Test cross-references and links
- Validate code examples and syntax

## Validation Commands
Execute these commands to validate the chore is complete:

- `python3 -m py_compile adws/adw_ecommerce_product_scraper.py` - Verify scraper compiles
- `./adws/adw_ecommerce_product_scraper.py --help` - Check command-line options reference
- `head -5 inputs/ecommerce/thaiwatsadu_urls.csv` - Validate sample input files exist
- `ls -la docs/USER_MANUAL.md` - Confirm new manual file exists
- `grep -c "## " docs/USER_MANUAL.md` - Verify comprehensive section coverage
- `./debug_tools/test_all_retailers.sh` - Test retailer examples work
- `markdownlint docs/USER_MANUAL.md` - Check markdown formatting (if available)

## Notes
The existing manual provides a solid foundation but needs significant expansion in:
1. Retailer-specific usage examples and configurations
2. Advanced troubleshooting scenarios beyond basic issues
3. Large-scale scraping strategies and enterprise usage patterns
4. Performance optimization with specific benchmarks
5. Integration examples with other tools and systems
6. Complete reference materials for all configuration options
7. Windows/macOS compatibility instructions
8. Container/deployment options for production use

The enhanced manual should serve as the definitive reference for both beginners and advanced users, with practical examples that can be copied and run directly.