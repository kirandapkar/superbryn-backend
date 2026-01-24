"""
Simplified LiveKit agent with voice pipeline.
Uses LiveKit Agents framework properly.
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
    JobProcess,
    WorkerOptions,
    cli,
    llm,
)
from livekit.agents.voice_assistant import VoiceAssistant
from livekit.plugins import deepgram, cartesia, openai

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def entrypoint(ctx: JobContext):
    """
    Main entrypoint when participant joins room.
    """
    logger.info(f"Agent starting for room: {ctx.room.name}")
    
    # Connect to the room
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    
    # Initialize Speech-to-Text (Deepgram)
    stt = deepgram.STT(
        model="nova-2",
        language="en-US",
    )
    
    # Initialize Text-to-Speech (Cartesia)
    tts = cartesia.TTS(
        voice=os.getenv("CARTESIA_VOICE_ID"),
    )
    
    # Initialize LLM (OpenRouter)
    assistant_llm = openai.LLM(
        model=os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct:free"),
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url="https://openrouter.ai/api/v1",
    )
    
    # Create initial chat context with system prompt
    initial_ctx = llm.ChatContext().append(
        role="system",
        text="""You are a friendly appointment booking assistant.

Your capabilities:
1. Identify users by phone number (10 digits)
2. Show available appointment slots  
3. Book appointments (need date and time)
4. Retrieve user's existing appointments
5. Cancel appointments
6. Modify appointments
7. End conversation with summary

Rules:
- ALWAYS ask for phone number first if user hasn't identified
- Be polite and conversational
- Confirm important actions before executing
- Keep responses under 50 words
- If user asks to book, get date and time first

Current available slots: 9 AM to 5 PM, Monday-Friday.
"""
    )
    
    # Create voice assistant
    assistant = VoiceAssistant(
        vad=ctx.proc.userdata["vad"],
        stt=stt,
        llm=assistant_llm,
        tts=tts,
        chat_ctx=initial_ctx,
    )
    
    # Start the assistant
    assistant.start(ctx.room)
    
    logger.info("Voice assistant started successfully")
    
    # Say hello
    await assistant.say("Hello! I'm your appointment assistant. May I have your phone number to get started?")


async def request_fnc(req: JobContext):
    """Request handler for job."""
    logger.info(f"Received request for room: {req.room}")
    await req.accept(entrypoint)


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            request_fnc=request_fnc,
        )
    )

