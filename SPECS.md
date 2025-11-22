### Especificaciones de la Aplicación: **Astroalex**

**Tagline:** *Tu pipeline de procesamiento astrofotográfico, automatizado e inteligente. Del caos de datos a la imagen final, con un flujo de trabajo reproducible.*

**Filosofía Central:** Astroalex no es una caja de herramientas, es un gestor de proyectos. Asume y se apoya en una estructura de directorios lógica para automatizar el 90% del trabajo tedioso, permitiendo al usuario centrarse en la toma de decisiones de calidad. El backend está impulsado por Python y las bibliotecas estándar de la astronomía (Astropy, CCDProc, Astroalign, etc.), garantizando resultados científicamente válidos.

---

#### **1. Gestión de Proyectos (El Núcleo)**

*   **Creación de Nuevo Proyecto:** Al crear un proyecto (ej. "Mosaico de Orión"), la aplicación genera automáticamente la estructura de directorios completa que definimos:
    *   `00_ingest/`
    *   `01_raw_data/ (calibration/, science/)`
    *   `02_processed_data/ (masters/, science/)`
    *   `03_scripts/` (Opcional, para usuarios avanzados)
*   **Panel de Control del Proyecto:** Una vista principal que muestra el estado del proyecto:
    *   Resumen de datos crudos (Nº de Lights por filtro, Darks, etc.).
    *   Estado de los Masters de Calibración (creado / no creado).
    *   Progreso del apilado por filtro y por panel.
    *   Vista previa de las imágenes finales generadas.

#### **2. Módulo 1: Ingesta y Organización Inteligente (El "Mayordomo")**

*   **Zona de Arrastrar y Soltar:** Una ventana que representa la carpeta `00_ingest`. El usuario simplemente arrastra los archivos del ASIAIR aquí.
*   **Análisis Automático:** La aplicación lee los nombres de archivo y extrae metadatos clave: Tipo de Imagen (Light, Dark, Bias, Flat), Objeto, Filtro, Tiempo de Exposición, Ganancia y Fecha.
*   **Clasificación con un Clic:** Un botón "Organizar Archivos" que ejecuta la lógica de nuestro script "mayordomo". Mueve cada archivo a su ubicación correcta dentro de `01_raw_data`, creando las subcarpetas necesarias (ej. `M31_Andromeda_Galaxy/2025-10-26/Filter_L/`).
*   **Manejo de Sesiones:** El usuario define una "Sesión de Calibración" (ej. "2025-10-26_Newton200_ASI533") para que todos los Darks y Flats de esa sesión se agrupen correctamente.

#### **3. Módulo 2: Creación de Masters de Calibración**

*   **Interfaz Visual:** Una sección dedicada a cada tipo de master (Bias, Darks, Flats).
*   **Carga Automática:** La aplicación sabe dónde buscar los archivos crudos (ej. en `01_raw_data/calibration/SESSION_NAME/darks/`).
*   **Inspección y Rechazo:** Muestra miniaturas de todas las tomas. El usuario puede revisarlas rápidamente (usando "Blink") y desmarcar las que tengan artefactos (ej. trazas de satélite en un Dark).
*   **Parámetros de Combinación:** Menús desplegables simples para elegir el método de combinación (Average, Median) y el de rechazo (Sigma Clipping, Min/Max). Los valores por defecto serán los más recomendados.
*   **Ejecución:** Un botón "Crear Master" que ejecuta el proceso y guarda el archivo final en la carpeta `02_processed_data/masters/SESSION_NAME/` con un nombre estandarizado (ej. `master_dark_300s_gain100.fits`).

#### **4. Módulo 3: Pipeline de Procesamiento (El Corazón de la App)**

Esta es una interfaz visual, modular, donde el usuario define el flujo de trabajo para un objeto.

*   **Selección de Datos:** El usuario selecciona el objeto a procesar (ej. "M31") y los filtros a incluir. Si es un mosaico, selecciona los paneles.
*   **Cadena de Procesos:** Una serie de bloques que representan cada paso:
    1.  **Calibración:** El usuario arrastra los Masters de Calibración correctos a este bloque. La app sugiere los correctos basándose en la fecha y los metadatos.
    2.  **Análisis de Calidad:** (Opcional) Un bloque que mide FWHM (nitidez) y excentricidad de las estrellas en las tomas calibradas, permitiendo al usuario descartar las que estén por debajo de un umbral de calidad.
    3.  **Registro (Alineación):** Un bloque que alinea todas las imágenes a una de referencia. Parámetros simples (ej. "Usar Astroalign").
    4.  **Apilado (Integración):** El bloque final. El usuario elige el método de combinación y rechazo, igual que en los masters.
*   **Ejecución del Pipeline:** Un gran botón "Ejecutar" que procesa todo el lote. Los resultados intermedios (calibrados, registrados) se guardan en sus respectivas carpetas dentro de `02_processed_data/science/OBJECT_NAME/`. El apilado final se guarda en `stacked/`.

#### **5. Módulo 4: Ensamblaje de Mosaicos y Combinación de Color**

*   **Ensamblaje de Mosaico:** Una herramienta que toma los apilados finales de cada panel (ej. `Panel1_L.fits`, `Panel2_L.fits`) y los une.
    *   **Detección Automática:** La app lee los WCS de los archivos FITS para saber cómo encajan.
    *   **Parámetros:** Opciones para la igualación de fondo y el método de proyección.
*   **Combinación de Color:**
    *   **LRGB:** Ventana con 4 ranuras (L, R, G, B) donde el usuario arrastra sus imágenes apiladas. Controles deslizantes para el balance de color y la saturación de luminancia.
    *   **HaLRGB / SHO:** Mapeo de canales flexible. El usuario puede asignar cualquier imagen a cualquier canal (ej. Hα a Rojo, SII a Verde, etc.). Incluye una herramienta "PixelMath" simplificada para mezclas avanzadas (ej. `R = 0.8*Ha + 0.2*R`).

#### **6. Módulo 5: Visualización y Herramientas Finales**

*   **Visor de FITS:** Un visor integrado de alto rango dinámico.
*   **Estiramiento de Histograma No Destructivo:** Herramienta visual para aplicar estiramientos (Asinh, Log, Linear) y ver el resultado en tiempo real. La transformación se guarda como una "receta" y no modifica el archivo lineal subyacente.
*   **Extracción de Fondo:** Herramienta que permite seleccionar puntos del fondo o usar un método automático (ABE/DBE) para eliminar gradientes.
*   **Exportación:** Exporta la imagen final (lineal o estirada) a formatos como FITS, TIFF (16-bit) o JPG para compartir.

---
**Stack Tecnológico:**
*   **Backend:** Python
*   **Librerías Principales:** Astropy, CCDProc, Astroalign, Photutils, Reproject, NumPy.
*   **Interfaz Gráfica:** PyQt / PySide para una aplicación de escritorio nativa, o un framework como Electron para una interfaz basada en tecnologías web.

Esta aplicación sería un "game-changer" porque no compite en tener mil algoritmos, sino en ofrecer un **flujo de trabajo increíblemente eficiente, lógico y reproducible** que guía al usuario desde el caos inicial hasta un resultado de alta calidad.