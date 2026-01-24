-- Supabase SQL Schema for Appointment System
-- Run this in Supabase SQL Editor

-- Create appointments table
CREATE TABLE IF NOT EXISTS appointments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_phone VARCHAR(20) NOT NULL,
    user_name VARCHAR(100),
    appointment_date DATE NOT NULL,
    appointment_time TIME NOT NULL,
    status VARCHAR(20) DEFAULT 'booked' CHECK (status IN ('booked', 'cancelled', 'completed')),
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_appointments_user_phone ON appointments(user_phone);
CREATE INDEX IF NOT EXISTS idx_appointments_status ON appointments(status);
CREATE INDEX IF NOT EXISTS idx_appointments_date ON appointments(appointment_date);

-- CRITICAL: Unique constraint to prevent double-booking
-- Only one 'booked' appointment per date/time slot
CREATE UNIQUE INDEX IF NOT EXISTS idx_appointments_active_slot 
ON appointments(appointment_date, appointment_time) 
WHERE status = 'booked';

-- Create conversation logs table (optional but recommended)
CREATE TABLE IF NOT EXISTS conversation_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(100) NOT NULL,
    user_phone VARCHAR(20),
    conversation_summary TEXT,
    tool_calls JSONB,
    duration_seconds INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_conversation_logs_session ON conversation_logs(session_id);
CREATE INDEX IF NOT EXISTS idx_conversation_logs_user ON conversation_logs(user_phone);

-- Function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to auto-update updated_at
CREATE TRIGGER update_appointments_updated_at BEFORE UPDATE ON appointments
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Enable Row Level Security (RLS) - Important for security
ALTER TABLE appointments ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversation_logs ENABLE ROW LEVEL SECURITY;

-- Policy: Allow all operations for authenticated users (backend service role)
-- Frontend will NOT have direct access
CREATE POLICY "Allow backend service full access" ON appointments
FOR ALL USING (true);

CREATE POLICY "Allow backend service full access to logs" ON conversation_logs
FOR ALL USING (true);

-- Insert some test data (optional)
-- Uncomment to add sample appointments
/*
INSERT INTO appointments (user_phone, user_name, appointment_date, appointment_time, notes)
VALUES 
    ('555-123-4567', 'John Doe', '2026-01-28', '09:00:00', 'Initial consultation'),
    ('555-987-6543', 'Jane Smith', '2026-01-28', '10:00:00', 'Follow-up');
*/

-- Verify schema
SELECT 
    table_name,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_name IN ('appointments', 'conversation_logs')
ORDER BY table_name, ordinal_position;

