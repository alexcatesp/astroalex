# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Astroalex V2.0** is an intelligent astrophotography assistant that guides users through the complete workflow - from planning observations before sunset to delivering the final processed image. It's not a toolbox of passive tools; it's an **Active Assistant with Guided Workflow (Wizard)** that tells users what to do next.

**Core Philosophy:** Guide the user through a chronological timeline. The app presents the next logical step instead of making users search through menus. Leverages AI, statistics, and astronomical data to provide certainty and optimization at every stage.

**Differentiation:** Unlike PixInsight ("here are 500 tools, build your solution"), Astroalex says "tell me what you want, I've analyzed the conditions, calculated the exact parameters, and here are the results."

## Technology Stack

- **Frontend:** Next.js 15, TypeScript, Tailwind CSS
- **Backend:** Python, FastAPI
- **Astronomy Libraries:** Astropy, CCDProc, Astroalign, Photutils, Reproject, Astroquery
- **ML/AI:** scikit-learn (Isolation Forest for quality control, potential U-Net for background extraction)
- **External APIs:** Meteoblue/OpenMeteo (weather/seeing), APASS/Vizier (photometric calibration)
- **Communication:** REST API with CORS support

## Architecture Overview - The Guided Workflow

The application follows a strict chronological workflow divided into two main phases:

### NIGHT PHASE (Steps 1-5): Planning & Acquisition

#### Step 1: Environmental Context (Pre-observation)
**User opens app before observing session**

- **Automatic Inputs:**
  - Geolocation (automatic)
  - Current date/time
- **Backend Processes:**
  - Query weather API (Meteoblue/OpenMeteo) for Seeing, Jet Stream, clouds
  - Calculate ephemerides (astronomical darkness window, moon phase)
- **Assistant Output Example:**
  > "Good evening, Alex. Tonight you have 5h 30m of astronomical darkness (23:00 - 04:30).
  > Seeing is mediocre (2.5"), I recommend avoiding extreme focal lengths or using 2x2 binning.
  > Moon is at 80%, suggesting narrowband work (H-alpha)."

**Implementation:**
- Service: `EnvironmentalService` (weather API + ephemerides calculation)
- Models: `ObservingSession`, `SkyConditions`, `Ephemeris`
- Endpoints: `/session/context`, `/session/conditions`

#### Step 2: "The Laboratory" (Camera Characterization)
**Astroalex needs to know the camera's physics for the current night**

- **User Action:** Take 2 Bias + 2 Flats and upload
- **Backend Processes:**
  - Calculate actual Read Noise (e-)
  - Calculate Gain (e-/ADU)
  - Calculate Full Well Capacity
  - Save "Night Sensor Profile"
- **Assistant Output Example:**
  > "Profile updated. Your camera is performing at 1.5e- read noise. System calibrated."

**Implementation:**
- Service: `CameraCharacterizer`
- Methods: `calculate_read_noise()`, `calculate_gain()`, `calculate_fwc()`
- Models: `SensorProfile`, `CameraCharacteristics`
- Database: Pre-populated camera specs (ZWO, QHY, ToupTek)

#### Step 3: Target Selection (The Strategist)
**Intelligent target recommendation based on conditions**

**Option A: Intelligent Suggestion**
- Cross-reference: FOV + Time Window + Location + Moon Phase
- Filter object database (NGC/IC/Messier)
- Discard: Objects too low, too small for pixel scale, too large for sensor
- **Output:** "Best Targets for Tonight" with encuadre simulation

**Option B: Manual Selection**
- User enters "Horsehead"
- Visual framing simulator validates feasibility

**Implementation:**
- Service: `TargetSelector`
- Database: `objects_catalog.db` (NGC/IC/Messier with coordinates, size, surface brightness)
- Methods: `suggest_targets()`, `validate_target()`, `simulate_fov()`
- Models: `CelestialTarget`, `FOVSimulation`

#### Step 4: "Smart Scout" (Real Field Analysis)
**Empirical validation using a test frame**

- **User Action:** Point at object, take one 30s test shot, upload
- **AI/Math Analysis:**
  - Light pollution measurement (electrons/second)
  - Dynamic range analysis (detect stellar saturation)
  - If >3% pixels saturated → Flag "HDR Required"
  - Calculate optimal exposure using: $SkyNoise > 10 \times ReadNoise^2$
- **Assistant Output Example:**
  > "Sky background: 45 e-/s. Detected saturation in Alnitak.
  > Optimal exposure: 180s for H-alpha, 120s for RGB.
  > HDR strategy required for star cores."

**Implementation:**
- Service: `SmartScout`
- Methods: `analyze_sky_background()`, `detect_saturation()`, `calculate_optimal_exposure()`
- Models: `ScoutAnalysis`, `ExposureRecommendation`

#### Step 5: Flight Plan Generator (The Mission)
**Generates precise acquisition instructions**

- **Logic:** Combines available time + optimal exposure + object structure
- **Output Example:**
  > **Optimized Plan for Horsehead Nebula:**
  > - **Lights:** 120 × 180s (H-alpha), 30 × 120s (R, G, B)
  > - **Calibration:** Darks: 20 × 180s + 20 × 120s, Flats: 20 per filter, Bias: 50
- **Export:**
  - ASIAIR format (.plan)
  - N.I.N.A. format (.json)
- **Automation:** Creates project directory structure automatically

**Implementation:**
- Service: `FlightPlanGenerator`
- Methods: `generate_plan()`, `export_asiair()`, `export_nina()`
- Models: `AcquisitionPlan`, `PlanExport`

---

### DAY PHASE (Steps 6-8): Processing & Delivery

#### Step 6: "El Mayordomo" (Ingestion & Organization)
**User dumps SD card into `00_ingest/`**

- Click "Organize & Process"
- Automatic: Read FITS metadata, move to proper directories
- Separate HDR exposures (short vs long) if required

**Implementation:** (Already implemented - Phase 1)
- Service: `IngestionService`
- Maintains existing functionality

#### Step 7: "Quality Control" (AI Filter)
**ML-based anomaly detection**

- **Technology:** Unsupervised ML (Isolation Forest)
- **Process:**
  - Analyze each image: FWHM, Eccentricity, Background, Star Count
  - Detect anomalies (clouds, wind, guiding failures)
  - Move rejected images to `_Rejected/`
- **Feedback:** Graph showing "12 images rejected (8 clouds, 4 guiding)"

**Implementation:**
- Service: `QualityControl`
- Methods: `extract_features()`, `train_isolation_forest()`, `detect_anomalies()`
- Models: `FrameQualityMetrics`, `RejectionReport`
- Library: `sklearn.ensemble.IsolationForest`

#### Step 8: Processing Pipeline (Autorun)
**The central engine**

Enhanced from existing implementation with:
1. **Master Generation** (existing)
2. **Calibration** (existing)
3. **Registration** (existing)
4. **Integration/Stacking** (existing) + **HDR Fusion** (new)
5. **Linear Prep & AI:**
   - Auto-Crop (dithering borders)
   - AI Background Extraction (U-Net neural network)
   - Linear Fit (equalize RGB brightness)
6. **Color & Luminance:**
   - LRGB or HaLRGB intelligent combination
   - PCC (Photometric Color Calibration via APASS/Vizier)
   - Blind deconvolution (sharpness restoration)
7. **Transform & Finish:**
   - Auto-Stretch (histogram-based)
   - Final noise reduction
   - Export JPG (social media) + TIFF 16-bit (fine editing)

**Implementation:**
- Extend existing `PipelineService`
- New services: `HDRFusion`, `AIBackgroundExtractor`, `PhotometricColorCalibrator`, `AutoStretcher`
- Models: Enhanced `ProcessingPipeline` with new steps

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
│               ├── Filter_X/
│               └── HDR/          # If HDR required (short + long exposures)
├── 02_processed_data/
│   ├── masters/
│   │   └── SESSION_NAME/
│   ├── science/
│   │   └── OBJECT_NAME/
│   │       ├── calibrated/
│   │       ├── registered/
│   │       ├── stacked/
│   │       └── final/           # Auto-stretched outputs
│   └── _Rejected/               # Failed quality control
├── 03_scripts/                  # Optional user scripts
└── session_plan.json            # Flight plan metadata
```

## Data Models

### New Models for V2.0

```python
# Environmental Context
class SkyConditions(BaseModel):
    seeing: float  # arcseconds
    clouds: int    # percentage
    jet_stream: float  # m/s
    transparency: Optional[int]

class Ephemeris(BaseModel):
    darkness_start: datetime
    darkness_end: datetime
    darkness_duration: timedelta
    moon_phase: float  # 0-1
    moon_illumination: int  # percentage

class ObservingSession(BaseModel):
    id: str
    date: datetime
    location: GeoLocation
    conditions: SkyConditions
    ephemeris: Ephemeris
    camera_profile: Optional[SensorProfile]
    target: Optional[CelestialTarget]
    plan: Optional[AcquisitionPlan]

# Camera Characterization
class SensorProfile(BaseModel):
    camera_model: str
    read_noise: float  # electrons
    gain: float  # e-/ADU
    full_well_capacity: int  # electrons
    measured_date: datetime
    temperature: Optional[float]

# Target Selection
class CelestialTarget(BaseModel):
    name: str
    catalog_id: str  # NGC, IC, M, etc.
    ra: float  # degrees
    dec: float  # degrees
    size: float  # arcminutes
    surface_brightness: float  # mag/arcsec²
    optimal_filters: List[str]

# Smart Scout
class ScoutAnalysis(BaseModel):
    sky_background: float  # e-/s
    saturation_detected: bool
    saturation_percentage: float
    hdr_required: bool
    optimal_exposure: Dict[str, int]  # {filter: seconds}
    snr_estimate: float

# Flight Plan
class AcquisitionPlan(BaseModel):
    target: CelestialTarget
    lights: Dict[str, PlanItem]  # {filter: PlanItem}
    darks: List[PlanItem]
    flats: List[PlanItem]
    bias: PlanItem
    total_time: timedelta
    export_formats: List[str]
```

## Development Guidelines

### Wizard UX Principles
- **Linear Flow:** User cannot skip steps (Step N requires Step N-1 completion)
- **Smart Defaults:** Pre-fill all calculable parameters
- **Clear Feedback:** Assistant speaks in natural language with concrete numbers
- **Progressive Disclosure:** Show only current step + next step preview
- **Escape Hatches:** Allow advanced users to override recommendations

### FITS File Handling
- Always preserve WCS (World Coordinate System) metadata through the pipeline
- Use Astropy for FITS I/O to ensure header integrity
- Store processing history in FITS headers (HISTORY keyword)

### API Integration
- **Weather APIs:** Implement with fallback (Meteoblue → OpenMeteo)
- **Catalog Queries:** Cache APASS/Vizier results (avoid repeated queries)
- **Rate Limiting:** Respect API limits with exponential backoff

### ML/AI Considerations
- **Isolation Forest:** Train per-session (not global model)
- **Feature Engineering:** Normalize FWHM by session median
- **Contamination Parameter:** Default 0.1 (10% expected anomalies)

### Testing Strategy
- **Unit Tests:** Each calculation (read noise, exposure, ephemerides)
- **Integration Tests:** Full wizard flow with mock data
- **E2E Tests:** Real FITS files through complete pipeline

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
python -m app.main   # Start from backend/ directory (not backend/app/)
```

### API Documentation
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Repository Structure

```
astroalex/
├── frontend/          # Next.js 15 + TypeScript frontend
│   ├── app/
│   │   ├── page.tsx           # Home (session list/create)
│   │   ├── session/
│   │   │   └── [id]/
│   │   │       ├── step1/     # Environmental context
│   │   │       ├── step2/     # Camera characterization
│   │   │       ├── step3/     # Target selection
│   │   │       ├── step4/     # Smart scout
│   │   │       ├── step5/     # Flight plan
│   │   │       ├── step6/     # Ingestion
│   │   │       ├── step7/     # Quality control
│   │   │       └── step8/     # Processing
│   ├── components/
│   │   ├── wizard/            # Wizard navigation components
│   │   ├── session/           # Session-specific components
│   │   └── shared/            # Reusable components
│   └── lib/
│       ├── api.ts             # API client
│       └── calculations.ts    # Client-side astronomy math
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── routers/
│   │   │   ├── session.py          # Session management
│   │   │   ├── environmental.py    # Weather + ephemerides
│   │   │   ├── characterization.py # Camera analysis
│   │   │   ├── targets.py          # Target selection
│   │   │   ├── scout.py            # Smart scout
│   │   │   ├── planner.py          # Flight plan generation
│   │   │   └── ...existing...
│   │   ├── services/
│   │   │   ├── environmental_service.py
│   │   │   ├── camera_characterizer.py
│   │   │   ├── target_selector.py
│   │   │   ├── smart_scout.py
│   │   │   ├── flight_planner.py
│   │   │   ├── quality_control.py
│   │   │   └── ...existing...
│   │   ├── models/
│   │   │   ├── session.py
│   │   │   ├── environmental.py
│   │   │   ├── camera.py
│   │   │   └── ...existing...
│   │   ├── data/
│   │   │   ├── objects_catalog.db  # NGC/IC/Messier database
│   │   │   └── cameras.json        # Pre-populated camera specs
│   │   └── ml/
│   │       └── quality_control.py  # Isolation Forest model
│   └── tests/
└── docs/
```

## Current Implementation Status

### ✅ COMPLETED (V1.0 Foundation)
- Phase 0: Project configuration
- Phase 1: Project management & ingestion
- Phase 2: Master calibration
- Phase 3: Processing pipeline (basic)
- Phase 4-5: Visualization & export (basic)
- Testing infrastructure

### ✅ COMPLETED (V2.0 Wizard - UI & Core Features)
- **Wizard UI framework** with step navigation and progress tracking
- **Session Management** with full CRUD operations
- **Equipment Profiles** management and activation
- **Step 1: Environmental Context**
  - Open-Meteo integration for real-time weather
  - Ephemeris calculation with Astropy
  - Location editing with geolocation
  - Auto-refresh on location change
  - Manual refresh button for conditions
  - Color-coded weather metrics
- **Step 2: Camera Characterization**
  - FITS upload and analysis
  - Read noise, gain, and FWC calculation
  - Optional skip with defaults
- **Step 3: Target Selection**
  - Equipment-based filtering (shows only compatible targets)
  - Intelligent recommendations with scoring algorithm
  - Filter compatibility checks
  - Manual search and selection
- **Session Cards** redesigned with full-width layout
- **Onboarding Flow** with storage and equipment setup

### 🚧 IN PROGRESS (V2.0 Wizard - Advanced Features)
- **Step 3 Enhancements:**
  - Expand object database beyond 6 mock objects to full NGC/IC/Messier catalog
  - Add visibility curve visualization (similar to ASIAir)
  - Implement FOV simulation with visual preview
- **Step 4:** Smart Scout implementation
- **Step 5:** Flight Plan Generator
- **Step 7:** ML Quality Control with Isolation Forest
- **Step 8:** Enhanced Processing Pipeline with HDR fusion

## Migration Strategy from V1 to V2

1. **Preserve existing functionality:** V1 routes remain available under `/v1/` prefix
2. **Session-based approach:** All V2 operations tied to `ObservingSession` entity
3. **Progressive enhancement:** Wizard can use existing calibration/processing services
4. **Data compatibility:** V1 projects can be imported into V2 sessions

## Important Notes for Future Development
- Each wizard step must save state (allow resume if user closes app)
- Assistant messages stored in session history for reproducibility
- All recommendations must show underlying calculation/data source
- Export all session data as JSON for external analysis
- Keep V1 API stable for backwards compatibility
