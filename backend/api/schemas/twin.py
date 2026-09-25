"""
POLARIS-EMS — Digital Twin Spatial & Simulation API Schemas
SIH26061: Polar Energy Management & Resilience System

Defines request/response schemas for spatial floorplan visualization,
instantaneous TwinState telemetry, and multi-horizon forward trajectories.
"""

from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field


class TwinZoneBoundsSchema(BaseModel):
    x: float
    y: float
    width: float
    height: float


class TwinZoneSchema(BaseModel):
    id: str
    name: str
    label: str
    category: str
    bounds: TwinZoneBoundsSchema


class TwinSpatialNodePositionSchema(BaseModel):
    x: float
    y: float


class TwinSpatialNodeSchema(BaseModel):
    id: str
    kind: str  # SOURCE | BUS | STORAGE | LOAD | THERMAL | DEVICE
    label: str
    zoneId: Optional[str] = None
    deviceId: Optional[str] = None
    circuitId: Optional[str] = None
    position: TwinSpatialNodePositionSchema
    iconKey: Optional[str] = None
    selectable: bool = True


class TwinFlowGeometrySchema(BaseModel):
    type: Literal["polyline", "path"]
    points: Optional[List[TwinSpatialNodePositionSchema]] = None
    d: Optional[str] = None


class TwinSourceMixSchema(BaseModel):
    solarKw: float = 0.0
    windKw: float = 0.0
    dieselKw: float = 0.0
    batteryKw: float = 0.0


class TwinFlowEdgeSchema(BaseModel):
    id: str
    fromNodeId: str
    toNodeId: str
    circuitId: Optional[str] = None
    geometry: TwinFlowGeometrySchema
    direction: Literal["FORWARD", "REVERSE", "NONE"] = "FORWARD"
    powerKw: float = 0.0
    sourceMix: TwinSourceMixSchema
    active: bool = True


class TwinSpatialProfileSchema(BaseModel):
    stationId: str
    version: str = "1.0"
    layoutStatus: Literal["REPRESENTATIVE", "CONFIGURED"] = "REPRESENTATIVE"
    geometryBasis: str = "CONFIG_ASSUMED"
    width: float = 1000
    height: float = 640
    zones: List[TwinZoneSchema]
    nodes: List[TwinSpatialNodeSchema]
    edges: List[TwinFlowEdgeSchema]


class TwinTrajectoryRequestSchema(BaseModel):
    station_id: str = Field(..., description="Target polar research station (BHARATI, MAITRI, HIMADRI)")
    horizon_hours: int = Field(default=24, ge=1, le=168, description="Replay horizon in hours (24, 48, 168)")
    mode: Literal["EXPECTED", "CONSERVATIVE", "OPTIMISTIC"] = Field(
        default="EXPECTED", description="Forecast trajectory mode"
    )
    scenario_id: Optional[str] = Field(None, description="Optional stress scenario ID to perturb baseline")
    start_timestamp: Optional[str] = Field(None, description="Starting ISO timestamp")


class TwinTrajectoryResponseData(BaseModel):
    station_id: str
    mode: str
    steps_count: int
    duration_hours: float
    states: List[Dict[str, Any]]
    summary: Dict[str, Any]
    provenance: str = "SIMULATED"
