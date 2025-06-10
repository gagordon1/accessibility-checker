# Accessibility Checker

A comprehensive WCAG 2.2 accessibility scanning tool that combines automated axe-core testing with AI-powered analysis to identify accessibility violations on websites.

## Features

- **Automated axe-core scanning** for standards-based accessibility testing
- **AI-powered WCAG analysis** using OpenAI GPT-4 or DeepSeek models
- **Visual accessibility reports** with highlighted violation screenshots
- **HTML and PDF report generation** for professional accessibility audits
- **Batch processing** of multiple URLs from CSV files
- **Federal government website scanning** using .gov domain data
- **Real-time progress monitoring** with JSON output
- **Low hanging fruit identification** for prioritizing accessibility fixes

## Installation

### Prerequisites

- Python 3.8 or higher
- Node.js 16 or higher
- npm (comes with Node.js)

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/accessibility-checker.git
cd accessibility-checker
```

### 2. Python Dependencies

Create a virtual environment and install Python packages:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Install Playwright browsers:

```bash
playwright install
```

### 3. JavaScript Dependencies

Install the axe-core scanning dependencies:

```bash
cd axe-core-screen
npm install
cd ..
```

### 4. Environment Setup

Create a `.env` file in the root directory with your API keys:

```bash
# For AI-powered analysis (optional)
OPENAI_API_KEY=your_openai_api_key_here
DEEPSEEK_API_KEY=your_deepseek_api_key_here

# Vector store for WCAG rules (if using AI features)
WCAG_RULES_VECTOR_STORE_ID=your_vector_store_id
```

## Usage

### Single URL Scanning with `url_check.py`

Scan a single website for accessibility violations:

```bash
# Axe-core only (no AI)
python url_check.py https://example.com

# With AI analysis using OpenAI GPT-4
python url_check.py https://example.com --model gpt-4o

# With AI analysis using DeepSeek
python url_check.py https://example.com --model deepseek-chat
```

**Available Models:**
- `gpt-4o` - OpenAI GPT-4 Omni (requires OPENAI_API_KEY)
- `gpt-4o-mini` - OpenAI GPT-4 Omni Mini (requires OPENAI_API_KEY)  
- `deepseek-chat` - DeepSeek Chat (requires DEEPSEEK_API_KEY)

**Output:**
- Violations saved to `violations/violations.json`
- Screenshots saved to `model_context/screenshot.png` (when using AI)
- Console output with violation counts and details

### Batch Scanning with `batch_axe_scan.py`

Process multiple federal government websites from the .gov domains CSV:

```bash
python batch_axe_scan.py
```

**Features:**
- Loads URLs from `dotgov-data/current-federal.csv`
- Runs axe-core scans on each domain (AI analysis disabled for batch processing)
- Saves results to `results/federal_axe_violations.json` after each scan
- Real-time progress monitoring
- Identifies "low hanging fruit" - sites with ≤5 violations
- Respectful 1-second delay between scans

**Interactive Prompts:**
- Shows estimated scan time based on number of URLs
- Requires confirmation before starting batch process
- Can be interrupted with Ctrl+C

**Output Format:**
```json
{
  "metadata": {
    "timestamp": "2024-01-15T10:30:00",
    "total_urls": 1500,
    "successful_scans": 1450,
    "failed_scans": 50,
    "total_violations": 25000
  },
  "violation_counts": {
    "https://example.gov": 5,
    "https://another.gov": 12,
    "https://failed-site.gov": -1
  },
  "failed_urls": [
    {"url": "https://failed-site.gov", "error": "Connection timeout"}
  ]
}
```

### Visual Report Generation with `visual_report_generator.py`

Generate professional accessibility reports with annotated screenshots showing where violations occur on the webpage:

```bash
# Generate visual report for a single URL
python visual_report_generator.py https://example.com

# Specify custom output directory
python visual_report_generator.py https://example.com --output my-reports
```

**Prerequisites:**
- Must run an axe-core scan first (`url_check.py` or `batch_axe_scan.py`) to populate violation data
- Uses cached violation data from previous scans

**Features:**
- **Annotated Screenshots**: Full-page website screenshots with red numbered boxes highlighting each violation
- **Comprehensive Reports**: Detailed HTML reports with embedded screenshots and violation explanations
- **PDF Generation**: Professional PDF reports as single continuous pages (no page breaks)
- **Violation Details**: Each violation includes description, impact level, target selector, and remediation guidance
- **Impact Color Coding**: Visual indicators for critical, serious, moderate, and minor violations

**Report Contents:**
- Executive summary with violation count and timestamp
- Full-page website screenshot with numbered violation annotations
- Detailed breakdown of each violation with:
  - WCAG rule ID and description
  - Impact level (Critical, Serious, Moderate, Minor)
  - CSS selector targeting the problematic element
  - Specific failure explanation
  - Element index information for multi-element violations

**Output Files:**
- `reports/[domain]_[timestamp]_comprehensive.html` - Interactive HTML report
- `reports/[domain]_[timestamp]_comprehensive.pdf` - Printable PDF report (single long page)

**Example Workflow:**
```bash
# Step 1: Scan website for violations
python url_check.py https://example.com

# Step 2: Generate visual report
python visual_report_generator.py https://example.com

# Step 3: Open generated reports
open reports/example_com_20241201_143022_comprehensive.html
open reports/example_com_20241201_143022_comprehensive.pdf
```

### Monitoring Progress

Since `batch_axe_scan.py` saves results after each scan, you can monitor progress in real-time:

```bash
# Watch the results file update
tail -f results/federal_axe_violations.json

# Or check specific stats
cat results/federal_axe_violations.json | jq '.metadata'

# Find low hanging fruit
cat results/federal_axe_violations.json | jq '.violation_counts | to_entries | map(select(.value >= 0 and .value <= 5)) | sort_by(.value)'
```

## Output Files

### Violation Data
- `violations/violations.json` - Single URL scan results with full violation details
- `results/federal_axe_violations.json` - Batch scan results with violation counts

### Visual Reports
- `reports/[domain]_[timestamp]_comprehensive.html` - Interactive HTML accessibility report with annotated screenshots
- `reports/[domain]_[timestamp]_comprehensive.pdf` - Professional PDF accessibility report (single continuous page)

### Screenshots and Context
- `model_context/screenshot.png` - Full page screenshot (when using AI models)
- `temp_axe_scan_*.json` - Temporary axe-core results (cleaned up automatically)

## Federal Government Data

The project includes federal government domain data from the .gov registry:

- `dotgov-data/current-federal.csv` - Current federal domains
- Updated regularly from the official .gov data source
- Contains ~1,500+ federal government websites

## AI Models Comparison

| Model | Provider | Speed | Quality | Cost |
|-------|----------|-------|---------|------|
| gpt-4o | OpenAI | Medium | Excellent | High |
| gpt-4o-mini | OpenAI | Fast | Good | Medium |
| deepseek-chat | DeepSeek | Fast | Good | Low |

## Troubleshooting

### Common Issues

1. **Playwright browser not found**
   ```bash
   playwright install
   ```

2. **Node.js dependencies missing**
   ```bash
   cd axe-core-screen && npm install
   ```

3. **Permission errors on macOS/Linux**
   ```bash
   chmod +x batch_axe_scan.py url_check.py visual_report_generator.py
   ```

4. **API key errors**
   - Ensure `.env` file exists with valid API keys
   - Check that environment variables are loaded

5. **Visual report generator shows "No violations found"**
   - Run `url_check.py` or `batch_axe_scan.py` first to populate violation data
   - Check that `violations/violations.json` exists and contains data for the target URL

6. **PDF generation fails**
   - Ensure Playwright browsers are installed: `playwright install`
   - Check that HTML report is generated successfully first
   - Verify sufficient disk space for PDF creation

### Performance Tips

- For large batch scans, consider running on a server with good internet connectivity
- Monitor disk space as violation data and screenshots can accumulate
- Use `--model` parameter only when detailed AI analysis is needed (slower but more comprehensive)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Next Steps

1. Create API endpoints for web integration
2. Develop browser extension for real-time scanning
3. Build web interface for results visualization
4. Enhance AI features for detecting additional accessibility issues