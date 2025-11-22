# Input Folder Structure for Web Scraping

This directory contains organized URL collections for different types of websites and scraping purposes.

## 📁 Folder Structure

```
inputs/
├── websites/           # General website URLs
├── ecommerce/          # E-commerce product pages
├── social_media/       # Social media profiles and posts
├── news/              # News articles and media sites
├── blogs/             # Blog posts and articles
├── documentation/     # Technical documentation
├── api_docs/          # API documentation sites
├── images/            # Image galleries and media
└── specialized/       # Specialized scraping targets
```

## 🚀 Usage Examples

### Single Category Scraping
```bash
# Scrape all e-commerce URLs
./adws/adw_crawl4ai_scraper.py --input-folder inputs/ecommerce

# Scrape news websites
./adws/adw_crawl4ai_scraper.py --input-folder inputs/news

# Scrape social media
./adws/adw_crawl4ai_scraper.py --input-folder inputs/social_media
```

### Multiple Categories
```bash
# Scrape multiple categories
./adws/adw_crawl4ai_scraper.py --input-folder inputs/ --filter "ecommerce,social_media"
```

## 📝 File Formats Supported

- **`.txt`** - Simple text files (one URL per line)
- **`.urls`** - URL collection files
- **`.list`** - Organized lists
- **`.csv`** - CSV files with URLs in first column

## 🎯 Best Practices

1. **Organize by purpose** - Group similar websites together
2. **Use descriptive names** - Clear file names indicate content
3. **Add comments** - Use `#` for comments in text files
4. **Keep lists manageable** - 50-100 URLs per file is optimal
5. **Test small batches** - Test with few URLs before full runs

## 🔧 File Naming Conventions

- Use lowercase letters
- Separate words with underscores
- Include website/domain name
- Add date or version if needed

Examples:
- `thaiwatsadu_products.txt`
- `amazon_electronics_2024.txt`
- `news_tech_websites.urls`