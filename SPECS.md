Aquí tienes el **Documento de Especificaciones Funcionales (V2.0)** para **Astroalex**.

Este documento integra toda la lógica técnica que hemos desarrollado (IA, estadística, gestión de archivos, astrofísica) pero reestructura la aplicación bajo un nuevo paradigma: **El Flujo Guiado (Wizard)**.

Astroalex deja de ser una "caja de herramientas" pasiva y se convierte en un **Asistente Activo** que lleva al usuario de la mano desde antes de que se ponga el sol hasta la imagen final procesada.

---

# ASTROALEX: Especificaciones Funcionales (V2.0)
**Visión:** Asistente integral de astrofotografía guiado por datos. Planificación, Adquisición, Gestión y Procesado en un flujo único.

---

## I. EL FLUJO DE USUARIO GUIADO (The User Journey)

La aplicación se estructura en una línea de tiempo cronológica. El usuario no busca herramientas en menús; la aplicación le presenta el paso siguiente lógico.

### PASO 1: Contexto y Medio Ambiente (Al iniciar la app)
*El usuario abre Astroalex antes de empezar la sesión.*

*   **Entrada:** Geolocalización automática y Hora actual.
*   **Procesos de Fondo:**
    *   Consulta a API Meteorológica (Meteoblue/OpenMeteo) para Seeing, Jet Stream y Nubes.
    *   Cálculo de Efemérides (Ventana de oscuridad astronómica, Fase Lunar).
*   **Interacción (El Asistente Dice):**
    > "Buenas noches, Alex. Hoy tienes una ventana de oscuridad de **5h 30m** (23:00 - 04:30).
    > El Seeing es mediocre (2.5"), por lo que te recomiendo no usar focales extremas o hacer Binning 2x2.
    > La Luna está al 80%, sugiero trabajar en Banda Estrecha (H-alfa)."

### PASO 2: "El Laboratorio" (Calibración del Equipo)
*Astroalex necesita conocer la física de la cámara para la noche actual.*

*   **Interacción:**
    > "Para optimizar tus tiempos de exposición, necesito caracterizar tu cámara hoy. Por favor, toma ahora mismo **2 Bias** (tapada, tiempo min) y **2 Flats** (a la mitad del histograma) y arrástralos aquí."
*   **Procesos Internos:**
    *   Cálculo de **Ruido de Lectura (Read Noise)** real actual.
    *   Cálculo de **Ganancia (e-/ADU)** y **Full Well Capacity**.
    *   Guardado del "Perfil de Sensor de la Noche".
*   **Salida:**
    > "Perfil actualizado. Tu cámara está rindiendo a **1.5e-** de ruido. El sistema está calibrado."

### PASO 3: Selección de Objetivo (El Estratega)
*El usuario decide qué fotografiar con ayuda inteligente.*

*   **Opción A: Sugerencia Inteligente**
    *   Astroalex cruza: Tu FOV (Campo de visión) + Tu Ventana de Tiempo (Step 1) + Tu Ubicación + Fase Lunar.
    *   **Algoritmo:** Filtra la base de datos de objetos (NGC/IC/Messier). Descarta objetos muy bajos, muy pequeños para tu pixel scale, o muy grandes para tu sensor.
    *   **Salida:** Lista de "Mejores Objetivos para Hoy" (Ej: "Nebulosa Roseta - Encaja perfecto en tu sensor, altura óptima a las 01:00").
*   **Opción B: Selección Manual**
    *   El usuario escribe "Horsehead". Astroalex muestra el encuadre en un simulador visual y confirma si es viable.

### PASO 4: "Smart Scout" (Análisis de Campo Real)
*Validación empírica de la exposición.*

*   **Interacción:**
    > "Apunta al objeto y toma una sola foto de prueba (ej. 30s, filtro L o sin filtro). Arrástrala aquí."
*   **Análisis IA/Matemático:**
    *   **Análisis de Cielo:** Mide la contaminación lumínica en electrones/segundo.
    *   **Análisis de Rango Dinámico:** Detecta saturación estelar. Si el núcleo del objeto quema más del 3% de píxeles, activa el flag **"HDR Necesario"**.
    *   **Cálculo de Exposición:** Aplica la fórmula de exposición óptima ($SkyNoise > 10 \times ReadNoise^2$) usando los datos del Paso 2.

### PASO 5: Generación del Plan de Vuelo (La Misión)
*Astroalex redacta las instrucciones precisas.*

*   **Lógica:** Combina el tiempo disponible (Paso 1) con la exposición óptima (Paso 4) y la estructura del objeto (Paso 3).
*   **Salida (El Plan):**
    > **Plan Optimizado para Horsehead Nebula:**
    > *   **Luces (Lights):**
    >     *   120 x 180s (H-alpha) - *Limitado por saturación de Alnitak.*
    >     *   30 x 120s (R, G, B)
    > *   **Calibración Necesaria:**
    >     *   Darks: 20 x 180s, 20 x 120s.
    >     *   Flats: 20 por filtro.
    >     *   Bias: 50.
*   **Acción:** Botones "Exportar a ASIAIR (.plan)" y "Exportar a N.I.N.A.".
*   **Preparación de Carpetas:** Astroalex crea automáticamente la estructura de directorios (`00_Ingest`, `01_Raw`, etc.) en el disco duro del usuario.

---
*(Aquí termina la fase de "Noche". Al día siguiente, comienza la fase de "Día".)*
---

### PASO 6: El "Mayordomo" (Ingesta y Organización)
*El usuario vuelca la tarjeta SD en la carpeta `00_Ingest`.*

*   **Acción:** Clic en "Organizar y Procesar".
*   **Proceso Automático:**
    *   El script lee los metadatos FITS.
    *   Mueve cada archivo a su carpeta correspondiente (`01_Raw/Science/Object/Filter...`).
    *   Separa las tomas HDR (cortas vs largas) si el plan lo requería.

### PASO 7: "Quality Control" (El Filtro IA)
*Limpieza de datos antes de cocinar.*

*   **Tecnología:** Machine Learning No Supervisado (Isolation Forest).
*   **Proceso:**
    *   Analiza estadísticas de cada imagen (FWHM, Excentricidad, Fondo, Nº Estrellas).
    *   Detecta anomalías (nubes, golpes de viento, fallos de guiado).
    *   Mueve las imágenes rechazadas a una carpeta `_Rejected`.
*   **Feedback:** Muestra un gráfico: "Se han rechazado 12 imágenes (8 por nubes, 4 por guiado)".

### PASO 8: El Pipeline de Procesado (Autorun)
*El motor central se pone en marcha.*

1.  **Generación de Masters:** Crea Bias, Darks y Flats maestros.
2.  **Calibración:** Aplica los masters a los Lights aceptados.
3.  **Registro:** Alinea todas las imágenes (usando *astroalign*).
4.  **Integración (Stacking):**
    *   Apila por filtro.
    *   Si hay HDR, fusiona automáticamente las tomas cortas y largas en este punto.
    *   Salida: Masters Lineales L, R, G, B (y H-alpha).
5.  **Linear Prep & IA:**
    *   **Auto-Crop:** Recorta bordes de dithering.
    *   **AI Background Extraction:** Red neuronal (U-Net) detecta gradientes y los elimina.
    *   **Linear Fit:** Iguala brillos RGB.
6.  **Color & Luminancia:**
    *   Combinación LRGB (o HaLRGB inteligente).
    *   **PCC (Photometric Color Calibration):** Conexión a base de datos APASS/Vizier para balance de blancos real.
    *   Deconvolución ciega (restauración de nitidez).
7.  **Transformación y Acabado:**
    *   Estirado automático (Auto-Stretch basado en histograma).
    *   Reducción de ruido final.
    *   Generación de JPG para redes sociales y TIFF 16-bit para edición fina manual.

---

## II. ARQUITECTURA TÉCNICA

### Stack Tecnológico
*   **Interfaz (Frontend):** Next.js 15+ frontend with TypeScript and Tailwind CSS
*   **Motor (Backend):** FastAPI backend with Python.
*   **Librerías Clave:**
    *   `astropy` (Núcleo astronómico).
    *   `ccdproc` (Calibración y procesado).
    *   `photutils` (Estadística y fotometría).
    *   `scikit-learn` (ML para Quality Control).
    *   `reproject` / `montage-wrapper` (Mosaicos).
    *   `astroquery` (Conexión a Meteoblue, Vizier, Simbad).

### Bases de Datos Internas
1.  **DB Sensores:** Lista pre-poblada de cámaras comunes (ZWO, QHY, ToupTek) con specs base (para usar si el usuario salta el Paso 2).
2.  **DB Objetos:** Catálogo simplificado NGC/IC/Messier con coordenadas, tamaño angular y magnitud superficial (para el Paso 3).

### Requisitos de Hardware
*   **CPU:** Multicore (para apilado paralelo).
*   **RAM:** 16GB mínimo recomendado.
*   **GPU:** Opcional (aceleraría la extracción de fondo IA y Starnet si se integra, pero el ML estadístico corre en CPU).

---

## III. DIFERENCIACIÓN DE MERCADO

Astroalex no compite con PixInsight en cantidad de herramientas matemáticas manuales. Compite ofreciendo **Certeza y Flujo**.

*   **PixInsight:** "Aquí tienes 500 martillos, construye tu casa."
*   **Astroalex:** "Dime qué casa quieres, he analizado el terreno, he pedido los materiales exactos y aquí tienes las llaves."