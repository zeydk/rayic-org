"use client";

import React, { useEffect } from "react";
import { MapContainer, TileLayer, GeoJSON, Marker, useMap } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

// Fix leaflet default icon issue in Next.js
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});

interface LeafletPolygonMapProps {
  lat: number;
  lng: number;
  polygonGeoJson?: any;
  zoom?: number;
  showFaultLines?: boolean;
}

function MapController({ center, zoom }: { center: [number, number]; zoom: number }) {
  const map = useMap();
  useEffect(() => {
    map.setView(center, zoom);
  }, [center, zoom, map]);
  return null;
}

export default function LeafletPolygonMap({ lat, lng, polygonGeoJson, zoom = 19, showFaultLines = true }: LeafletPolygonMapProps) {
  const center: [number, number] = [lat, lng];
  const [faultLines, setFaultLines] = React.useState<any[]>([]);

  useEffect(() => {
    if (!showFaultLines) return;
    const fetchFaults = async () => {
      try {
        const segments = [
          "/geo/avcilar_segmenti.geojson",
          "/geo/cinarcik_segmenti.geojson",
          "/geo/kumburgaz_segmenti.geojson",
          "/geo/orta_marmara_cukuru.geojson",
          "/geo/tekirdag_segmenti.geojson"
        ];
        
        const fetched = await Promise.all(
          segments.map(s => fetch(s).then(r => r.ok ? r.json() : null))
        );
        setFaultLines(fetched.filter(f => f !== null));
      } catch (e) {
        console.error("Error loading fault lines:", e);
      }
    };
    fetchFaults();
  }, [showFaultLines]);

  return (
    <div style={{ height: "100%", width: "100%" }}>
      <MapContainer 
        center={center} 
        zoom={zoom} 
        scrollWheelZoom={false} 
        style={{ height: "100%", width: "100%", zIndex: 10 }}
      >
        <TileLayer
          url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
          attribution="Tiles &copy; Esri"
        />
        <MapController center={center} zoom={zoom} />
        
        {/* Render Fault Lines */}
        {showFaultLines && faultLines.map((fault, idx) => (
          <GeoJSON 
            key={idx}
            data={fault} 
            style={() => ({
              color: "#ef4444", // Red fault lines
              weight: 4,
              opacity: 0.8
            })} 
          />
        ))}

        {polygonGeoJson && (
          <GeoJSON 
            data={polygonGeoJson} 
            style={() => ({
              color: "#10b981",
              weight: 3,
              fillColor: "#10b981",
              fillOpacity: 0.3
            })} 
          />
        )}
        
        {!polygonGeoJson && (
          <Marker position={center} />
        )}
      </MapContainer>
    </div>
  );
}
