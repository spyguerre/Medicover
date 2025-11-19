"use client";

import Panzoom from "@panzoom/panzoom";
import { useEffect, useRef } from "react";

export default function Page() {
  const panzoomRef = useRef<HTMLDivElement | null>(null);
  const viewportRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const panzoomEl = panzoomRef.current;
    const viewport = viewportRef.current;
    if (!panzoomEl || !viewport) return;

    const img = panzoomEl.querySelector("img") as HTMLImageElement | null;
    if (!img) return;

    const initPanzoom = () => {
      // Ensure the panzoom element has the image's natural size
      panzoomEl.style.width = `${img.naturalWidth}px`;
      panzoomEl.style.height = `${img.naturalHeight}px`;
      panzoomEl.style.position = "absolute";
      panzoomEl.style.top = "0";
      panzoomEl.style.left = "0";
      panzoomEl.style.transformOrigin = "0 0";

      const vpRect = viewport.getBoundingClientRect();
      const vpW = vpRect.width;
      const vpH = vpRect.height;

      const scale = Math.min(vpW / img.naturalWidth, vpH / img.naturalHeight);

      // Initialize Panzoom
      const panzoom = Panzoom(panzoomEl, {
        maxScale: 10,
        minScale: 0.1,
        step: 0.1,
        startScale: scale,
        contain: "outside", // centers image automatically
      });

      // Wheel zoom
      const wheelHandler = (e: WheelEvent) => {
        e.preventDefault();
        panzoom.zoomWithWheel(e);
      };
      viewport.addEventListener("wheel", wheelHandler, { passive: false });

      // Cleanup on unmount
      return () => {
        viewport.removeEventListener("wheel", wheelHandler);
        panzoom.destroy();
      };
    };

    if (img.complete && img.naturalWidth) {
      initPanzoom();
    } else {
      img.onload = initPanzoom;
    }
  }, []);

  return (
    <div
      ref={viewportRef}
      style={{
        width: "100%",
        height: "90vh",
        border: "1px solid #ccc",
        overflow: "hidden",
        position: "relative",
      }}
    >
      <div ref={panzoomRef} style={{ cursor: "grab" }}>
        <img
          src="/sample.jpg"
          alt="Zoomable"
          style={{
            display: "block",
            userSelect: "none",
            width: "auto",
            height: "auto",
            pointerEvents: "none",
          }}
        />
      </div>
    </div>
  );
}
