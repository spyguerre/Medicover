"use client"

import { Professions } from "./ProfessionCheckboxes"

export default function ConfirmButton(
    {handleConfirm}: {
        handleConfirm: () => void
    }
) {
    return (
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
    )
}
