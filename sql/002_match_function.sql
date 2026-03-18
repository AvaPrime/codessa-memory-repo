create or replace function match_codex_entries(
  query_embedding vector(384),
  match_count int default 5,
  filter_source text default null
)
returns table (
  entry_id uuid,
  title text,
  content text,
  source text,
  similarity float
)
language sql
as $$
  select e.id, e.title, e.content, e.source,
         1 - (ce.embedding <=> query_embedding) as similarity
  from codex_embeddings ce
  join codex_entries e on e.id = ce.entry_id
  where filter_source is null or e.source = filter_source
  order by ce.embedding <=> query_embedding
  limit match_count;
$$;
