# Astroalex Backend

Python FastAPI backend for the Astroalex astrophotography processing pipeline.

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
```

2. Activate the virtual environment:
```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Copy environment configuration:
```bash
cp .env.example .env
```

5. Run the development server:
```bash
cd app
python main.py
```

The API will be available at `http://localhost:8000`

## API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI application entry point
│   ├── models/          # Data models (Pydantic)
│   ├── routers/         # API route handlers
│   ├── services/        # Business logic
│   └── utils/           # Utility functions
├── tests/               # Test files
├── requirements.txt     # Python dependencies
└── .env.example         # Environment variables template
```
