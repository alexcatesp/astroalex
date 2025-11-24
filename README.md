# Astroalex V2.0

**Tu Asistente Inteligente de Astrofotografía - De la Planificación a la Imagen Final**

Astroalex no es una caja de herramientas, es un **Asistente Activo** que te guía paso a paso desde antes de que se ponga el sol hasta la imagen procesada final. No busques herramientas en menús - la aplicación te dice qué hacer a continuación.

## Filosofía

> **PixInsight:** "Aquí tienes 500 martillos, construye tu casa."
> **Astroalex:** "Dime qué casa quieres, he analizado el terreno, he pedido los materiales exactos y aquí tienes las llaves."

Astroalex combina **IA, estadística y datos astronómicos** para darte certeza en cada paso del proceso.

## El Flujo Guiado (Wizard)

### Fase NOCHE (Pasos 1-5): Planificación & Adquisición

#### 1️⃣ Contexto y Medio Ambiente
Abres la app antes de la sesión y Astroalex te dice:
> "Buenas noches, Alex. Hoy tienes 5h 30m de oscuridad (23:00 - 04:30).
> Seeing mediocre (2.5"), mejor usar Binning 2x2 o evitar focales extremas.
> Luna al 80%, te recomiendo Banda Estrecha (H-alfa)."

**Tecnología:** APIs meteorológicas + cálculo de efemérides automático

#### 2️⃣ "El Laboratorio" - Caracterización de Cámara
Astroalex necesita conocer tu cámara HOY:
- Toma 2 Bias + 2 Flats ahora mismo
- Cálculo automático de **Read Noise, Gain y Full Well Capacity**
- Perfil guardado para optimizar exposiciones

#### 3️⃣ Selección de Objetivo - El Estratega
**Opción A:** Astroalex te sugiere objetivos basándose en:
- Tu FOV (campo de visión)
- Tu ventana de tiempo
- Ubicación y altura del objeto
- Fase lunar

**Opción B:** Escribes "Horsehead" y Astroalex simula el encuadre y valida viabilidad

#### 4️⃣ "Smart Scout" - Análisis de Campo Real
- Toma UNA foto de prueba (30s)
- Astroalex analiza:
  - Contaminación lumínica real
  - Saturación estelar (detecta si necesitas HDR)
  - **Calcula exposición óptima** para cada filtro

> "Sky background: 45 e-/s. Detectada saturación en Alnitak.
> Exposición óptima: 180s (H-alpha), 120s (RGB).
> Estrategia HDR necesaria para núcleos estelares."

#### 5️⃣ Plan de Vuelo - La Misión
Astroalex genera el plan completo:
```
PLAN OPTIMIZADO PARA HORSEHEAD NEBULA
───────────────────────────────────────
Luces:
  • 120 × 180s (H-alpha)
  • 30 × 120s (R, G, B)

Calibración:
  • Darks: 20 × 180s + 20 × 120s
  • Flats: 20 por filtro
  • Bias: 50

Exportar: [ASIAIR .plan] [N.I.N.A .json]
```

**Bonus:** Crea automáticamente la estructura de carpetas del proyecto

---

### Fase DÍA (Pasos 6-8): Procesado & Entrega

#### 6️⃣ "El Mayordomo" - Ingesta Inteligente
- Vuelcas la SD en `00_ingest/`
- Click en "Organizar"
- Astroalex lee metadatos y organiza TODO automáticamente
- Separa exposiciones HDR si fue necesario

#### 7️⃣ Quality Control - Filtro IA
**Machine Learning detecta anomalías:**
- Analiza FWHM, excentricidad, fondo, nº estrellas
- Detecta nubes, viento, fallos de guiado
- Mueve imágenes malas a `_Rejected/`
- Te muestra: "12 imágenes rechazadas (8 nubes, 4 guiado)"

**Tecnología:** Isolation Forest (scikit-learn)

#### 8️⃣ Pipeline de Procesado - Autorun
El motor central ejecuta automáticamente:

1. **Generación de Masters** (Bias, Darks, Flats)
2. **Calibración** (aplica masters a Lights)
3. **Registro** (alinea todas las imágenes)
4. **Integración**
   - Apila por filtro
   - Fusión HDR automática si se requirió
5. **Preparación Lineal + IA**
   - Auto-Crop de bordes (dithering)
   - Extracción de fondo con red neuronal (U-Net)
   - Linear Fit (iguala brillos RGB)
6. **Color & Luminancia**
   - Combinación LRGB/HaLRGB inteligente
   - **PCC (Photometric Color Calibration)** - balance de blancos real vía APASS/Vizier
   - Deconvolución ciega (restaura nitidez)
7. **Acabado**
   - Auto-Stretch basado en histograma
   - Reducción de ruido final
   - Export: **JPG** (redes sociales) + **TIFF 16-bit** (edición fina)

---

## Stack Tecnológico

### Frontend
- **Next.js 15** + TypeScript + Tailwind CSS
- Interfaz de wizard paso a paso
- Visualización FITS integrada

### Backend
- **Python** + **FastAPI**
- **Astronomy:** Astropy, CCDProc, Astroalign, Photutils, Reproject, Astroquery
- **ML/IA:** scikit-learn (Isolation Forest), U-Net (background extraction)
- **APIs externas:** Meteoblue/OpenMeteo, APASS, Vizier

---

## Quick Start

### Requisitos
- Node.js 20+
- Python 3.11+
- 16GB RAM recomendado

### Instalación

1. **Clonar repositorio**
```bash
git clone <repository-url>
cd astroalex
```

2. **Backend**
```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux/Mac
pip install -r requirements.txt
```

3. **Frontend**
```bash
cd frontend
npm install
```

4. **Iniciar Aplicación**

Consulta **START.md** para guía detallada de inicio rápido.

```bash
# Terminal 1 - Backend
cd backend
venv\Scripts\activate
python -m app.main

# Terminal 2 - Frontend
cd frontend
npm run dev
```

5. **Acceder**
- 🌐 Frontend: http://localhost:3000
- 🔧 API: http://localhost:8000
- 📚 Docs API: http://localhost:8000/docs

---

## Estructura de Proyectos

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
│               ├── Filter_X/
│               └── HDR/          # Si se requirió HDR
├── 02_processed_data/
│   ├── masters/
│   │   └── SESSION_NAME/
│   ├── science/
│   │   └── OBJECT_NAME/
│   │       ├── calibrated/
│   │       ├── registered/
│   │       ├── stacked/
│   │       └── final/           # Outputs auto-stretched
│   └── _Rejected/               # Fallos quality control
├── 03_scripts/                  # Opcional
└── session_plan.json            # Flight plan metadata
```

---

## Características Clave

### 🎯 Asistente Inteligente
- Te dice qué hacer en cada momento
- Cálculos basados en física real (no estimaciones)
- Recomendaciones personalizadas según condiciones

### 🌤️ Contexto Ambiental
- Seeing, nubes, jet stream en tiempo real
- Ventanas de oscuridad astronómica
- Fase lunar y recomendaciones de filtros

### 📸 Optimización de Adquisición
- Caracterización de cámara in-situ
- Cálculo de exposición óptima por filtro
- Detección automática de necesidad HDR
- Generación de planes exportables (ASIAIR, N.I.N.A.)

### 🤖 IA & Machine Learning
- Detección de anomalías (nubes, guiado, viento)
- Extracción de fondo con redes neuronales
- Calibración fotométrica automática

### 🔬 Procesado Científico
- Librerías validadas (Astropy, CCDProc)
- Preservación de WCS en todo el pipeline
- Reproducibilidad total con metadata

### 📊 Automatización Completa
- Del raw al JPG sin intervención manual
- Solo tomas decisiones de calidad, no tedioso trabajo

---

## Documentación

- 📖 [Guía de Inicio Rápido](START.md)
- 📋 [Especificaciones V2.0](SPECS.md)
- 🤖 [Guía para Claude Code](CLAUDE.md)
- 🛠️ [Guía de Desarrollo](docs/DEVELOPMENT.md)

---

## Estado del Proyecto

### ✅ V1.0 Foundation (Completado)
- Gestión de proyectos
- Ingesta inteligente
- Masters de calibración
- Pipeline básico de procesado
- Visualización y export

### ✅ V2.0 Wizard - UI & Core Features (Completado)
- ✅ Framework de wizard UI con navegación paso a paso
- ✅ Gestión completa de sesiones y perfiles de equipo
- ✅ **Step 1:** Contexto ambiental con Open-Meteo + efemérides
  - Auto-refresh al cambiar ubicación
  - Botón de refresco manual para condiciones
  - Métricas meteorológicas con codificación de colores
- ✅ **Step 2:** Caracterización de cámara (Read Noise, Gain, FWC)
- ✅ **Step 3:** Selección de objetivos con filtrado inteligente
  - Filtrado basado en equipamiento disponible
  - Sistema de recomendaciones con scoring
  - Compatibilidad con filtros del usuario
- ✅ Cards de sesión rediseñadas con layout completo
- ✅ Flujo de onboarding con configuración de almacenamiento

### 🚧 V2.0 Wizard - Advanced Features (En Progreso)
Próximos pasos:
1. Expansión de base de datos de objetos celestes (NGC/IC/Messier completo)
2. Curva de visibilidad para objetivos (estilo ASIAir)
3. Simulación FOV con vista previa visual
4. Smart Scout (análisis de frame de prueba)
5. Generador de Flight Plan con export ASIAIR/N.I.N.A
6. Quality Control con ML (Isolation Forest)
7. Pipeline mejorado (HDR fusion, PCC, Auto-Stretch)

---

## Contribuir

Lee la [Guía de Desarrollo](docs/DEVELOPMENT.md) para:
- Arquitectura del código
- Convenciones de commits
- Testing strategy
- Proceso de pull requests

---

## Licencia

[MIT License](LICENSE)

---

## Créditos

Astroalex utiliza y agradece a:
- **Astropy** - Core astronomy functionality
- **CCDProc** - Scientific calibration
- **Astroalign** - Star-based registration
- **Photutils** - Photometry and quality metrics
- **scikit-learn** - Machine learning
- **FastAPI** - High-performance API framework
- **Next.js** - Modern React framework

---

**¿Listo para la sesión de hoy?** 🌟

Abre Astroalex, deja que analice las condiciones y te guíe hacia la mejor imagen posible.
