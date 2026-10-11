import { useState } from 'react';
import {
  CheckCircle2,
  Clock,
  MapPin,
  ArrowRight,
  X,
  Check,
  RefreshCw,
  AlertOctagon,
  Navigation,
} from 'lucide-react';
import type { OrderDispatchItem } from '../api/operations';

interface DepotOperationsProps {
  orders: OrderDispatchItem[];
  loading: boolean;
  onRefresh: () => void;
  onAcknowledge: (orderId: string) => Promise<void>;
  onCannotComply: (orderId: string, reason: string) => Promise<void>;
  onViewRoute?: (source: string, destination: string) => void;
}

export default function DepotOperations({
  orders,
  loading,
  onRefresh,
  onAcknowledge,
  onCannotComply,
  onViewRoute,
}: DepotOperationsProps) {
  const [selectedOrderForCC, setSelectedOrderForCC] = useState<OrderDispatchItem | null>(null);
  const [ccReason, setCcReason] = useState('Bus mechanical failure reported by depot inspection');
  const [submittingAction, setSubmittingAction] = useState<string | null>(null);
  const [actionSuccessMsg, setActionSuccessMsg] = useState('');

  const handleAcknowledge = async (orderId: string) => {
    setSubmittingAction(orderId);
    setActionSuccessMsg('');
    try {
      await onAcknowledge(orderId);
      setActionSuccessMsg(`Order ${orderId} acknowledged. Crew dispatch alert sent.`);
    } finally {
      setSubmittingAction(null);
    }
  };

  const handleCannotComplySubmit = async () => {
    if (!selectedOrderForCC) return;
    setSubmittingAction(selectedOrderForCC.id);
    setActionSuccessMsg('');
    try {
      await onCannotComply(selectedOrderForCC.id, ccReason);
      setActionSuccessMsg(
        `Order ${selectedOrderForCC.id} marked CANNOT COMPLY. Alternative vehicle allocated.`
      );
      setSelectedOrderForCC(null);
    } finally {
      setSubmittingAction(null);
    }
  };

  const pendingOrders = orders.filter((o) => o.status === 'DISPATCH_PENDING');
  const acknowledgedOrders = orders.filter((o) => o.status === 'ACKNOWLEDGED' || o.status === 'EN_ROUTE');
  const cannotComplyOrders = orders.filter((o) => o.status === 'CANNOT_COMPLY');

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-white">Depot Operations & Dispatch</h1>
            <span className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-950/80 text-emerald-400 border border-emerald-800">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              LIVE DISPATCH
            </span>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Depot Manager interface for reviewing approved movement orders, issuing crew assignments, and managing fleet compliance.
          </p>
        </div>

        <button
          onClick={onRefresh}
          disabled={loading}
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition self-start md:self-auto disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Sync Orders
        </button>
      </div>

      {actionSuccessMsg && (
        <div className="p-3 bg-emerald-950/80 border border-emerald-800 text-emerald-300 text-xs rounded-xl flex items-center gap-2 shadow">
          <CheckCircle2 className="w-4 h-4" />
          {actionSuccessMsg}
        </div>
      )}

      {/* Orders Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
          <div className="text-xs font-semibold uppercase tracking-wider text-amber-400">
            Pending Dispatch ({pendingOrders.length})
          </div>
          <div className="text-2xl font-bold text-white mt-1">{pendingOrders.length}</div>
          <div className="text-xs text-slate-400 mt-1">Awaiting depot acknowledgment</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
          <div className="text-xs font-semibold uppercase tracking-wider text-emerald-400">
            Acknowledged / Active ({acknowledgedOrders.length})
          </div>
          <div className="text-2xl font-bold text-emerald-400 mt-1">{acknowledgedOrders.length}</div>
          <div className="text-xs text-slate-400 mt-1">Crew dispatched on corridor</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
          <div className="text-xs font-semibold uppercase tracking-wider text-rose-400">
            Cannot Comply ({cannotComplyOrders.length})
          </div>
          <div className="text-2xl font-bold text-rose-400 mt-1">{cannotComplyOrders.length}</div>
          <div className="text-xs text-slate-400 mt-1">Exceptions resolved with alternatives</div>
        </div>
      </div>

      {/* Orders List */}
      <div className="space-y-4">
        <h2 className="text-base font-bold text-white">Movement Orders Board</h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {orders.map((order) => {
            const isPending = order.status === 'DISPATCH_PENDING';
            const isAck = order.status === 'ACKNOWLEDGED' || order.status === 'EN_ROUTE';
            const isCC = order.status === 'CANNOT_COMPLY';

            return (
              <div
                key={order.id}
                className={`p-4 rounded-xl border space-y-3 transition ${
                  isPending
                    ? 'bg-slate-900/90 border-amber-800/60 shadow-md'
                    : isAck
                    ? 'bg-slate-900/60 border-emerald-900/60'
                    : 'bg-slate-900/40 border-rose-900/60'
                }`}
              >
                {/* Header */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="font-mono font-bold text-sm text-white">{order.id}</span>
                    <span className="text-xs px-2 py-0.5 rounded bg-slate-800 text-cyan-300 font-bold border border-slate-700">
                      {order.bus_id}
                    </span>
                  </div>

                  <span
                    className={`text-[11px] font-bold px-2 py-0.5 rounded border ${
                      isPending
                        ? 'bg-amber-950 text-amber-300 border-amber-800'
                        : isAck
                        ? 'bg-emerald-950 text-emerald-300 border-emerald-800'
                        : 'bg-rose-950 text-rose-300 border-rose-800'
                    }`}
                  >
                    {order.status.replace('_', ' ')}
                  </span>
                </div>

                {/* Corridor */}
                <div className="bg-slate-950 p-3 rounded-lg border border-slate-800/80 text-xs space-y-2">
                  <div className="flex items-center justify-between font-semibold">
                    <span className="text-slate-300 flex items-center gap-1">
                      <MapPin className="w-3.5 h-3.5 text-slate-400" />
                      {order.source_stop}
                    </span>
                    <ArrowRight className="w-4 h-4 text-cyan-400" />
                    <span className="text-cyan-300 flex items-center gap-1">
                      <MapPin className="w-3.5 h-3.5 text-cyan-400" />
                      {order.destination_stop}
                    </span>
                  </div>

                  <div className="flex items-center justify-between text-slate-400 text-[11px] pt-1 border-t border-slate-800/60">
                    <span className="flex items-center gap-1">
                      <Clock className="w-3 h-3" /> Depart: <strong>{order.departure_time}</strong>
                    </span>
                    <span>
                      Arrive: <strong>{order.arrival_time}</strong>
                    </span>
                  </div>
                </div>

                {/* Cannot Comply note if applicable */}
                {isCC && (
                  <div className="p-2.5 bg-rose-950/40 border border-rose-900/60 rounded-lg text-xs space-y-1">
                    <div className="font-bold text-rose-400 flex items-center gap-1">
                      <AlertOctagon className="w-3.5 h-3.5" /> Compliance Exception:
                    </div>
                    <div className="text-slate-300">{order.cannot_comply_reason}</div>
                    {order.alternative_bus_id && (
                      <div className="text-cyan-300 pt-1 font-semibold">
                        Alternative Allocated: {order.alternative_bus_id}
                      </div>
                    )}
                  </div>
                )}

                {/* Actions */}
                <div className="flex items-center justify-between pt-1">
                  {onViewRoute && (
                    <button
                      onClick={() => onViewRoute(order.source_stop, order.destination_stop)}
                      className="px-2.5 py-1 text-xs rounded text-slate-300 hover:text-white hover:bg-slate-800 border border-slate-700 transition flex items-center gap-1"
                    >
                      <Navigation className="w-3 h-3" /> View Route
                    </button>
                  )}

                  {isPending && (
                    <div className="flex items-center gap-2 ml-auto">
                      <button
                        disabled={submittingAction === order.id}
                        onClick={() => setSelectedOrderForCC(order)}
                        className="px-3 py-1.5 text-xs rounded bg-slate-900 hover:bg-slate-800 text-rose-400 border border-rose-900/60 transition font-medium"
                      >
                        Cannot Comply
                      </button>
                      <button
                        disabled={submittingAction === order.id}
                        onClick={() => handleAcknowledge(order.id)}
                        className="px-3 py-1.5 text-xs rounded bg-emerald-600 hover:bg-emerald-500 text-white font-bold transition shadow flex items-center gap-1"
                      >
                        <Check className="w-3.5 h-3.5" />
                        {submittingAction === order.id ? 'Saving...' : 'Acknowledge Order'}
                      </button>
                    </div>
                  )}
                </div>
              </div>
            );
          })}

          {orders.length === 0 && (
            <div className="col-span-2 p-12 text-center text-slate-400 border border-dashed border-slate-800 rounded-xl">
              No movement orders issued yet. When Duty Manager approves recommendations in the Command Center, orders appear here for depot dispatch.
            </div>
          )}
        </div>
      </div>

      {/* Cannot Comply Modal */}
      {selectedOrderForCC && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2 text-rose-400 font-bold">
                <AlertOctagon className="w-5 h-5" />
                <span>Cannot Comply — {selectedOrderForCC.id}</span>
              </div>
              <button
                onClick={() => setSelectedOrderForCC(null)}
                className="p-1 rounded text-slate-400 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <p className="text-xs text-slate-300">
              Select reason why vehicle <strong>{selectedOrderForCC.bus_id}</strong> cannot execute this repositioning order. NILA will trigger alternative candidate search from available fleet.
            </p>

            <div className="space-y-2">
              <label className="text-xs font-semibold text-slate-400">Exception Reason:</label>
              {[
                'Bus mechanical failure reported by depot inspection',
                'Driver unavailable / duty hours exceeded',
                'Road blockage / congestion impediment on designated corridor',
                'Vehicle reassigned to emergency sacred perimeter shuttle',
              ].map((reason) => (
                <label
                  key={reason}
                  className={`flex items-start gap-2 p-2.5 rounded-lg border text-xs cursor-pointer transition ${
                    ccReason === reason
                      ? 'bg-rose-950/40 border-rose-800 text-rose-200'
                      : 'bg-slate-950 border-slate-800 text-slate-400 hover:bg-slate-800'
                  }`}
                >
                  <input
                    type="radio"
                    name="ccReason"
                    checked={ccReason === reason}
                    onChange={() => setCcReason(reason)}
                    className="mt-0.5"
                  />
                  <span>{reason}</span>
                </label>
              ))}
            </div>

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-800">
              <button
                onClick={() => setSelectedOrderForCC(null)}
                className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium"
              >
                Cancel
              </button>
              <button
                onClick={handleCannotComplySubmit}
                disabled={submittingAction === selectedOrderForCC.id}
                className="px-4 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-500 text-white text-xs font-bold transition shadow"
              >
                Submit Exception & Find Alternative
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
