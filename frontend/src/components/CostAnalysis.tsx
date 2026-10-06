import React, { useState } from 'react';
import { DollarSign, TrendingDown, Calculator, ShieldCheck, HelpCircle } from 'lucide-react';

interface CostAnalysisProps {
  costDelta100k?: number;
  unitCostGemini?: number;
}

export const CostAnalysis: React.FC<CostAnalysisProps> = ({
  costDelta100k = 2.7,
  unitCostGemini = 0.000027,
}) => {
  const [monthlyVolume, setMonthlyVolume] = useState<number>(100000);

  const totalGeminiCost = monthlyVolume * unitCostGemini;
  const totalClefCost = 0.0; // Marginal cost 0 on existing local hardware
  const totalSavings = totalGeminiCost - totalClefCost;

  return (
    <div className="bg-zinc-900/90 border border-zinc-800 rounded-xl p-5 shadow-lg backdrop-blur-sm space-y-4">
      {/* Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-zinc-800 pb-3">
        <div className="flex items-center gap-2">
          <Calculator className="w-4 h-4 text-emerald-400" />
          <h3 className="text-sm font-semibold text-white">
            Simulador Actuarial de Costos de Inferencia
          </h3>
        </div>
        <div className="flex items-center gap-1.5 text-xs text-zinc-400">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
          <span>Fórmulas oficiales de tarificación según Constitución</span>
        </div>
      </div>

      {/* Interactive Volume Slider */}
      <div className="p-4 rounded-lg bg-zinc-950/60 border border-zinc-800 space-y-2">
        <div className="flex items-center justify-between text-xs">
          <label htmlFor="volume-slider" className="font-medium text-zinc-300">
            Volumen Proyectado de Siniestros Mensuales:
          </label>
          <span className="font-mono font-bold text-sm text-emerald-400">
            {monthlyVolume.toLocaleString('es-EC')} reclamos/mes
          </span>
        </div>

        <input
          id="volume-slider"
          type="range"
          min={10000}
          max={1000000}
          step={10000}
          value={monthlyVolume}
          onChange={(e) => setMonthlyVolume(Number(e.target.value))}
          className="w-full accent-emerald-500 bg-zinc-800 rounded-lg cursor-pointer h-1.5"
        />

        <div className="flex justify-between text-[10px] text-zinc-500 font-mono">
          <span>10k / mes</span>
          <span>100k (Base)</span>
          <span>500k / mes</span>
          <span>1M / mes</span>
        </div>
      </div>

      {/* Comparative Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {/* Clef-Flash Local Cost */}
        <div className="p-3.5 rounded-lg bg-emerald-950/20 border border-emerald-500/30 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between text-xs mb-1">
              <span className="font-semibold text-emerald-300">Clef-Flash Local</span>
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-500/30">
                GPU Edge
              </span>
            </div>
            <p className="text-[11px] text-zinc-400">
              Costo marginal de API por solicitud: <strong>$0.00</strong>
            </p>
          </div>
          <div className="mt-3 pt-2 border-t border-emerald-500/20">
            <span className="text-xl font-bold font-mono text-emerald-400">
              $0.00 USD
            </span>
            <span className="text-[10px] text-zinc-500 block">
              Gasto recurrente de API
            </span>
          </div>
        </div>

        {/* Gemini 2.5 Flash Cloud Cost */}
        <div className="p-3.5 rounded-lg bg-sky-950/20 border border-sky-500/30 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between text-xs mb-1">
              <span className="font-semibold text-sky-300">Gemini 2.5 Flash</span>
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-sky-950 text-sky-400 border border-sky-500/30">
                AI Studio
              </span>
            </div>
            <p className="text-[11px] text-zinc-400">
              $0.075 / 1M input • $0.30 / 1M output tokens
            </p>
          </div>
          <div className="mt-3 pt-2 border-t border-sky-500/20">
            <span className="text-xl font-bold font-mono text-sky-400">
              ${totalGeminiCost.toFixed(2)} USD
            </span>
            <span className="text-[10px] text-zinc-500 block">
              ${(costDelta100k).toFixed(2)} por cada 100k incidentes
            </span>
          </div>
        </div>

        {/* Total Projected Savings */}
        <div className="p-3.5 rounded-lg bg-gradient-to-br from-emerald-950/40 to-zinc-950 border border-emerald-500/40 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between text-xs mb-1">
              <span className="font-semibold text-white flex items-center gap-1">
                <TrendingDown className="w-3.5 h-3.5 text-emerald-400" />
                Ahorro Neto en Cloud
              </span>
              <DollarSign className="w-4 h-4 text-emerald-400" />
            </div>
            <p className="text-[11px] text-zinc-400">
              Reducción del 100% en costos de inferencia en la nube
            </p>
          </div>
          <div className="mt-3 pt-2 border-t border-zinc-800">
            <span className="text-xl font-bold font-mono text-emerald-300">
              +${totalSavings.toFixed(2)} USD
            </span>
            <span className="text-[10px] text-emerald-400/80 block">
              Ahorro mensual neto estimado
            </span>
          </div>
        </div>
      </div>

      {/* Constitution Note */}
      <div className="flex items-start gap-2 p-3 rounded-lg bg-zinc-950/40 border border-zinc-800/80 text-[11px] text-zinc-400">
        <HelpCircle className="w-3.5 h-3.5 text-zinc-500 mt-0.5 flex-shrink-0" />
        <span>
          <strong>Principio Constitucional 5 (Transparencia):</strong> El costo de Clef-Flash no incluye amortización de hardware ni consumo eléctrico (NVIDIA RTX 4060 ~65W durante ráfaga), mientras que Gemini refleja únicamente el consumo directo de tokens de la API de Google Cloud.
        </span>
      </div>
    </div>
  );
};
