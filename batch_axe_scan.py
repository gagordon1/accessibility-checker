#!/usr/bin/env python3
"""
Batch Axe-Core Scanner for Federal Government Websites
Processes URLs from dotgov-data/current-federal.csv and runs axe-core scans
"""

import csv
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List
from datetime import datetime
import time
import traceback

# Import our url_check scan function
from url_check import scan_url

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def load_federal_urls(csv_path: str) -> List[str]:
    """
    Load URLs from the federal CSV file.
    
    Args:
        csv_path: Path to the federal CSV file
        
    Returns:
        List of domain names (URLs)
    """
    urls = []
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                domain = row.get('Domain name', '').strip()
                if domain:
                    # Add https:// prefix if not present
                    if not domain.startswith(('http://', 'https://')):
                        domain = f'https://{domain}'
                    urls.append(domain)
        
        logger.info(f"Loaded {len(urls)} URLs from {csv_path}")
        return urls
        
    except Exception as e:
        logger.error(f"Failed to load URLs from {csv_path}: {e}")
        raise


def batch_scan_urls(urls: List[str], output_file: str = "federal_axe_violations.json", delay: float = 1.0) -> Dict[str, int]:
    """
    Run axe-core scans on a list of URLs and return violation counts.
    
    Args:
        urls: List of URLs to scan
        output_file: Output JSON file path
        delay: Delay between scans in seconds
        
    Returns:
        Dictionary mapping URL to violation count
    """
    results = {}
    failed_urls = []
    
    logger.info(f"Starting batch scan of {len(urls)} URLs")
    logger.info(f"Results will be saved to: {output_file}")
    
    for i, url in enumerate(urls, 1):
        logger.info(f"[{i}/{len(urls)}] Scanning: {url}")
        
        try:
            # Run scan_url without AI model (axe-core only)
            violations = scan_url(url, model=None)
            violation_count = len(violations)
            
            results[url] = violation_count
            logger.info(f"✅ {url}: {violation_count} violations found")
            
        except Exception as e:
            logger.error(f"❌ Failed to scan {url}: {e}")
            failed_urls.append({"url": url, "error": str(e)})
            results[url] = -1  # Mark as failed
        
        # Save results after each scan for real-time monitoring
        save_results(results, output_file, failed_urls)
        
        # Log progress every 10 scans
        if i % 10 == 0:
            logger.info(f"Progress checkpoint - {i}/{len(urls)} completed")
        
        # Delay between requests to be respectful
        if i < len(urls):  # Don't delay after the last URL
            time.sleep(delay)
    
    # Final save
    save_results(results, output_file, failed_urls)
    
    # Summary
    successful_scans = sum(1 for count in results.values() if count >= 0)
    total_violations = sum(count for count in results.values() if count >= 0)
    
    logger.info(f"\n📊 Batch Scan Summary:")
    logger.info(f"Total URLs processed: {len(urls)}")
    logger.info(f"Successful scans: {successful_scans}")
    logger.info(f"Failed scans: {len(failed_urls)}")
    logger.info(f"Total violations found: {total_violations}")
    logger.info(f"Results saved to: {output_file}")
    
    return results


def save_results(results: Dict[str, int], output_file: str, failed_urls: List[Dict]):
    """Save results to JSON file with metadata."""
    
    # Prepare output data
    output_data = {
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "total_urls": len(results),
            "successful_scans": sum(1 for count in results.values() if count >= 0),
            "failed_scans": sum(1 for count in results.values() if count < 0),
            "total_violations": sum(count for count in results.values() if count >= 0)
        },
        "violation_counts": results,
        "failed_urls": failed_urls
    }
    
    # Ensure output directory exists
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    
    # Save to JSON
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)


def main():
    """Main function to run the batch scanner."""
    
    # Configuration
    csv_file = "dotgov-data/current-federal.csv"
    output_file = "results/federal_axe_violations.json"
    delay_seconds = 1.0  # Delay between scans
    
    try:
        # Load URLs from CSV
        urls = load_federal_urls(csv_file)
        
        if not urls:
            logger.error("No URLs found in CSV file")
            return
        
        # Ask user if they want to proceed
        logger.info(f"\nAbout to scan {len(urls)} federal government websites")
        logger.info(f"Estimated time: ~{len(urls) * 30 / 60:.1f} minutes")
        logger.info(f"Results will be saved to: {output_file}")
        
        proceed = input("\nProceed with batch scan? (y/N): ").strip().lower()
        if proceed != 'y':
            logger.info("Scan cancelled.")
            return
        
        # Run batch scan
        results = batch_scan_urls(urls, output_file, delay_seconds)
        
    except KeyboardInterrupt:
        logger.info("Scan interrupted by user")
    except Exception as e:
        logger.error(f"Batch scan failed: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    main() 