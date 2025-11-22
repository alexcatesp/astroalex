# Astroalex Development Guide

## Getting Started

### Prerequisites

- Node.js 20+ (for frontend)
- Python 3.11+ (for backend)
- npm or yarn (for frontend package management)
- pip (for Python package management)

### Quick Start

1. **Clone the repository**
```bash
git clone <repository-url>
cd astroalex
```

2. **Setup Backend**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

3. **Setup Frontend**
```bash
cd frontend
npm install
cp .env.example .env.local
```

4. **Run Development Servers**

Terminal 1 - Backend:
```bash
cd backend/app
python main.py
```

Terminal 2 - Frontend:
```bash
cd frontend
npm run dev
```

5. **Access the Application**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Project Structure

```
astroalex/
├── frontend/          # Next.js 15 + TypeScript
│   ├── app/          # App Router pages
│   ├── components/   # React components
│   └── lib/          # Utilities and API client
├── backend/          # FastAPI Python backend
│   ├── app/
│   │   ├── main.py   # API entry point
│   │   ├── routers/  # API endpoints
│   │   ├── services/ # Business logic
│   │   └── models/   # Pydantic models
│   └── tests/        # Backend tests
├── shared/           # Shared types/schemas
└── docs/             # Documentation
```

## Development Workflow

### Adding a New Feature

1. **Plan the feature** - Define requirements and architecture
2. **Update shared types** - Add/modify TypeScript types in `shared/types.ts`
3. **Backend development**:
   - Create Pydantic models matching shared types
   - Implement service logic
   - Add API endpoints in routers
   - Write tests
4. **Frontend development**:
   - Create/update components
   - Implement API calls using the client
   - Add UI pages
5. **Test integration** - Ensure frontend and backend work together
6. **Update documentation** - Update CLAUDE.md and relevant docs
7. **Commit and push** - Follow conventional commits

### Conventional Commits

We use conventional commits for clear version control history:

- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `style:` - Code style changes (formatting, etc.)
- `refactor:` - Code refactoring
- `test:` - Adding or updating tests
- `chore:` - Maintenance tasks

Example: `feat: add project creation endpoint`

## Testing

### Backend Tests
```bash
cd backend
pytest
```

### Frontend Tests
```bash
cd frontend
npm test
```

## Common Tasks

### Adding a New API Endpoint

1. Define Pydantic models in `backend/app/models/`
2. Create router in `backend/app/routers/`
3. Register router in `backend/app/main.py`
4. Add corresponding method in `frontend/lib/api.ts`

### Adding a New Page

1. Create file in `frontend/app/[page-name]/page.tsx`
2. Implement component with TypeScript
3. Use shared types from `shared/types.ts`
4. Make API calls using `apiClient` from `lib/api.ts`

## Troubleshooting

### CORS Issues
- Ensure backend CORS middleware includes frontend URL
- Check that requests are going to correct backend URL

### Type Mismatches
- Verify shared types match Pydantic models
- Check API response format matches expected types

### Port Conflicts
- Backend default: 8000
- Frontend default: 3000
- Change ports in respective config files if needed
