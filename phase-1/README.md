# PulseIQ – Phase 1

## Tasks Covered
Phase 1 contains Tasks 1–5 of the PulseIQ ETL project.

## Project Files

### Source
Contains the ETL pipeline, data validation, Pandera schemas, pipeline runner, and application source files.

### Warehouse
Contains the PostgreSQL warehouse schema, warehouse loader, and metric view SQL files.

### Data_Quality
Contains data-quality check scripts and supporting SQL files.

### Data
Contains the project datasets, including raw, clean, and rejected data files.

### Reports
Contains task-wise evidence, validation results, data-quality reports, and dashboard or analysis outputs for Tasks 1–5.

### Docs
Contains the Task 1 delivery report, data contract notes, metric dictionary, and warehouse schema documentation.

### Logs
Contains ETL pipeline logs and execution summaries.

### tests
Contains automated test files for the ETL pipeline and data validation.

## Main Configuration Files
- Dockerfile – Docker image configuration
- docker-compose.yml – Docker Compose configuration
- requirements.txt – Python dependencies

## Verification
- Task 1 ETL pipeline executed successfully using Docker Compose.
- ETL validation counts reconciled between input, clean, and rejected records.
- PostgreSQL warehouse database and key populated fact tables were verified for Task 2.
- Task-specific implementation and evidence files for Tasks 3–5 are included in Reports and supporting folders.

Note: Task 1 production sign-off remains pending data-owner decisions on the outstanding data-quality issues documented in the delivery report.

## Original Files
The original project files remain in their existing locations. Phase 1 contains copies of the relevant files and evidence.
