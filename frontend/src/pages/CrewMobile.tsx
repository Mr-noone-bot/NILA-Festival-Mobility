import { useState } from 'react';
import {
  Bus,
  CheckCircle2,
  Clock,
  MapPin,
  ShieldCheck,
  Check,
  Users,
} from 'lucide-react';
import type { OrderDispatchItem, OccupancyBand, BusTelemetryItem } from '../api/operations';

interface CrewMobileProps {
  orders: OrderDispatchItem[];
  buses: BusTelemetryItem[];
  onAcknowledgeOrder: (orderId: string) => Promise<void>;
  onUpdateOccupancy: (busId: string, band: OccupancyBand) => Promise<void>;
}

export default function CrewMobile({
  orders,
  buses,
  onAcknowledgeOrder,
  onUpdateOccupancy,
}: CrewMobileProps) {
  const [selectedBusId, setSelectedBusId] = useState<string>('BUS-12');
  const [updatingBand, setUpdatingBand] = useState<string | null>(null);
  const [acknowledging, setAcknowledging] = useState(false);
  const [toastMessage, setToastMessage] = useState<string>('');

  const assignedBus = buses.find((b) => b.bus_id === selectedBusId) || buses[0];
  const activeOrder = orders.find(
    (o) => o.bus_id === selectedBusId && o.status !== 'COMPLETED' && o.status !== 'CANNOT_COMPLY'
  );

  const handleOccupancyTap = async (band: OccupancyBand) => {
    setUpdatingBand(band);
    setToastMessage('');
    try {
      await onUpdateOccupancy(selectedBusId, band);
      setToastMessage(`Occupancy updated to ${band.replace('_', ' ')}. Transmitted to Control Room.`);
    } finally {
      setUpdatingBand(null);
    }
  };

  const handleAck = async (orderId: string) => {
    setAcknowledging(true);
    setToastMessage('');
    try {
      await onAcknowledgeOrder(orderId);
      setToastMessage('Order acknowledged. Safe travels on designated festival corridor!');
    } finally {
      setAcknowledging(false);
    }
  };

  return (
    <div className="max-w-md mx-auto space-y-5 py-2">
      {/* Mobile Top Header */}
      <div className="bg-slate-900 border border-slate-800 p-4 rounded-2xl flex items-center justify-between shadow-lg">
        <div className="flex items-center gap-2.5">
          <div className="w-10 h-10 rounded-xl bg-cyan-950 border border-cyan-800 flex items-center justify-center text-cyan-400">
            <Bus className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xs uppercase font-extrabold tracking-wider text-cyan-400">
              NILA Crew Mobile
            </div>
            <div className="text-lg font-bold text-white flex items-center gap-1.5">
              <span>Bus:</span>
              <select
                value={selectedBusId}
                onChange={(e) => setSelectedBusId(e.target.value)}
                className="bg-slate-950 border border-slate-700 rounded px-2 py-0.5 text-cyan-300 font-mono text-sm focus:outline-none"
              >
                {buses.map((b) => (
                  <option key={b.bus_id} value={b.bus_id}>
                    {b.bus_id} ({b.status})
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        <div className="text-right">
          <span className="inline-block px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-950 text-emerald-400 border border-emerald-800">
            ONLINE
          </span>
          <div className="text-[10px] text-slate-400 mt-0.5">Crew Mode</div>
        </div>
      </div>

      {/* Confirmation Toast */}
      {toastMessage && (
        <div className="p-3 bg-emerald-950/90 border border-emerald-800 text-emerald-300 text-xs rounded-xl flex items-center gap-2 shadow-lg animate-fadeIn">
          <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-400" />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Next Order Card */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-4 shadow-xl">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1">
            <Clock className="w-4 h-4 text-cyan-400" /> Operational Movement Order
          </span>
          {activeOrder && (
            <span
              className={`text-[10px] font-extrabold px-2 py-0.5 rounded border uppercase ${
                activeOrder.status === 'ACKNOWLEDGED'
                  ? 'bg-emerald-950 text-emerald-300 border-emerald-800'
                  : 'bg-amber-950 text-amber-300 border-amber-800 animate-pulse'
              }`}
            >
              {activeOrder.status.replace('_', ' ')}
            </span>
          )}
        </div>

        {activeOrder ? (
          <div className="space-y-4">
            <div>
              <div className="text-xs text-slate-400">DESTINATION STOP</div>
              <div className="text-2xl font-extrabold text-cyan-300 mt-0.5 flex items-center gap-2">
                <MapPin className="w-6 h-6 text-rose-500 shrink-0" />
                {activeOrder.destination_stop}
              </div>
              <div className="text-xs text-slate-400 mt-1">
                From: <strong>{activeOrder.source_stop}</strong>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3 bg-slate-950 p-3.5 rounded-xl border border-slate-800">
              <div>
                <div className="text-[11px] text-slate-400">DEPART TIME</div>
                <div className="text-lg font-bold text-white font-mono">{activeOrder.departure_time}</div>
              </div>
              <div>
                <div className="text-[11px] text-slate-400">EXPECTED ARRIVAL</div>
                <div className="text-lg font-bold text-emerald-400 font-mono">{activeOrder.arrival_time}</div>
              </div>
            </div>

            {activeOrder.status === 'DISPATCH_PENDING' ? (
              <button
                disabled={acknowledging}
                onClick={() => handleAck(activeOrder.id)}
                className="w-full py-3.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-extrabold text-base transition shadow-xl flex items-center justify-center gap-2 active:scale-98"
              >
                <Check className="w-5 h-5" />
                {acknowledging ? 'Confirming...' : 'ACKNOWLEDGE ORDER'}
              </button>
            ) : (
              <div className="p-3 bg-emerald-950/40 border border-emerald-900 rounded-xl text-center text-xs text-emerald-400 font-bold flex items-center justify-center gap-2">
                <ShieldCheck className="w-4 h-4" /> ORDER CONFIRMED — EN ROUTE
              </div>
            )}
          </div>
        ) : (
          <div className="p-8 text-center text-slate-400 space-y-2">
            <p className="text-sm font-semibold text-slate-300">No Pending Movement Orders</p>
            <p className="text-xs">
              Vehicle {selectedBusId} is currently nominal. Remain stationed at{' '}
              <strong>{assignedBus?.current_stop || 'Assigned Stop'}</strong>.
            </p>
          </div>
        )}
      </div>

      {/* 1-Tap Passenger Occupancy Reporter */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-4 shadow-xl">
        <div className="border-b border-slate-800 pb-3">
          <h2 className="text-sm font-extrabold uppercase tracking-wider text-white flex items-center gap-2">
            <Users className="w-4 h-4 text-cyan-400" /> Report Current Passenger Load
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Tap once to transmit on-board capacity status directly to the Duty Manager:
          </p>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <button
            onClick={() => handleOccupancyTap('EMPTY')}
            disabled={updatingBand === 'EMPTY'}
            className={`py-4 px-3 rounded-xl border font-bold text-sm transition flex flex-col items-center justify-center gap-1 active:scale-95 ${
              assignedBus?.occupancy_band === 'EMPTY'
                ? 'bg-emerald-950 text-emerald-300 border-emerald-600 ring-2 ring-emerald-500'
                : 'bg-slate-950 hover:bg-slate-800 text-emerald-400 border-slate-800'
            }`}
          >
            <span className="text-lg">🟢</span>
            <span>EMPTY</span>
            <span className="text-[10px] text-slate-400 font-normal">0 - 10 pax</span>
          </button>

          <button
            onClick={() => handleOccupancyTap('SEATS_FREE')}
            disabled={updatingBand === 'SEATS_FREE'}
            className={`py-4 px-3 rounded-xl border font-bold text-sm transition flex flex-col items-center justify-center gap-1 active:scale-95 ${
              assignedBus?.occupancy_band === 'SEATS_FREE'
                ? 'bg-cyan-950 text-cyan-300 border-cyan-600 ring-2 ring-cyan-500'
                : 'bg-slate-950 hover:bg-slate-800 text-cyan-400 border-slate-800'
            }`}
          >
            <span className="text-lg">🔵</span>
            <span>SEATS FREE</span>
            <span className="text-[10px] text-slate-400 font-normal">11 - 35 pax</span>
          </button>

          <button
            onClick={() => handleOccupancyTap('STANDING')}
            disabled={updatingBand === 'STANDING'}
            className={`py-4 px-3 rounded-xl border font-bold text-sm transition flex flex-col items-center justify-center gap-1 active:scale-95 ${
              assignedBus?.occupancy_band === 'STANDING'
                ? 'bg-amber-950 text-amber-300 border-amber-600 ring-2 ring-amber-500'
                : 'bg-slate-950 hover:bg-slate-800 text-amber-400 border-slate-800'
            }`}
          >
            <span className="text-lg">🟡</span>
            <span>STANDING</span>
            <span className="text-[10px] text-slate-400 font-normal">36 - 48 pax</span>
          </button>

          <button
            onClick={() => handleOccupancyTap('CROWDED')}
            disabled={updatingBand === 'CROWDED'}
            className={`py-4 px-3 rounded-xl border font-bold text-sm transition flex flex-col items-center justify-center gap-1 active:scale-95 ${
              assignedBus?.occupancy_band === 'CROWDED'
                ? 'bg-rose-950 text-rose-300 border-rose-600 ring-2 ring-rose-500'
                : 'bg-slate-950 hover:bg-slate-800 text-rose-400 border-slate-800'
            }`}
          >
            <span className="text-lg">🔴</span>
            <span>CROWDED</span>
            <span className="text-[10px] text-slate-400 font-normal">Full capacity (&gt;48)</span>
          </button>
        </div>

        <div className="text-center text-[11px] text-slate-500 pt-1">
          Current Reported: <strong className="text-slate-300">{assignedBus?.occupancy_band.replace('_', ' ')}</strong> (Updated {assignedBus?.free_at !== 'NOW' ? 'recently' : 'just now'})
        </div>
      </div>
    </div>
  );
}
