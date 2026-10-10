import { type FormEvent, useEffect, useRef } from 'react';
import {
  AlertTriangle,
  Bot,
  Compass,
  MessageSquare,
  Send,
  ShieldCheck,
  Sparkles,
  User,
  Zap,
} from 'lucide-react';
import type { BusMove, Festival, ForecastResponse, OptimizeResponse } from '../types/nila';

interface AskNilaProps {
  festival: Festival;
  forecast: ForecastResponse;
  optimization: OptimizeResponse;
  chatMessages: Array<{ role: 'user' | 'assistant'; text: string; source?: 'api' | 'demo' }>;
  chatLoading: boolean;
  chatError: string;
  chatInput: string;
  onChatInputChange: (value: string) => void;
  onSubmitQuestion: (question: string) => void;
}

const SUGGESTED_QUERIES = [
  'Why is Periyar Bus Stand flagged as critical risk?',
  'Why reassign buses specifically from Mattuthavani rather than Aarapalayam?',
  'What is the service trade-off for pilgrims at the source terminal?',
  'How will a 20% attendance surge affect passenger wait times?',
  'What are the departure and arrival schedules for repositioned buses?',
];

export default function AskNila({
  festival,
  forecast,
  optimization,
  chatMessages,
  chatLoading,
  chatError,
  chatInput,
  onChatInputChange,
  onSubmitQuestion,
}: AskNilaProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const activeMove: BusMove = optimization.move;

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages, chatLoading]);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (chatInput.trim() && !chatLoading) {
      onSubmitQuestion(chatInput.trim());
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white border border-sky-200 rounded-2xl p-6 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="text-[11px] font-bold uppercase tracking-wider text-sky-700 flex items-center gap-1.5">
            <Sparkles size={14} className="text-sky-600" /> Natural Language Operational Audit Layer
          </div>
          <h2 className="text-xl font-black text-slate-900 mt-1 flex items-center gap-2">
            ASK NILA — AI Mobility Copilot
            <span className="text-xs px-2.5 py-0.5 rounded-full font-bold bg-sky-100 text-sky-800 border border-sky-200">
              Gemini Powered
            </span>
          </h2>
          <p className="text-xs text-slate-600 mt-1">
            Query crowd surge triggers, justify vehicle repositioning schedules, and audit service trade-offs in plain language.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="px-3 py-1.5 rounded-full text-xs font-bold bg-sky-50 text-sky-800 border border-sky-200 flex items-center gap-1.5">
            <Bot size={15} /> Context: {festival.name}
          </span>
        </div>
      </div>

      {/* Main Grid: Chat Window & Context Rail */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column (8 cols): Conversational Window */}
        <div className="lg:col-span-8 bg-white border border-sky-100 rounded-2xl shadow-sm flex flex-col h-[600px] overflow-hidden">
          {/* Messages Area */}
          <div className="flex-1 overflow-y-auto p-5 space-y-4 bg-slate-50/40">
            {chatMessages.map((msg, index) => {
              const isAssistant = msg.role === 'assistant';
              return (
                <div
                  key={`${msg.role}-${index}`}
                  className={`flex gap-3 max-w-[88%] ${
                    isAssistant ? 'self-start mr-auto' : 'self-end ml-auto flex-row-reverse'
                  }`}
                >
                  <div
                    className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 shadow-sm ${
                      isAssistant
                        ? 'bg-sky-600 text-white'
                        : 'bg-slate-800 text-slate-100'
                    }`}
                  >
                    {isAssistant ? <Sparkles size={16} /> : <User size={16} />}
                  </div>

                  <div className="space-y-1">
                    <div
                      className={`flex items-center gap-2 text-[11px] font-bold ${
                        isAssistant ? 'text-sky-800' : 'text-slate-600 justify-end'
                      }`}
                    >
                      <span>{isAssistant ? 'NILA AI Copilot' : 'Transport Operator'}</span>
                      {msg.source === 'demo' && (
                        <span className="text-[10px] font-normal px-1.5 py-0.2 rounded bg-amber-50 text-amber-700 border border-amber-200">
                          Demo Preview
                        </span>
                      )}
                    </div>

                    <div
                      className={`p-4 rounded-2xl text-xs leading-relaxed shadow-sm ${
                        isAssistant
                          ? 'bg-white text-slate-800 border border-sky-100 rounded-tl-sm'
                          : 'bg-sky-600 text-white rounded-tr-sm'
                      }`}
                    >
                      {msg.text}
                    </div>
                  </div>
                </div>
              );
            })}

            {chatLoading && (
              <div className="flex gap-3 max-w-[85%] self-start mr-auto">
                <div className="w-8 h-8 rounded-xl bg-sky-600 text-white flex items-center justify-center shrink-0 shadow-sm">
                  <Sparkles size={16} />
                </div>
                <div className="p-4 rounded-2xl bg-white text-slate-800 border border-sky-100 text-xs flex items-center gap-2 shadow-sm">
                  <span className="spinner spinner-small" /> NILA is reasoning through the fixed-fleet constraint model…
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Error Notice */}
          {chatError && (
            <div className="px-5 py-2 bg-amber-50 border-t border-amber-200 text-xs text-amber-900 flex items-center gap-2">
              <AlertTriangle size={14} className="text-amber-600 shrink-0" />
              <span>{chatError}</span>
            </div>
          )}

          {/* Quick Query Pills */}
          <div className="p-3 bg-white border-t border-slate-100 flex items-center gap-2 overflow-x-auto">
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider shrink-0 flex items-center gap-1">
              <MessageSquare size={12} /> Prompts:
            </span>
            <div className="flex gap-1.5 shrink-0">
              {SUGGESTED_QUERIES.map((q) => (
                <button
                  key={q}
                  onClick={() => onSubmitQuestion(q)}
                  disabled={chatLoading}
                  className="px-3 py-1.5 bg-slate-50 hover:bg-sky-50 text-slate-700 hover:text-sky-800 rounded-xl text-[11px] font-semibold border border-slate-200 transition-colors whitespace-nowrap"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>

          {/* Composer Form */}
          <form
            onSubmit={handleSubmit}
            className="p-3 bg-white border-t border-slate-200 flex items-center gap-2"
          >
            <input
              type="text"
              value={chatInput}
              onChange={(e) => onChatInputChange(e.target.value)}
              placeholder="Ask NILA about crowd predictions, trade-offs, or fixed fleet reassignments…"
              className="flex-1 bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 text-xs font-medium text-slate-900 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:bg-white"
              disabled={chatLoading}
            />
            <button
              type="submit"
              disabled={!chatInput.trim() || chatLoading}
              className="px-5 py-3 bg-sky-600 hover:bg-sky-700 disabled:opacity-50 text-white rounded-xl text-xs font-bold flex items-center gap-1.5 shadow-sm transition-all shrink-0"
            >
              <Send size={15} /> Send
            </button>
          </form>
        </div>

        {/* Right Column (4 cols): Active Operational Context Grounding Rail */}
        <div className="lg:col-span-4 space-y-4">
          <div className="bg-white border border-sky-100 rounded-2xl p-5 shadow-sm space-y-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700 flex items-center gap-2">
              <Bot size={16} className="text-sky-600" />
              Operational Grounding Context
            </h4>
            <p className="text-xs text-slate-500">
              Copilot explanations are directly bound to the mathematical model's current state:
            </p>

            <div className="space-y-2.5 pt-2">
              <div className="p-3 bg-sky-50/70 rounded-xl border border-sky-100">
                <div className="text-[11px] font-bold text-sky-800 uppercase flex items-center gap-1">
                  <Compass size={12} /> Active Festival Context
                </div>
                <div className="text-xs font-bold text-slate-900 mt-0.5">{festival.name}</div>
                <div className="text-[11px] text-slate-500">
                  {festival.city} · Peak {festival.peakTime}
                </div>
              </div>

              <div className="p-3 bg-sky-50/70 rounded-xl border border-sky-100">
                <div className="text-[11px] font-bold text-sky-800 uppercase flex items-center gap-1">
                  <Zap size={12} /> Active Bus Move
                </div>
                <div className="text-xs font-bold text-slate-900 mt-0.5">
                  Shift {activeMove.buses} buses to {activeMove.destinationStop}
                </div>
                <div className="text-[11px] text-slate-500">
                  Origin: {activeMove.sourceStop} · Transit: {activeMove.travelMinutes}m
                </div>
              </div>

              <div className="p-3 bg-sky-50/70 rounded-xl border border-sky-100">
                <div className="text-[11px] font-bold text-sky-800 uppercase flex items-center gap-1">
                  <ShieldCheck size={12} /> Fleet Conservation Invariant
                </div>
                <div className="text-xs font-bold text-slate-900 mt-0.5">Enforced: True</div>
                <div className="text-[11px] text-slate-500">
                  Zero net vehicle creation · {forecast.stops.length} stops monitored
                </div>
              </div>
            </div>
          </div>

          <div className="p-4 bg-gradient-to-br from-sky-50 to-white border border-sky-200 rounded-2xl text-xs text-slate-600 space-y-1.5 shadow-sm">
            <strong className="text-sky-900 block font-bold">Why Ask NILA?</strong>
            <p>
              Unlike generic AI chatbots, NILA acts as an operator audit layer, explaining the <em>why</em> behind integer programming reassignments without modifying the safety solver.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
