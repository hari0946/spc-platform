-- Required PostgreSQL extensions.
-- pgcrypto provides gen_random_uuid() used as the default for all UUID
-- primary keys across the schema.

CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
