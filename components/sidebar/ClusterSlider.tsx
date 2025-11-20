"use client"

export default function ClusterSlider(
    {sliderValue, setSliderValue, clusterValue}: {
        sliderValue: number,
        setSliderValue: React.Dispatch<React.SetStateAction<number>>,
        clusterValue: number
    }
) {
    return (
        <div style={{margin: "5px 0 16px 0"}}>
            <div style={{ fontWeight: "bold" }}>
                Cluster range: {
                clusterValue >= 1000 &&
                (Math.round(clusterValue/100)/10 + " km")
                || clusterValue < 1000 &&
                (Math.round(clusterValue) + " m")
                }
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
    )
}
