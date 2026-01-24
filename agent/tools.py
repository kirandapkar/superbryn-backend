"""
Tool implementations with database integration.
Each tool validates state and returns structured responses.
"""
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta, time
import re
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.conversation import ConversationContext, ConversationState
from database import db


# Hardcoded available slots (9 AM to 5 PM, weekdays)
AVAILABLE_HOURS = list(range(9, 17))  # 9:00 to 16:00
AVAILABLE_DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']


def identify_user(context: ConversationContext, phone: str, name: Optional[str] = None) -> Dict[str, Any]:
    """
    Tool: Identify user by phone number.
    State requirement: UNIDENTIFIED
    Transition to: IDENTIFIED
    """
    # Validate phone number format (basic validation)
    phone = phone.strip().replace('-', '').replace(' ', '').replace('(', '').replace(')', '')
    if not re.match(r'^\+?1?\d{10,}$', phone):
        return {
            "success": False,
            "error": "Invalid phone number format. Please provide a valid 10-digit phone number.",
            "phone": phone
        }
    
    # Update context
    context.user_phone = phone
    context.user_name = name
    context.transition_to(ConversationState.IDENTIFIED)
    
    return {
        "success": True,
        "message": f"Thank you {name or 'there'}! I've identified you with phone number {phone}. How can I help you today?",
        "phone": phone,
        "name": name
    }


def fetch_slots(context: ConversationContext, date: Optional[str] = None) -> Dict[str, Any]:
    """
    Tool: Fetch available appointment slots.
    State requirement: IDENTIFIED
    Transition to: BROWSING_SLOTS
    Returns: Mock available slots
    """
    if not context.is_identified():
        return {
            "success": False,
            "error": "Please provide your phone number first so I can check available slots for you."
        }
    
    context.transition_to(ConversationState.BROWSING_SLOTS)
    
    # Generate mock slots for next 7 days (excluding booked ones - mock)
    slots = []
    today = datetime.now().date()
    
    for day_offset in range(1, 8):
        check_date = today + timedelta(days=day_offset)
        day_name = check_date.strftime('%A')
        
        if day_name in AVAILABLE_DAYS:
            for hour in AVAILABLE_HOURS:
                # Mock: exclude some random slots as "booked"
                if not (hour == 12 or (day_offset == 1 and hour in [9, 10])):
                    slots.append({
                        "date": check_date.isoformat(),
                        "time": f"{hour:02d}:00",
                        "available": True
                    })
    
    return {
        "success": True,
        "message": f"I found {len(slots)} available slots in the next week.",
        "slots": slots[:10],  # Return first 10 for brevity
        "total_available": len(slots)
    }


def book_appointment(
    context: ConversationContext,
    date: str,
    time: str,
    notes: Optional[str] = None
) -> Dict[str, Any]:
    """
    Tool: Book an appointment.
    State requirement: IDENTIFIED or BROWSING_SLOTS
    Transition to: CONFIRMING
    Saves to database with double-booking prevention
    """
    if not context.is_identified():
        return {
            "success": False,
            "error": "Please identify yourself first before booking an appointment."
        }
    
    # Basic validation
    try:
        appointment_date = datetime.fromisoformat(date).date()
        appointment_time = datetime.strptime(time, "%H:%M").time()
    except ValueError:
        return {
            "success": False,
            "error": "Invalid date or time format. Please use YYYY-MM-DD for date and HH:MM for time."
        }
    
    # Check if date is in the past
    if appointment_date < datetime.now().date():
        return {
            "success": False,
            "error": "Cannot book appointments in the past. Please choose a future date."
        }
    
    # Check if during business hours
    if appointment_time.hour not in AVAILABLE_HOURS:
        return {
            "success": False,
            "error": f"Appointments are only available between 9 AM and 5 PM. You requested {time}."
        }
    
    # Create appointment in database (with double-booking check)
    result = db.create_appointment(
        user_phone=context.user_phone,
        user_name=context.user_name,
        appointment_date=date,
        appointment_time=time,
        notes=notes
    )
    
    if not result["success"]:
        return result  # Return error (e.g., slot already booked)
    
    # Update context
    context.pending_appointment = result["appointment"]
    context.transition_to(ConversationState.COMPLETED)
    
    appointment = result["appointment"]
    return {
        "success": True,
        "message": f"Perfect! I've booked your appointment for {date} at {time}. Confirmation ID: {appointment.get('id', 'N/A')}",
        "appointment": appointment,
        "confirmation_id": appointment.get('id')
    }


def retrieve_appointments(context: ConversationContext) -> Dict[str, Any]:
    """
    Tool: Retrieve user's appointments from database.
    State requirement: IDENTIFIED
    """
    if not context.is_identified():
        return {
            "success": False,
            "error": "Please provide your phone number first."
        }
    
    context.transition_to(ConversationState.RETRIEVING)
    
    # Get appointments from database
    result = db.get_user_appointments(user_phone=context.user_phone, status="booked")
    
    if not result["success"]:
        return result
    
    appointments = result["appointments"]
    
    return {
        "success": True,
        "message": f"You have {len(appointments)} upcoming appointment(s).",
        "appointments": appointments,
        "user_phone": context.user_phone
    }


def cancel_appointment(context: ConversationContext, appointment_id: str) -> Dict[str, Any]:
    """
    Tool: Cancel an appointment in database.
    State requirement: IDENTIFIED
    """
    if not context.is_identified():
        return {
            "success": False,
            "error": "Please identify yourself first."
        }
    
    context.transition_to(ConversationState.CANCELLING)
    
    if not appointment_id:
        return {
            "success": False,
            "error": "Please provide the appointment ID you want to cancel."
        }
    
    # Cancel in database
    result = db.cancel_appointment(
        appointment_id=appointment_id,
        user_phone=context.user_phone
    )
    
    if result["success"]:
        return {
            "success": True,
            "message": f"Your appointment has been cancelled successfully.",
            "appointment": result["appointment"]
        }
    
    return result


def modify_appointment(
    context: ConversationContext,
    appointment_id: str,
    new_date: Optional[str] = None,
    new_time: Optional[str] = None
) -> Dict[str, Any]:
    """
    Tool: Modify an existing appointment in database.
    State requirement: IDENTIFIED
    Checks for conflicts before updating
    """
    if not context.is_identified():
        return {
            "success": False,
            "error": "Please identify yourself first."
        }
    
    context.transition_to(ConversationState.MODIFYING)
    
    if not appointment_id:
        return {
            "success": False,
            "error": "Please provide the appointment ID you want to modify."
        }
    
    if not new_date and not new_time:
        return {
            "success": False,
            "error": "Please specify what you'd like to change (date and/or time)."
        }
    
    # Modify in database
    result = db.modify_appointment(
        appointment_id=appointment_id,
        user_phone=context.user_phone,
        new_date=new_date,
        new_time=new_time
    )
    
    if result["success"]:
        changes = []
        if new_date:
            changes.append(f"date to {new_date}")
        if new_time:
            changes.append(f"time to {new_time}")
        
        return {
            "success": True,
            "message": f"Your appointment has been modified: {', '.join(changes)}.",
            "appointment": result["appointment"]
        }
    
    return result


def end_conversation(context: ConversationContext) -> Dict[str, Any]:
    """
    Tool: End conversation and generate summary.
    Can be called from any state.
    Transition to: COMPLETED
    """
    context.transition_to(ConversationState.COMPLETED)
    
    # Generate summary based on conversation history
    summary = {
        "user_phone": context.user_phone,
        "user_name": context.user_name,
        "conversation_turns": len(context.conversation_history),
        "session_duration_seconds": (datetime.now() - context.started_at).seconds,
        "intents_identified": context.identified_intents,
        "final_state": context.state.value,
        "timestamp": datetime.now().isoformat()
    }
    
    # Check if there was a pending appointment
    if context.pending_appointment:
        summary["pending_appointment"] = context.pending_appointment
    
    return {
        "success": True,
        "message": "Thank you for using our appointment system. Here's a summary of our conversation.",
        "summary": summary
    }


# Tool registry for router
AVAILABLE_TOOLS = {
    "identify_user": identify_user,
    "fetch_slots": fetch_slots,
    "book_appointment": book_appointment,
    "retrieve_appointments": retrieve_appointments,
    "cancel_appointment": cancel_appointment,
    "modify_appointment": modify_appointment,
    "end_conversation": end_conversation
}

