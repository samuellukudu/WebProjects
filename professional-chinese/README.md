# Professional Chinese Learning Platform

A web application for learning professional Chinese vocabulary with context-based learning and spaced repetition.

## Features

- Vocabulary management with traditional and simplified Chinese characters
- Interactive practice sessions
- Progress tracking
- Context-based learning categories
- Spaced repetition system for efficient learning

## Project Structure

```
professional-chinese/
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── routers/     # API endpoints
│   │   ├── models.py    # Database models
│   │   └── main.py      # Main application
│   └── requirements.txt  # Python dependencies
└── frontend/            # React frontend
    ├── public/
    ├── src/
    │   ├── components/  # Reusable components
    │   ├── pages/       # Page components
    │   └── services/    # API services
    └── package.json     # Node.js dependencies
```

## Setup

### Backend

1. Create a virtual environment:
```bash
python -m venv lang_env
source lang_env/bin/activate  # On Windows: lang_env\Scripts\activate
```

2. Install dependencies:
```bash
cd backend
pip install -r requirements.txt
```

3. Run the server:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Start the development server:
```bash
npm start
```

The application will be available at http://localhost:3000

## API Documentation

Once the backend is running, visit http://localhost:8000/docs for the interactive API documentation.

## Contributing

Feel free to open issues and pull requests for any improvements you'd like to contribute.
