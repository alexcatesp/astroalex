# Astroalex

**Tu pipeline de procesamiento astrofotográfico, automatizado e inteligente.**

Astroalex es una aplicación de gestión de proyectos de astrofotografía que automatiza el flujo de trabajo desde la ingesta de datos hasta la imagen final procesada, con un enfoque en la reproducibilidad y la eficiencia.

## Características

### Módulos Implementados

- ✅ **Gestión de Proyectos**: Crea y organiza proyectos con estructura de directorios estandarizada
- ✅ **Ingesta Inteligente**: Organización automática de archivos basada en metadatos
- 🚧 **Masters de Calibración**: Creación de master darks, flats y bias con interfaz visual
- 🚧 **Pipeline de Procesamiento**: Calibración, registro y apilado con workflow modular
- 🚧 **Mosaicos y Color**: Ensamblaje de mosaicos y combinación LRGB/SHO
- 🚧 **Visualización**: Visor FITS con herramientas de stretch y exportación

### Stack Tecnológico

- **Frontend**: Next.js 15, TypeScript, Tailwind CSS
- **Backend**: Python, FastAPI
- **Procesamiento**: Astropy, CCDProc, Astroalign, Photutils, Reproject

## Quick Start

### Requisitos

- Node.js 20+
- Python 3.11+
- npm/yarn
- pip

### Instalación

1. **Clonar el repositorio**
```bash
git clone <repository-url>
cd astroalex
```

2. **Backend**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
cd app
python main.py
```

3. **Frontend**
```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

4. **Acceder a la aplicación**
- Frontend: http://localhost:3000
- API: http://localhost:8000
- Documentación API: http://localhost:8000/docs

## Estructura del Proyecto

```
astroalex/
├── frontend/        # Next.js application
├── backend/         # FastAPI backend
├── shared/          # Shared types and schemas
├── docs/            # Documentation
└── CLAUDE.md        # AI assistant guidance
```

## Filosofía

Astroalex no es una caja de herramientas, es un **gestor de proyectos**. Asume y se apoya en una estructura de directorios lógica para automatizar el 90% del trabajo tedioso, permitiendo al usuario centrarse en la toma de decisiones de calidad.

## Documentación

- [Guía de Desarrollo](docs/DEVELOPMENT.md)
- [Especificaciones](SPECS.md)
- [Guía para Claude Code](CLAUDE.md)

## Estructura de Directorios de Proyectos

Cada proyecto sigue esta estructura estandarizada:

```
PROJECT_NAME/
├── 00_ingest/                    # Drop zone
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
└── 03_scripts/                   # Optional
```

## Contribuir

Por favor lee la [Guía de Desarrollo](docs/DEVELOPMENT.md) para detalles sobre el proceso de desarrollo y cómo enviar pull requests.

## Licencia

[MIT License](LICENSE)

## Estado del Proyecto

🚧 **En desarrollo activo** - Fase 0 completada, implementando Fase 1 (Gestión de Proyectos + Ingesta)
