from flask import Flask, jsonify, request
from llm_check import scan_url
from type_hints.wcag_types import Violation

app = Flask(__name__)

def serialize_violation(violation):
    """Convert a Violation object to a dictionary, including nested NodeResult objects."""
    violation_dict = violation.__dict__.copy()
    if 'nodes' in violation_dict:
        violation_dict['nodes'] = [node.__dict__ for node in violation_dict['nodes']]
    return violation_dict

@app.route('/api/violations', methods=['GET'])
def get_violations():
    url = request.args.get('url')
    if not url:
        return jsonify({'error': 'URL parameter is required'}), 400
    
    try:
        violations = scan_url(url)
        # Convert violations to dictionary format for JSON serialization
        violations_dict = [serialize_violation(v) for v in violations]
        return jsonify({
            'url': url,
            'violations': violations_dict
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000) 