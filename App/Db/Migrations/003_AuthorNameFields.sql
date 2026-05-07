ALTER TABLE authors
    ADD COLUMN IF NOT EXISTS last_name VARCHAR(255)
        CHECK (last_name IS NULL OR length(trim(last_name)) > 0),
    ADD COLUMN IF NOT EXISTS middle_name VARCHAR(255)
        CHECK (middle_name IS NULL OR length(trim(middle_name)) > 0);

DROP INDEX IF EXISTS idx_authors_name_penname;

CREATE UNIQUE INDEX IF NOT EXISTS idx_authors_unique_name
    ON authors (
        name,
        COALESCE(middle_name, ''),
        COALESCE(last_name, ''),
        COALESCE(pen_name, '')
    );
