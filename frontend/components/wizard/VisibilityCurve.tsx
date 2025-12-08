'use client';

import { useState, useEffect } from 'react';
import { CelestialTarget } from '@/lib/types';

interface VisibilityPoint {
  time: string;
  altitude: number;
  azimuth: number;
  airmass: number;
}

interface TwilightPeriod {
  threshold: number;
  times: [string, string];
}

interface DarknessPeriods {
  civil_twilight: TwilightPeriod;
  nautical_twilight: TwilightPeriod;
  astronomical_twilight: TwilightPeriod;
  darkness_window: {
    start: string;
    end: string;
    duration_hours: number;
  };
}

interface OptimalWindow {
  start: string | null;
  end: string | null;
  duration_hours: number;
  max_altitude: number;
  max_altitude_time: string;
}

interface MoonInfo {
  phase: number;
  illumination: number;
  altitude: number;
  azimuth: number;
}

interface VisibilityData {
  target: CelestialTarget;
  visibility_curve: VisibilityPoint[];
  darkness_periods: DarknessPeriods;
  optimal_window: OptimalWindow;
  moon: MoonInfo;
}

interface Props {
  sessionId: string;
  targetCatalogId: string;
}

export default function VisibilityCurve({ sessionId, targetCatalogId }: Props) {
  const [data, setData] = useState<VisibilityData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [hoverData, setHoverData] = useState<{ x: number; time: string; altitude: number } | null>(null);

  useEffect(() => {
    const fetchVisibility = async () => {
      try {
        setLoading(true);
        const response = await fetch(
          `http://localhost:8000/sessions/${sessionId}/targets/${targetCatalogId}/visibility`
        );

        if (!response.ok) {
          throw new Error('Failed to fetch visibility data');
        }

        const visData = await response.json();
        setData(visData);
        setError(null);
      } catch (err) {
        console.error('Error fetching visibility:', err);
        setError('No se pudo cargar la curva de visibilidad');
      } finally {
        setLoading(false);
      }
    };

    fetchVisibility();
  }, [sessionId, targetCatalogId]);

  if (loading) {
    return (
      <div className="w-full bg-slate-800/50 rounded-lg p-6 animate-pulse">
        <div className="h-6 bg-slate-700 rounded w-1/3 mb-4"></div>
        <div className="h-48 bg-slate-700 rounded"></div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="w-full bg-red-900/20 border border-red-800 rounded-lg p-4">
        <p className="text-red-300 text-sm">{error || 'Error desconocido'}</p>
      </div>
    );
  }

  // Parse times for chart
  const parseTime = (timeStr: string) => {
    const date = new Date(timeStr);
    return date.getHours() + date.getMinutes() / 60;
  };

  // Chart dimensions
  const width = 800;
  const height = 300;
  const padding = { top: 20, right: 80, bottom: 50, left: 60 };
  const chartWidth = width - padding.left - padding.right;
  const chartHeight = height - padding.top - padding.bottom;

  // Get time range (use full night from civil twilight for better context)
  const sunsetTime = parseTime(data.darkness_periods.civil_twilight.times[0]);
  const sunriseTime = parseTime(data.darkness_periods.civil_twilight.times[1]);

  // Calculate time range accounting for midnight crossing
  let timeRange: number;
  if (sunriseTime < sunsetTime) {
    // Crosses midnight
    timeRange = (24 - sunsetTime) + sunriseTime;
  } else {
    timeRange = sunriseTime - sunsetTime;
  }

  // Altitude range (0-90 degrees)
  const altitudeMin = 0;
  const altitudeMax = 90;

  // Convert data points to chart coordinates, filtering to visible times
  const points = data.visibility_curve
    .map((point) => {
      let time = parseTime(point.time);

      // Adjust time if it crosses midnight
      if (sunriseTime < sunsetTime && time < 12) {
        time += 24;
      }

      // Calculate x position
      const x = padding.left + ((time - sunsetTime) / timeRange) * chartWidth;
      const y = padding.top + chartHeight - ((point.altitude - altitudeMin) / (altitudeMax - altitudeMin)) * chartHeight;

      return { x, y, time: time, altitude: point.altitude, ...point };
    })
    // Filter to only show points within the chart range
    .filter((p) => p.x >= padding.left && p.x <= padding.left + chartWidth);

  // Create path for altitude curve
  const pathData = points.map((p, i) =>
    `${i === 0 ? 'M' : 'L'} ${p.x},${p.y}`
  ).join(' ');

  // Darkness periods shading (times[0] = end of twilight, times[1] = start of twilight)
  const astroStart = parseTime(data.darkness_periods.astronomical_twilight.times[0]);
  const astroEnd = parseTime(data.darkness_periods.astronomical_twilight.times[1]);

  let astroStartAdj = astroStart;
  let astroEndAdj = astroEnd;

  if (sunriseTime < sunsetTime) {
    if (astroStartAdj < 12) astroStartAdj += 24;
    if (astroEndAdj < 12) astroEndAdj += 24;
  }

  const astroX1 = padding.left + ((astroStartAdj - sunsetTime) / timeRange) * chartWidth;
  const astroX2 = padding.left + ((astroEndAdj - sunsetTime) / timeRange) * chartWidth;

  // Format time for display
  const formatTime = (timeStr: string) => {
    const date = new Date(timeStr);
    return date.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' });
  };

  // Handle mouse move over chart
  const handleMouseMove = (e: React.MouseEvent<SVGSVGElement>) => {
    const svg = e.currentTarget;
    const rect = svg.getBoundingClientRect();
    const mouseX = ((e.clientX - rect.left) / rect.width) * width;

    // Check if mouse is within chart area
    if (mouseX < padding.left || mouseX > padding.left + chartWidth) {
      setHoverData(null);
      return;
    }

    // Find closest point
    let closestPoint = points[0];
    let minDistance = Math.abs(points[0].x - mouseX);

    for (const point of points) {
      const distance = Math.abs(point.x - mouseX);
      if (distance < minDistance) {
        minDistance = distance;
        closestPoint = point;
      }
    }

    setHoverData({
      x: closestPoint.x,
      time: closestPoint.time,
      altitude: closestPoint.altitude
    });
  };

  const handleMouseLeave = () => {
    setHoverData(null);
  };

  return (
    <div className="w-full bg-slate-800/50 rounded-lg p-6 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-white">
            Curva de Visibilidad - {data.target.name}
          </h3>
          <p className="text-sm text-slate-400">
            {data.target.catalog_id} • {data.target.object_type}
          </p>
        </div>

        {data.optimal_window.start && (
          <div className="text-right">
            <p className="text-xs text-emerald-400 font-medium">Ventana Óptima</p>
            <p className="text-sm text-white">
              {formatTime(data.optimal_window.start)} - {formatTime(data.optimal_window.end!)}
            </p>
            <p className="text-xs text-slate-400">
              {data.optimal_window.duration_hours.toFixed(1)}h •
              Alt. máx: {data.optimal_window.max_altitude.toFixed(0)}°
            </p>
          </div>
        )}
      </div>

      {/* Chart */}
      <div className="relative w-full overflow-x-auto">
        <svg
          viewBox={`0 0 ${width} ${height}`}
          className="w-full h-auto"
          style={{ maxWidth: '100%', height: 'auto', cursor: 'crosshair' }}
          onMouseMove={handleMouseMove}
          onMouseLeave={handleMouseLeave}
        >
          {/* Background grid */}
          <defs>
            <pattern id="grid" width="40" height="30" patternUnits="userSpaceOnUse">
              <path
                d="M 40 0 L 0 0 0 30"
                fill="none"
                stroke="rgb(71, 85, 105)"
                strokeWidth="0.5"
                opacity="0.3"
              />
            </pattern>
          </defs>
          <rect
            x={padding.left}
            y={padding.top}
            width={chartWidth}
            height={chartHeight}
            fill="url(#grid)"
          />

          {/* Astronomical darkness shading */}
          {astroX1 < width && astroX2 > padding.left && (
            <rect
              x={Math.max(astroX1, padding.left)}
              y={padding.top}
              width={Math.min(astroX2, padding.left + chartWidth) - Math.max(astroX1, padding.left)}
              height={chartHeight}
              fill="rgb(30, 41, 59)"
              opacity="0.4"
            />
          )}

          {/* 20° minimum altitude line (red dashed) */}
          <line
            x1={padding.left}
            y1={padding.top + chartHeight - (20 / altitudeMax) * chartHeight}
            x2={padding.left + chartWidth}
            y2={padding.top + chartHeight - (20 / altitudeMax) * chartHeight}
            stroke="rgb(239, 68, 68)"
            strokeWidth="1"
            strokeDasharray="4,4"
            opacity="0.5"
          />

          {/* Altitude curve */}
          <path
            d={pathData}
            fill="none"
            stroke="rgb(96, 165, 250)"
            strokeWidth="2.5"
          />

          {/* Fill under curve */}
          <path
            d={`${pathData} L ${points[points.length - 1].x},${padding.top + chartHeight} L ${points[0].x},${padding.top + chartHeight} Z`}
            fill="rgb(96, 165, 250)"
            opacity="0.15"
          />

          {/* Y-axis labels (altitude) */}
          {[0, 20, 40, 60, 90].map((alt) => (
            <g key={alt}>
              <text
                x={padding.left - 10}
                y={padding.top + chartHeight - (alt / altitudeMax) * chartHeight + 4}
                textAnchor="end"
                fontSize="11"
                fill="rgb(148, 163, 184)"
              >
                {alt}°
              </text>
            </g>
          ))}

          {/* X-axis labels (time) */}
          {Array.from({ length: 7 }, (_, i) => {
            const time = sunsetTime + (i * timeRange) / 6;
            const hour = Math.floor(time) % 24;
            const x = padding.left + (i / 6) * chartWidth;

            return (
              <text
                key={i}
                x={x}
                y={height - padding.bottom + 20}
                textAnchor="middle"
                fontSize="11"
                fill="rgb(148, 163, 184)"
              >
                {hour.toString().padStart(2, '0')}:00
              </text>
            );
          })}

          {/* Axis labels */}
          <text
            x={padding.left - 40}
            y={padding.top + chartHeight / 2}
            textAnchor="middle"
            fontSize="12"
            fill="rgb(148, 163, 184)"
            transform={`rotate(-90, ${padding.left - 40}, ${padding.top + chartHeight / 2})`}
          >
            Altitud (°)
          </text>

          <text
            x={padding.left + chartWidth / 2}
            y={height - 10}
            textAnchor="middle"
            fontSize="12"
            fill="rgb(148, 163, 184)"
          >
            Hora Local
          </text>

          {/* Hover line and tooltip */}
          {hoverData && (
            <g>
              {/* Vertical line */}
              <line
                x1={hoverData.x}
                y1={padding.top}
                x2={hoverData.x}
                y2={padding.top + chartHeight}
                stroke="rgb(248, 113, 113)"
                strokeWidth="1.5"
                strokeDasharray="4,4"
                opacity="0.8"
              />

              {/* Circle at intersection */}
              <circle
                cx={hoverData.x}
                cy={padding.top + chartHeight - ((hoverData.altitude - altitudeMin) / (altitudeMax - altitudeMin)) * chartHeight}
                r="4"
                fill="rgb(248, 113, 113)"
                stroke="white"
                strokeWidth="2"
              />

              {/* Tooltip background */}
              <rect
                x={hoverData.x < padding.left + chartWidth / 2 ? hoverData.x + 10 : hoverData.x - 110}
                y={padding.top + 10}
                width="100"
                height="50"
                fill="rgb(15, 23, 42)"
                stroke="rgb(248, 113, 113)"
                strokeWidth="1"
                rx="4"
                opacity="0.95"
              />

              {/* Tooltip text - Time */}
              <text
                x={hoverData.x < padding.left + chartWidth / 2 ? hoverData.x + 60 : hoverData.x - 60}
                y={padding.top + 28}
                textAnchor="middle"
                fontSize="12"
                fill="rgb(248, 113, 113)"
                fontWeight="600"
              >
                {formatTime(hoverData.time)}
              </text>

              {/* Tooltip text - Altitude */}
              <text
                x={hoverData.x < padding.left + chartWidth / 2 ? hoverData.x + 60 : hoverData.x - 60}
                y={padding.top + 46}
                textAnchor="middle"
                fontSize="11"
                fill="rgb(203, 213, 225)"
              >
                Alt: {hoverData.altitude.toFixed(1)}°
              </text>
            </g>
          )}
        </svg>
      </div>

      {/* Info cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="bg-slate-900/50 rounded-lg p-3">
          <p className="text-xs text-slate-400 mb-1">Puesta de Sol</p>
          <p className="text-sm font-medium text-white">
            {formatTime(data.darkness_periods.civil_twilight.times[0])}
          </p>
        </div>

        <div className="bg-slate-900/50 rounded-lg p-3">
          <p className="text-xs text-slate-400 mb-1">Inicio Oscuridad</p>
          <p className="text-sm font-medium text-emerald-400">
            {formatTime(data.darkness_periods.astronomical_twilight.times[0])}
          </p>
        </div>

        <div className="bg-slate-900/50 rounded-lg p-3">
          <p className="text-xs text-slate-400 mb-1">Fin Oscuridad</p>
          <p className="text-sm font-medium text-amber-400">
            {formatTime(data.darkness_periods.astronomical_twilight.times[1])}
          </p>
        </div>

        <div className="bg-slate-900/50 rounded-lg p-3">
          <p className="text-xs text-slate-400 mb-1">Salida de Sol</p>
          <p className="text-sm font-medium text-white">
            {formatTime(data.darkness_periods.civil_twilight.times[1])}
          </p>
        </div>
      </div>

      {/* Warning if not visible */}
      {!data.optimal_window.start && (
        <div className="bg-amber-900/20 border border-amber-700 rounded-lg p-3">
          <p className="text-sm text-amber-300">
            ⚠️ Este objeto no alcanza los 20° de altitud mínima durante la noche.
            No es observable en esta fecha y ubicación.
          </p>
        </div>
      )}
    </div>
  );
}
