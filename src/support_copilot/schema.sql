-- Idempotent initial schema. No DROP statements or destructive migration steps.
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS tenants (
    id text PRIMARY KEY,
    name text NOT NULL
);

CREATE TABLE IF NOT EXISTS api_tokens (
    token_hash text PRIMARY KEY,
    tenant_id text NOT NULL REFERENCES tenants(id),
    scopes text[] NOT NULL DEFAULT '{}',
    created_at timestamptz NOT NULL DEFAULT now(),
    expires_at timestamptz,
    revoked_at timestamptz
);

CREATE TABLE IF NOT EXISTS documents (
    tenant_id text NOT NULL REFERENCES tenants(id),
    id text NOT NULL,
    title text NOT NULL,
    source text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, id)
);

CREATE TABLE IF NOT EXISTS chunks (
    tenant_id text NOT NULL,
    id uuid NOT NULL,
    document_id text NOT NULL,
    position integer NOT NULL CHECK (position >= 0),
    text text NOT NULL CHECK (length(text) > 0),
    embedding vector(384) NOT NULL,
    embed_model text NOT NULL,
    PRIMARY KEY (tenant_id, id),
    UNIQUE (tenant_id, document_id, position),
    FOREIGN KEY (tenant_id, document_id)
        REFERENCES documents(tenant_id, id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS chunks_tenant_idx ON chunks (tenant_id);
CREATE INDEX IF NOT EXISTS api_tokens_tenant_idx ON api_tokens (tenant_id);

-- Fictional Day 6 backend. Composite keys keep every relationship tenant-local.
CREATE TABLE IF NOT EXISTS customers (
    tenant_id text NOT NULL REFERENCES tenants(id),
    id text NOT NULL,
    name text NOT NULL,
    PRIMARY KEY (tenant_id, id)
);

CREATE TABLE IF NOT EXISTS orders (
    tenant_id text NOT NULL,
    id text NOT NULL,
    customer_id text NOT NULL,
    status text NOT NULL CHECK (status IN ('processing','shipped','delivered','cancelled','refunded')),
    total_cents integer NOT NULL CHECK (total_cents >= 0),
    currency text NOT NULL CHECK (currency = 'USD'),
    tracking_number text,
    placed_on date NOT NULL,
    PRIMARY KEY (tenant_id, id),
    FOREIGN KEY (tenant_id, customer_id) REFERENCES customers(tenant_id, id)
);

CREATE TABLE IF NOT EXISTS tickets (
    tenant_id text NOT NULL,
    id text NOT NULL,
    customer_id text NOT NULL,
    text text NOT NULL,
    status text NOT NULL CHECK (status IN ('open','closed')),
    PRIMARY KEY (tenant_id, id),
    FOREIGN KEY (tenant_id, customer_id) REFERENCES customers(tenant_id, id)
);
