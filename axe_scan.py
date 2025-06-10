#!/usr/bin/env python3
"""
Axe-Core Scanner Python Wrapper
Runs the TypeScript axe-core scanner using subprocess and returns Violation objects
"""

import subprocess
import sys
import os
from pathlib import Path
import json
import argparse
import logging
from typing import List, Optional

# Import the violation types to match the structure used by url_check.py
from type_hints.wcag_types import Violation, NodeResult

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def run_axe_scan(url: str, output_file: Optional[str] = None) -> List[Violation]:
    """
    Run the axe-core TypeScript scanner on a given URL
    
    Args:
        url: The URL to scan
        output_file: Optional path to save the violations JSON (if None, uses temp file)
        
    Returns:
        List[Violation]: List of accessibility violations found
    """
    # Use temp file if no output specified
    temp_file_created = False
    if output_file is None:
        output_file = f"temp_axe_scan_{url.replace('/', '_').replace(':', '')}.json"
        temp_file_created = True
    
    # Construct the command
    cmd = [
        "npx", "ts-node", 
        "axe-core-screen/src/axe-core-scan.ts",
        "--url", url,
        "--output", output_file
    ]
    
    logger.info(f"Running axe-core scan on: {url}")
    logger.info(f"Command: {' '.join(cmd)}")
    logger.info("-" * 50)
    
    try:
        # Run the command
        result = subprocess.run(
            cmd,
            cwd=Path.cwd(),  # Run from current directory
            capture_output=True,
            text=True,
            timeout=120  # 2 minute timeout
        )
        
        # Print stderr if there are any warnings/errors
        if result.stderr:
            logger.info("STDERR:")
            logger.info(result.stderr)
        
        # Check if command succeeded
        if result.returncode == 0:
            logger.info(f"✅ Scan completed successfully!")
            
            # Read and parse the violations JSON
            if os.path.exists(output_file):
                with open(output_file, 'r') as f:
                    data = json.load(f)
                
                # Convert axe violations to our Violation format
                violations = []
                axe_violations = data.get('violations', [])
                
                for axe_violation in axe_violations:
                    # Convert axe nodes to our NodeResult format
                    nodes = []
                    for axe_node in axe_violation.get('nodes', []):
                        node = NodeResult(
                            html=axe_node.get('html', ''),
                            target=axe_node.get('target', []),
                            failureSummary=axe_node.get('failureSummary')
                        )
                        nodes.append(node)
                    
                    # Create Violation object
                    violation = Violation(
                        id=axe_violation.get('id', ''),
                        description=axe_violation.get('description', ''),
                        nodes=nodes,
                        impact=axe_violation.get('impact')
                    )
                    violations.append(violation)
                
                logger.info(f"📊 Found {len(violations)} accessibility violations")
                
                # Show top violation types
                if violations:
                    logger.info("\n🔍 Top violation types:")
                    violation_types = {}
                    for v in violations:
                        violation_types[v.id] = violation_types.get(v.id, 0) + 1
                    
                    for v_type, count in sorted(violation_types.items(), key=lambda x: x[1], reverse=True)[:5]:
                        logger.info(f"  • {v_type}: {count} instances")
                
                return violations
            else:
                raise RuntimeError(f"Output file {output_file} was not created")
                
        else:
            raise RuntimeError(f"Scan failed with return code: {result.returncode}")
            
    except subprocess.TimeoutExpired:
        raise RuntimeError("Scan timed out after 2 minutes")
    except FileNotFoundError:
        raise RuntimeError("Command not found. Make sure Node.js and npm are installed.")
    except Exception as e:
        raise RuntimeError(f"Error running scan: {e}")
    finally:
        # Always clean up temp file if we created one, regardless of success or failure
        if temp_file_created and os.path.exists(output_file):
            try:
                os.remove(output_file)
                logger.debug(f"Cleaned up temporary file: {output_file}")
            except Exception as e:
                logger.warning(f"Failed to clean up temporary file {output_file}: {e}")


def scan_url_with_axe(url: str, output_file: Optional[str] = None) -> List[Violation]:
    """
    Alias function that matches the interface of scan_url from url_check.py
    
    Args:
        url: The URL to scan
        output_file: Optional path to save the violations JSON
        
    Returns:
        List[Violation]: List of accessibility violations found
    """
    return run_axe_scan(url, output_file)


def main():
    parser = argparse.ArgumentParser(description="Run axe-core accessibility scan via Python subprocess")
    parser.add_argument("--url", default="https://arc.gov", help="URL to scan")
    parser.add_argument("--output", help="Output JSON file (optional)")
    
    args = parser.parse_args()
    
    try:
        # Run the scan and get violations
        violations = run_axe_scan(args.url, args.output)
        
        # Print summary
        print(f"\n📋 Scan Results Summary:")
        print(f"Total violations: {len(violations)}")
        
        # Print detailed violations if requested
        if len(violations) > 0:
            print("\n🔍 Detailed violations:")
            for i, violation in enumerate(violations[:3], 1):  # Show first 3
                print(f"{i}. {violation.id}: {violation.description}")
                print(f"   Impact: {violation.impact}")
                print(f"   Affected elements: {len(violation.nodes)}")
            
            if len(violations) > 3:
                print(f"   ... and {len(violations) - 3} more violations")
        
    except RuntimeError as e:
        print(f"❌ {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Default run with the specified parameters
    if len(sys.argv) == 1:  # No arguments provided
        print("Running default scan: https://arc.gov")
        try:
            violations = run_axe_scan("https://arc.gov")
            print(f"\n📋 Found {len(violations)} total violations")
        except RuntimeError as e:
            print(f"❌ {e}")
            sys.exit(1)
    else:
        main()
