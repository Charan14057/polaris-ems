/**
 * POLARIS-EMS — Digital Twin Junction Markers Component
 * Phase 18: Spatial Digital Twin Engine
 * 
 * Renders small electrical junction points at bus split nodes and source connections.
 */

import React from 'react';
import { VisualEdgeState } from '../model/twinTypes';

interface TwinJunctionsProps {
  edges: VisualEdgeState[];
}

export const TwinJunctions: React.FC<TwinJunctionsProps> = ({ edges }) => {
  // Extract junction points from polyline turns and connections
  const junctionPoints: Array<{ x: number; y: number; active: boolean; hasDiesel: boolean }> = [];

  edges.forEach(edge => {
    if (edge.geometry.type === 'polyline' && edge.geometry.points && edge.geometry.points.length > 2) {
      // Internal vertices of polyline are wireway turn junctions
      for (let i = 1; i < edge.geometry.points.length - 1; i++) {
        const pt = edge.geometry.points[i];
        junctionPoints.push({
          x: pt.x,
          y: pt.y,
          active: edge.active,
          hasDiesel: edge.hasDieselContribution
        });
      }
    }
  });

  return (
    <g className="twin-junctions-layer select-none pointer-events-none">
      {junctionPoints.map((pt, idx) => (
        <circle
          key={`junc-${idx}`}
          cx={pt.x}
          cy={pt.y}
          r={pt.active ? 2.5 : 1.5}
          className={`transition-all duration-300 ${
            pt.active
              ? pt.hasDiesel
                ? 'fill-copper'
                : 'fill-teal'
              : 'fill-border'
          }`}
        />
      ))}
    </g>
  );
};
