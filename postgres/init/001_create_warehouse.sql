CREATE SCHEMA IF NOT EXISTS bronze;
CREATE SCHEMA IF NOT EXISTS silver;
CREATE SCHEMA IF NOT EXISTS gold;
CREATE SCHEMA IF NOT EXISTS mart;

CREATE TABLE IF NOT EXISTS mart.pipeline_registry (
    pipeline_name TEXT PRIMARY KEY,
    owner_team TEXT NOT NULL,
    layer TEXT NOT NULL CHECK (layer IN ('bronze', 'silver', 'gold', 'serving')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO mart.pipeline_registry (pipeline_name, owner_team, layer)
VALUES
    ('orders_stream_to_bronze', 'data-platform', 'bronze'),
    ('sales_gold_models', 'analytics-engineering', 'gold')
ON CONFLICT (pipeline_name) DO NOTHING;
