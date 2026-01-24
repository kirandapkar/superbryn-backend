"""
Simple token generation server for LiveKit
Run this alongside your agent to generate access tokens for the frontend
"""
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from livekit import api
from dotenv import load_dotenv
from beyond_presence_service import create_livekit_session

# Load environment
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

LIVEKIT_API_KEY = os.getenv('LIVEKIT_API_KEY')
LIVEKIT_API_SECRET = os.getenv('LIVEKIT_API_SECRET')
LIVEKIT_URL = os.getenv('LIVEKIT_URL')
BEYOND_PRESENCE_AVATAR_ID = os.getenv('BEYOND_PRESENCE_AVATAR_ID', '2bc759ab-a7e5-4b91-941d-9e42450d6546')

@app.route('/token', methods=['POST'])
def generate_token():
    """Generate a LiveKit access token for the frontend"""
    try:
        data = request.get_json()
        room_name = data.get('roomName', f'appointment-room-{os.urandom(4).hex()}')
        participant_name = data.get('participantName', 'User')
        
        # Create token
        token = api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
        token.with_identity(participant_name)
        token.with_name(participant_name)
        token.with_grants(api.VideoGrants(
            room_join=True,
            room=room_name,
            can_publish=True,
            can_subscribe=True,
        ))
        
        # Generate JWT
        jwt_token = token.to_jwt()
        
        return jsonify({
            'token': jwt_token,
            'url': LIVEKIT_URL,
            'roomName': room_name
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok'})

@app.route('/avatar/create', methods=['POST'])
def create_avatar_session():
    """Create a Beyond Presence avatar session connected to LiveKit"""
    try:
        data = request.get_json() or {}
        room_name = data.get('roomName')
        livekit_token = data.get('token')
        
        if not room_name or not livekit_token:
            return jsonify({
                'success': False,
                'error': 'Missing roomName or token',
                'fallback': True
            }), 400
        
        # Create Beyond Presence session with LiveKit connection
        result = create_livekit_session(
            avatar_id=BEYOND_PRESENCE_AVATAR_ID,
            livekit_url=LIVEKIT_URL,
            livekit_token=livekit_token
        )
        
        if result.get('success'):
            return jsonify({
                'success': True,
                'session_id': result.get('session_id'),
                'stream_url': result.get('stream_url'),
                'status': result.get('status')
            })
        else:
            # Return fallback mode
            return jsonify({
                'success': False,
                'fallback': True,
                'error': result.get('error', 'Unknown error')
            })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'fallback': True,
            'error': str(e)
        })

if __name__ == '__main__':
    PORT = 5001
    print(f"🔐 Token Server starting on http://localhost:{PORT}")
    print(f"📡 LiveKit URL: {LIVEKIT_URL}")
    print(f"🎭 Beyond Presence Avatar: {BEYOND_PRESENCE_AVATAR_ID}")
    print(f"💡 Frontend endpoints:")
    print(f"   - http://localhost:{PORT}/token")
    print(f"   - http://localhost:{PORT}/avatar/create")
    app.run(host='0.0.0.0', port=PORT, debug=True)

