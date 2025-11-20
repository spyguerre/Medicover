"use client"

import { Sidebar as SidebarIcon } from "@deemlol/next-icons";

export default function SidebarButton(
    {showSidebar, setShowSidebar}: {
        showSidebar: boolean,
        setShowSidebar: React.Dispatch<React.SetStateAction<boolean>>
    }
) {

    const handleSidebarButton = () => {
        setShowSidebar(!showSidebar);
    };

    return (
        <button
            onClick={handleSidebarButton}
            style={{
            padding: "8px",
            backgroundColor: "#888888",
            color: "white",
            fontWeight: "bold",
            border: "none",
            borderRadius: 4,
            cursor: "pointer",
            marginRight: "auto",
            marginTop: "auto",
            marginBottom: "auto",
            maxHeight: 40,
            maxWidth: 40
            }}
        >
            <SidebarIcon/>
        </button>
    )
}
