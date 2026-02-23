# Flight Management System

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-2.x-black?logo=flask&logoColor=white)

## Overview

**A real-time flight search and price comparison engine built with Flask and the Amadeus API.**

This project provides an end-to-end flight discovery and booking-oriented workflow with a clean web interface, live flight data integration, and backend persistence for passenger and reservation operations.

## Features

- Real-time API data fetching
- Dynamic search (source, destination, date)
- SQL-based passenger management
- Responsive UI

## Tech Stack

- Python
- Flask
- Amadeus SDK
- SQL
- HTML/CSS

## Setup

### 1) Clone the repository

```bash
git clone <your-repo-url>
cd Flight_app
```

### 2) Create and activate a virtual environment

**Windows (PowerShell):**

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**macOS/Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3) Install dependencies

```bash
pip install -r requirements.txt
```

### 4) Configure credentials

- Copy `.env.example` to a local `.env` file.
- Set your Amadeus credentials in `.env`:

```bash
AMADEUS_CLIENT_ID=your_amadeus_client_id_here
AMADEUS_CLIENT_SECRET=your_amadeus_client_secret_here
```

- Keep `.env` private (it is gitignored by default).

### 5) Run the application

```bash
python src/app.py
```


## Security Best Practice

- Never hardcode API keys in source files.
- Keep secrets only in local `.env` or your deployment platform's secret manager.
- If any credential was previously committed, rotate it immediately in the provider dashboard.

## Developer Note

This project was developed by a **B.Tech CS-AI/ML student at RVCE**.
