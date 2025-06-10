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
from collections import defaultdict
import base64

from utils.scrape import capture_website_with_playwright, resize_viewport_to_full_page
from utils.highlight_violations import highlight_violations_on_page
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
        Create an annotated screenshot using the proven extension highlighting logic
        
        Args:
            url: The URL to capture
            violations: List of violation dictionaries with target selectors
            
        Returns:
            Base64 encoded PNG with violation annotations
        """
        logger.info(f"Creating annotated website screenshot for {url}")
        
        if not violations:
            logger.info("No violations found, returning clean screenshot")
            # Return clean screenshot if no violations
            _, _, clean_png = capture_website_with_playwright(url)
            return clean_png
        
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(device_scale_factor=1)
            page.goto(url, wait_until="networkidle")
            
            # Resize viewport to capture full content efficiently
            resize_viewport_to_full_page(page)
            
            # Use the reusable highlighting utility
            result = highlight_violations_on_page(page, violations)
            
            # Wait for annotations to render
            page.wait_for_timeout(1000)
            
            # Take screenshot with annotations
            png_screenshot = page.screenshot(full_page=True, type='png')
            png_base64 = base64.b64encode(png_screenshot).decode('utf-8')
            
            browser.close()
        
        successful = result.get('successful_annotations', 0)
        total = result.get('total_violations', 0)
        logger.info(f"Created annotated screenshot with {successful}/{total} successful annotations")
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
        numbered_violations = self.create_numbered_violations_list(url, violations)
        
        # Step 4: Create comprehensive report with embedded screenshot and violation details
        logger.info("Generating comprehensive report...")
        comprehensive_report = self._generate_comprehensive_report_with_image(
            report_data, png_base64, numbered_violations, output_path, safe_url, timestamp
        )
        report_data["files"]["comprehensive_report"] = comprehensive_report
        
        # Step 5: Generate PDF version of the report
        logger.info("Generating PDF report...")
        pdf_report = self._generate_pdf_report(comprehensive_report, output_path, safe_url, timestamp)
        report_data["files"]["pdf_report"] = pdf_report
        
        logger.info(f"Reports generated successfully!")
        return report_data
    
    def create_numbered_violations_list(self, url: str, violations: List[Dict]) -> List[Dict]:
        """
        Create a numbered list that matches exactly what the JavaScript annotation logic produces
        This queries the actual DOM to count elements per selector, ensuring 1:1 alignment
        
        Args:
            url: The URL to query for element counts
            violations: List of violation dictionaries
            
        Returns:
            List of numbered violations with details that match the annotations
        """
        numbered_violations = []
        violation_number = 0
        
        # We need to query the actual DOM to count elements like the JavaScript does
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(url, wait_until="networkidle")
            
            # Resize viewport to match what we do for annotations
            resize_viewport_to_full_page(page)
            
            for violation in violations:
                nodes = violation.get('nodes', [])
                
                for node in nodes:
                    targets = node.get('target', [])
                    
                    for target in targets:
                        try:
                            # Count how many elements this selector will match (same as JavaScript)
                            element_count = page.evaluate(f"document.querySelectorAll('{target}').length")
                            
                            # Create one description entry for each element that will be annotated
                            for element_index in range(element_count):
                                violation_number += 1
                                
                                numbered_violations.append({
                                    'number': violation_number,
                                    'rule_id': violation.get('id', 'unknown'),
                                    'description': violation.get('description', 'No description'),
                                    'impact': violation.get('impact', 'unknown'),
                                    'target': target,
                                    'element_index': element_index + 1,  # Human-readable index
                                    'total_elements': element_count,      # Total for this selector
                                    'html': node.get('html', ''),
                                    'failure_summary': node.get('failureSummary', 'No failure summary available'),
                                    'help': violation.get('help', 'No help available'),
                                    'help_url': violation.get('helpUrl', '')
                                })
                                
                        except Exception as e:
                            # If selector fails, still create one entry
                            violation_number += 1
                            numbered_violations.append({
                                'number': violation_number,
                                'rule_id': violation.get('id', 'unknown'),
                                'description': violation.get('description', 'No description'),
                                'impact': violation.get('impact', 'unknown'),
                                'target': target,
                                'element_index': 1,
                                'total_elements': 1,
                                'html': node.get('html', ''),
                                'failure_summary': node.get('failureSummary', 'No failure summary available'),
                                'help': violation.get('help', 'No help available'),
                                'help_url': violation.get('helpUrl', '')
                            })
                            logger.warning(f"Failed to count elements for selector '{target}': {e}")
            
            browser.close()
        
        logger.info(f"Created {len(numbered_violations)} numbered violation entries matching DOM element count")
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
            
            # Show element index if there are multiple elements for this selector
            element_info = ""
            if violation.get('total_elements', 1) > 1:
                element_info = f" (Element {violation.get('element_index', 1)} of {violation.get('total_elements', 1)})"
            
            violation_items.append(f'''
            <div class="violation-detail" style="border-left: 4px solid {impact_color};">
                <h4>#{violation['number']} - {violation['rule_id']}{element_info}</h4>
                <p><strong>Impact:</strong> <span style="color: {impact_color}; font-weight: bold;">{violation['impact'].title()}</span></p>
                <p><strong>Description:</strong> {violation['description']}</p>
                <p><strong>Target Element:</strong> <code>{violation['target']}</code></p>
                <div class="failure-summary">
                    <strong>Issue:</strong> {violation['failure_summary']}
                </div>
            </div>
            ''')
        
        return ''.join(violation_items)
    
    def _generate_pdf_report(self, html_file_path: str, output_path: Path, safe_url: str, timestamp: str) -> str:
        """
        Generate a PDF version of the HTML report using Playwright
        
        Args:
            html_file_path: Path to the HTML report file
            output_path: Directory to save the PDF
            safe_url: Sanitized URL for filename
            timestamp: Timestamp string for filename
            
        Returns:
            Path to the generated PDF file
        """
        try:
            pdf_file = output_path / f"{safe_url}_{timestamp}_comprehensive.pdf"
            
            with sync_playwright() as p:
                browser = p.chromium.launch()
                page = browser.new_page()
                
                # Load the HTML file
                html_file_url = f"file://{Path(html_file_path).absolute()}"
                page.goto(html_file_url, wait_until="networkidle")
                
                # Get the full content height to create one long page
                content_height = page.evaluate("document.body.scrollHeight")
                
                # Set a reasonable width (A4 width in pixels at 96 DPI)
                page_width = 794  # ~8.27 inches at 96 DPI (A4 width)
                
                # Add some padding to the height to ensure nothing gets cut off
                page_height = content_height + 100
                
                # Generate PDF as one long page with custom dimensions
                page.pdf(
                    path=str(pdf_file),
                    width=f"{page_width}px",
                    height=f"{page_height}px",
                    print_background=True,
                    margin={
                        'top': '0.5cm',
                        'right': '0.5cm', 
                        'bottom': '0.5cm',
                        'left': '0.5cm'
                    }
                )
                
                browser.close()
            
            logger.info(f"PDF report saved as single long page: {pdf_file}")
            return str(pdf_file)
            
        except Exception as e:
            logger.error(f"Failed to generate PDF report: {e}")
            raise
    
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
        print(f"📄 HTML Report: {report_data['files']['comprehensive_report']}")
        print(f"📋 PDF Report: {report_data['files']['pdf_report']}")
        print(f"🌐 View violations on website: {args.url}")
    
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        raise


if __name__ == "__main__":
    main() 