"""
Test script for backend skeleton (no voice, just logic).
Tests conversation flow and state transitions.
"""
import sys
sys.path.insert(0, '/Users/kirandapkar/Documents/superbryn_assignment/superbryn-backend')

from agent import ConversationContext, IntentRouter


def test_conversation_flow():
    """Test the complete conversation flow."""
    print("=== Testing Backend Skeleton ===\n")
    
    # Initialize
    context = ConversationContext()
    router = IntentRouter()
    
    print(f"Initial state: {context.state.value}\n")
    
    # Test 1: Try to book without identifying (should fail)
    print("Test 1: Try to book without identifying")
    result = router.dispatch_tool("I want to book an appointment", context)
    print(f"Result: {result}")
    print(f"State: {context.state.value}\n")
    
    # Test 2: Identify user
    print("Test 2: Identify user")
    result = router.dispatch_tool("My phone number is 555-123-4567 and my name is John", context)
    print(f"Result: {result}")
    print(f"State: {context.state.value}")
    print(f"User identified: {context.is_identified()}\n")
    
    # Test 3: Fetch available slots
    print("Test 3: Fetch available slots")
    result = router.dispatch_tool("Show me available times", context)
    print(f"Result: {result.get('message')}")
    print(f"Slots found: {result.get('total_available', 0)}")
    print(f"State: {context.state.value}\n")
    
    # Test 4: Book appointment
    print("Test 4: Book appointment")
    result = router.dispatch_tool("Book appointment for tomorrow at 2pm", context)
    print(f"Result: {result.get('message')}")
    print(f"State: {context.state.value}\n")
    
    # Test 5: Retrieve appointments
    print("Test 5: Retrieve appointments")
    result = router.dispatch_tool("Show my appointments", context)
    print(f"Result: {result.get('message')}")
    print(f"State: {context.state.value}\n")
    
    # Test 6: End conversation
    print("Test 6: End conversation")
    result = router.dispatch_tool("Goodbye", context)
    print(f"Result: {result.get('message')}")
    print(f"Summary: {result.get('summary')}")
    print(f"State: {context.state.value}\n")
    
    print("=== Context Summary ===")
    print(context.get_context_summary())


if __name__ == "__main__":
    test_conversation_flow()

