/**
 * POLARIS-EMS — Digital Twin Viewport Navigation Hook
 * Phase 18: Spatial Digital Twin Engine
 * 
 * Implements smooth pointer-centered zoom, drag pan, fit-to-view, and reset.
 */

import { useState, useCallback, useRef, useEffect } from 'react';

export interface ViewportState {
  panX: number;
  panY: number;
  zoom: number;
}

export interface UseTwinViewportOptions {
  canvasWidth: number;
  canvasHeight: number;
  minZoom?: number;
  maxZoom?: number;
}

export function useTwinViewport(options: UseTwinViewportOptions) {
  const {
    canvasWidth = 1000,
    canvasHeight = 640,
    minZoom = 0.5,
    maxZoom = 3.0
  } = options;

  const [viewport, setViewport] = useState<ViewportState>({
    panX: 0,
    panY: 0,
    zoom: 1.0
  });

  const isDraggingRef = useRef(false);
  const dragStartRef = useRef({ x: 0, y: 0, panX: 0, panY: 0 });

  const clampZoom = useCallback((z: number) => {
    return Math.min(maxZoom, Math.max(minZoom, z));
  }, [minZoom, maxZoom]);

  const handleWheel = useCallback((e: React.WheelEvent<SVGSVGElement | HTMLDivElement>) => {
    e.preventDefault();
    const rect = e.currentTarget.getBoundingClientRect();
    const pointerX = e.clientX - rect.left;
    const pointerY = e.clientY - rect.top;

    const zoomFactor = e.deltaY < 0 ? 1.15 : 0.87;
    setViewport(prev => {
      const nextZoom = clampZoom(prev.zoom * zoomFactor);
      if (nextZoom === prev.zoom) return prev;

      // Pointer-centered zoom equation:
      // nextPan = pointer - (pointer - prevPan) * (nextZoom / prevZoom)
      const nextPanX = pointerX - (pointerX - prevPanX(prev.panX)) * (nextZoom / prev.zoom);
      const nextPanY = pointerY - (pointerY - prevPanY(prev.panY)) * (nextZoom / prev.zoom);

      return {
        zoom: nextZoom,
        panX: Math.round(nextPanX),
        panY: Math.round(nextPanY)
      };
    });
  }, [clampZoom]);

  const prevPanX = (x: number) => x;
  const prevPanY = (y: number) => y;

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    if (e.button !== 0) return; // Primary click only
    // Only drag if clicking on the background canvas, not interactive nodes
    const target = e.target as HTMLElement;
    if (target.closest('[data-interactive="true"]')) return;

    isDraggingRef.current = true;
    dragStartRef.current = {
      x: e.clientX,
      y: e.clientY,
      panX: viewport.panX,
      panY: viewport.panY
    };
  }, [viewport.panX, viewport.panY]);

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (!isDraggingRef.current) return;
    const dx = e.clientX - dragStartRef.current.x;
    const dy = e.clientY - dragStartRef.current.y;
    setViewport(prev => ({
      ...prev,
      panX: Math.round(dragStartRef.current.panX + dx),
      panY: Math.round(dragStartRef.current.panY + dy)
    }));
  }, []);

  const handleMouseUp = useCallback(() => {
    isDraggingRef.current = false;
  }, []);

  const zoomIn = useCallback(() => {
    setViewport(prev => ({
      ...prev,
      zoom: clampZoom(prev.zoom * 1.25)
    }));
  }, [clampZoom]);

  const zoomOut = useCallback(() => {
    setViewport(prev => ({
      ...prev,
      zoom: clampZoom(prev.zoom * 0.8)
    }));
  }, [clampZoom]);

  const reset = useCallback(() => {
    setViewport({
      panX: 0,
      panY: 0,
      zoom: 1.0
    });
  }, []);

  const fitToView = useCallback((containerWidth?: number, containerHeight?: number) => {
    if (!containerWidth || !containerHeight) {
      reset();
      return;
    }
    const scaleX = (containerWidth * 0.92) / canvasWidth;
    const scaleY = (containerHeight * 0.92) / canvasHeight;
    const newZoom = clampZoom(Math.min(scaleX, scaleY));
    const newPanX = (containerWidth - canvasWidth * newZoom) / 2;
    const newPanY = (containerHeight - canvasHeight * newZoom) / 2;

    setViewport({
      zoom: newZoom,
      panX: Math.round(newPanX),
      panY: Math.round(newPanY)
    });
  }, [canvasWidth, canvasHeight, clampZoom, reset]);

  return {
    viewport,
    setViewport,
    handleWheel,
    handleMouseDown,
    handleMouseMove,
    handleMouseUp,
    zoomIn,
    zoomOut,
    reset,
    fitToView
  };
}
