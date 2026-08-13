"use client";

import React, { useMemo } from "react";
import Map, { Marker, Layer } from "react-map-gl/maplibre";
import "maplibre-gl/dist/maplibre-gl.css";

export default function OsmBuildingsMap({ lat, lng, zoom = 16 }: { lat: number, lng: number, zoom?: number }) {
  
  const buildingLayer = useMemo(() => ({
    id: "3d-buildings",
    source: "openmaptiles",
    "source-layer": "building",
    filter: ["==", "extrude", "true"],
    type: "fill-extrusion",
    minzoom: 14,
    paint: {
      "fill-extrusion-color": "#e5e5e5",
      "fill-extrusion-height": [
        "interpolate",
        ["linear"],
        ["zoom"],
        14,
        0,
        14.05,
        ["get", "render_height"]
      ],
      "fill-extrusion-base": [
        "interpolate",
        ["linear"],
        ["zoom"],
        14,
        0,
        14.05,
        ["get", "render_min_height"]
      ],
      "fill-extrusion-opacity": 0.8
    }
  }), []);

  return (
    <div style={{ width: "100%", height: "100%", position: "absolute", top: 0, left: 0 }}>
      <Map
        initialViewState={{
          longitude: lng,
          latitude: lat,
          zoom: zoom,
          pitch: 45,
          bearing: -17.6
        }}
        style={{ width: "100%", height: "100%" }}
        mapStyle="https://tiles.openfreemap.org/styles/liberty"
        interactive={true}
        attributionControl={false}
      >
        <Marker longitude={lng} latitude={lat} color="#ef4444" />
        
        {/* We add the 3D layer on top of the style's existing openmaptiles source */}
        <Layer {...(buildingLayer as any)} /> 
      </Map>
    </div>
  );
}
