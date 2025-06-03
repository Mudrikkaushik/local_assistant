# Web Scraper Module

## Overview
The Web Scraper module allows you to scrape entire websites page by page, extracting content and saving it for analysis. This feature is integrated into the main application as a dedicated tab.

## Features

### 🌐 Comprehensive Website Scraping
- **Automatic link discovery**: The scraper automatically finds and follows links within the same domain
- **Page-by-page scraping**: Scrapes each page individually and displays progress in real-time
- **Content extraction**: Extracts titles, descriptions, headings, main content, and metadata from each page
- **Link analysis**: Counts and tracks internal links on each page

### 🛠️ Flexible Scraping Methods
- **HTTP Requests**: Fast scraping using Python requests + BeautifulSoup (default)
- **Selenium WebDriver**: For JavaScript-heavy websites that require browser rendering
- **Automatic fallback**: If Selenium fails, it automatically falls back to requests method

### ⚙️ Configurable Options
- **Max pages limit**: Set the maximum number of pages to scrape (1-200)
- **Domain restriction**: Only scrapes pages within the same domain as the starting URL
- **Respectful scraping**: Built-in delays between requests to avoid overwhelming servers

### 💾 Data Export
- **CSV format**: Structured data export with all page information
- **JSON format**: Complete data export preserving data types and structure
- **Automatic naming**: Files are automatically named with domain and timestamp
- **Results folder**: All exports are saved in the `results/` directory

## How to Use

### 1. Navigate to Web Scraper Tab
Click on the "🌐 Web Scraper" tab in the main application.

### 2. Configure Your Scraping Session
- **Enter URL**: Input the starting website URL (e.g., `https://example.com`)
- **Set Max Pages**: Choose how many pages to scrape (default: 20)
- **Choose Method**: 
  - Uncheck "Use Selenium" for fast scraping of simple websites
  - Check "Use Selenium" for JavaScript-heavy websites (slower but more comprehensive)

### 3. Start Scraping
Click the "🚀 Start Scraping" button to begin the process.

### 4. Monitor Progress
- Real-time status updates appear in the results area
- Each page is displayed as a card showing:
  - ✅ Success or ❌ Error status
  - Page title and URL
  - Content preview (first 300 characters)
  - Word count and links found
  - Timestamp

### 5. Access Results
After scraping completes:
- Check the `results/` folder for exported CSV and JSON files
- Files are named like: `web_scrape_example_com_20241201_143052.csv`

## Scraped Data Fields

Each scraped page contains the following information:

| Field | Description |
|-------|-------------|
| `url` | Full URL of the scraped page |
| `title` | Page title from `<title>` tag |
| `description` | Meta description if available |
| `headings` | All H1-H6 headings found on the page |
| `content` | Main text content (cleaned, first 5000 chars) |
| `word_count` | Total number of words in the content |
| `links_found` | Number of internal links discovered |
| `timestamp` | When the page was scraped |
| `error` | Error message (only present if scraping failed) |

## Use Cases

### 📊 Content Analysis
- Analyze competitor websites
- Research industry trends
- Content audit and inventory
- SEO analysis and optimization

### 📚 Knowledge Base Creation
- Build datasets for AI training
- Create comprehensive documentation
- Research and fact-checking
- Academic research projects

### 🔍 Market Research
- Product information gathering
- Price comparison data
- Feature analysis
- Customer review analysis

### 📈 Business Intelligence
- Competitor monitoring
- Industry news tracking
- Lead generation
- Market opportunity identification

## Technical Details

### Dependencies
- `beautifulsoup4`: HTML parsing and content extraction
- `requests`: HTTP requests for web scraping
- `selenium`: Browser automation for JavaScript sites
- `urllib3`: URL handling and parsing

### Scraping Algorithm
1. **Initialize**: Parse starting URL and set domain restrictions
2. **Queue URLs**: Add starting URL to scraping queue
3. **Process Pages**: For each URL in queue:
   - Fetch page content (requests or Selenium)
   - Extract title, content, and metadata
   - Find internal links and add to queue
   - Display results in real-time
4. **Save Data**: Export to CSV and JSON formats
5. **Complete**: Show summary statistics

### Rate Limiting
- 1-second delay between page requests
- Respectful scraping practices built-in
- Automatic timeout handling (10 seconds per request)

### Error Handling
- Network timeouts and connection errors
- Invalid HTML and parsing errors
- JavaScript rendering issues
- Permission and access restrictions

## Tips for Best Results

### 🎯 Choosing the Right Method
- **Use HTTP Requests when**:
  - Website loads quickly without JavaScript
  - Content is visible in page source
  - You need fast scraping speeds

- **Use Selenium when**:
  - Website heavily relies on JavaScript
  - Content loads dynamically
  - You see empty or missing content with requests method

### 📏 Setting Page Limits
- Start with 10-20 pages for testing
- Increase gradually based on website size
- Consider server load and your bandwidth

### 🛡️ Respecting Websites
- Check robots.txt before scraping
- Don't scrape too aggressively
- Respect rate limits and server resources
- Use data responsibly and ethically

## Troubleshooting

### Common Issues

**Empty Content**
- Try enabling Selenium for JavaScript-heavy sites
- Check if the website blocks automated requests
- Verify the URL is accessible in a browser

**Slow Performance**
- Reduce the max pages limit
- Disable Selenium if not needed
- Check your internet connection speed

**Missing Pages**
- Some pages might not be linked from others
- Check if pages require authentication
- Verify the website structure and navigation

**Selenium Errors**
- Ensure Microsoft Edge is installed
- Check if WebDriver downloads automatically
- Try running without Selenium first

### Getting Help
If you encounter issues:
1. Check the error messages in the scraper results
2. Try with a smaller page limit first
3. Test with different websites to isolate the issue
4. Review the exported files to understand the data structure

## Legal and Ethical Considerations

### ⚖️ Legal Compliance
- Respect website Terms of Service
- Check robots.txt files
- Don't overload servers with requests
- Use scraped data responsibly

### 🤝 Ethical Guidelines
- Don't scrape personal or private information
- Respect copyright and intellectual property
- Give attribution when using scraped content
- Consider contacting website owners for permission

---

**Happy Scraping! 🕷️**

The Web Scraper is designed to be a powerful yet responsible tool for data collection and analysis. Use it wisely and ethically to gather insights and build amazing projects. 