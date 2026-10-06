import React, { useState } from 'react';
import { Ticket, Link2, Clock, AlertCircle, Layers, Tag, ArrowRight } from 'lucide-react';
import type { JiraIssuePayload, JiraTicketSet } from '../types/triage';

interface JiraPreviewProps {
  clefTicketSet?: JiraTicketSet | null;
  geminiTicketSet?: JiraTicketSet | null;
}

export const JiraPreview: React.FC<JiraPreviewProps> = ({
  clefTicketSet,
  geminiTicketSet,
}) => {
  const [activeTab, setActiveTab] = useState<'clef' | 'gemini'>('clef');

  const currentSet = activeTab === 'clef' ? clefTicketSet : geminiTicketSet;

  if (!clefTicketSet && !geminiTicketSet) {
    return (
      <div className="bg-zinc-900/90 border border-zinc-800 rounded-xl p-5 shadow-lg backdrop-blur-sm">
        <div className="flex items-center gap-2 mb-3">
          <Ticket className="w-4 h-4 text-emerald-400" />
          <h3 className="text-sm font-semibold text-zinc-200">
            Jira Service Management Ticket Generation
          </h3>
        </div>
        <div className="p-8 border border-dashed border-zinc-800 rounded-lg text-center text-xs text-zinc-500">
          Envíe un siniestro para previsualizar los tickets automatizados que se generarán en Jira.
        </div>
      </div>
    );
  }

  return (
    <div className="bg-zinc-900/90 border border-zinc-800 rounded-xl p-5 shadow-lg backdrop-blur-sm space-y-4">
      {/* Header with model switch tabs */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-zinc-800 pb-3">
        <div className="flex items-center gap-2">
          <Ticket className="w-4 h-4 text-emerald-400" />
          <h3 className="text-sm font-semibold text-white">
            Tickets Generados para Jira Service Management
          </h3>
        </div>

        {/* Tab switcher */}
        <div className="flex items-center p-1 bg-zinc-950 rounded-lg border border-zinc-800 text-xs">
          <button
            type="button"
            onClick={() => setActiveTab('clef')}
            className={`px-3 py-1 rounded-md font-medium transition-all ${
              activeTab === 'clef'
                ? 'bg-emerald-600 text-white shadow-sm'
                : 'text-zinc-400 hover:text-zinc-200'
            }`}
          >
            Payload Clef-Flash
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('gemini')}
            className={`px-3 py-1 rounded-md font-medium transition-all ${
              activeTab === 'gemini'
                ? 'bg-sky-600 text-white shadow-sm'
                : 'text-zinc-400 hover:text-zinc-200'
            }`}
          >
            Payload Gemini Flash
          </button>
        </div>
      </div>

      {/* Render Current Ticket Set */}
      {currentSet ? (
        <div className="space-y-3">
          {currentSet.is_dual_ticket && (
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-indigo-950/40 border border-indigo-500/40 text-indigo-300 text-xs">
              <Layers className="w-4 h-4 text-indigo-400 flex-shrink-0" />
              <span>
                <strong>Doble Ticket Vinculado:</strong> Siniestro crítico/mixto genera tickets paralelos (Patrimonial + Personas).
              </span>
            </div>
          )}

          {/* Ticket Cards Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
            <TicketCard
              badgeLabel="Ticket Principal"
              badgeColor="emerald"
              ticket={currentSet.primary_ticket}
            />

            {currentSet.secondary_ticket && (
              <TicketCard
                badgeLabel="Ticket Secundario (Vinculado)"
                badgeColor="purple"
                ticket={currentSet.secondary_ticket}
              />
            )}
          </div>
        </div>
      ) : (
        <div className="p-6 text-center text-xs text-zinc-500">
          No hay tickets disponibles para este modelo en la evaluación actual.
        </div>
      )}
    </div>
  );
};

interface TicketCardProps {
  badgeLabel: string;
  badgeColor: 'emerald' | 'purple';
  ticket: JiraIssuePayload;
}

const TicketCard: React.FC<TicketCardProps> = ({ badgeLabel, badgeColor, ticket }) => {
  const isEmerald = badgeColor === 'emerald';

  return (
    <div className="p-4 rounded-lg bg-zinc-950/70 border border-zinc-800 flex flex-col justify-between space-y-3 shadow-inner">
      {/* Top Header */}
      <div className="flex items-center justify-between gap-2">
        <span
          className={`text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded border ${
            isEmerald
              ? 'bg-emerald-950/60 text-emerald-300 border-emerald-500/30'
              : 'bg-purple-950/60 text-purple-300 border-purple-500/30'
          }`}
        >
          {badgeLabel}
        </span>
        <span className="font-mono text-xs text-zinc-400 font-medium">
          {ticket.project_key} • {ticket.issue_type}
        </span>
      </div>

      {/* Summary */}
      <div>
        <h5 className="text-xs font-semibold text-zinc-200 line-clamp-2 leading-snug">
          {ticket.summary}
        </h5>
        {ticket.description && (
          <p className="text-[11px] text-zinc-500 line-clamp-2 mt-1 italic">
            &ldquo;{ticket.description}&rdquo;
          </p>
        )}
      </div>

      {/* Meta Pills (Priority, SLA, Components) */}
      <div className="pt-2 border-t border-zinc-800/80 flex flex-wrap items-center gap-2 text-[11px]">
        {/* Priority */}
        <span className="px-2 py-0.5 rounded bg-zinc-900 border border-zinc-800 text-zinc-300 font-medium flex items-center gap-1">
          <AlertCircle className="w-3 h-3 text-amber-400" />
          {ticket.priority}
        </span>

        {/* SLA */}
        <span className="px-2 py-0.5 rounded bg-zinc-900 border border-zinc-800 text-emerald-400 font-mono font-medium flex items-center gap-1">
          <Clock className="w-3 h-3 text-emerald-400" />
          SLA: &lt; {ticket.sla_hours}h
        </span>

        {/* Components */}
        {ticket.components.map((comp) => (
          <span
            key={comp}
            className="px-2 py-0.5 rounded bg-zinc-900 border border-zinc-800 text-zinc-400 flex items-center gap-1 font-mono text-[10px]"
          >
            <Tag className="w-2.5 h-2.5" />
            {comp}
          </span>
        ))}
      </div>

      {/* Linked Issues */}
      {ticket.linked_issues && ticket.linked_issues.length > 0 && (
        <div className="pt-1.5 flex items-center gap-1.5 text-[10px] text-indigo-400 font-mono">
          <Link2 className="w-3 h-3" />
          <span>Enlazado con:</span>
          {ticket.linked_issues.map((link) => (
            <span key={link} className="underline flex items-center gap-0.5">
              {link}
              <ArrowRight className="w-2.5 h-2.5 inline" />
            </span>
          ))}
        </div>
      )}
    </div>
  );
};
