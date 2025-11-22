# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Astroalex** is an intelligent astrophotography processing pipeline application. It's a project manager rather than a toolbox - it automates tedious workflow steps by leveraging a logical directory structure, allowing users to focus on quality decisions.

**Core Philosophy:** Assume and enforce a structured directory layout to automate 90% of the tedious work. Backend powered by Python with standard astronomy libraries (Astropy, CCDProc, Astroalign) for scientifically valid results.

## Technology Stack

- **Frontend:** Next.js 15, TypeScript, Tailwind CSS
- **Backend:** Python, FastAPI
- **Core Libraries:** Astropy, CCDProc, Astroalign, Photutils, Reproject, NumPy
- **Communication:** REST API with CORS support

## Architecture Overview

The application is organized around 5 main modules that follow the astrophotography processing pipeline:

### 1. Project Management (Core)
- Auto-generates standardized directory structure for each project:
  - `00_ingest/` - Drop zone for raw files
  - `01_raw_data/` - Organized raw data (calibration/, science/)
  - `02_processed_data/` - Processed outputs (masters/, science/)
  - `03_scripts/` - Optional advanced user scripts
- Project dashboard showing data summary, calibration status, stacking progress, and preview images

### 2. Ingestion Module ("El Mayordomo")
- Drag-and-drop interface for `00_ingest/` folder
- Automatic metadata extraction from ASIAIR filenames:
  - Image type (Light, Dark, Bias, Flat)
  - Object, Filter, Exposure time, Gain, Date
- One-click file organization into `01_raw_data/` with auto-created subdirectories
- Calibration session management (e.g., "2025-10-26_Newton200_ASI533")

### 3. Calibration Masters Module
- Visual interface for each master type (Bias, Darks, Flats)
- Auto-detection of raw calibration files in `01_raw_data/calibration/SESSION_NAME/`
- Thumbnail inspection with blink comparison
- User can reject frames with artifacts
- Combination methods: Average, Median
- Rejection methods: Sigma Clipping, Min/Max
- Outputs to `02_processed_data/masters/SESSION_NAME/` with standardized naming (e.g., `master_dark_300s_gain100.fits`)

### 4. Processing Pipeline (Core Module)
Modular visual workflow builder with processing blocks:
1. **Calibration Block** - Apply master calibration frames (auto-suggested based on metadata)
2. **Quality Analysis Block** (Optional) - Measure FWHM and eccentricity, reject poor frames
3. **Registration Block** - Align images using Astroalign
4. **Stacking Block** - Integrate aligned frames with chosen combination/rejection methods

Outputs:
- Intermediate results: `02_processed_data/science/OBJECT_NAME/` (calibrated/, registered/)
- Final stacks: `02_processed_data/science/OBJECT_NAME/stacked/`

### 5. Mosaic Assembly & Color Combination
- **Mosaic Assembly:**
  - Auto-detects panel alignment from WCS metadata
  - Background equalization and projection method options
- **Color Combination:**
  - LRGB: 4-slot interface (L, R, G, B) with color balance and luminance saturation controls
  - HaLRGB/SHO: Flexible channel mapping with simplified PixelMath (e.g., `R = 0.8*Ha + 0.2*R`)

### 6. Visualization & Export
- Integrated high-dynamic-range FITS viewer
- Non-destructive histogram stretching (Asinh, Log, Linear) saved as "recipes"
- Background extraction tool (ABE/DBE methods)
- Export formats: FITS, TIFF (16-bit), JPG

## Directory Structure Convention

Projects follow this structure:
```
PROJECT_NAME/
├── 00_ingest/                    # Drop zone for raw files
├── 01_raw_data/
│   ├── calibration/
│   │   └── SESSION_NAME/
│   │       ├── darks/
│   │       ├── flats/
│   │       └── bias/
│   └── science/
│       └── OBJECT_NAME/
│           └── DATE/
│               └── Filter_X/
├── 02_processed_data/
│   ├── masters/
│   │   └── SESSION_NAME/
│   └── science/
│       └── OBJECT_NAME/
│           ├── calibrated/
│           ├── registered/
│           └── stacked/
└── 03_scripts/                   # Optional user scripts
```

## File Naming Conventions

The application expects ASIAIR-style filenames that encode metadata:
- Pattern: `{OBJECT}_{TYPE}_{FILTER}_{EXPOSURE}s_gain{GAIN}_{DATE}_{SEQUENCE}.fit`
- Example: `M31_Andromeda_Galaxy_Light_Filter_L_300s_gain100_2025-10-26_001.fit`

Master calibration files use standardized naming:
- Pattern: `master_{TYPE}_{EXPOSURE}s_gain{GAIN}.fits`
- Example: `master_dark_300s_gain100.fits`

## Development Guidelines

### FITS File Handling
- Always preserve WCS (World Coordinate System) metadata through the pipeline
- Use Astropy for FITS I/O to ensure header integrity
- Calibration operations should use CCDProc for scientifically valid results

### Pipeline Design
- Each processing step must be reproducible and logged
- Intermediate results should be saved to allow pipeline restart from any point
- Processing blocks should be modular and reusable across different workflows

### Metadata Management
- Extract and validate metadata early (during ingestion)
- Store processing history in FITS headers
- Track calibration frame associations (which masters were applied to which science frames)

### UI Considerations
- The interface should guide users through the logical workflow sequence
- Auto-suggest appropriate calibration frames based on matching exposure time, gain, and temporal proximity
- Provide visual feedback on processing progress for long operations
- Allow batch processing while showing per-frame status

## Development Commands

### Frontend (Next.js)
```bash
cd frontend
npm install          # Install dependencies
npm run dev          # Start development server (http://localhost:3000)
npm run build        # Build for production
npm run lint         # Run ESLint
```

### Backend (FastAPI)
```bash
cd backend
python -m venv venv  # Create virtual environment
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt  # Install dependencies
cd app
python main.py       # Start development server (http://localhost:8000)
```

### API Documentation
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Repository Structure

```
astroalex/
├── frontend/          # Next.js 15 + TypeScript frontend
│   ├── app/          # App Router pages and layouts
│   ├── components/   # React components
│   ├── lib/          # Utilities and API client
│   └── public/       # Static assets
├── backend/          # FastAPI Python backend
│   ├── app/
│   │   ├── main.py   # API entry point
│   │   ├── routers/  # API endpoint handlers
│   │   ├── services/ # Business logic layer
│   │   ├── models/   # Pydantic data models
│   │   └── utils/    # Utility functions
│   └── tests/        # Backend tests
├── shared/           # Shared TypeScript types/schemas
│   └── types.ts      # Type definitions
└── docs/             # Documentation
    └── DEVELOPMENT.md # Development guide
```

## Current Implementation Status

### Phase 0: Configuration (✅ COMPLETED)
- ✅ Next.js 15 frontend with TypeScript and Tailwind CSS
- ✅ FastAPI backend with Python
- ✅ API client configuration for frontend-backend communication
- ✅ Shared type definitions
- ✅ Project documentation structure

### Phase 1: Project Management & Ingestion (✅ COMPLETED)

**Backend Implementation:**
- ✅ Pydantic models for projects, metadata, and pipelines
- ✅ DirectoryManager utility for creating standardized project structures
- ✅ MetadataParser supporting ASIAIR and generic FITS filename formats
- ✅ ProjectService for CRUD operations with JSON metadata storage
- ✅ IngestionService ("El Mayordomo") for file organization
- ✅ REST API endpoints:
  - `/projects/` - Create, list, get, update, delete projects
  - `/projects/{id}/ingest/scan` - Scan ingestion directory
  - `/projects/{id}/ingest/stats` - Get file statistics
  - `/projects/{id}/ingest/organize` - Organize files into structure

**Frontend Implementation:**
- ✅ Updated API client with project and ingestion methods
- ✅ Home page with projects grid and create modal
- ✅ ProjectCard component for displaying project info
- ✅ CreateProjectModal for new project creation
- ✅ Project detail page with ingestion interface
- ✅ File scanning and statistics display
- ✅ One-click file organization with session naming

**Key Features:**
- Automatic directory structure generation (00_ingest, 01_raw_data, 02_processed_data, 03_scripts)
- Metadata extraction from ASIAIR and other filename formats
- Intelligent file organization based on image type (Light, Dark, Flat, Bias)
- Calibration session management for grouping calibration frames
- Science frame organization by object, date, and filter
- Real-time file statistics (by type, filter, object, date)

### Next Steps: Phase 2 - Masters de Calibración
- Visual interface for Bias/Darks/Flats management
- Frame selection and rejection interface
- Combination algorithms (Average, Median)
- Rejection methods (Sigma Clipping, Min/Max)
- Master frame generation and storage

## Important Notes for Future Development
- After each successful implementation, update this file and commit changes
- Keep shared types in sync between TypeScript and Pydantic models
- Use conventional commits (feat:, fix:, docs:, etc.)
- Test frontend-backend integration after API changes