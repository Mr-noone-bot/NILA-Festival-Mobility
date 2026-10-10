import React from 'react';

export default function App() {
  const modules = [
    { name: 'Command Center', description: 'Real-time festival mobility monitoring and surge detection', owner: 'Chandhana' },
    { name: 'Map Engine', description: 'MapLibre + OpenFreeMap + deck.gl crowd density heatmap and route visualization', owner: 'Chandhana' },
    { name: 'Planner', description: 'Fixed-fleet allocation and redistribution scheduling', owner: 'Chandhana / Sanjay' },
    { name: 'Scenario Simulator', description: 'Surge scenario modeling and crowd distribution simulation', owner: 'Chandhana / Gugaan' },
    { name: 'AI Copilot', description: 'Natural language explanation and decision audit layer powered by Gemini', owner: 'Chandhana / Gugaan' },
  ];

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      {/* Header */}
      <header className="border-b border-slate-800 bg-slate-900/60 backdrop-blur px-6 py-4 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="w-3 h-3 rounded-full bg-cyan-400 animate-pulse" />
          <h1 className="text-xl font-bold tracking-tight text-white">NILA</h1>
          <span className="text-xs px-2.5 py-0.5 rounded-full bg-cyan-950 text-cyan-400 border border-cyan-800 font-medium">
            SAKTHI HACKFEST'26 Foundation
          </span>
        </div>
        <div className="text-xs text-slate-400">
          Festival Mobility &amp; Crowd Management System
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 max-w-5xl w-full mx-auto p-6 md:p-10 flex flex-col justify-center">
        <div className="space-y-4 mb-8">
          <h2 className="text-3xl font-extrabold tracking-tight text-white sm:text-4xl">
            Repository Foundation Active
          </h2>
          <p className="text-slate-400 max-w-2xl text-base leading-relaxed">
            NILA predicts festival crowd buildup and computes time-aware redistribution of an existing fixed bus fleet.
            The foundation provides strict separation of concerns across backend, frontend, simulation, and data layers.
          </p>
        </div>

        {/* Modules Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
          {modules.map((mod) => (
            <div
              key={mod.name}
              className="p-5 rounded-lg border border-slate-800 bg-slate-900/40"
            >
              <div className="text-sm font-semibold text-cyan-300 mb-1">{mod.name}</div>
              <p className="text-xs text-slate-400 leading-relaxed mb-3">{mod.description}</p>
              <div className="text-[11px] text-slate-500 font-mono">Assigned: {mod.owner}</div>
            </div>
          ))}
        </div>

        {/* System Principle Callout */}
        <div className="p-4 rounded-lg border border-slate-800 bg-slate-900/20 text-xs text-slate-400">
          <span className="font-semibold text-slate-300">Core Invariant:</span> Fixed Fleet Constraint — The fleet size is conserved across all repositioning steps. Every bus movement exposes its origin service trade-off, travel time, and network benefit.
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/80 px-6 py-4 text-center text-xs text-slate-500">
        NILA Core Team: Gugaan · Sanjay · Chandhana · Madhu
      </footer>
    </div>
  );
}
