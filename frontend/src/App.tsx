import React, { useState, useEffect, useCallback } from 'react';
import { Header } from './components/Header';
import { ClaimInput } from './components/ClaimInput';
import { ComparisonCards } from './components/ComparisonCards';
import { JiraPreview } from './components/JiraPreview';
import { CostAnalysis } from './components/CostAnalysis';
import type { TriageComparisonResponse, HealthResponse } from './types/triage';

export const App: React.FC = () => {
  const [comparison, setComparison] = useState<TriageComparisonResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchHealth = useCallback(async () => {
    try {
      const res = await fetch('/api/health');
      if (res.ok) {
        const data: HealthResponse = await res.json();
        setHealth(data);
      }
    } catch {
      // Backend not running or unreachable
      setHealth((prev) =>
        prev
          ? { ...prev, status: 'offline' }
          : {
              status: 'offline',
              gpu_available: true,
              gpu_name: 'NVIDIA GeForce RTX 4060 Laptop GPU',
              clef_loaded: false,
              gemini_model: 'gemini-2.5-flash',
            }
      );
    }
  }, []);

  useEffect(() => {
    fetchHealth();
    const interval = setInterval(fetchHealth, 10000);
    return () => clearInterval(interval);
  }, [fetchHealth]);

  const handleCompare = async (incidentText: string) => {
    if (incidentText.trim().length < 15) {
      setError('El relato del siniestro debe contener al menos 15 caracteres.');
      return;
    }

    setIsLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/triage/compare', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ incident_text: incidentText.trim() }),
      });
      if (!res.ok) {
        let msg = `Error en el servidor (${res.status})`;
        try {
          const errData = await res.json();
          if (errData.detail) {
            msg = typeof errData.detail === 'string' ? errData.detail : JSON.stringify(errData.detail);
          }
        } catch {
          // fallback to statusText
          msg = `${msg}: ${res.statusText}`;
        }
        throw new Error(msg);
      }
      const data: TriageComparisonResponse = await res.json();
      setComparison(data);
      // Refresh health to reflect Clef model loaded status
      fetchHealth();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Error al comunicarse con el backend de inferencia.'
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#090a0f] text-zinc-100 flex flex-col font-sans">
      <Header health={health} />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 py-6 space-y-6">
        {error && (
          <div className="p-3.5 rounded-lg bg-red-950/40 border border-red-500/40 text-red-300 text-xs flex items-center justify-between shadow-sm">
            <span>{error}</span>
            <button
              type="button"
              onClick={() => setError(null)}
              className="text-zinc-400 hover:text-white underline text-[11px] cursor-pointer"
            >
              Cerrar
            </button>
          </div>
        )}

        {/* Claim Input Form */}
        <section aria-label="Ingreso de Siniestro">
          <ClaimInput onSubmit={handleCompare} isLoading={isLoading} />
        </section>

        {/* Parallel Inference Comparison */}
        <section aria-label="Comparativa de Modelos">
          <ComparisonCards
            clefResult={comparison?.clef_result}
            geminiResult={comparison?.gemini_result}
            discrepancyDetected={comparison?.discrepancy_detected}
            isLoading={isLoading}
          />
        </section>

        {/* Jira Tickets Generation Preview */}
        <section aria-label="Tickets de Jira Service Management">
          <JiraPreview
            clefTicketSet={comparison?.clef_result?.jira_tickets}
            geminiTicketSet={comparison?.gemini_result?.jira_tickets}
          />
        </section>

        {/* Cost Analysis & Projection */}
        <section aria-label="Análisis Actuarial de Costos">
          <CostAnalysis
            costDelta100k={comparison?.cost_delta_projected_100k_usd}
            unitCostGemini={comparison?.gemini_result?.metrics?.estimated_cost_usd}
          />
        </section>
      </main>

      <footer className="border-t border-zinc-900 bg-zinc-950/50 py-4 text-center text-xs text-zinc-600">
        <span>Seguros Triage AI Engine • PoC Actuarial Clef vs Gemini • Arquitectura Desacoplada</span>
      </footer>
    </div>
  );
};

export default App;
