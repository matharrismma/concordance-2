import { useState } from "react";

const SCALE = 8.5;
const CX = 250;
const CY = 250;

const wheels = [
  { name: "Center", x: 0, y: 0, r: 5.76, color: "#D4A843", clock: "center", teeth: "64T wheel" },
  { name: "Barrel", x: -5.97, y: -4.18, r: 6.48, color: "#C0935A", clock: "~10h", teeth: "72T, m0.18" },
  { name: "Third", x: 6.46, y: 0.56, r: 5.76, color: "#D4A843", clock: "~3h", teeth: "64T/8T (=Fourth)" },
  { name: "Fourth", x: 0.63, y: 3.41, r: 5.76, color: "#D4A843", clock: "~6h", teeth: "64T/8T (=Third)" },
  { name: "Escape", x: -1.69, y: 9.46, r: 1.35, color: "#A0A0A0", clock: "~6:20", teeth: "15T/8T" },
  { name: "Balance", x: -4.41, y: 5.26, r: 5.0, color: "#7BA4C7", clock: "~7:20", teeth: "10mm Glucydur" },
  { name: "Pallet", x: -2.78, y: 7.78, r: 0.8, color: "#E06060", clock: "~6:45", teeth: "Swiss lever" },
];

const meshPairs = [
  ["Barrel", "Center"], ["Center", "Third"],
  ["Third", "Fourth"], ["Fourth", "Escape"], ["Escape", "Balance"],
];

const toSVG = (x, y) => [CX + x * SCALE, CY + y * SCALE];

export default function PivotMap() {
  const [selected, setSelected] = useState(null);
  const usableR = 19.0;
  const caseR = 21.0;
  const wheelMap = {};
  wheels.forEach(w => { wheelMap[w.name] = w; });

  return (
    <div className="flex flex-col items-center bg-zinc-900 min-h-screen p-4">
      <h1 className="text-xl font-bold text-zinc-100 mb-1">Calibre 44 — Pivot Map</h1>
      <p className="text-zinc-400 text-sm mb-4">42mm case, 38mm usable, 3 Hz, 4096:1</p>

      <svg width="500" height="500" viewBox="0 0 500 500" className="bg-zinc-950 rounded-lg border border-zinc-700">
        <defs>
          <pattern id="grid" width={SCALE} height={SCALE} patternUnits="userSpaceOnUse">
            <path d={`M ${SCALE} 0 L 0 0 0 ${SCALE}`} fill="none" stroke="#222" strokeWidth="0.3" />
          </pattern>
        </defs>
        <rect width="500" height="500" fill="url(#grid)" />

        {/* Case outlines */}
        <circle cx={CX} cy={CY} r={caseR * SCALE} fill="none" stroke="#444" strokeWidth="2" />
        <circle cx={CX} cy={CY} r={usableR * SCALE} fill="none" stroke="#666" strokeWidth="1" strokeDasharray="3,3" />

        {/* Mesh lines */}
        {meshPairs.map(([a, b], i) => {
          const wa = wheelMap[a]; const wb = wheelMap[b];
          const [x1, y1] = toSVG(wa.x, wa.y);
          const [x2, y2] = toSVG(wb.x, wb.y);
          return <line key={i} x1={x1} y1={y1} x2={x2} y2={y2} stroke="#444" strokeWidth="1" strokeDasharray="4,3" />;
        })}

        {/* Rotor outline */}
        <circle cx={CX} cy={CY} r={15 * SCALE} fill="none" stroke="#3A5A3A" strokeWidth="1" strokeDasharray="8,4" opacity="0.4" />
        <text x={CX + 15 * SCALE - 30} y={CY - 15 * SCALE + 14} fontSize="9" fill="#3A5A3A">Rotor 30mm</text>

        {/* Wheels */}
        {wheels.map((w) => {
          const [cx, cy] = toSVG(w.x, w.y);
          const isSel = selected === w.name;
          return (
            <g key={w.name} onClick={() => setSelected(isSel ? null : w.name)} className="cursor-pointer">
              <circle cx={cx} cy={cy} r={w.r * SCALE}
                fill={w.color} fillOpacity={isSel ? 0.3 : 0.12}
                stroke={w.color} strokeWidth={isSel ? 2.5 : 1} />
              <circle cx={cx} cy={cy} r={2} fill={w.color} />
              <line x1={cx-4} y1={cy} x2={cx+4} y2={cy} stroke={w.color} strokeWidth="0.5" />
              <line x1={cx} y1={cy-4} x2={cx} y2={cy+4} stroke={w.color} strokeWidth="0.5" />
              <text x={cx} y={cy - w.r * SCALE - 5}
                textAnchor="middle" fontSize="10" fill={w.color} fontWeight={isSel ? "bold" : "normal"}>
                {w.name}
              </text>
            </g>
          );
        })}

        {/* Crown at 3 */}
        <circle cx={CX + caseR * SCALE + 7} cy={CY} r="4" fill="#666" stroke="#888" strokeWidth="1" />

        {/* Case labels */}
        <text x={CX} y={CY - caseR * SCALE - 6} textAnchor="middle" fontSize="8" fill="#555">42mm case</text>
        <text x={CX} y={CY - usableR * SCALE - 4} textAnchor="middle" fontSize="8" fill="#777">38mm usable</text>
      </svg>

      {/* Detail panel */}
      <div className="mt-4 w-full max-w-sm">
        {selected ? (() => {
          const w = wheelMap[selected];
          const dist = Math.sqrt(w.x * w.x + w.y * w.y);
          const wallGap = usableR - dist - w.r;
          return (
            <div className="bg-zinc-800 rounded-lg p-4 border border-zinc-700">
              <h2 className="font-bold text-zinc-100 mb-2">{w.name}</h2>
              <div className="grid grid-cols-2 gap-y-1 text-sm">
                <span className="text-zinc-500">Coordinates</span>
                <span className="text-zinc-200">({w.x.toFixed(2)}, {w.y.toFixed(2)}) mm</span>
                <span className="text-zinc-500">Wheel radius</span>
                <span className="text-zinc-200">{w.r.toFixed(2)} mm</span>
                <span className="text-zinc-500">From center</span>
                <span className="text-zinc-200">{dist.toFixed(2)} mm</span>
                <span className="text-zinc-500">Wall clearance</span>
                <span className="text-zinc-200">{wallGap.toFixed(2)} mm</span>
                <span className="text-zinc-500">Clock position</span>
                <span className="text-zinc-200">{w.clock}</span>
                <span className="text-zinc-500">Spec</span>
                <span className="text-zinc-200">{w.teeth}</span>
              </div>
            </div>
          );
        })() : (
          <div className="bg-zinc-800 rounded-lg p-3 border border-zinc-700">
            <p className="text-zinc-500 text-sm text-center mb-2">Tap a wheel for details</p>
            <div className="grid grid-cols-2 gap-1 text-xs text-zinc-600">
              <div>Barrel→Center: 7.29</div>
              <div>Center→Third: 6.48</div>
              <div>Third→Fourth: 6.48</div>
              <div>Fourth→Escape: 6.48</div>
              <div>Escape→Balance: 5.00</div>
              <div>Min wall gap: 5.23mm</div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
