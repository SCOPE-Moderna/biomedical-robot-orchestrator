CREATE TYPE run_status AS ENUM (
    'in-progress',
    'waiting',
    'completed',
    'failed',
    'paused'
    );

-- Flow Runs
CREATE TABLE flow_runs
(
    id                 SERIAL PRIMARY KEY,
    name               TEXT       NOT NULL,
    start_flow_node_id TEXT       NOT NULL,
    current_node_id    TEXT       NOT NULL,
    started_at         TIMESTAMP           DEFAULT NOW(),
    status             run_status NOT NULL DEFAULT 'in-progress'
);

-- Node Runs
CREATE TABLE node_runs
(
    id          SERIAL PRIMARY KEY,
    flow_run_id INTEGER    NOT NULL REFERENCES flow_runs (id),
    node_id     TEXT       NOT NULL,
    input_data  JSONB,
    output_data JSONB,
    started_at  TIMESTAMP           DEFAULT NOW(),
    finished_at TIMESTAMP,
    status      run_status NOT NULL DEFAULT 'in-progress'
);

-- Instruments
CREATE TABLE instruments
(
    id                SERIAL PRIMARY KEY,
    name              TEXT NOT NULL,
    type              TEXT NOT NULL,
    connection_method TEXT NOT NULL,
    created_at        TEXT NOT NULL,
    updated_at        TIMESTAMP DEFAULT NOW()
);

-- Plate Locations
CREATE TABLE plate_locations
(
    id            TEXT UNIQUE PRIMARY KEY,
    type          TEXT, -- e.g. instrument, hotel, plate_holder, etc.
    in_use_by     INTEGER REFERENCES node_runs (id),
    instrument_id INTEGER REFERENCES instruments (id),
    parent_id     TEXT REFERENCES plate_locations (id),
    x_capacity    NUMERIC,
    y_capacity    NUMERIC
);
