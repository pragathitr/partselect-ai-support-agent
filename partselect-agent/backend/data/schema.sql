-- PartSelect Agent — SQLite Schema
-- Extensibility anchor: new product type = insert row + YAML + data, zero code changes

CREATE TABLE IF NOT EXISTS appliance_categories (
    id                    INTEGER PRIMARY KEY,
    slug                  TEXT UNIQUE NOT NULL,
    display_name          TEXT NOT NULL,
    specialist_config_path TEXT,
    is_active             BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS parts (
    part_number    TEXT PRIMARY KEY,
    name           TEXT NOT NULL,
    category_id    INTEGER REFERENCES appliance_categories(id),
    brand          TEXT,
    price          REAL,
    description    TEXT,
    in_stock       BOOLEAN DEFAULT TRUE,
    image_url      TEXT,
    mfr_part_number TEXT
);

CREATE TABLE IF NOT EXISTS models (
    model_number TEXT PRIMARY KEY,
    brand        TEXT,
    category_id  INTEGER REFERENCES appliance_categories(id),
    display_name TEXT
);

CREATE TABLE IF NOT EXISTS compatibility (
    part_number  TEXT REFERENCES parts(part_number),
    model_number TEXT REFERENCES models(model_number),
    confidence   TEXT DEFAULT 'confirmed',
    PRIMARY KEY (part_number, model_number)
);
CREATE INDEX IF NOT EXISTS idx_compat_part  ON compatibility(part_number);
CREATE INDEX IF NOT EXISTS idx_compat_model ON compatibility(model_number);

CREATE TABLE IF NOT EXISTS symptoms (
    id                TEXT PRIMARY KEY,
    description       TEXT NOT NULL,
    category_id       INTEGER REFERENCES appliance_categories(id),
    is_safety_critical BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS symptom_fixes (
    symptom_id  TEXT REFERENCES symptoms(id),
    part_number TEXT REFERENCES parts(part_number),
    rank        INTEGER DEFAULT 1,
    PRIMARY KEY (symptom_id, part_number)
);

-- install_guides: deterministic lookup by part — no RAG
CREATE TABLE IF NOT EXISTS install_guides (
    part_number  TEXT REFERENCES parts(part_number),
    step_order   INTEGER,
    instruction  TEXT,
    tool_required TEXT,
    safety_note  TEXT,
    PRIMARY KEY (part_number, step_order)
);

-- conversation persistence
CREATE TABLE IF NOT EXISTS conversations (
    id           TEXT PRIMARY KEY,
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    appliance_type TEXT,
    model_number TEXT
);

CREATE TABLE IF NOT EXISTS messages (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id  TEXT REFERENCES conversations(id),
    role             TEXT,
    content          TEXT,
    tool_calls_json  TEXT,
    validator_verdict TEXT,
    created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS orders (
    order_id           TEXT PRIMARY KEY,
    part_number        TEXT,
    status             TEXT,
    tracking_number    TEXT,
    estimated_delivery TEXT,
    customer_email     TEXT
);

-- -----------------------------------------------------------------------
-- Multi-hop query: symptom -> parts -> models (used in diagnose_symptom)
-- "What parts fix symptom X AND fit model Y?"
--
-- WITH RECURSIVE candidates AS (
--     SELECT sf.part_number, sf.rank
--     FROM symptom_fixes sf
--     WHERE sf.symptom_id = ?
-- )
-- SELECT c.part_number, c.rank, co.confidence
-- FROM candidates c
-- JOIN compatibility co ON co.part_number = c.part_number
-- WHERE co.model_number = ?
--   AND co.confidence IN ('confirmed', 'inferred')
-- ORDER BY c.rank;
-- -----------------------------------------------------------------------
