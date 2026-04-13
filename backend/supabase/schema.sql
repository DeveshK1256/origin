-- Supabase schema for AI Recruitment Intelligence Platform

create extension if not exists pgcrypto;

create table if not exists public.resume_analyses (
  id text primary key,
  created_at timestamptz not null default timezone('utc', now()),
  source text,
  resume_filename text,
  candidate_name text,
  resume_score int,
  payload jsonb not null
);

create table if not exists public.job_analyses (
  id text primary key,
  created_at timestamptz not null default timezone('utc', now()),
  source text,
  role_title text,
  quality_score int,
  match_score int,
  payload jsonb not null
);

create table if not exists public.fake_job_checks (
  id text primary key,
  created_at timestamptz not null default timezone('utc', now()),
  source text,
  job_url text,
  scam_probability numeric,
  risk_level text,
  payload jsonb not null
);

create table if not exists public.resume_ai_generations (
  id text primary key,
  created_at timestamptz not null default timezone('utc', now()),
  source text,
  source_mode text,
  role_title text,
  resume_filename text,
  payload jsonb not null
);

create index if not exists idx_resume_analyses_created_at on public.resume_analyses (created_at desc);
create index if not exists idx_job_analyses_created_at on public.job_analyses (created_at desc);
create index if not exists idx_fake_job_checks_created_at on public.fake_job_checks (created_at desc);
create index if not exists idx_resume_ai_generations_created_at on public.resume_ai_generations (created_at desc);
