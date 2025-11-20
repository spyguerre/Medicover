"use client"

export default function ClusterSlider(
    {sliderValue, setSliderValue}: {
        sliderValue: number,
        setSliderValue: React.Dispatch<React.SetStateAction<number>>
    }
) {
    return (
        <div style={{margin: "5px 0 16px 0"}}>
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
    )
}
