"""
Beyond Presence Avatar Service
Handles Beyond Presence API integration for lip-synced avatars with LiveKit
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

BEYOND_PRESENCE_API_KEY = os.getenv('BEYOND_PRESENCE_API_KEY')
BEYOND_PRESENCE_API_BASE = "https://api.bey.dev/v1"


def get_avatars():
    """
    List available Beyond Presence avatars
    
    Returns:
        dict: List of available avatars
    """
    headers = {
        "x-api-key": BEYOND_PRESENCE_API_KEY,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(
            f"{BEYOND_PRESENCE_API_BASE}/avatars",
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        return {
            "success": True,
            "avatars": response.json().get("data", [])
        }
    except requests.exceptions.RequestException as e:
        print(f"Beyond Presence API error: {e}")
        return {
            "success": False,
            "error": str(e)
        }


def create_livekit_session(avatar_id, livekit_url, livekit_token):
    """
    Create a Beyond Presence session that connects to LiveKit for audio input
    
    Args:
        avatar_id: Beyond Presence avatar ID
        livekit_url: LiveKit WebSocket URL
        livekit_token: LiveKit access token
    
    Returns:
        dict: Session details including video stream URL
    """
    headers = {
        "x-api-key": BEYOND_PRESENCE_API_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "avatar_id": avatar_id,
        "url": livekit_url,
        "token": livekit_token
    }
    
    try:
        response = requests.post(
            f"{BEYOND_PRESENCE_API_BASE}/sessions",
            headers=headers,
            json=payload,
            timeout=10
        )
        response.raise_for_status()
        
        data = response.json()
        return {
            "success": True,
            "session_id": data.get("id"),
            "stream_url": data.get("stream_url"),
            "status": data.get("status"),
            "data": data
        }
    except requests.exceptions.RequestException as e:
        print(f"Beyond Presence session creation error: {e}")
        if hasattr(e.response, 'text'):
            print(f"Response: {e.response.text}")
        return {
            "success": False,
            "error": str(e),
            "fallback": True
        }


def get_session_status(session_id):
    """
    Get the status of a Beyond Presence session
    
    Args:
        session_id: Session ID
    
    Returns:
        dict: Session status details
    """
    headers = {
        "x-api-key": BEYOND_PRESENCE_API_KEY,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(
            f"{BEYOND_PRESENCE_API_BASE}/sessions/{session_id}",
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        
        data = response.json()
        return {
            "success": True,
            "status": data.get("status"),
            "data": data
        }
    except requests.exceptions.RequestException as e:
        print(f"Beyond Presence session status error: {e}")
        return {
            "success": False,
            "error": str(e)
        }


def delete_session(session_id):
    """
    Delete/end a Beyond Presence session
    
    Args:
        session_id: Session ID to delete
    
    Returns:
        dict: Deletion status
    """
    headers = {
        "x-api-key": BEYOND_PRESENCE_API_KEY,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.delete(
            f"{BEYOND_PRESENCE_API_BASE}/sessions/{session_id}",
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        
        return {
            "success": True,
            "message": "Session deleted successfully"
        }
    except requests.exceptions.RequestException as e:
        print(f"Beyond Presence session deletion error: {e}")
        return {
            "success": False,
            "error": str(e)
        }


if __name__ == "__main__":
    # Test Beyond Presence integration
    print("Testing Beyond Presence API...")
    
    # List avatars
    result = get_avatars()
    if result.get("success"):
        print(f"✅ Found {len(result['avatars'])} avatars")
        print(f"   Target avatar ID: 2bc759ab-a7e5-4b91-941d-9e42450d6546")
        
        # Check if our avatar exists
        target_avatar = next(
            (a for a in result['avatars'] if a['id'] == '2bc759ab-a7e5-4b91-941d-9e42450d6546'),
            None
        )
        if target_avatar:
            print(f"   ✅ Avatar 'Fjolla' found and available!")
        else:
            print(f"   ❌ Target avatar not found")
    else:
        print(f"❌ Failed to list avatars: {result.get('error')}")

