"use client"

import { useState, useEffect } from "react";

export default function ProfessionSelector(
    {checkedItems, setCheckedItems}: {
        checkedItems: Record<string, boolean>,
        setCheckedItems: React.Dispatch<React.SetStateAction<Record<string, boolean>>>
    }) {
    const [filter, setFilter] = useState("");
    
    // Filter options based on textbox input
    const filteredOptions = Object.keys(checkedItems).filter((key) =>
        key.toLowerCase().includes(filter.toLowerCase())
    );

    const toggleCheckbox = (key: string) => {
        setCheckedItems((prev) => ({ ...prev, [key]: !prev[key] }));
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
    <div>
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
    </div>
    )
}
