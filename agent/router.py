"""
Intent classification and deterministic tool dispatcher.
Two-layer approach: LLM classifies intent → Python validates and executes.
"""
from typing import Dict, Any, Optional
from agent.conversation import ConversationContext, ConversationState
from agent.tools import AVAILABLE_TOOLS
import json


class IntentRouter:
    """
    Routes user intents to appropriate tools with validation.
    Prevents edge cases by enforcing state requirements.
    """
    
    def __init__(self):
        self.tool_functions = AVAILABLE_TOOLS
    
    def classify_intent(self, user_message: str, context: ConversationContext) -> Dict[str, Any]:
        """
        Mock intent classification (will be replaced with LLM in Step 4).
        For now, uses simple keyword matching.
        """
        user_message_lower = user_message.lower()
        
        # Simple keyword-based intent detection (mock)
        if any(word in user_message_lower for word in ['phone', 'number', 'identify', 'my name is']):
            return {
                "intent": "identify_user",
                "entities": self._extract_phone_and_name(user_message)
            }
        
        elif any(word in user_message_lower for word in ['available', 'slots', 'when', 'times']):
            return {
                "intent": "fetch_slots",
                "entities": {}
            }
        
        elif any(word in user_message_lower for word in ['book', 'schedule', 'appointment']):
            return {
                "intent": "book_appointment",
                "entities": self._extract_booking_details(user_message)
            }
        
        elif any(word in user_message_lower for word in ['my appointments', 'show', 'list', 'retrieve']):
            return {
                "intent": "retrieve_appointments",
                "entities": {}
            }
        
        elif any(word in user_message_lower for word in ['cancel', 'delete']):
            return {
                "intent": "cancel_appointment",
                "entities": {"appointment_id": "mock_id"}
            }
        
        elif any(word in user_message_lower for word in ['modify', 'change', 'reschedule']):
            return {
                "intent": "modify_appointment",
                "entities": {"appointment_id": "mock_id"}
            }
        
        elif any(word in user_message_lower for word in ['bye', 'end', 'goodbye', 'finish']):
            return {
                "intent": "end_conversation",
                "entities": {}
            }
        
        else:
            return {
                "intent": "unknown",
                "entities": {}
            }
    
    def _extract_phone_and_name(self, message: str) -> Dict[str, Any]:
        """Mock entity extraction for phone and name."""
        import re
        
        # Extract phone number (simple pattern)
        phone_pattern = r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b'
        phone_match = re.search(phone_pattern, message)
        
        # Extract name (look for "my name is" or "I'm")
        name = None
        if "my name is" in message.lower():
            name = message.lower().split("my name is")[-1].strip().split()[0].capitalize()
        elif "i'm" in message.lower():
            name = message.lower().split("i'm")[-1].strip().split()[0].capitalize()
        
        return {
            "phone": phone_match.group() if phone_match else None,
            "name": name
        }
    
    def _extract_booking_details(self, message: str) -> Dict[str, Any]:
        """Mock entity extraction for booking details."""
        # This is simplified - will use LLM for proper extraction in Step 4
        return {
            "date": "2026-01-28",  # Mock
            "time": "14:00",       # Mock
            "notes": None
        }
    
    def validate_and_dispatch(
        self,
        intent: str,
        entities: Dict[str, Any],
        context: ConversationContext
    ) -> Dict[str, Any]:
        """
        Deterministic dispatcher: validates state and executes tool.
        This prevents LLM hallucinations from breaking the flow.
        """
        
        # Check if intent is valid
        if intent not in self.tool_functions:
            if intent == "unknown":
                return {
                    "success": False,
                    "error": "I didn't understand that. Could you please rephrase?",
                    "suggestions": self._get_suggestions(context)
                }
            return {
                "success": False,
                "error": f"Unknown intent: {intent}"
            }
        
        # State-based validation BEFORE executing tool
        validation_result = self._validate_state_for_intent(intent, context)
        if not validation_result["valid"]:
            return {
                "success": False,
                "error": validation_result["message"],
                "current_state": context.state.value
            }
        
        # Execute the tool function
        tool_function = self.tool_functions[intent]
        
        try:
            # Call tool with validated entities
            result = tool_function(context, **entities)
            
            # Track intent in context
            context.identified_intents.append(intent)
            
            return result
            
        except TypeError as e:
            # Handle missing or invalid parameters
            return {
                "success": False,
                "error": f"Invalid parameters for {intent}: {str(e)}",
                "required_params": self._get_required_params(intent)
            }
        except Exception as e:
            # Catch any other errors
            return {
                "success": False,
                "error": f"Error executing {intent}: {str(e)}"
            }
    
    def _validate_state_for_intent(self, intent: str, context: ConversationContext) -> Dict[str, Any]:
        """
        Validate if current state allows this intent.
        Critical for preventing edge cases.
        """
        
        # identify_user can only be called when UNIDENTIFIED
        if intent == "identify_user":
            if context.state != ConversationState.UNIDENTIFIED:
                return {
                    "valid": False,
                    "message": f"You're already identified as {context.user_name or context.user_phone}."
                }
        
        # Most other tools require identification
        elif intent in ["fetch_slots", "book_appointment", "retrieve_appointments", 
                       "cancel_appointment", "modify_appointment"]:
            if not context.is_identified():
                return {
                    "valid": False,
                    "message": "Please provide your phone number first so I can help you."
                }
        
        # end_conversation can be called anytime
        # No restrictions
        
        return {"valid": True}
    
    def _get_suggestions(self, context: ConversationContext) -> list:
        """Provide helpful suggestions based on current state."""
        if context.state == ConversationState.UNIDENTIFIED:
            return ["Please provide your phone number to get started"]
        elif context.state == ConversationState.IDENTIFIED:
            return [
                "Check available appointment slots",
                "View your existing appointments",
                "Book a new appointment"
            ]
        else:
            return ["Continue with your current request or say 'help'"]
    
    def _get_required_params(self, intent: str) -> list:
        """Return required parameters for a given intent."""
        params_map = {
            "identify_user": ["phone"],
            "book_appointment": ["date", "time"],
            "cancel_appointment": ["appointment_id"],
            "modify_appointment": ["appointment_id"],
        }
        return params_map.get(intent, [])
    
    def dispatch_tool(self, user_message: str, context: ConversationContext) -> Dict[str, Any]:
        """
        Main entry point: classify intent then dispatch.
        Returns tool execution result.
        """
        # Step 1: Classify intent (mock for now, LLM in Step 4)
        classification = self.classify_intent(user_message, context)
        intent = classification["intent"]
        entities = classification["entities"]
        
        # Step 2: Validate and dispatch
        result = self.validate_and_dispatch(intent, entities, context)
        
        # Add intent info to result for frontend display
        result["intent"] = intent
        result["entities"] = entities
        
        return result

