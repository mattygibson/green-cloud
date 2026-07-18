-- Initial schema for GreenCloud sample app
-- This runs on first PostgreSQL startup if the database is empty

CREATE TABLE IF NOT EXISTS items (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description VARCHAR(500),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Seed with a sample item so the UI has something to show
INSERT INTO items (name, description) VALUES
    ('GreenCloud', 'Carbon-aware self-hosted PaaS running on Raspberry Pi');
