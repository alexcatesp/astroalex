# 🚀 Guía de Inicio Rápido - Astroalex

## Paso 1: Setup del Backend (Python)

### Abrir Terminal 1 - Backend

```bash
# Ir al directorio backend
cd D:\Development\astroalex\backend

# Crear entorno virtual (solo primera vez)
python -m venv venv

# Activar entorno virtual
venv\Scripts\activate

# Instalar dependencias (solo primera vez)
pip install -r requirements.txt

# Copiar configuración de entorno (solo primera vez)
copy .env.example .env

# Ejecutar servidor backend
cd app
python main.py
```

**El backend estará corriendo en:**
- API: http://localhost:8000
- Documentación Swagger: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## Paso 2: Setup del Frontend (Next.js)

### Abrir Terminal 2 - Frontend

```bash
# Ir al directorio frontend
cd D:\Development\astroalex\frontend

# Instalar dependencias (solo primera vez)
npm install

# Copiar configuración de entorno (solo primera vez)
copy .env.example .env.local

# Ejecutar servidor de desarrollo
npm run dev
```

**El frontend estará corriendo en:**
- Aplicación: http://localhost:3000

---

## Paso 3: Usar la Aplicación

### 1. Abrir el navegador
Ir a: **http://localhost:3000**

### 2. Crear tu primer proyecto
- Click en **"+ Nuevo Proyecto"**
- Nombre: "Mi Primer Proyecto"
- Descripción: "Prueba de Astroalex"
- Click **"Crear Proyecto"**

### 3. Explorar funcionalidades

**Dashboard Principal:**
- Ver lista de proyectos
- Crear, eliminar proyectos

**Dentro de un Proyecto:**
- Ver carpeta del proyecto
- Ir a **"Masters de Calibración"**

**Masters de Calibración:**
- Crear sesiones de calibración
- Escanear frames (si tienes archivos FITS)
- Crear master bias/dark/flat

---

## Verificar que Todo Funciona

### Backend
1. Abrir: http://localhost:8000/docs
2. Deberías ver la documentación Swagger con todos los endpoints
3. Probar endpoint: `GET /health` → Debería responder "healthy"

### Frontend
1. Abrir: http://localhost:3000
2. Deberías ver el dashboard de Astroalex
3. Crear un proyecto de prueba
4. Verificar que aparece en la lista

---

## Solución de Problemas Comunes

### Backend no inicia
```bash
# Verificar que Python está instalado
python --version

# Reinstalar dependencias
pip install -r requirements.txt --force-reinstall
```

### Frontend no inicia
```bash
# Limpiar caché de npm
npm cache clean --force

# Reinstalar
rm -rf node_modules
npm install
```

### Puerto ya en uso
```bash
# Cambiar puerto del backend en backend/app/main.py (línea 58)
# Cambiar puerto del frontend: npm run dev -- -p 3001
```

---

## Detener los Servidores

### Backend
En la terminal del backend: `Ctrl + C`

### Frontend
En la terminal del frontend: `Ctrl + C`

---

## Próximos Pasos

Una vez que la app esté corriendo:
1. ✅ Crear un proyecto
2. ✅ Explorar la interfaz
3. 📸 Si tienes archivos FITS, prueba la ingesta
4. 🔬 Explora la creación de masters
5. 📊 Revisa la API en /docs

¡Disfruta usando Astroalex! 🌟
