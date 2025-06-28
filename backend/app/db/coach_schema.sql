-- Coach Feature Database Schema
-- This file defines the database schema for the Sara AI Coach feature in ChatChonk.
-- Author: Rip Jonesy

-- -----------------------------------------------------------------------------
-- Table: coach_conversations
-- Purpose: Stores metadata about coach conversations between users and Sara.
-- Each conversation can contain multiple messages.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS coach_conversations (
    -- Unique identifier for the conversation
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Reference to the user who owns this conversation
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    
    -- When the conversation was created
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    
    -- Flexible metadata storage for conversation context, settings, etc.
    -- Can include persona_id, session_data, UI context, etc.
    metadata JSONB DEFAULT '{}'::JSONB
);

-- Index on user_id for faster lookup of a user's conversations
CREATE INDEX IF NOT EXISTS idx_coach_conversations_user_id ON coach_conversations(user_id);

-- -----------------------------------------------------------------------------
-- Table: coach_messages
-- Purpose: Stores individual messages exchanged in coach conversations.
-- Each message belongs to a specific conversation and can have associated audio.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS coach_messages (
    -- Auto-incrementing ID for messages (bigserial for high volume)
    id BIGSERIAL PRIMARY KEY,
    
    -- Reference to the conversation this message belongs to
    conversation_id UUID NOT NULL REFERENCES coach_conversations(id) ON DELETE CASCADE,
    
    -- Reference to the user associated with this message
    -- (useful for multi-user conversations in the future)
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    
    -- Who sent the message: 'user' (the human) or 'assistant' (Sara)
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    
    -- The actual text content of the message
    content TEXT NOT NULL,
    
    -- Optional URL to the audio file for this message
    -- (primarily for assistant messages, but could be used for user voice input too)
    audio_url TEXT,
    
    -- When the message was created
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL
);

-- Index on conversation_id for faster retrieval of messages in a conversation
CREATE INDEX IF NOT EXISTS idx_coach_messages_conversation_id ON coach_messages(conversation_id);

-- Index on user_id for faster lookup of a user's messages across conversations
CREATE INDEX IF NOT EXISTS idx_coach_messages_user_id ON coach_messages(user_id);

-- Composite index on conversation_id and created_at for efficient chronological retrieval
CREATE INDEX IF NOT EXISTS idx_coach_messages_conversation_time 
    ON coach_messages(conversation_id, created_at);

-- Enable Row-Level Security (RLS) for both tables
ALTER TABLE coach_conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE coach_messages ENABLE ROW LEVEL SECURITY;

-- Create policies to ensure users can only access their own conversations and messages
CREATE POLICY coach_conversations_user_policy ON coach_conversations
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY coach_messages_user_policy ON coach_messages
    FOR ALL USING (auth.uid() = user_id);

-- Add comment to explain the overall schema
COMMENT ON SCHEMA public IS 'ChatChonk schema including the Sara AI Coach feature tables';
