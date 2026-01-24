"""
Supabase database client and operations.
Backend-only access - frontend NEVER writes to database directly.
"""
import os
from typing import Optional, List, Dict, Any
from datetime import datetime, date, time
from dotenv import load_dotenv

# For testing without actual Supabase initially
MOCK_MODE = False

try:
    from supabase import create_client, Client
    load_dotenv()
    
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    
    if SUPABASE_URL and SUPABASE_KEY:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    else:
        MOCK_MODE = True
        supabase = None
except ImportError:
    MOCK_MODE = True
    supabase = None


class AppointmentDB:
    """
    Database operations for appointments.
    All writes are backend-only for security.
    """
    
    def __init__(self):
        self.client = supabase
        self.mock_mode = MOCK_MODE
        self._mock_appointments = []  # Mock storage for testing
    
    def create_appointment(
        self,
        user_phone: str,
        user_name: Optional[str],
        appointment_date: str,
        appointment_time: str,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new appointment.
        Returns: Created appointment or error.
        """
        if self.mock_mode:
            # Mock implementation
            appointment = {
                "id": f"mock_{len(self._mock_appointments) + 1}",
                "user_phone": user_phone,
                "user_name": user_name,
                "appointment_date": appointment_date,
                "appointment_time": appointment_time,
                "status": "booked",
                "notes": notes,
                "created_at": datetime.now().isoformat()
            }
            
            # Check for double-booking (mock)
            for appt in self._mock_appointments:
                if (appt["appointment_date"] == appointment_date and
                    appt["appointment_time"] == appointment_time and
                    appt["status"] == "booked"):
                    return {
                        "success": False,
                        "error": "This time slot is already booked. Please choose another time."
                    }
            
            self._mock_appointments.append(appointment)
            return {"success": True, "appointment": appointment}
        
        try:
            # Check for existing booking at this time (double-booking prevention)
            existing = self.client.table("appointments").select("*").eq(
                "appointment_date", appointment_date
            ).eq("appointment_time", appointment_time).eq("status", "booked").execute()
            
            if existing.data:
                return {
                    "success": False,
                    "error": "This time slot is already booked. Please choose another time."
                }
            
            # Create appointment
            result = self.client.table("appointments").insert({
                "user_phone": user_phone,
                "user_name": user_name,
                "appointment_date": appointment_date,
                "appointment_time": appointment_time,
                "status": "booked",
                "notes": notes
            }).execute()
            
            return {"success": True, "appointment": result.data[0]}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_user_appointments(
        self,
        user_phone: str,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Retrieve appointments for a user.
        Optionally filter by status.
        """
        if self.mock_mode:
            # Mock implementation
            appointments = [
                appt for appt in self._mock_appointments
                if appt["user_phone"] == user_phone
            ]
            if status:
                appointments = [a for a in appointments if a["status"] == status]
            
            return {"success": True, "appointments": appointments}
        
        try:
            query = self.client.table("appointments").select("*").eq("user_phone", user_phone)
            
            if status:
                query = query.eq("status", status)
            
            result = query.execute()
            return {"success": True, "appointments": result.data}
            
        except Exception as e:
            return {"success": False, "error": str(e), "appointments": []}
    
    def cancel_appointment(self, appointment_id: str, user_phone: str) -> Dict[str, Any]:
        """
        Cancel an appointment (mark as cancelled, don't delete).
        Verifies user owns the appointment.
        """
        if self.mock_mode:
            # Mock implementation
            for appt in self._mock_appointments:
                if appt["id"] == appointment_id:
                    if appt["user_phone"] != user_phone:
                        return {
                            "success": False,
                            "error": "You don't have permission to cancel this appointment."
                        }
                    appt["status"] = "cancelled"
                    return {"success": True, "appointment": appt}
            
            return {"success": False, "error": "Appointment not found."}
        
        try:
            # Verify ownership
            appointment = self.client.table("appointments").select("*").eq(
                "id", appointment_id
            ).eq("user_phone", user_phone).execute()
            
            if not appointment.data:
                return {
                    "success": False,
                    "error": "Appointment not found or you don't have permission to cancel it."
                }
            
            # Update status
            result = self.client.table("appointments").update({
                "status": "cancelled",
                "updated_at": datetime.now().isoformat()
            }).eq("id", appointment_id).execute()
            
            return {"success": True, "appointment": result.data[0]}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def modify_appointment(
        self,
        appointment_id: str,
        user_phone: str,
        new_date: Optional[str] = None,
        new_time: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Modify appointment date/time.
        Checks for conflicts and user ownership.
        """
        if self.mock_mode:
            # Mock implementation
            for appt in self._mock_appointments:
                if appt["id"] == appointment_id:
                    if appt["user_phone"] != user_phone:
                        return {
                            "success": False,
                            "error": "You don't have permission to modify this appointment."
                        }
                    
                    # Check for conflicts if changing date/time
                    check_date = new_date or appt["appointment_date"]
                    check_time = new_time or appt["appointment_time"]
                    
                    for other in self._mock_appointments:
                        if (other["id"] != appointment_id and
                            other["appointment_date"] == check_date and
                            other["appointment_time"] == check_time and
                            other["status"] == "booked"):
                            return {
                                "success": False,
                                "error": "The new time slot is already booked."
                            }
                    
                    if new_date:
                        appt["appointment_date"] = new_date
                    if new_time:
                        appt["appointment_time"] = new_time
                    
                    return {"success": True, "appointment": appt}
            
            return {"success": False, "error": "Appointment not found."}
        
        try:
            # Verify ownership
            appointment = self.client.table("appointments").select("*").eq(
                "id", appointment_id
            ).eq("user_phone", user_phone).execute()
            
            if not appointment.data:
                return {
                    "success": False,
                    "error": "Appointment not found or you don't have permission to modify it."
                }
            
            current = appointment.data[0]
            check_date = new_date or current["appointment_date"]
            check_time = new_time or current["appointment_time"]
            
            # Check for conflicts
            existing = self.client.table("appointments").select("*").eq(
                "appointment_date", check_date
            ).eq("appointment_time", check_time).eq("status", "booked").neq(
                "id", appointment_id
            ).execute()
            
            if existing.data:
                return {
                    "success": False,
                    "error": "The new time slot is already booked."
                }
            
            # Update appointment
            updates = {"updated_at": datetime.now().isoformat()}
            if new_date:
                updates["appointment_date"] = new_date
            if new_time:
                updates["appointment_time"] = new_time
            
            result = self.client.table("appointments").update(updates).eq(
                "id", appointment_id
            ).execute()
            
            return {"success": True, "appointment": result.data[0]}
            
        except Exception as e:
            return {"success": False, "error": str(e)}


# Global database instance
db = AppointmentDB()

