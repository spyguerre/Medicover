"use client";

import { useState } from "react";
import Logo from "./Logo";
import ProfessionSelector from "./sidebar/ProfessionCheckboxes";
import ClusterSlider from "./sidebar/ClusterSlider";
import ConfirmButton from "./sidebar/ConfirmButton";
import Stats from "./sidebar/Stats";

export default function Sidebar() {
  // Slider state
  const [sliderValue, setSliderValue] = useState(50);
  const [checkedItems, setCheckedItems] = useState<Record<string, boolean>>({});

  const handleConfirm = () => {
    console.log("Confirmed items:", checkedItems, "Slider:", sliderValue);
    alert("Selection confirmed!");
  };

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
      <div style={{ padding: 16, borderBottom: "1px solid #ccc" }}>
        <Logo />
        <div style={{ fontSize: 14, color: "#555", marginTop: 4 }}>
          Check your country's healthcare coverage!
        </div>
      </div>
  
      <ProfessionSelector
        checkedItems={checkedItems}
        setCheckedItems={setCheckedItems}
      />
  
      <div style={{ marginTop: "auto", padding: 16, borderTop: "1px solid #ccc" }}>

        <ClusterSlider sliderValue={sliderValue} setSliderValue={setSliderValue} />
  
        <ConfirmButton handleConfirm={handleConfirm} />
  
        <div style={{ marginTop: 12 }}>
          <Stats biggestArea={0} medianArea={0} meanArea={0} />
        </div>
      </div>
    </nav>
  );  
}
