from flask import Flask, jsonify, request
from llm_check import scan_url
import json
from pathlib import Path
from utils.scrape import normalize_url
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

def get_cached_violations(url: str) -> dict | None:
    """Get cached violations for a URL if they exist and are recent (less than 24 hours old)."""
    violations_file = Path("violations/violations.json")
    normalized_url = normalize_url(url)
    if not violations_file.exists():
        return None
        
    with open(violations_file, 'r') as f:
        data = json.load(f)
        
    if normalized_url not in data:
        return None
        
    return data[normalized_url]

@app.route('/api/violations', methods=['GET'])
def get_violations():
    url = request.args.get('url')
    if not url:
        return jsonify({'error': 'URL parameter is required'}), 400
    
    try:
        # First check if we have cached results
        cached_data = get_cached_violations(url)
        if cached_data:
            logger.info(f"Returning cached violations for {url}")
            return jsonify({
                'url': url,
                'violations': cached_data['violations'],
                'cached': True,
                'timestamp': cached_data['timestamp']
            })
        
        else:
            raise Exception("No cached violations found")
    except Exception as e:
        logger.error(f"Error processing {url}: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000) 