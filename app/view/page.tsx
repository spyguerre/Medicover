"use client";

import Sidebar from "@/components/Sidebar";
import { Professions } from "@/components/sidebar/ProfessionCheckboxes";
import Panzoom from "@panzoom/panzoom";
import { useEffect, useRef, useState } from "react";
import { Oval } from 'react-loader-spinner'
import { ToastContainer, toast } from 'react-toastify';

export default function Page() {
  const [isLoading, setLoading] = useState<boolean>(false); // Boolean to store whether the image is being generated or shown
  const [currentImage, setCurrentImage] = useState<string>("/sample.jpg"); // Sample image by default, then path to current map image.

  const panzoomRef = useRef<HTMLDivElement | null>(null);
  const viewportRef = useRef<HTMLDivElement | null>(null);

  const handleConfirm = async (checkedBoxes: Professions, clusterValue: number) => {
    setLoading(true);

    try {
      // Collect selected profession codes
      const selectedCodes = Object.entries(checkedBoxes)
        .filter(([_, v]) => v.selected)
        .map(([code]) => code);

      if (selectedCodes.length === 0) {
        toast("Please select at least one profession.");
        return;
      }

      toast("Selection confirmed. The image is being generated...");

      // Build query string (comma-separated values)
      const params = new URLSearchParams({
        professions: selectedCodes.join(","),
      });

      // Call API route (GET or POST with query params — your route expects POST)
      const res = await fetch(`/api/generateMap?${params.toString()}`, {
        method: "POST",
      });

      const data = await res.json();

      if (!res.ok || !data.success) {
        throw new Error(data.error || "Server error");
      }

      console.log("Map generated:", data);

      // Show result to user
      toast("Image successfully generated!");
      setCurrentImage("/generatedImages/" + selectedCodes.join(",") + ".png");

    } catch (err: any) {
      console.error(err);
      toast("An error occurred: " + err.message);
    } finally {
      setLoading(false);
    }
  };

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
    <div>
      <Sidebar handleConfirm={handleConfirm}/>
      <ToastContainer />
      {
        !isLoading &&
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
              src={currentImage}
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

        || isLoading &&
        <div
          style={{
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            height: "100vh"
          }}
        >
          <Oval/>
        </div>
      }
  </div>
  );
}
