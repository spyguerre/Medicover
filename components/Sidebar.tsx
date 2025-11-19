"use client";

import { useState } from "react";
import Logo from "./Logo";
import ProfessionSelector from "./sidebar/ProfessionCheckboxes";
import ClusterSlider from "./sidebar/ClusterSlider";
import ConfirmButton from "./sidebar/ConfirmButton";
import Stats from "./sidebar/Stats";
import SidebarButton from "./sidebar/SidebarButton";

export default function Sidebar() {
  // Slider state
  const [sliderValue, setSliderValue] = useState(50);
  const [checkedItems, setCheckedItems] = useState<Record<string, boolean>>({});
  const [showSidebar, setShowSidebar] = useState<boolean>(true);

  const handleConfirm = () => {
    console.log("Confirmed items:", checkedItems, "Slider:", sliderValue);
    alert("Selection confirmed!");
  };

  return (
      showSidebar &&
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
      
      <div style={{display: "flex", padding: "16px 0 16px 0", flexDirection: "row", borderBottom: "1px solid #ccc"}}>
        <SidebarButton showSidebar={showSidebar} setShowSidebar={setShowSidebar}/>
        <div style={{ display: "flex", flexDirection: "column", marginLeft: 50 }}>
          <Logo />
          <div style={{ fontSize: 14, color: "#555", marginTop: 4 }}>
          Check your country's healthcare coverage!
          </div>
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
    || !showSidebar &&
    <nav>
      <div style={{ margin: 16 }}>
        <SidebarButton
          showSidebar={showSidebar}
          setShowSidebar={setShowSidebar}
        />
      </div>
    </nav>
  );  
}
