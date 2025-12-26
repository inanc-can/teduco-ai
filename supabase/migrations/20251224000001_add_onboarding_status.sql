-- Add onboarding status columns to users table
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS onboarding_completed BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS onboarding_completed_at TIMESTAMPTZ;

-- Add index for faster onboarding status queries
CREATE INDEX IF NOT EXISTS idx_users_onboarding_completed ON users(onboarding_completed);

-- Add comment to explain the columns
COMMENT ON COLUMN users.onboarding_completed IS 'Indicates whether the user has completed the onboarding process';
COMMENT ON COLUMN users.onboarding_completed_at IS 'Timestamp when the user completed onboarding';
