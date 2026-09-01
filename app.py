from flask import Flask, request, jsonify
from flask.helpers import make_response
import random
import string

app = Flask(__name__)


def generate_random_string(length=10):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


@app.route('/')
def home():
    return jsonify({'message': 'Hello, World!'})


@app.route('/data', methods=['POST'])
def data():
    try:
        req_data = request.get_json()
        if not req_data:
            return make_response(jsonify({'error': 'Request body must be JSON'}), 400)
        if 'name' not in req_data:
            return make_response(jsonify({'error': 'Missing "name" in request body'}), 400)
        name = req_data['name']
        if not isinstance(name, str) or not name.strip():
            return make_response(jsonify({'error': '"name" must be a non-empty string'}), 400)
        return jsonify({'greeting': f'Hello, {name}!'}), 201
    except Exception as e:
        app.logger.error(f'Unexpected error: {e}')
        return make_response(jsonify({'error': 'Internal server error'}), 500)


@app.route('/extras')
def extras():
    try:
        extra_type = request.args.get('type', 'all')
        result = {}
        if extra_type == 'all' or extra_type == 'random_string':
            result['random_string'] = generate_random_string()
        if extra_type == 'all' or extra_type == 'random_int':
            result['random_int'] = random.randint(1, 1000)
        if extra_type == 'all' or extra_type == 'random_float':
            result['random_float'] = round(random.uniform(0, 100), 2)
        if extra_type not in ['all', 'random_string', 'random_int', 'random_float']:
            return make_response(jsonify({'error': 'Invalid type parameter. Must be one of: all, random_string, random_int, random_float'}), 400)
        return jsonify(result)
    except Exception as e:
        app.logger.error(f'Unexpected error: {e}')
        return make_response(jsonify({'error': 'Internal server error'}), 500)


@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({'error': 'Method not allowed'}), 405


if __name__ == '__main__':
    app.run(debug=True)
