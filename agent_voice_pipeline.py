"""
Voice Agent using LiveKit v1.3.12+ VoicePipelineAgent pattern
This uses the NEW pipeline-based approach (not callbacks)
"""
from typing import Optional
import asyncio
import os
import logging
from dotenv import load_dotenv

# Load environment
load_dotenv()

# LiveKit imports (v1.3.12+)
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    WorkerOptions,
    cli,
)
from livekit import agents, rtc
from livekit.plugins import deepgram, cartesia, openai

# Our logic (OUTSIDE the voice pipeline)
from agent.conversation import ConversationContext, ConversationState
from agent.router import IntentRouter
from agent import tools as appointment_tools
from livekit.agents import llm

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AppointmentAgent:
    """
    Application logic - SEPARATED from voice pipeline
    This is the "brain" that handles conversation state and tool routing
    """
    
    def __init__(self):
        self.context = ConversationContext()
        self.router = IntentRouter()
    
    async def before_llm_callback(self, text: str) -> str:
        """
        Called AFTER user speaks, BEFORE LLM processes
        This is where we do: routing, state management, tool calling
        
        Args:
            text: The transcribed user text from Deepgram
            
        Returns:
            Modified text or context for LLM
        """
        logger.info(f"User said: {text}")
        
        # Update conversation context
        self.context.last_user_message = text
        self.context.conversation_turns += 1
        
        # Router analyzes intent and executes tools if needed
        # This happens BEFORE the LLM, so we can inject results
        result = await self.router.route(text, self.context)
        
        # Log for debugging
        logger.info(f"Router result: {result}")
        
        # Return modified context or original text
        # The LLM will see this instead of raw user input
        if result and 'context_for_llm' in result:
            return result['context_for_llm']
        
        return text
    
    async def after_llm_callback(self, response: str):
        """
        Called AFTER LLM generates response, BEFORE TTS
        This is where we: log, send UI updates, track state
        
        Args:
            response: The LLM's text response
        """
        logger.info(f"Agent responding: {response}")
        
        # Update context
        self.context.last_agent_response = response
        
        # Send state updates to frontend via data channel
        await self.send_ui_update({
            'type': 'agent_response',
            'text': response,
            'state': self.context.state.value,
            'timestamp': self.context.to_dict()
        })
        
        # Log to database
        # await log_conversation_turn(self.context)
    
    async def send_ui_update(self, data: dict):
        """Send updates to frontend via LiveKit data channel"""
        # This will be implemented with actual room reference
        logger.info(f"UI update: {data}")


async def entrypoint(ctx: JobContext):
    """
    Main entrypoint - uses LiveKit Voice Agent with AgentSession
    """
    logger.info(f"🎙️ Voice Agent connecting to room: {ctx.room.name}")
    
    # Connect to room
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    
    logger.info(f"📡 Connected to room: {ctx.room.name}")
    
    # Create conversation context
    conversation_ctx = ConversationContext()
    
    # Define LLM function tools
    @llm.function_tool()
    async def identify_user(phone: str, name: Optional[str] = None):
        """Identify the user by their phone number. Must be called before any other operation."""
        result = appointment_tools.identify_user(conversation_ctx, phone, name)
        logger.info(f"🔧 identify_user called: {result}")
        return result
    
    @llm.function_tool()
    async def fetch_slots(date: Optional[str] = None):
        """Fetch available appointment slots. User must be identified first."""
        result = appointment_tools.fetch_slots(conversation_ctx, date)
        logger.info(f"🔧 fetch_slots called: {result}")
        return result
    
    @llm.function_tool()
    async def book_appointment(date: str, time: str, notes: Optional[str] = None):
        """Book an appointment for the identified user at the specified date and time."""
        result = appointment_tools.book_appointment(conversation_ctx, date, time, notes)
        logger.info(f"🔧 book_appointment called: {result}")
        return result
    
    @llm.function_tool()
    async def retrieve_appointments():
        """Get all appointments for the current user."""
        result = appointment_tools.retrieve_appointments(conversation_ctx)
        logger.info(f"🔧 retrieve_appointments called: {result}")
        return result
    
    @llm.function_tool()
    async def cancel_appointment(appointment_id: str):
        """Cancel an existing appointment by ID."""
        result = appointment_tools.cancel_appointment(conversation_ctx, appointment_id)
        logger.info(f"🔧 cancel_appointment called: {result}")
        return result
    
    @llm.function_tool()
    async def modify_appointment(appointment_id: str, new_date: Optional[str] = None, new_time: Optional[str] = None):
        """Modify an existing appointment's date or time."""
        result = appointment_tools.modify_appointment(conversation_ctx, appointment_id, new_date, new_time)
        logger.info(f"🔧 modify_appointment called: {result}")
        return result
    
    # Create the Voice Agent with tools
    assistant = agents.voice.Agent(
        instructions="""You are a helpful AI appointment assistant.

Your role:
- Help users identify themselves (ALWAYS call identify_user with their phone number)
- Show available appointment slots (call fetch_slots)
- Book, modify, or cancel appointments using the provided tools
- Be friendly, concise, and professional

CRITICAL RULES:
- ALWAYS call identify_user first with the user's phone number before any other operation
- NEVER make up or hallucinate appointment information
- ONLY use information returned from the tool calls
- If a tool returns an error, explain it to the user
- After booking, ALWAYS call retrieve_appointments to confirm

Important:
- Always get the user's phone number first before any booking
- Confirm all appointment details before booking
- Use the tools - don't make up information!""",
        stt=deepgram.STT(
            api_key=os.getenv('DEEPGRAM_API_KEY'),
            model='nova-2',
            language='en-US',
        ),
        llm=openai.LLM(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv('OPENROUTER_API_KEY'),
            model="openai/gpt-oss-20b:free",  # Free model with reasoning support
        ),
        tts=cartesia.TTS(
            api_key=os.getenv('CARTESIA_API_KEY'),
            voice=os.getenv('CARTESIA_VOICE_ID', 'f9836c6e-a0bd-460e-9d3c-f7299fa60f94'),
        ),
        tools=[
            identify_user,
            fetch_slots,
            book_appointment,
            retrieve_appointments,
            cancel_appointment,
            modify_appointment,
        ]
    )
    
    # Create AgentSession and start the agent
    logger.info("🚀 Starting voice agent session with tools...")
    session = agents.voice.AgentSession()
    await session.start(assistant, room=ctx.room)
    
    logger.info("✅ Voice agent active with function calling!")


if __name__ == "__main__":
    """
    Start the Voice Agent with NEW v1.3.12+ architecture
    
    Usage: python agent_voice_pipeline.py start
    """
    logger.info("🚀 Starting Voice Pipeline Agent (v1.3.12+)...")
    logger.info(f"📡 LiveKit URL: {os.getenv('LIVEKIT_URL')}")
    logger.info("🎤 Deepgram STT ready")
    logger.info("🔊 Cartesia TTS ready")
    logger.info("🧠 OpenRouter LLM ready")
    
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
        )
    )

