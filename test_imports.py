"""
Simple test to verify LiveKit Agents can start.
This is a minimal version without voice assistant complexity.
"""
import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Try importing livekit agents
try:
    from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli
    print("✅ Basic LiveKit agents imports successful")
except ImportError as e:
    print(f"❌ Error importing basic agents: {e}")
    exit(1)

# Try importing plugins
try:
    from livekit.plugins import deepgram, cartesia, openai
    print("✅ Plugin imports successful")
except ImportError as e:
    print(f"❌ Error importing plugins: {e}")
    exit(1)

# Try importing voice assistant
try:
    from livekit.agents.voice_assistant import VoiceAssistant
    print("✅ VoiceAssistant import successful")
except ImportError as e:
    print(f"⚠️  VoiceAssistant not available: {e}")
    print("   This module may have been moved or renamed in the current version")

print("\n✅ All basic imports working!")
print("\nEnvironment variables check:")
print(f"LIVEKIT_URL: {'✅ Set' if os.getenv('LIVEKIT_URL') else '❌ Missing'}")
print(f"LIVEKIT_API_KEY: {'✅ Set' if os.getenv('LIVEKIT_API_KEY') else '❌ Missing'}")
print(f"LIVEKIT_API_SECRET: {'✅ Set' if os.getenv('LIVEKIT_API_SECRET') else '❌ Missing'}")
print(f"DEEPGRAM_API_KEY: {'✅ Set' if os.getenv('DEEPGRAM_API_KEY') else '❌ Missing'}")
print(f"CARTESIA_API_KEY: {'✅ Set' if os.getenv('CARTESIA_API_KEY') else '❌ Missing'}")

