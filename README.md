# PulseIQ Analytics Project

## Project Overview

This repository contains the PulseIQ Analytics project, organized into three phases. Each phase contains a set of tasks completed as part of the project.

The project covers ETL pipeline development, data warehousing, data quality validation, analytics, reporting, and dashboard development.

## Repository Structure

```text
pulseiq-etl-new/
├── README.md
├── phase-1/
│   └── README.md
├── phase-2/
│   └── README.md
├── phase-3/
│   └── README.md
├── 03_Data/
├── 05_Starter/
├── Data/
├── Data_Quality/
├── Docs/
├── Logs/
├── Reports/
├── Src/
├── Warehouse/
└── tests/
```

## Requirements

- Git
- Docker Desktop with Docker Compose
- Python 3.12

## How to Run

### 1. Clone the Repository

```bash
git clone https://github.com/Prathap310/pulseiq-etl-new.git
cd pulseiq-etl-new
```

### 2. Run the ETL Pipeline

Make sure Docker Desktop is running, then execute:

```bash
docker compose run --rm etl
```

### 3. Run Automated Tests

Activate your Python virtual environment, install the dependencies from `requirements.txt`, and execute:

```bash
python -m unittest discover -s Src -p "test_etl.py" -v
```

## Project Phases

- **Phase 1:** Tasks 1–5
- **Phase 2:** Tasks 6–10
- **Phase 3:** Tasks 11–15
- **Phase 4:** To be added after completion and release.

Each phase folder contains its relevant application files, reports, datasets, screenshots, and documentation.

## Original Project Files

The original project files remain in their existing locations. The phase folders contain copies of the relevant project deliverables.

## Repository

All project phases are maintained in this single GitHub repository.