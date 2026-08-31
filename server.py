from flask import Flask, jsonify, request
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({"status": "ok"}), 200

@app.route('/api/data', methods=['GET'])
def get_data():
    """Return sample data."""
    try:
        data = {
            "message": "Hello from the backend!",
            "items": [1, 2, 3, 4, 5]
        }
        return jsonify(data), 200
    except Exception as e:
        logger.error(f"Error in /api/data: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
