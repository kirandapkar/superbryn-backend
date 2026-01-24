"""
Conversation state machine and context management.
This module defines the states and tracks conversation flow.
"""
from enum import Enum
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime


class ConversationState(Enum):
    """
    Explicit conversation states to prevent edge cases.
    State transitions are enforced to ensure logical flow.
    """
    UNIDENTIFIED = "unidentified"          # Initial state, need phone number
    IDENTIFIED = "identified"              # User identified, can use tools
    BROWSING_SLOTS = "browsing_slots"      # Viewing available time slots
    BOOKING = "booking"                    # In process of booking
    CONFIRMING = "confirming"              # Confirming booking details
    RETRIEVING = "retrieving"              # Fetching appointments
    CANCELLING = "cancelling"              # Cancelling appointment
    MODIFYING = "modifying"                # Modifying appointment
    COMPLETED = "completed"                # Task completed


@dataclass
class ConversationContext:
    """
    Maintains conversation state and history.
    This prevents booking before identification and other edge cases.
    """
    state: ConversationState = ConversationState.UNIDENTIFIED
    user_phone: Optional[str] = None
    user_name: Optional[str] = None
    pending_appointment: Optional[Dict[str, Any]] = None
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)
    identified_intents: List[str] = field(default_factory=list)
    session_id: Optional[str] = None
    started_at: datetime = field(default_factory=datetime.now)
    
    def can_transition_to(self, target_state: ConversationState) -> bool:
        """
        Validate if state transition is allowed.
        Prevents invalid state changes.
        """
        # Define valid state transitions
        valid_transitions = {
            ConversationState.UNIDENTIFIED: [ConversationState.IDENTIFIED],
            ConversationState.IDENTIFIED: [
                ConversationState.BROWSING_SLOTS,
                ConversationState.RETRIEVING,
                ConversationState.CANCELLING,
                ConversationState.MODIFYING,
                ConversationState.COMPLETED
            ],
            ConversationState.BROWSING_SLOTS: [
                ConversationState.BOOKING,
                ConversationState.IDENTIFIED
            ],
            ConversationState.BOOKING: [
                ConversationState.CONFIRMING,
                ConversationState.IDENTIFIED
            ],
            ConversationState.CONFIRMING: [
                ConversationState.COMPLETED,
                ConversationState.IDENTIFIED
            ],
            ConversationState.RETRIEVING: [ConversationState.IDENTIFIED],
            ConversationState.CANCELLING: [ConversationState.IDENTIFIED],
            ConversationState.MODIFYING: [ConversationState.IDENTIFIED],
            ConversationState.COMPLETED: []  # Terminal state
        }
        
        return target_state in valid_transitions.get(self.state, [])
    
    def transition_to(self, target_state: ConversationState) -> bool:
        """
        Attempt to transition to a new state.
        Returns True if successful, False if invalid transition.
        """
        if self.can_transition_to(target_state):
            self.state = target_state
            return True
        return False
    
    def add_to_history(self, role: str, content: str, metadata: Optional[Dict] = None):
        """Add message to conversation history."""
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        })
    
    def is_identified(self) -> bool:
        """Check if user has been identified."""
        return self.user_phone is not None and self.state != ConversationState.UNIDENTIFIED
    
    def get_context_summary(self) -> Dict[str, Any]:
        """Get a summary of current conversation context."""
        return {
            "state": self.state.value,
            "user_phone": self.user_phone,
            "user_name": self.user_name,
            "has_pending_appointment": self.pending_appointment is not None,
            "conversation_turns": len(self.conversation_history),
            "session_duration": (datetime.now() - self.started_at).seconds
        }

