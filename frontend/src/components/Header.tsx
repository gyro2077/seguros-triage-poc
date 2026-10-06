import React from 'react';
import { Cpu, Cloud, ShieldCheck, Activity } from 'lucide-react';
import type { HealthResponse } from '../types/triage';

interface HeaderProps {
  health?: HealthResponse | null;
}

export const Header: React.FC<HeaderProps> = ({ health }) => {
  return (
    <header className="border-b border-zinc-800 bg-zinc-950/70 backdrop-blur-md sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-3.5 flex flex-col md:flex-row items-center justify-between gap-4">
        {/* Brand / Logo */}
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400 shadow-sm shadow-emerald-500/10">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-semibold text-base tracking-tight text-white">
                Seguros Triage Engine
              </span>
              <span className="text-[10px] font-medium tracking-wide uppercase px-2 py-0.5 rounded-full bg-zinc-800 text-zinc-300 border border-zinc-700">
                PoC Benchmark
              </span>
            </div>
            <p className="text-xs text-zinc-400">
              Decisión Actuarial: System 1 (Clef-Flash Local) vs System 2 (Gemini Cloud)
            </p>
          </div>
        </div>

        {/* Infrastructure telemetry pills */}
        <div className="flex flex-wrap items-center gap-2 sm:gap-3 text-xs">
          {/* Local GPU Badge */}
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-zinc-900 border border-zinc-800 text-zinc-300">
            <Cpu className="w-3.5 h-3.5 text-emerald-400" />
            <div className="flex items-center gap-1.5">
              <span className="font-medium text-zinc-200">RTX 4060 (8GB)</span>
              <span className="text-zinc-500">•</span>
              <span className="text-emerald-400 font-mono text-[11px]">Clef-Flash 4-bit</span>
            </div>
          </div>

          {/* Cloud Model Badge */}
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-zinc-900 border border-zinc-800 text-zinc-300">
            <Cloud className="w-3.5 h-3.5 text-sky-400" />
            <div className="flex items-center gap-1.5">
              <span className="font-medium text-zinc-200">AI Studio</span>
              <span className="text-zinc-500">•</span>
              <span className="text-sky-400 font-mono text-[11px]">
                {health?.gemini_model || 'gemini-2.5-flash'}
              </span>
            </div>
          </div>

          {/* Connection status */}
          <div className="flex items-center gap-2 px-2.5 py-1.5 rounded-lg bg-zinc-900/80 border border-zinc-800">
            <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-[11px] font-medium text-zinc-300 flex items-center gap-1">
              <Activity className="w-3 h-3 text-zinc-400" />
              {health?.status === 'ok' ? 'Online' : 'Conectando'}
            </span>
          </div>
        </div>
      </div>
    </header>
  );
};
