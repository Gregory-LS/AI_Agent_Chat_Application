from flask import Flask, request, jsonify
import time

app = Flask(__name__)

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_message = data.get('message', '')
    
    # Simulate model response with metadata
    start_time = time.time()
    # In a real app, here we would call the model
    response_text = f"Echo: {user_message}"
    latency = round(time.time() - start_time, 3)
    
    return jsonify({
        'role': 'assistant',
        'content': response_text,
        'model': 'gpt-3.5-turbo',
        'latency': latency,
        'token_count': len(user_message.split()) + len(response_text.split())
    })

if __name__ == '__main__':
    app.run(debug=True)