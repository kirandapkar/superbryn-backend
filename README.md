# SuperBryn AI Voice Agent - Backend

Production-ready AI voice agent backend using LiveKit Agents framework.

## 🏗️ Architecture

```
Backend Components:
┌─────────────────────────────────────────────┐
│         LiveKit Agent (Voice Pipeline)      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
│  │ Deepgram │→ │ OpenRouter│→ │ Cartesia │ │
│  │   STT    │  │    LLM    │  │   TTS    │ │
│  └──────────┘  └──────────┘  └──────────┘ │
└──────────────────┬──────────────────────────┘
                   ↓
          ┌────────────────┐
          │ Intent Router   │ ← State Machine
          │ (Deterministic) │
          └────────┬───────┘
                   ↓
       ┌──────────────────────┐
       │   Tool Functions      │
       │ (7 appointment tools) │
       └──────────┬───────────┘
                  ↓
          ┌──────────────┐
          │   Supabase   │
          │   Database   │
          └──────────────┘
```

## 📊 Conversation State Machine

```
UNIDENTIFIED → IDENTIFIED → BROWSING_SLOTS → BOOKING → COMPLETED
                    ↓
                RETRIEVING
                    ↓
                CANCELLING
                    ↓
                MODIFYING
```

**State Transitions:**
- `UNIDENTIFIED`: User must provide phone number
- `IDENTIFIED`: Can access all appointment functions
- State validation prevents edge cases (e.g., booking before identification)

## 🛠️ Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp env.example .env
```

Required variables:
- LiveKit credentials (URL, API key, secret)
- Deepgram API key (STT)
- Cartesia API key + voice ID (TTS)
- OpenRouter API key (LLM)
- Supabase URL + key (Database)
- Tavus API key (Avatar)

### 3. Setup Database

Run the schema in Supabase SQL Editor:

```bash
# Copy schema.sql contents and run in Supabase
```

**Key constraints:**
- Unique index on (date, time) WHERE status='booked' → Prevents double-booking at DB level
- Row Level Security enabled
- Auto-update timestamps

### 4. Run Agent

```bash
python agent_simple.py start
```

## 📦 Project Structure

```
superbryn-backend/
├── agent/
│   ├── __init__.py
│   ├── conversation.py    # State machine & context
│   ├── router.py          # Intent → Tool dispatcher
│   ├── tools.py           # 7 appointment functions
│   ├── main.py            # Full LiveKit integration
│   └── summary.py         # (Future) Summary generation
├── database.py            # Supabase client
├── agent_simple.py        # Simplified agent entry
├── schema.sql             # Database schema
├── requirements.txt
├── .env                   # Your credentials
└── README.md
```

## 🔧 Tool Functions

### Available Tools:

1. **identify_user** - Get phone number & name
   - Validates phone format
   - Transitions: UNIDENTIFIED → IDENTIFIED

2. **fetch_slots** - Show available times
   - Returns 9 AM - 5 PM, weekdays
   - Excludes already booked slots

3. **book_appointment** - Create booking
   - Validates date/time
   - DB constraint prevents double-booking
   - Transitions: IDENTIFIED → COMPLETED

4. **retrieve_appointments** - Get user's bookings
   - Filters by phone number
   - Shows active appointments only

5. **cancel_appointment** - Mark as cancelled
   - Verifies user ownership
   - Soft delete (status change)

6. **modify_appointment** - Change date/time
   - Checks for conflicts
   - Validates ownership

7. **end_conversation** - Generate summary
   - Summarizes conversation
   - Lists actions performed
   - Returns pending appointments

## 🔐 Security Features

✅ **Backend-only database writes**
- Frontend has NO Supabase credentials
- All DB operations through backend API

✅ **User ownership validation**
- Cancel/modify only if user owns appointment
- Phone number verification

✅ **State machine enforcement**
- Can't book before identifying
- Prevents invalid action sequences

✅ **Database constraints**
- Unique slot booking (prevents race conditions)
- Check constraints on status field

## 🧪 Testing

Test the logic (no voice):

```bash
python test_skeleton.py
```

Tests cover:
- State transitions
- Tool validation
- Edge cases (booking before ID, etc.)

## 🚀 Deployment

### Option 1: Railway/Render (Recommended)

```bash
# Push to GitHub
git add .
git commit -m "Initial backend"
git push

# Connect to Railway:
1. Import repo
2. Add environment variables
3. Deploy
```

### Option 2: Docker

```dockerfile
FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "agent_simple.py", "start"]
```

## 📝 Known Limitations

1. **Intent Classification**: Currently uses simple keyword matching
   - Production: Use LLM function calling
   - Workaround: Clear prompt engineering

2. **Entity Extraction**: Mock implementation
   - Production: Use NER or LLM structured output
   - Workaround: Ask user to confirm extracted values

3. **Tavus Integration**: Avatar setup requires backend API endpoint
   - Production: Create Tavus conversation via API
   - Current: Visual emoji avatar placeholder

4. **Token Generation**: Frontend can't generate LiveKit tokens securely
   - Production: Backend endpoint for token creation
   - Current: Direct connection (development only)

5. **Error Recovery**: Basic error messages
   - Production: Contextual retry logic
   - Current: User must rephrase

## 🔗 Related

- Frontend: `../superbryn-frontend/`
- LiveKit Docs: https://docs.livekit.io/agents
- Supabase: https://supabase.com/docs

## 📧 Support

For issues, check:
1. Environment variables are set
2. Supabase schema is created
3. LiveKit credentials are valid
4. Python 3.9+ is installed

