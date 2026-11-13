-- Almacén de vectores del flujo n8n (Nivel 1) en Supabase con pgvector.
-- Guarda los fragmentos de las fuentes OWASP que consulta el agente (RAG).
-- Ejecutar una sola vez en Supabase → SQL Editor.
--
-- Embeddings: OpenAI text-embedding-3-small (1536 dimensiones).
-- En el nodo "Supabase Vector Store" de n8n usar:
--   Table Name = documentos_owasp      Query Name = match_documentos_owasp

create extension if not exists vector;

create table if not exists documentos_owasp (
    id        bigserial primary key,
    content   text,          -- texto del fragmento
    metadata  jsonb,         -- fuente (ASVS, API Top 10, Threat Modeling) y posición
    embedding vector(1536)
);

create or replace function match_documentos_owasp(
    query_embedding vector(1536),
    match_count     int   default null,
    filter          jsonb default '{}'
)
returns table (id bigint, content text, metadata jsonb, similarity float)
language plpgsql
as $$
#variable_conflict use_column
begin
    return query
    select id, content, metadata,
           1 - (documentos_owasp.embedding <=> query_embedding) as similarity
    from documentos_owasp
    where metadata @> filter
    order by documentos_owasp.embedding <=> query_embedding
    limit match_count;
end;
$$;
