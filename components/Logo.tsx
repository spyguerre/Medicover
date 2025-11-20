"use client"

import Link from "next/link"

export default function Logo() {
    return (
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
    )
}
