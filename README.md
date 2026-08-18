# Car Parking Management System

Web system for managing parking lines and their vehicles.

## MVP features
- Dashboard with total lines, vehicles, active vehicles and maintenance vehicles.
- Add/edit lines.
- Automatic vehicle count per line.
- Add/edit vehicles.
- Vehicle fields: plate number, type, brand, model, chassis number, engine number, year, status, driver, line.
- Search by plate/chassis/engine/type/line.
- Arabic RTL interface.
- SQLite for quick local use or MySQL via Docker Compose.

## Run with Docker
```bash
docker compose up -d --build
```
Open `http://localhost:5000`.

## Run locally
```bash
python -m venv .venv
. .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
python app.py
```
