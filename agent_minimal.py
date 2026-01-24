"""
Minimal LiveKit Voice Agent - Works with current API
This demonstrates the backend is ready for voice integration.
"""
import asyncio
import os
import logging
from dotenv import load_dotenv

# Load environment
load_dotenv()

# LiveKit imports
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    WorkerOptions,
    cli,
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def entrypoint(ctx: JobContext):
    """
    Main entrypoint when participant joins room.
    Simplified version for testing.
    """
    logger.info(f"✅ Agent connected to room: {ctx.room.name}")
    
    # Connect to the room
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    
    logger.info("✅ Agent successfully connected and listening!")
    logger.info("📝 Note: Full voice pipeline with STT/TTS/LLM requires additional setup")
    logger.info("🎯 This confirms LiveKit agent infrastructure is working")
    
    # Keep agent alive
    await asyncio.Event().wait()


if __name__ == "__main__":
    """
    Start the LiveKit agent.
    Usage: python agent_minimal.py start
    """
    logger.info("🚀 Starting LiveKit Agent...")
    logger.info(f"📡 Connecting to: {os.getenv('LIVEKIT_URL')}")
    
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
        )
    )

