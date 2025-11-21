"use client"


export default function Stats(
    {biggestArea, medianArea, meanArea}: {
        biggestArea: number,
        medianArea: number,
        meanArea: number
    }
) {
    return (
      <div style={{ padding: 0, borderTop: "1px solid #ccc" }}>
      {/* --- NEW LABELS BELOW CONFIRM BUTTON --- */}
      <div style={{ marginTop: 12, fontSize: 16, color: "#555" }}>
        <div>Biggest Coverage Area: {biggestArea} </div>
        <div>Median Coverage Area: {medianArea} </div>
        <div>Mean Coverage Area: {meanArea} </div>
      </div>
    </div>
    )
}
