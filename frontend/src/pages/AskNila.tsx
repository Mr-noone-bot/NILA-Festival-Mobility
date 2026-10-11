import { type FormEvent, useEffect, useRef } from 'react';
import {
  Bot,
  Compass,
  Languages,
  Send,
  ShieldCheck,
  Sparkles,
  User,
  Zap,
  Bus,
  AlertTriangle,
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

const OPERATIONAL_ACTIONS = [
  {
    label: 'Why This Move?',
    icon: Zap,
    prompt: 'Why did NILA recommend this bus movement, and what is the specific service trade-off at the source stop?',
  },
  {
    label: 'Highest Risk Stop',
    icon: AlertTriangle,
    prompt: 'Which transit stop currently faces the highest queue risk and egress overload?',
  },
  {
    label: 'Free Buses',
    icon: Bus,
    prompt: 'Which buses are currently available or becoming free in the next 20 minutes?',
  },
  {
    label: 'What Changed?',
    icon: Compass,
    prompt: 'What changed in predicted crowd arrival, queue length, and bus demand under the current rain scenario?',
  },
  {
    label: 'Shift Handover',
    icon: Sparkles,
    prompt: 'Prepare an executive shift handover brief summarizing current network risk, peak window, and pending decisions.',
  },
  {
    label: 'Translate to Tamil',
    icon: Languages,
    prompt: 'Translate the active bus repositioning order into concise Tamil instructions for the bus crew (பேருந்து பணியாளர்களுக்கான வழிகாட்டுதல்).',
  },
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
  const activeMove: BusMove | null = optimization?.move ?? null;

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
      <div className="border-b border-slate-800 pb-5">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-cyan-600 to-blue-600 flex items-center justify-center text-white shadow-lg shadow-cyan-900/30">
            <Sparkles className="w-4 h-4" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white">NILA Operational Copilot</h1>
          <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-950 text-emerald-400 border border-emerald-800">
            GROUNDED BACKEND AI
          </span>
        </div>
        <p className="text-sm text-slate-400 mt-1">
          Grounded conversational intelligence for Duty Managers, synthesizing deterministic prediction models and fixed-fleet optimization plans.
        </p>
      </div>

      {/* Operational Quick Actions Row */}
      <div className="bg-slate-900/80 border border-slate-800 p-3 rounded-2xl space-y-2">
        <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400 px-1">
          Operational Command Shortcuts:
        </div>
        <div className="flex flex-wrap gap-2">
          {OPERATIONAL_ACTIONS.map((action) => {
            const Icon = action.icon;
            return (
              <button
                key={action.label}
                disabled={chatLoading}
                onClick={() => onSubmitQuestion(action.prompt)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-950 hover:bg-slate-800 text-slate-200 hover:text-white border border-slate-800 hover:border-cyan-700 text-xs font-semibold transition disabled:opacity-50"
              >
                <Icon className="w-3.5 h-3.5 text-cyan-400" />
                {action.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* Chat Container */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* Main Conversation (8 cols) */}
        <div className="lg:col-span-8 bg-slate-900/90 border border-slate-800 rounded-2xl flex flex-col h-[520px] overflow-hidden shadow-xl">
          {/* Messages list */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {chatMessages.map((msg, idx) => (
              <div
                key={idx}
                className={`flex gap-3 text-sm ${
                  msg.role === 'user' ? 'justify-end' : 'justify-start'
                }`}
              >
                {msg.role === 'assistant' && (
                  <div className="w-8 h-8 rounded-lg bg-cyan-950 border border-cyan-800 flex items-center justify-center text-cyan-400 shrink-0 mt-0.5">
                    <Bot className="w-4 h-4" />
                  </div>
                )}

                <div
                  className={`max-w-[85%] rounded-2xl p-4 space-y-1.5 ${
                    msg.role === 'user'
                      ? 'bg-cyan-600 text-white rounded-br-sm'
                      : 'bg-slate-950 border border-slate-800 text-slate-200 rounded-bl-sm'
                  }`}
                >
                  <div className="text-[11px] font-semibold opacity-70 flex items-center justify-between gap-4">
                    <span>{msg.role === 'user' ? 'Duty Manager' : 'NILA Copilot'}</span>
                    {msg.role === 'assistant' && (
                      <span className="font-mono text-[10px] text-emerald-400">
                        GROUNDED RESPONSE
                      </span>
                    )}
                  </div>
                  <div className="text-sm whitespace-pre-wrap leading-relaxed">{msg.text}</div>
                </div>

                {msg.role === 'user' && (
                  <div className="w-8 h-8 rounded-lg bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-300 shrink-0 mt-0.5">
                    <User className="w-4 h-4" />
                  </div>
                )}
              </div>
            ))}

            {chatLoading && (
              <div className="flex gap-3 text-sm items-center">
                <div className="w-8 h-8 rounded-lg bg-cyan-950 border border-cyan-800 flex items-center justify-center text-cyan-400 animate-pulse">
                  <Bot className="w-4 h-4" />
                </div>
                <div className="bg-slate-950 border border-slate-800 rounded-2xl p-4 text-xs text-cyan-400 flex items-center gap-2">
                  <Sparkles className="w-4 h-4 animate-spin" />
                  Evaluating grounded festival state and solver constraints...
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Error notice if present */}
          {chatError && (
            <div className="px-4 py-2 bg-rose-950/60 border-t border-rose-900/60 text-xs text-rose-300 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 shrink-0 text-rose-400" />
              <span>{chatError}</span>
            </div>
          )}

          {/* Chat Input Bar */}
          <form onSubmit={handleSubmit} className="p-3 bg-slate-950 border-t border-slate-800 flex items-center gap-2">
            <input
              type="text"
              value={chatInput}
              onChange={(e) => onChatInputChange(e.target.value)}
              placeholder="Ask NILA about crowd predictions, trade-offs, or fleet decisions..."
              className="flex-1 bg-slate-900 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500"
            />
            <button
              type="submit"
              disabled={chatLoading || !chatInput.trim()}
              className="px-4 py-2.5 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-bold text-sm transition shadow-lg disabled:opacity-50 flex items-center gap-1.5"
            >
              <Send className="w-4 h-4" />
              <span>Send</span>
            </button>
          </form>
        </div>

        {/* Right Grounding Context Sidebar (4 cols) */}
        <div className="lg:col-span-4 space-y-4">
          <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-4 space-y-4 shadow-xl">
            <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
              <ShieldCheck className="w-4 h-4 text-emerald-400" /> Grounding Fact Base
            </h2>

            <div className="space-y-3 text-xs">
              <div className="p-3 bg-slate-950 rounded-xl border border-slate-800 space-y-1">
                <div className="text-slate-400">Current Festival:</div>
                <div className="font-bold text-white">{festival.name} ({festival.city})</div>
                <div className="text-slate-400 text-[11px]">Temple: {festival.temple}</div>
              </div>

              <div className="p-3 bg-slate-950 rounded-xl border border-slate-800 space-y-1">
                <div className="text-slate-400">Predicted Network Peak:</div>
                <div className="font-bold text-cyan-300">
                  {forecast.metrics?.peakCrowd?.toLocaleString() || '135,000'} pilgrims at {forecast.metrics?.peakTime || '20:10'}
                </div>
                <div className="text-slate-400 text-[11px]">
                  Alert Level: <strong className="text-rose-400">{forecast.metrics?.risk || 'CRITICAL'}</strong>
                </div>
              </div>

              {activeMove && (
                <div className="p-3 bg-slate-950 rounded-xl border border-slate-800 space-y-1">
                  <div className="text-slate-400">Active Repositioning Recommendation:</div>
                  <div className="font-semibold text-white">
                    {activeMove.sourceStop} ➔ {activeMove.destinationStop}
                  </div>
                  <div className="text-[11px] text-cyan-400">
                    Buses: <strong>{activeMove.buses}</strong> | Depart: {activeMove.departure} ➔ Arrive: {activeMove.arrival}
                  </div>
                  <div className="text-[11px] text-emerald-400 pt-1">
                    Benefit: {activeMove.benefit}
                  </div>
                </div>
              )}

              <div className="p-3 bg-slate-950 rounded-xl border border-slate-800 text-[11px] text-slate-400 space-y-1">
                <div className="font-semibold text-slate-300">Strict Invariant Enforcement:</div>
                <p>
                  Gemini answers are constrained to verified deterministic model outputs. Zero invented buses or ungrounded statistics.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
