"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";

export default function Sidebar() {
  const [checkedItems, setCheckedItems] = useState<Record<string, boolean>>({});

  const [filter, setFilter] = useState("");

  const toggleCheckbox = (key: string) => {
    setCheckedItems((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  // Filter options based on textbox input
  const filteredOptions = Object.keys(checkedItems).filter((key) =>
    key.toLowerCase().includes(filter.toLowerCase())
  );

  const handleConfirm = () => {
    console.log("Confirmed items:", checkedItems);
    alert("Selection confirmed!");
  };

  useEffect(() => {
    // Fetch professions from public/professions.txt
    fetch("/professions.txt")
    .then((res) => res.text())
    .then((text) => {
      const lines = text
      .split("\n")
      .map((l) => l.trim())
      .filter((l) => l.length > 0);

      // Build checkbox state dynamically
      const initialState: Record<string, boolean> = {};
      lines.forEach((l) => initialState[l] = false);

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
      <div style={{ padding: 16 }}>
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
          Your healthcare dashboard
        </div>
      </div>

      {/* Middle section: Filterable checkbox list */}
      <div style={{ flex: 1, overflowY: "auto", padding: "0 16px" }}>
        {/* Menu title */}
        <div
          style={{ fontWeight: "bold", marginBottom: 8, cursor: "default" }}
        >
          Professions
        </div>

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

        {/* Checkbox list */}
        <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
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

      {/* Bottom section: Confirm button */}
      <div style={{ padding: 16, borderTop: "1px solid #ccc" }}>
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
          }}
        >
          Confirm
        </button>
      </div>
    </nav>
  );
}
