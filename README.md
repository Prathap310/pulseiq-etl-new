# PulseIQ - PQ-01 ETL Pipeline

Repeatable ETL pipeline for validating PulseIQ data feeds, retaining rejected records with reasons, and logging row counts.

## Run the pipeline

Requirements: Docker Desktop running.

    docker compose run --rm etl

## Validation summary

- Input rows: 29,775
- Accepted rows: 29,345
- Rejected rows: 430

## Documentation

- [Delivery report](Docs/PQ-01-Task-1-Delivery-Report.md)
- [Data contract notes](Docs/data-contract-notes.md)
- [Metric dictionary](Docs/metric-dictionary.md)

## GitHub repository

https://github.com/Prathap310/pulseiq-etl-new
