import React from 'react';
import {
  Cpu,
  Cloud,
  CheckCircle2,
  XCircle,
  Clock,
  Coins,
  AlertTriangle,
  Users,
  HeartPulse,
  Scale,
  Zap,
} from 'lucide-react';
import type { ModelTriageResult, Severidad } from '../types/triage';

interface ComparisonCardsProps {
  clefResult?: ModelTriageResult | null;
  geminiResult?: ModelTriageResult | null;
  discrepancyDetected?: boolean;
}

const SEVERITY_CONFIG: Record<Severidad, { label: string; bg: string; text: string; border: string }> = {
  1: { label: 'P1 - Crítico (< 2h)', bg: 'bg-red-950/40', text: 'text-red-400', border: 'border-red-500/40' },
  2: { label: 'P2 - Alto (< 6h)', bg: 'bg-amber-950/40', text: 'text-amber-400', border: 'border-amber-500/40' },
  3: { label: 'P3 - Medio (< 24h)', bg: 'bg-yellow-950/40', text: 'text-yellow-400', border: 'border-yellow-500/40' },
  4: { label: 'P4 - Bajo (< 48h)', bg: 'bg-emerald-950/40', text: 'text-emerald-400', border: 'border-emerald-500/40' },
};

export const ComparisonCards: React.FC<ComparisonCardsProps> = ({
  clefResult,
  geminiResult,
  discrepancyDetected = false,
}) => {
  return (
    <div className="space-y-3">
      {/* Discrepancy indicator banner */}
      {discrepancyDetected && (
        <div className="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-amber-950/30 border border-amber-500/40 text-amber-300 text-xs shadow-sm">
          <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0" />
          <span className="font-medium">
            Discrepancia Actuarial Detectada: Los modelos discrepan en el Macro-Ramo o nivel de Severidad. Se recomienda arbitraje por perito humano.
          </span>
        </div>
      )}

      {/* Two-column mirror layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Clef-Flash Card (System 1) */}
        <ModelCard
          title="Clef-Flash"
          subtitle="System 1 Local (Joint Schema Head 4-bit)"
          systemType="SYSTEM 1 • EDGE"
          icon={<Cpu className="w-4 h-4 text-emerald-400" />}
          accentColor="emerald"
          result={clefResult}
          isLocal={true}
        />

        {/* Gemini 2.5 Flash Card (System 2) */}
        <ModelCard
          title="Gemini 2.5 Flash"
          subtitle="System 2 Cloud (Google AI Studio LLM)"
          systemType="SYSTEM 2 • CLOUD"
          icon={<Cloud className="w-4 h-4 text-sky-400" />}
          accentColor="sky"
          result={geminiResult}
          isLocal={false}
        />
      </div>
    </div>
  );
};

interface ModelCardProps {
  title: string;
  subtitle: string;
  systemType: string;
  icon: React.ReactNode;
  accentColor: 'emerald' | 'sky';
  result?: ModelTriageResult | null;
  isLocal: boolean;
}

const ModelCard: React.FC<ModelCardProps> = ({
  title,
  subtitle,
  systemType,
  icon,
  accentColor,
  result,
  isLocal,
}) => {
  const isEmerald = accentColor === 'emerald';
  const cardBorder = isEmerald ? 'border-emerald-500/20 hover:border-emerald-500/40' : 'border-sky-500/20 hover:border-sky-500/40';
  const headerBg = isEmerald ? 'bg-emerald-950/20' : 'bg-sky-950/20';

  if (!result) {
    return (
      <div className={`bg-zinc-900/60 border ${cardBorder} rounded-xl p-6 flex flex-col items-center justify-center min-h-[300px] text-center transition-all`}>
        <div className="w-10 h-10 rounded-full bg-zinc-800/80 flex items-center justify-center text-zinc-500 mb-3">
          {icon}
        </div>
        <h4 className="text-sm font-semibold text-zinc-300">{title}</h4>
        <p className="text-xs text-zinc-500 mt-1 max-w-xs">{subtitle}</p>
        <span className="text-[11px] font-mono mt-4 px-2.5 py-1 rounded bg-zinc-800/60 text-zinc-400">
          En espera de siniestro para evaluar
        </span>
      </div>
    );
  }

  const decision = result.decision;
  const metrics = result.metrics;
  const sevConfig = decision ? SEVERITY_CONFIG[decision.severidad] : null;

  return (
    <div className={`bg-zinc-900/90 border ${cardBorder} rounded-xl overflow-hidden shadow-lg flex flex-col justify-between transition-all backdrop-blur-sm`}>
      {/* Card Header */}
      <div className={`p-4 border-b border-zinc-800/80 ${headerBg} flex items-center justify-between`}>
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-zinc-900 border border-zinc-700/60 flex items-center justify-center shadow-sm">
            {icon}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h4 className="text-sm font-bold text-white tracking-tight">{title}</h4>
              <span className={`text-[10px] font-mono px-2 py-0.5 rounded border ${isEmerald ? 'bg-emerald-950/60 text-emerald-300 border-emerald-500/30' : 'bg-sky-950/60 text-sky-300 border-sky-500/30'}`}>
                {systemType}
              </span>
            </div>
            <p className="text-[11px] text-zinc-400">{subtitle}</p>
          </div>
        </div>

        {/* Status Pill */}
        <div className="flex items-center gap-1.5 text-xs">
          {result.success ? (
            <span className="flex items-center gap-1 text-emerald-400 font-medium text-xs bg-emerald-950/40 border border-emerald-500/30 px-2 py-1 rounded-md">
              <CheckCircle2 className="w-3.5 h-3.5" />
              Esquema Válido
            </span>
          ) : (
            <span className="flex items-center gap-1 text-red-400 font-medium text-xs bg-red-950/40 border border-red-500/30 px-2 py-1 rounded-md">
              <XCircle className="w-3.5 h-3.5" />
              Falla
            </span>
          )}
        </div>
      </div>

      {/* Card Body: Decision Details */}
      <div className="p-4 space-y-3.5 flex-1 text-xs">
        {result.error_message ? (
          <div className="p-3 rounded-lg bg-red-950/30 border border-red-500/30 text-red-300">
            <span className="font-semibold block mb-1">Error de inferencia:</span>
            <code className="text-[11px] break-all">{result.error_message}</code>
          </div>
        ) : decision ? (
          <>
            {/* Actuarial taxonomy grid */}
            <div className="grid grid-cols-2 gap-2.5">
              <div className="p-2.5 rounded-lg bg-zinc-950/60 border border-zinc-800/80">
                <span className="text-[10px] text-zinc-500 uppercase tracking-wider block font-semibold mb-1">
                  Macro-Ramo
                </span>
                <span className="font-semibold text-zinc-200 font-mono text-[13px]">
                  {decision.macro_ramo}
                </span>
              </div>

              <div className="p-2.5 rounded-lg bg-zinc-950/60 border border-zinc-800/80">
                <span className="text-[10px] text-zinc-500 uppercase tracking-wider block font-semibold mb-1">
                  Ramo Específico
                </span>
                <span className="font-semibold text-zinc-200 truncate block text-[12px]" title={decision.ramo_especifico}>
                  {decision.ramo_especifico}
                </span>
              </div>
            </div>

            {/* Secondary Branch if MIXTO */}
            {decision.ramo_secundario && (
              <div className="p-2 rounded-lg bg-purple-950/20 border border-purple-500/30 flex items-center justify-between text-purple-200">
                <span className="text-[11px] font-medium">Ramo Secundario (MIXTO):</span>
                <span className="font-mono text-xs font-semibold">{decision.ramo_secundario}</span>
              </div>
            )}

            {/* Severity Pill */}
            {sevConfig && (
              <div className="flex items-center justify-between p-2.5 rounded-lg bg-zinc-950/60 border border-zinc-800/80">
                <span className="text-zinc-400 font-medium">Severidad y SLA:</span>
                <span className={`px-2.5 py-1 rounded-md text-xs font-semibold border ${sevConfig.bg} ${sevConfig.text} ${sevConfig.border}`}>
                  {sevConfig.label}
                </span>
              </div>
            )}

            {/* Regulatory flags */}
            <div className="flex flex-wrap gap-2 pt-1">
              <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md border text-[11px] font-medium ${decision.involucra_terceros ? 'bg-amber-950/30 text-amber-300 border-amber-500/30' : 'bg-zinc-800/40 text-zinc-400 border-zinc-700/40'}`}>
                <Users className="w-3 h-3" />
                {decision.involucra_terceros ? 'Involucra Terceros' : 'Sin Terceros'}
              </span>

              <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md border text-[11px] font-medium ${decision.indicio_lesiones_corporales ? 'bg-red-950/30 text-red-300 border-red-500/30' : 'bg-zinc-800/40 text-zinc-400 border-zinc-700/40'}`}>
                <HeartPulse className="w-3 h-3" />
                {decision.indicio_lesiones_corporales ? 'Lesiones Corporales' : 'Sin Lesiones'}
              </span>

              {decision.requiere_revision_pericial && (
                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md border text-[11px] font-medium bg-purple-950/30 text-purple-300 border-purple-500/30">
                  <Scale className="w-3 h-3" />
                  Revisión Pericial
                </span>
              )}
            </div>
          </>
        ) : null}
      </div>

      {/* Card Footer: Telemetry & Economics */}
      <div className="p-3.5 bg-zinc-950/80 border-t border-zinc-800/80 grid grid-cols-3 gap-2 text-center text-xs">
        {/* Latency */}
        <div className="p-1.5 rounded bg-zinc-900/60 border border-zinc-800/60">
          <span className="text-[10px] text-zinc-500 block flex items-center justify-center gap-1">
            <Clock className="w-3 h-3" />
            Latencia
          </span>
          <span className="font-mono font-bold text-white text-xs">
            {metrics ? `${metrics.latency_ms.toFixed(1)} ms` : '--'}
          </span>
        </div>

        {/* Tokens / Execution */}
        <div className="p-1.5 rounded bg-zinc-900/60 border border-zinc-800/60">
          <span className="text-[10px] text-zinc-500 block flex items-center justify-center gap-1">
            <Zap className="w-3 h-3" />
            Tokens
          </span>
          <span className="font-mono font-semibold text-zinc-300 text-xs truncate" title={isLocal ? '0 tokens (Forward Pass)' : `${metrics?.total_tokens} tokens`}>
            {isLocal ? '0 (Direct)' : `${metrics?.total_tokens || 0}`}
          </span>
        </div>

        {/* Cost */}
        <div className="p-1.5 rounded bg-zinc-900/60 border border-zinc-800/60">
          <span className="text-[10px] text-zinc-500 block flex items-center justify-center gap-1">
            <Coins className="w-3 h-3" />
            Costo Unit.
          </span>
          <span className={`font-mono font-bold text-xs ${isLocal ? 'text-emerald-400' : 'text-sky-400'}`}>
            {isLocal ? '$0.00' : `$${(metrics?.estimated_cost_usd || 0).toFixed(5)}`}
          </span>
        </div>
      </div>
    </div>
  );
};
