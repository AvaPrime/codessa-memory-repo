create extension if not exists vector;

create table if not exists codex_entries (
  id uuid primary key,
  title text,
  content text not null,
  entry_type text not null,
  source text not null,
  source_ref text,
  tags text[] default '{}',
  reusable boolean default false,
  metadata jsonb default '{}'::jsonb,
  created_at timestamptz default now()
);

create table if not exists codex_embeddings (
  entry_id uuid primary key references codex_entries(id) on delete cascade,
  embedding vector(384) not null
);

create table if not exists chronospiral_logs (
  id uuid primary key,
  session_label text,
  summary text not null,
  decisions jsonb default '[]'::jsonb,
  next_steps jsonb default '[]'::jsonb,
  linked_entries uuid[] default '{}',
  metadata jsonb default '{}'::jsonb,
  created_at timestamptz default now()
);

create index if not exists idx_codex_entries_source on codex_entries(source);
create index if not exists idx_codex_entries_tags on codex_entries using gin(tags);
create index if not exists idx_codex_entries_metadata on codex_entries using gin(metadata);
