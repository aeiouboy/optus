# Chore: Update E-commerce Product Scraper User Manual for uv Usage

## Metadata
adw_id: `68e83e4f`
prompt: `Update the e-commerce product scraper user manual to use 'uv run' instead of 'python' in all command examples. Also add a note about environment setup using uv and ensure all CLI usage examples show the correct 'uv run' prefix. Update both the installation instructions and all command-line examples to reflect uv usage.`

## Chore Description
Update the e-commerce product scraper user manual (`docs/ecommerce_product_scraper_manual.md`) to replace all direct script execution (`./adws/adw_ecommerce_product_scraper.py`) with `uv run adws/adw_ecommerce_product_scraper.py`. Add comprehensive environment setup instructions using uv and ensure all command-line examples throughout the document use the correct uv run prefix.

## Relevant Files
Use these files to complete the chore:

- **docs/ecommerce_product_scraper_manual.md** - Main user manual that needs updating with all command examples
- **README.md** - Contains command examples that should be consistent with the manual
- **pyproject.toml** - Project configuration showing uv is used as the package manager

### New Files
None - updating existing documentation file only

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Update Installation Section
- Add comprehensive uv environment setup instructions
- Replace current installation steps with uv-based approach
- Add note about uv sync for dependency management
- Include uv version check and installation guidance

### 2. Update Basic Usage Examples
- Replace `./adws/adw_ecommerce_product_scraper.py` with `uv run adws/adw_ecommerce_product_scraper.py` in single product example
- Update batch scraping example to use uv run prefix
- Ensure all basic usage commands use uv run

### 3. Update Advanced Usage Examples
- Update organized output examples to use uv run
- Modify job-ID organization examples
- Update all advanced usage command examples throughout the section

### 4. Update Example Sections
- Update Example 1 (Single Product Scraping) to use uv run
- Update Example 2 (Batch Processing) to use uv run
- Update Example 3 (Daily Monitoring) to use uv run
- Update Example 4 (Price Monitoring) to use uv run
- Update cron job example in Example 3 to use uv run

### 5. Update Troubleshooting Section
- Update debugging mode examples to use uv run
- Update performance optimization examples
- Update rate-limited sites examples
- Ensure all command examples in troubleshooting use uv run

### 6. Update Integration Examples
- Update data pipeline examples to use uv run
- Modify Stage 1 extraction command to use uv run
- Ensure consistency across all integration examples

### 7. Add Environment Setup Note
- Add prominent note about uv being the required execution method
- Include troubleshooting for uv-related issues
- Add benefits of using uv (dependency management, consistency)

### 8. Update Quick Start Section
- Replace script execution examples with uv run equivalents
- Update quick start commands to be consistent with new uv approach

### 9. Update Best Practices Section
- Update any command examples in best practices
- Add note about using uv for consistent environments
- Include uv-specific recommendations

### 10. Validate All Command Examples
- Search document for any remaining direct script executions
- Ensure all command examples use uv run prefix
- Verify consistency across all sections

## Validation Commands
Execute these commands to validate the chore is complete:

- `grep -n "\./adws/adw_ecommerce_product_scraper.py" docs/ecommerce_product_scraper_manual.md` - Should return no results (all direct script calls replaced)
- `grep -c "uv run adws/adw_ecommerce_product_scraper.py" docs/ecommerce_product_scraper_manual.md` - Should count all command examples (should be 15+ instances)
- `grep -n "uv run" docs/ecommerce_product_scraper_manual.md` - Review all uv run instances to ensure they're correct
- `uv run adws/adw_ecommerce_product_scraper.py --help` - Test that uv run works with the scraper
- `markdownlint docs/ecommerce_product_scraper_manual.md` - Ensure markdown syntax is still valid

## Notes
- The project already uses uv (evidenced by pyproject.toml and .python-version files)
- Main README.md should also be updated for consistency but the primary focus is the user manual
- Ensure the chmod +x instruction is updated or removed since uv run doesn't require executable permissions
- All command examples should use the exact format: `uv run adws/adw_ecommerce_product_scraper.py`
- The cron job example needs special attention to properly escape the uv run command