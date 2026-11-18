# PulseIQ Analytics Project

## Project Overview

This repository contains the PulseIQ Analytics project, organized into four phases. The project covers ETL pipeline development, data warehousing, data quality validation, analytics, reporting, and dashboard development.

## Repository Structure

```text
pulseiq-etl-new/
+-- README.md
+-- phase-1/
+-- phase-2/
+-- phase-3/
+-- 03_Data/
+-- 05_Starter/
+-- Data/
+-- Data_Quality/
+-- Docs/
+-- Logs/
+-- Reports/
+-- Src/
+-- Warehouse/
+-- tests/
```

## Requirements

- Git
- Docker Desktop with Docker Compose
- Python 3.13
- PostgreSQL database for warehouse reporting

## Initial Setup

### 1. Clone the Repository

```bash
git clone https://github.com/Prathap310/pulseiq-etl-new.git
cd pulseiq-etl-new
```

### 2. Create a Virtual Environment

```bash
python -m venv .venv
```

Activate it in PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Configure Database Connection

Create a `.env` file in the project root using the database connection settings for your PostgreSQL environment.

Required variables:

```text
PGHOST=localhost
PGPORT=5433
PGDATABASE=your_database
PGUSER=your_username
PGPASSWORD=your_password
PGSCHEMA=dw
```

Use your own database credentials. Do not commit `.env` to Git.

## How to Run

### 1. Run the ETL Pipeline

Make sure Docker Desktop and the required PostgreSQL service are running.

```bash
docker compose run --rm etl
```

### 2. Run Automated Tests

```bash
python -m unittest discover -s Src -p "test_etl.py" -v
```

## Task 16 - Automated Report Builder

Task 16 generates monthly management reports in Excel and PDF formats using five warehouse metric views.

### Included Metrics

1. M01 - Monthly Department Headcount
2. M04 - Monthly Department Attrition
3. M09 - Department Employer Payroll Cost
4. M13 - Department Attendance Rate
5. M17 - Monthly Company Net Profit

### Generate a Report

Run the following command for the required reporting month:

```bash
python Src/build_report.py --month 2026-09
```

Replace `2026-09` with the required month in `YYYY-MM` format.

The generated files are saved in:

```text
Reports/Task16/
```

Each reporting month produces:
- Excel management report with a summary sheet, five metric sheets, and charts.
- PDF management report with the reporting period and warehouse data cut-off.

### Monthly Report Scheduling

The monthly scheduler script is:

```bash
python Src/run_monthly_report.py
```

It identifies the latest available reporting month in the warehouse and generates its report.

A Windows Task Scheduler task can run this script automatically on the first day of each month at 9:00 AM. The PostgreSQL service must be available when the task runs.

### Task 16 Evidence

Task 16 evidence and sample reports are stored in:

```text
Reports/Task16/
```

Evidence notes:

```text
Reports/Task16/Evidence/Task16_Evidence.md
```

## Project Phases

- **Phase 1:** Tasks 1–5
- **Phase 2:** Tasks 6–10
- **Phase 3:** Tasks 11–15
- **Phase 4:** Task 16-20

Each phase folder contains its relevant application files, reports, datasets, screenshots, and documentation.

## Original Project Files

The original project files remain in their existing locations. The phase folders contain copies of the relevant project deliverables.

## Repository

All project phases are maintained in this single GitHub repository.
