"""
Main LiveKit agent with voice pipeline.
Integrates STT (Deepgram), TTS (Cartesia), and LLM (OpenRouter).
"""
import asyncio
import os
import sys
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# LiveKit imports
from livekit import rtc
from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli, llm
from livekit.agents.voice_assistant import VoiceAssistant
from livekit.plugins import deepgram, cartesia, openai

# Our custom imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from agent import ConversationContext, IntentRouter


# Initialize router
intent_router = IntentRouter()

# Store active conversations
active_conversations: Dict[str, ConversationContext] = {}


async def entrypoint(ctx: JobContext):
    """
    Main entry point for LiveKit agent.
    This is called when a participant joins a room.
    """
    print(f"[Agent] Starting for room: {ctx.room.name}")
    
    # Initialize conversation context for this session
    session_id = ctx.room.name
    conversation_context = ConversationContext()
    conversation_context.session_id = session_id
    active_conversations[session_id] = conversation_context
    
    # Connect to room
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    
    # Configure speech-to-text (Deepgram)
    stt = deepgram.STT(
        model="nova-2-general",
        language="en-US"
    )
    
    # Configure text-to-speech (Cartesia)
    tts = cartesia.TTS(
        voice=os.getenv("CARTESIA_VOICE_ID", "f9836c6e-a0bd-460e-9d3c-f7299fa60f94")
    )
    
    # Configure LLM (OpenRouter with Llama)
    llm_instance = openai.LLM(
        model=os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct:free"),
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url="https://openrouter.ai/api/v1"
    )
    
    # Define assistant function for tool calling
    async def process_user_input(user_message: str) -> str:
        """
        Process user input through our intent router.
        This is where our state machine and tool logic kicks in.
        """
        print(f"[User] {user_message}")
        
        # Get conversation context
        context = active_conversations.get(session_id)
        if not context:
            return "Sorry, I lost track of our conversation. Can we start over?"
        
        # Add to history
        context.add_to_history("user", user_message)
        
        # Route through our deterministic dispatcher
        result = intent_router.dispatch_tool(user_message, context)
        
        # Generate response
        if result.get("success"):
            response = result.get("message", "Done!")
        else:
            response = result.get("error", "Sorry, I couldn't process that.")
        
        # Add to history
        context.add_to_history("assistant", response, metadata={
            "intent": result.get("intent"),
            "entities": result.get("entities"),
            "success": result.get("success")
        })
        
        print(f"[Assistant] {response}")
        
        return response
    
    # Create voice assistant
    assistant = VoiceAssistant(
        vad=ctx.proc.userdata.get("vad"),  # Voice activity detection
        stt=stt,
        llm=llm_instance,
        tts=tts,
        chat_ctx=llm.ChatContext(
            messages=[
                llm.ChatMessage(
                    role="system",
                    content="""You are a helpful appointment booking assistant. 
                    You help users book, retrieve, cancel, and modify appointments.
                    Always be polite and clear. Ask for phone number first if not identified.
                    Keep responses concise and natural."""
                )
            ]
        ),
        fnc_ctx=None,  # We handle functions through our router
    )
    
    # Start the assistant
    assistant.start(ctx.room)
    
    # Wait for session to end
    await asyncio.Event().wait()


if __name__ == "__main__":
    """
    Start the LiveKit agent.
    Usage: python agent/main.py start
    """
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            api_key=os.getenv("LIVEKIT_API_KEY"),
            api_secret=os.getenv("LIVEKIT_API_SECRET"),
            ws_url=os.getenv("LIVEKIT_URL"),
        )
    )

