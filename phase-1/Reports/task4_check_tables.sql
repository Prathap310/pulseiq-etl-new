SELECT table_schema, table_name
FROM information_schema.tables
WHERE table_schema IN ('raw', 'dw', 'public')
ORDER BY table_schema, table_name;
