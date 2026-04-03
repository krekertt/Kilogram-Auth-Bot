from flask import Flask, request, jsonify
import requests
import random

app = Flask(__name__)

BOT_TOKEN = '8081566708:AAHm4ppfiDQMVT_GCsTFmXXe-Z56UWae6AM'

@app.route('/send_code', methods=['POST'])
def send_code():
    data = request.json
    chat_id = data.get('chat_id')
    phone = data.get('phone')
    
    if not chat_id:
        return jsonify({'error': 'no_chat_id'}), 400
    
    code = random.randint(100000, 999999)
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    params = {'chat_id': chat_id, 'text': f"🔑 Код: {code}", 'parse_mode': 'HTML'}
    
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        return jsonify({'success': True, 'code': code})
    return jsonify({'error': 'telegram_error'}), 500

@app.route('/verify_code', methods=['POST'])
def verify_code():
    return jsonify({'success': True})

@app.route('/health')
def health():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
