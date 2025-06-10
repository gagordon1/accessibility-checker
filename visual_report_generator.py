#!/usr/bin/env python3
"""
Visual Report Generator for WCAG Violations
Fetches HTML, queries database for violations, and highlights them with red boxes
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict
import argparse
from bs4 import BeautifulSoup
from collections import defaultdict
import base64

from utils.scrape import normalize_url, capture_website_with_playwright
from app import get_cached_violations
from playwright.sync_api import sync_playwright

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class VisualReportGenerator:
    """Generate visual accessibility reports with highlighted violations"""
    
    def __init__(self):
        # No longer need backend_url since we're calling the function directly
        pass
    
    def get_violations_from_database(self, url: str) -> List[Dict]:
        """
        Get violations data directly from cached violations file
        
        Args:
            url: The URL to get violations for
            
        Returns:
            List of violation dictionaries from the database
        """
        try:
            logger.info(f"Getting cached violations for: {url}")
            
            cached_data = get_cached_violations(url)
            
            if cached_data:
                violations = cached_data.get('violations', [])
                logger.info(f"Retrieved {len(violations)} cached violations")
                return violations
            else:
                logger.warning(f"No cached violations found for {url}")
                return []
            
        except Exception as e:
            logger.error(f"Failed to get cached violations: {e}")
            raise
    
    def group_violations_by_type(self, violations: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Group violations by their type/rule ID
        
        Args:
            violations: List of violation dictionaries
            
        Returns:
            Dictionary with violation types as keys and lists of violations as values
        """
        grouped = defaultdict(list)
        
        for violation in violations:
            rule_id = violation.get('id', 'unknown')
            grouped[rule_id].append(violation)
        
        # Sort by rule ID for consistent ordering
        return dict(sorted(grouped.items()))
    
    def create_annotated_website_screenshot(self, url: str, violations: List[Dict]) -> str:
        """
        Create an annotated screenshot by injecting highlights directly into the DOM
        
        Args:
            url: The URL to capture
            violations: List of violation dictionaries with target selectors
            
        Returns:
            Base64 encoded PNG with violation annotations
        """
        logger.info(f"Creating annotated website screenshot for {url}")
        
        # Get violation targets and create numbered list
        violation_targets = []
        violation_number = 0
        
        for violation in violations:
            nodes = violation.get('nodes', [])
            for node in nodes:
                targets = node.get('target', [])
                for target in targets:
                    violation_number += 1
                    violation_targets.append({
                        'number': violation_number,
                        'target': target,
                        'impact': violation.get('impact', 'unknown')
                    })
        
        if not violation_targets:
            logger.info("No violation targets found, returning clean screenshot")
            # Return clean screenshot if no violations
            _, _, clean_png = capture_website_with_playwright(url)
            return clean_png
        
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(device_scale_factor=1)
            page.goto(url, wait_until="networkidle")
            
            # Scroll through page to trigger lazy loading
            page.evaluate("""
                async () => {
                    let totalHeight = 0;
                    const distance = 500;
                    while (totalHeight < document.body.scrollHeight) {
                        window.scrollBy(0, distance);
                        totalHeight += distance;
                        await new Promise(resolve => setTimeout(resolve, 500));
                    }
                }
            """)
            
            # Inject CSS for violation highlights
            page.add_style_tag(content="""
                .wcag-violation-highlight {
                    position: relative !important;
                    outline: 3px solid #ff0000 !important;
                    outline-offset: 2px !important;
                    background-color: rgba(255, 0, 0, 0.1) !important;
                    z-index: 9999 !important;
                }
                
                .wcag-violation-number {
                    position: absolute !important;
                    top: -15px !important;
                    left: -5px !important;
                    background-color: #ff0000 !important;
                    color: white !important;
                    font-size: 14px !important;
                    font-weight: bold !important;
                    padding: 4px 8px !important;
                    border-radius: 50% !important;
                    z-index: 10000 !important;
                    font-family: Arial, sans-serif !important;
                    min-width: 20px !important;
                    min-height: 20px !important;
                    display: flex !important;
                    align-items: center !important;
                    justify-content: center !important;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.3) !important;
                }
                
                .wcag-violation-serious .wcag-violation-number {
                    background-color: #ff6600 !important;
                }
                
                .wcag-violation-moderate .wcag-violation-number {
                    background-color: #ffcc00 !important;
                    color: black !important;
                }
                
                .wcag-violation-minor .wcag-violation-number {
                    background-color: #00aa00 !important;
                }
            """)
            
            # Inject violation highlights for each target
            successful_annotations = 0
            for violation_target in violation_targets:
                try:
                    target_selector = violation_target['target']
                    number = violation_target['number']
                    impact = violation_target['impact']
                    
                    # Try to find and annotate the element
                    success = page.evaluate(f"""
                        () => {{
                            try {{
                                const element = document.querySelector('{target_selector}');
                                if (element) {{
                                    // Add highlight class
                                    element.classList.add('wcag-violation-highlight');
                                    element.classList.add('wcag-violation-{impact}');
                                    
                                    // Create number badge
                                    const badge = document.createElement('div');
                                    badge.className = 'wcag-violation-number';
                                    badge.textContent = '{number}';
                                    
                                    // Position the badge
                                    element.style.position = element.style.position || 'relative';
                                    element.appendChild(badge);
                                    
                                    return true;
                                }}
                                return false;
                            }} catch (e) {{
                                console.log('Error annotating element:', e);
                                return false;
                            }}
                        }}
                    """)
                    
                    if success:
                        successful_annotations += 1
                        logger.debug(f"Successfully annotated violation {number}: {target_selector}")
                    else:
                        logger.warning(f"Could not find element for violation {number}: {target_selector}")
                        
                except Exception as e:
                    logger.warning(f"Error annotating violation {violation_target['number']}: {e}")
            
            # Wait a moment for annotations to render
            page.wait_for_timeout(1000)
            
            # Take screenshot with annotations
            png_screenshot = page.screenshot(full_page=True, type='png')
            png_base64 = base64.b64encode(png_screenshot).decode('utf-8')
            
            browser.close()
        
        logger.info(f"Created annotated screenshot with {successful_annotations}/{len(violation_targets)} successful annotations")
        return png_base64
    
    def generate_report(self, url: str, output_dir: str = "reports") -> Dict:
        """
        Generate a visual accessibility report for a URL
        
        Args:
            url: The URL to scan
            output_dir: Directory to save report files
            
        Returns:
            Dictionary with report metadata and file paths
        """
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Sanitize URL for filename
        safe_url = url.replace('https://', '').replace('http://', '').replace('/', '_').replace(':', '_')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        report_data = {
            "url": url,
            "timestamp": datetime.now().isoformat(),
            "files": {}
        }
        
        logger.info(f"Generating visual report for: {url}")
        
        # Step 1: Get violations from database
        logger.info("Querying database for violations...")
        violations = self.get_violations_from_database(url)
        report_data["violation_count"] = len(violations)
        
        if not violations:
            logger.warning(f"No violations found in database for {url}")
            logger.info("You may need to run an axe scan first to populate the database")
        
        # Step 2: Create annotated screenshot with violation highlights injected into DOM
        logger.info("Creating annotated website screenshot...")
        if violations:
            png_base64 = self.create_annotated_website_screenshot(url, violations)
        else:
            logger.info("No violations found, using clean screenshot")
            _, _, png_base64 = capture_website_with_playwright(url, take_screenshot=False)
        
        # Step 3: Group violations by type and create numbered list
        logger.info("Processing violations...")
        grouped_violations = self.group_violations_by_type(violations)
        numbered_violations = self.create_numbered_violations_list(violations)
        
        # Step 4: Create comprehensive report with embedded screenshot and violation details
        logger.info("Generating comprehensive report...")
        comprehensive_report = self._generate_comprehensive_report_with_image(
            report_data, png_base64, numbered_violations, output_path, safe_url, timestamp
        )
        report_data["files"]["comprehensive_report"] = comprehensive_report
        
        logger.info(f"Comprehensive report generated successfully!")
        return report_data
    
    def create_numbered_violations_list(self, violations: List[Dict]) -> List[Dict]:
        """
        Create a numbered list of all violations for reference
        
        Args:
            violations: List of violation dictionaries
            
        Returns:
            List of numbered violations with details
        """
        numbered_violations = []
        violation_number = 0
        
        for violation in violations:
            nodes = violation.get('nodes', [])
            
            for node in nodes:
                targets = node.get('target', [])
                
                for target in targets:
                    violation_number += 1
                    
                    numbered_violations.append({
                        'number': violation_number,
                        'rule_id': violation.get('id', 'unknown'),
                        'description': violation.get('description', 'No description'),
                        'impact': violation.get('impact', 'unknown'),
                        'target': target,
                        'html': node.get('html', ''),
                        'failure_summary': node.get('failureSummary', 'No failure summary available'),
                        'help': violation.get('help', 'No help available'),
                        'help_url': violation.get('helpUrl', '')
                    })
        
        logger.info(f"Created {len(numbered_violations)} numbered violation entries")
        return numbered_violations
    
    def _create_violation_details_html(self, numbered_violations: List[Dict]) -> str:
        """Create HTML for violation details section"""
        if not numbered_violations:
            return "<p>No violations found.</p>"
        
        violation_items = []
        for violation in numbered_violations:
            impact_color = {
                'critical': '#dc3545',
                'serious': '#fd7e14', 
                'moderate': '#ffc107',
                'minor': '#28a745'
            }.get(violation['impact'], '#6c757d')
            
            html_snippet = ""
            if violation['html']:
                html_content = violation['html'][:200]
                if len(violation['html']) > 200:
                    html_content += "..."
                html_snippet = f'<div class="html-snippet"><strong>HTML:</strong><br><code>{html_content}</code></div>'
            
            violation_items.append(f'''
            <div class="violation-detail" style="border-left: 4px solid {impact_color};">
                <h4>#{violation['number']} - {violation['rule_id']}</h4>
                <p><strong>Impact:</strong> <span style="color: {impact_color}; font-weight: bold;">{violation['impact'].title()}</span></p>
                <p><strong>Description:</strong> {violation['description']}</p>
                <p><strong>Target Element:</strong> <code>{violation['target']}</code></p>
                <div class="failure-summary">
                    <strong>Issue:</strong> {violation['failure_summary']}
                </div>
                {html_snippet}
            </div>
            ''')
        
        return ''.join(violation_items)
    
    def _generate_comprehensive_report_with_image(self, report_data: Dict, png_base64: str, 
                                                 numbered_violations: List[Dict], output_path: Path, 
                                                 safe_url: str, timestamp: str) -> str:
        """Generate a comprehensive HTML report with embedded screenshot and violation details"""
        
        # Create the comprehensive HTML document
        comprehensive_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Comprehensive Accessibility Report - {report_data['url']}</title>
            <style>
                /* Report Summary Styles */
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 0; line-height: 1.6; }}
                .report-header {{ background: linear-gradient(135deg, #ff6b6b, #ee5a52); color: white; padding: 30px; margin-bottom: 30px; }}
                .report-header h1 {{ margin: 0; font-size: 2em; }}
                .report-header p {{ margin: 5px 0; opacity: 0.9; }}
                
                .report-summary {{ background: #f8f9fa; padding: 25px; margin: 0 30px 30px 30px; border-radius: 8px; border-left: 5px solid #ff6b6b; }}
                
                /* Website Content Separator */
                .website-section {{ border-top: 3px solid #007bff; margin: 30px 0; padding: 20px 30px; background: #f8f9fc; }}
                .website-section h2 {{ color: #007bff; margin-top: 0; }}
                
                /* Website Content Container */
                .website-content {{ margin: 20px; padding: 20px; border: 2px dashed #007bff; border-radius: 8px; background: white; text-align: center; }}
                .website-content img {{ max-width: 100%; height: auto; border: 1px solid #ddd; border-radius: 4px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }}
                
                /* Violation Details Styles */
                .violation-details-section {{ background: #fff; padding: 30px; margin: 30px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
                .violation-detail {{ background: white; padding: 20px; margin: 15px 0; border-radius: 8px; border: 1px solid #e9ecef; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .violation-detail h4 {{ color: #dc3545; margin-top: 0; font-size: 1.1em; }}
                .failure-summary {{ background: #fff3cd; padding: 10px; border-radius: 4px; margin: 10px 0; border-left: 3px solid #ffc107; }}
                .html-snippet {{ background: #f8f9fa; padding: 10px; border-radius: 4px; margin: 10px 0; font-family: 'Courier New', monospace; font-size: 0.9em; }}
                .html-snippet code {{ background: none; }}
                code {{ background: #e9ecef; padding: 2px 4px; border-radius: 3px; font-size: 0.9em; }}
            </style>
        </head>
        <body>
            <!-- Report Summary Section -->
            <div class="report-header">
                <h1>🔍 Comprehensive Accessibility Report</h1>
                <p><strong>Website:</strong> {report_data['url']}</p>
                <p><strong>Generated:</strong> {report_data['timestamp']}</p>
                <p><strong>Total Violations:</strong> {report_data['violation_count']}</p>
            </div>
            
            <div class="report-summary">
                <h2>📊 Executive Summary</h2>
                <p>This comprehensive report contains the complete accessibility analysis for the website. 
                   The screenshot below shows the website as it appeared during scanning.</p>
                <p><strong>Found {len(numbered_violations)} specific violation instances</strong> that need attention.</p>
                <p>Review the detailed explanations below the screenshot for specific guidance on each violation.</p>
            </div>
            
            <!-- Website Content Section -->
            <div class="website-section">
                <h2>🌐 Website Screenshot</h2>
                <p>The website captured during accessibility scanning is displayed below.</p>
            </div>
            
            <!-- Website Screenshot -->
            <div class="website-content">
                <img src="data:image/png;base64,{png_base64}" alt="Website Screenshot" style="cursor: zoom-in;" onclick="this.style.transform = this.style.transform ? '' : 'scale(1.5)'; this.style.transition = 'transform 0.3s';">
                <p style="margin-top: 10px; font-size: 0.9em; color: #666;">Click image to zoom</p>
            </div>
            
            <!-- Violation Details Section -->
            <div class="violation-details-section">
                <h2>🔍 Detailed Violation Analysis</h2>
                <p>Each violation found during the accessibility scan is explained in detail below:</p>
                {self._create_violation_details_html(numbered_violations)}
            </div>
            
        </body>
        </html>
        """
        
        # Save the comprehensive report
        report_file = output_path / f"{safe_url}_{timestamp}_comprehensive.html"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(comprehensive_html)
        
        logger.info(f"Comprehensive report saved: {report_file}")
        return str(report_file)


def main():
    """Main function for command line usage"""
    parser = argparse.ArgumentParser(description="Generate visual accessibility reports")
    parser.add_argument("url", help="URL to scan")
    parser.add_argument("--output", "-o", default="reports", 
                       help="Output directory for reports (default: reports)")
    
    args = parser.parse_args()
    
    try:
        # Create report generator
        generator = VisualReportGenerator()
        
        # Generate report
        report_data = generator.generate_report(args.url, args.output)
        
        print(f"\n✅ Report generated successfully!")
        print(f"📁 Output directory: {args.output}")
        print(f"🔍 Violations found: {report_data['violation_count']}")
        print(f"📄 Comprehensive Report: {report_data['files']['comprehensive_report']}")
        print(f"🌐 View violations on website: {args.url}")
    
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        raise


if __name__ == "__main__":
    main() 