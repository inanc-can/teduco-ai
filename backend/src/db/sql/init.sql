-- Supabase initial schema for teduco
-- Extensions ------------------------------------------------------------
create extension if not exists "uuid-ossp";
create extension if not exists "pgcrypto";

-- ENUM types ------------------------------------------------------------
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'applicant_type') THEN
        CREATE TYPE applicant_type AS ENUM ('high-school', 'university');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'doc_type') THEN
        CREATE TYPE doc_type AS ENUM ('transcript', 'language', 'statement', 'other');
    END IF;
END$$;

-- Users (1‑1 with auth.users) -------------------------------------------
CREATE TABLE IF NOT EXISTS public.users (
    user_id      uuid PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    first_name   text            NOT NULL,
    last_name    text            NOT NULL,
    phone        text,
    birth_date   date,
    current_city text,
    applicant_type applicant_type,
    created_at   timestamptz     DEFAULT now(),
    updated_at   timestamptz     DEFAULT now()
);

-- Education tables ------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.high_school_education (
    user_id               uuid PRIMARY KEY REFERENCES public.users(user_id) ON DELETE CASCADE,
    high_school_name      text      NOT NULL,
    gpa                   numeric(4,2),
    gpa_scale             numeric(4,2),
    grad_year             smallint,
    yks_placed            text,
    extracurriculars      text,
    scholarship_interest  text,
    updated_at            timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.university_education (
    user_id              uuid PRIMARY KEY REFERENCES public.users(user_id) ON DELETE CASCADE,
    university_name      text      NOT NULL,
    university_program   text      NOT NULL,
    gpa                  numeric(4,2),
    credits_completed    integer,
    expected_graduation  date,
    study_mode           text,
    research_focus       text,
    portfolio_link       text,
    updated_at           timestamptz DEFAULT now()
);

-- Onboarding preferences -------------------------------------------------
CREATE TABLE IF NOT EXISTS public.onboarding_preferences (
    user_id            uuid PRIMARY KEY REFERENCES public.users(user_id) ON DELETE CASCADE,
    desired_countries  text[]      DEFAULT '{}',
    desired_fields     text[]      DEFAULT '{}',
    target_programs    text[]      DEFAULT '{}',
    preferred_intake   text,
    preferred_support  text,
    additional_notes   text,
    updated_at         timestamptz DEFAULT now()
);

-- Documents --------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.documents (
    document_id  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id      uuid      NOT NULL REFERENCES public.users(user_id) ON DELETE CASCADE,
    doc_type     doc_type  NOT NULL,
    storage_path text      NOT NULL,
    mime_type    text,
    uploaded_at  timestamptz DEFAULT now()
);

-- Reference data: universities ------------------------------------------
CREATE TABLE IF NOT EXISTS public.universities (
    university_id serial PRIMARY KEY,
    name          text NOT NULL,
    country       text NOT NULL
);

-- Timestamps trigger -----------------------------------------------------
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_users_updated
BEFORE UPDATE ON public.users
FOR EACH ROW EXECUTE PROCEDURE set_updated_at();

CREATE TRIGGER trg_hs_updated
BEFORE UPDATE ON public.high_school_education
FOR EACH ROW EXECUTE PROCEDURE set_updated_at();

CREATE TRIGGER trg_uni_updated
BEFORE UPDATE ON public.university_education
FOR EACH ROW EXECUTE PROCEDURE set_updated_at();

CREATE TRIGGER trg_pref_updated
BEFORE UPDATE ON public.onboarding_preferences
FOR EACH ROW EXECUTE PROCEDURE set_updated_at();

-- Row‑level security -----------------------------------------------------
ALTER TABLE public.users                 ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.high_school_education ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.university_education  ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.onboarding_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.documents             ENABLE ROW LEVEL SECURITY;

-- Owner‑based policies ---------------------------------------------------
CREATE POLICY "Own user row" ON public.users
  USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Own HS row" ON public.high_school_education
  USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Own UNI row" ON public.university_education
  USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Own prefs row" ON public.onboarding_preferences
  USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Own documents row" ON public.documents
  USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);