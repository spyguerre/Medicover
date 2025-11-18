"use client";

import { useState, useEffect } from "react";
import Link from "next/link";

export default function Sidebar() {
  const [checkedItems, setCheckedItems] = useState<Record<string, boolean>>({});
  const [filter, setFilter] = useState("");

  // Slider state
  const [sliderValue, setSliderValue] = useState(50);

  const toggleCheckbox = (key: string) => {
    setCheckedItems((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  // Filter options based on textbox input
  const filteredOptions = Object.keys(checkedItems).filter((key) =>
    key.toLowerCase().includes(filter.toLowerCase())
  );

  const handleConfirm = () => {
    console.log("Confirmed items:", checkedItems, "Slider:", sliderValue);
    alert("Selection confirmed!");
  };

  // Load profession list from public/professions.txt
  useEffect(() => {
    fetch("/professions.txt")
      .then((res) => res.text())
      .then((text) => {
        const lines = text
          .split("\n")
          .map((l) => l.trim())
          .filter((l) => l.length > 0);

        const initialState: Record<string, boolean> = {};
        lines.forEach((l) => (initialState[l] = false));

        setCheckedItems(initialState);
      })
      .catch((err) => console.log("Failed to load professions.txt:", err));
  }, []);

  return (
    <nav
      className="sidebar"
      style={{
        width: 250,
        height: "100vh",
        borderRight: "1px solid #ccc",
        display: "flex",
        flexDirection: "column",
      }}
    >
      {/* Top section: Logo + description */}
      <div style={{ padding: 16, borderBottom: "1px solid #ccc" }}>
        <Link
          href="/"
          style={{
            display: "inline-block",
            fontWeight: "bold",
            fontSize: 24,
            color: "#1D4ED8",
            textDecoration: "none",
            cursor: "pointer",
            userSelect: "none",
          }}
        >
          Medicover
        </Link>
        <div style={{ fontSize: 14, color: "#555", marginTop: 4 }}>
          Check your country's healthcare coverage!
        </div>
      </div>

      <div style={{ margin: 16, borderBottom: "1px solid #ccc" }}>
        {/* Menu title */}
        <div style={{ fontWeight: "bold", marginBottom: 8 }}>Professions</div>

        {/* Filter textbox */}
        <input
          type="text"
          placeholder="Filter options..."
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          style={{
            width: "100%",
            padding: "4px 8px",
            marginBottom: 8,
            boxSizing: "border-box",
          }}
        />
      </div>

      {/* Middle scrollable section */}
      <div style={{ flex: 1, overflowY: "auto", padding: "0 10px", maxHeight: "50vh" }}>

        {/* Checkbox list */}
        <ul style={{ listStyle: "none", padding: 0, margin: "0px 0 20px 0" }}>
          {filteredOptions.map((key) => (
            <li key={key} style={{ marginBottom: 4 }}>
              <label>
                <input
                  type="checkbox"
                  checked={checkedItems[key]}
                  onChange={() => toggleCheckbox(key)}
                />{" "}
                {key}
              </label>
            </li>
          ))}

          {filteredOptions.length === 0 && (
            <li style={{ fontStyle: "italic", color: "#999" }}>
              No matching options
            </li>
          )}
        </ul>
      </div>

      <div style={{ margin: 16, borderTop: "1px solid #ccc" }}>
        {/* --- NEW SLIDER SECTION --- */}
        <div style={{ marginTop: 20 }}>
          <div style={{ fontWeight: "bold" }}>
            Cluster range: {sliderValue}
          </div>

          <input
            type="range"
            min={0}
            max={100}
            value={sliderValue}
            onChange={(e) => setSliderValue(Number(e.target.value))}
            style={{ width: "100%" }}
          />
        </div>
      </div>
      
      <div style={{ margin: 0, borderTop: "1px solid #ccc" }}>
        <button
          onClick={handleConfirm}
          style={{
            width: "100%",
            padding: "8px 0",
            backgroundColor: "#1D4ED8",
            color: "white",
            fontWeight: "bold",
            border: "none",
            borderRadius: 4,
            cursor: "pointer",
            marginTop: "20px",
          }}
        >
          Confirm
        </button>
      </div>

      {/* Bottom section */}
      <div style={{ padding: 0, borderTop: "1px solid #ccc" }}>
        {/* --- NEW LABELS BELOW CONFIRM BUTTON --- */}
        <div style={{ marginTop: 12, fontSize: 12, color: "#555" }}>
          <div>Biggest Coverage Area: tbd</div>
          <div>Median Coverage Area: tbd</div>
          <div>Mean Coverage Area: tbd</div>
        </div>
      </div>
    </nav>
  );
}
