"use client";

import { useEffect, useState } from "react";
import Logo from "./Logo";
import ProfessionSelector, { Professions } from "./sidebar/ProfessionCheckboxes";
import ClusterSlider from "./sidebar/ClusterSlider";
import ConfirmButton from "./sidebar/ConfirmButton";
import Stats from "./sidebar/Stats";
import SidebarButton from "./sidebar/SidebarButton";

export default function Sidebar({handleConfirm}: {
  handleConfirm: (checkedBoxes: Professions, clusterValue: number) => void
}
) {
  const [checkedItems, setCheckedItems] = useState<Professions>({});
  const [showSidebar, setShowSidebar] = useState<boolean>(true);
  const [sliderValue, setSliderValue] = useState(50); // The value input by the user, from 0 to 100
  const [clusterValue, setClusterValue] = useState<number>(0); // The computed cluster value with input slider value, from 0 to 10km

  const computeExpClusterValue: (x: number) => number = (x: number) => {
    const maxOutput = 10000;
    const k = 0.05;
    const A = maxOutput / (Math.exp(k * 100) - 1);

    return A * (Math.exp(k * x) - 1);
  }

  useEffect(() => { // Compute exponential cluster value knowing new sliderValue
    setClusterValue(computeExpClusterValue(sliderValue));
  }, [sliderValue]);

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

        <ClusterSlider sliderValue={sliderValue} setSliderValue={setSliderValue} clusterValue={clusterValue} />
  
        <ConfirmButton handleConfirm={() => handleConfirm(checkedItems, clusterValue)} />
  
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
