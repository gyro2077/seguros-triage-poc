import React, { useState } from 'react';
import { Send, FileText, Sparkles, AlertCircle, RefreshCw } from 'lucide-react';

export interface ClaimTemplate {
  id: string;
  title: string;
  badge: string;
  text: string;
}

export const CLAIM_TEMPLATES: ClaimTemplate[] = [
  {
    id: 'grua-mixto',
    title: 'Colapso grúa mixto',
    badge: 'MIXTO / P1',
    text: 'Durante trabajos de izaje en la construcción del viaducto en la Av. Simón Bolívar (Quito), una grúa telescópica de 45 toneladas sufrió el colapso de su pluma principal. La estructura cayó sobre dos vehículos de terceros estacionados y causó heridas graves con politraumatismo al operador y a un obrero cercano, quienes fueron evacuados de urgencia al Hospital Eugenio Espejo.',
  },
  {
    id: 'choque-leve',
    title: 'Choque vehicular leve',
    badge: 'VEHICULOS / P4',
    text: 'Colisión por alcance a baja velocidad en el sector La Pradera, Guayaquil. El vehículo asegurado rozó el guardafango posterior de un sedán particular en el semáforo. Únicamente se evidencia raspón superficial de pintura y hendidura menor sin personas lesionadas ni activación de airbags.',
  },
  {
    id: 'incendio-fabrica',
    title: 'Incendio en fábrica',
    badge: 'INCENDIO / P2',
    text: 'Conato de incendio originado por cortocircuito en el área de bodega de empaques en la zona industrial de Durán. El fuego consumió palets de cartón y dañó la cubierta de láminas galvanizadas antes de ser controlado por los bomberos. No se registraron trabajadores asfixiados ni quemados, pero el inventario de materiales quedó inutilizado.',
  },
  {
    id: 'gastos-medicos',
    title: 'Gastos médicos ambulatorios',
    badge: 'SALUD / P3',
    text: 'El asegurado afiliado a la póliza corporativa de salud presentó cuadro de cólico vesicular agudo, acudiendo por emergencia al Hospital Metropolitano en Quito. Se realizaron exámenes de laboratorio, ecografía abdominal y medicación intravenosa para estabilización, solicitando reembolso de cobertura de gastos ambulatorios.',
  },
];

interface ClaimInputProps {
  onSubmit: (incidentText: string) => void;
  isLoading?: boolean;
}

export const ClaimInput: React.FC<ClaimInputProps> = ({ onSubmit, isLoading = false }) => {
  const [incidentText, setIncidentText] = useState<string>(CLAIM_TEMPLATES[0].text);
  const [selectedTemplateId, setSelectedTemplateId] = useState<string>(CLAIM_TEMPLATES[0].id);

  const handleSelectTemplate = (template: ClaimTemplate) => {
    setSelectedTemplateId(template.id);
    setIncidentText(template.text);
  };

  const handleTextChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setIncidentText(e.target.value);
    setSelectedTemplateId('');
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (incidentText.trim().length >= 15 && !isLoading) {
      onSubmit(incidentText.trim());
    }
  };

  const isTextTooShort = incidentText.trim().length < 15;

  return (
    <div className="bg-zinc-900/90 border border-zinc-800 rounded-xl p-5 shadow-lg backdrop-blur-sm">
      {/* Template selector pills */}
      <div className="mb-4">
        <div className="flex items-center gap-2 mb-2.5">
          <Sparkles className="w-4 h-4 text-emerald-400" />
          <span className="text-xs font-semibold uppercase tracking-wider text-zinc-300">
            Plantillas de Siniestros Ecuatorianos
          </span>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2">
          {CLAIM_TEMPLATES.map((tmpl) => {
            const isSelected = selectedTemplateId === tmpl.id;
            return (
              <button
                key={tmpl.id}
                type="button"
                onClick={() => handleSelectTemplate(tmpl)}
                className={`text-left p-2.5 rounded-lg border transition-all text-xs flex flex-col justify-between gap-1.5 ${
                  isSelected
                    ? 'bg-emerald-950/40 border-emerald-500/50 text-emerald-200 shadow-sm shadow-emerald-950'
                    : 'bg-zinc-950/60 border-zinc-800 hover:border-zinc-700 text-zinc-400 hover:text-zinc-200'
                }`}
              >
                <span className="font-medium truncate">{tmpl.title}</span>
                <span className="text-[10px] font-mono px-1.5 py-0.5 rounded w-fit bg-zinc-800/80 text-zinc-300">
                  {tmpl.badge}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Narrative input form */}
      <form onSubmit={handleSubmit} className="space-y-3">
        <div className="flex items-center justify-between">
          <label htmlFor="claim-narrative" className="text-xs font-medium text-zinc-400 flex items-center gap-1.5">
            <FileText className="w-3.5 h-3.5 text-zinc-400" />
            Relato del Siniestro (Entrada no estructurada)
          </label>
          <span className={`text-[11px] font-mono ${isTextTooShort ? 'text-amber-400' : 'text-zinc-500'}`}>
            {incidentText.trim().length} caracteres (mín. 15)
          </span>
        </div>

        <textarea
          id="claim-narrative"
          value={incidentText}
          onChange={handleTextChange}
          rows={4}
          placeholder="Escriba o pegue la descripción detallada del siniestro a evaluar..."
          className="w-full bg-zinc-950 border border-zinc-800 focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 rounded-lg p-3 text-sm text-zinc-100 placeholder-zinc-600 outline-none transition-colors font-sans leading-relaxed resize-y"
        />

        {isTextTooShort && (
          <div className="flex items-center gap-1.5 text-amber-400 text-xs">
            <AlertCircle className="w-3.5 h-3.5 flex-shrink-0" />
            <span>El relato debe contener al menos 15 caracteres para evaluar la consistencia actuarial.</span>
          </div>
        )}

        {/* Action bar */}
        <div className="flex items-center justify-end gap-3 pt-1">
          <button
            type="button"
            onClick={() => handleSelectTemplate(CLAIM_TEMPLATES[0])}
            disabled={isLoading}
            className="px-3 py-2 rounded-lg text-xs font-medium text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/60 transition-colors flex items-center gap-1.5 border border-transparent"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Restablecer
          </button>

          <button
            type="submit"
            disabled={isTextTooShort || isLoading}
            className="px-5 py-2.5 rounded-lg text-xs font-semibold text-white bg-emerald-600 hover:bg-emerald-500 active:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-md shadow-emerald-950 flex items-center gap-2 cursor-pointer"
          >
            {isLoading ? (
              <>
                <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                <span>Ejecutando Triage Dual...</span>
              </>
            ) : (
              <>
                <Send className="w-3.5 h-3.5" />
                <span>Ejecutar Triage Comparativo (Clef vs Gemini)</span>
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};
