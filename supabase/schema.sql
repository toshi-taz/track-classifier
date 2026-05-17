-- Track Classifier — Supabase schema
-- Ejecutar en el SQL Editor de Supabase (https://app.supabase.com)

create table if not exists public.classifications (
    id                     bigint generated always as identity primary key,
    created_at             timestamptz default now(),
    timestamp              text        not null,
    species                text,
    scientific_name        text,
    confidence             real,
    mode                   text,
    latitude               real,
    longitude              real,
    gps_source             text,
    conservation_status    text,
    track_condition        text,
    animal_size_estimate   text,
    estimated_nesting_time text,
    immediate_action       text
);

-- Row Level Security
alter table public.classifications enable row level security;

-- Política para la service_role key (backend): acceso total
create policy "backend_full_access"
    on public.classifications
    for all
    to service_role
    using (true)
    with check (true);
