"""
Tavus Avatar Service
Handles Tavus API integration for creating conversational avatars
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

TAVUS_API_KEY = os.getenv('TAVUS_API_KEY')
TAVUS_API_BASE = "https://tavusapi.com/v2"


def create_conversation(persona_id=None):
    """
    Create a new Tavus conversation
    
    Args:
        persona_id: Optional Tavus persona ID. If not provided, uses default.
    
    Returns:
        dict: Conversation details including conversation_url
    """
    headers = {
        "x-api-key": TAVUS_API_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "replica_id": persona_id or os.getenv('TAVUS_REPLICA_ID', 'r9fa0878977a'),
        "conversation_name": "AI Appointment Assistant"
    }
    
    try:
        response = requests.post(
            f"{TAVUS_API_BASE}/conversations",
            headers=headers,
            json=payload,
            timeout=10
        )
        response.raise_for_status()
        
        data = response.json()
        return {
            "success": True,
            "conversation_id": data.get("conversation_id"),
            "conversation_url": data.get("conversation_url"),
            "status": data.get("status")
        }
    except requests.exceptions.RequestException as e:
        print(f"Tavus API error: {e}")
        return {
            "success": False,
            "error": str(e),
            "fallback": True
        }


def get_conversation_status(conversation_id):
    """
    Get the status of a Tavus conversation
    
    Args:
        conversation_id: The Tavus conversation ID
    
    Returns:
        dict: Conversation status details
    """
    headers = {
        "x-api-key": TAVUS_API_KEY
    }
    
    try:
        response = requests.get(
            f"{TAVUS_API_BASE}/conversations/{conversation_id}",
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        
        return {
            "success": True,
            "data": response.json()
        }
    except requests.exceptions.RequestException as e:
        print(f"Tavus API error: {e}")
        return {
            "success": False,
            "error": str(e)
        }


def end_conversation(conversation_id):
    """
    End a Tavus conversation
    
    Args:
        conversation_id: The Tavus conversation ID
    
    Returns:
        dict: Success status
    """
    headers = {
        "x-api-key": TAVUS_API_KEY
    }
    
    try:
        response = requests.delete(
            f"{TAVUS_API_BASE}/conversations/{conversation_id}",
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        
        return {
            "success": True,
            "message": "Conversation ended"
        }
    except requests.exceptions.RequestException as e:
        print(f"Tavus API error: {e}")
        return {
            "success": False,
            "error": str(e)
        }


if __name__ == "__main__":
    # Test Tavus integration
    print("Testing Tavus API...")
    result = create_conversation()
    if result.get("success"):
        print(f"✅ Tavus conversation created!")
        print(f"   Conversation ID: {result.get('conversation_id')}")
        print(f"   URL: {result.get('conversation_url')}")
    else:
        print(f"❌ Tavus API failed: {result.get('error')}")
        print(f"   Fallback mode enabled")

