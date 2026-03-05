"use client";

import { useEffect, useState } from "react";
import { useSession } from "next-auth/react";
import Link from "next/link";
import {
  TrialResponse,
  TrialListResponse,
  getMyTrials,
  cancelMyTrial,
} from "@/lib/api";

// Status badge colors
const STATUS_STYLES: Record<string, string> = {
  reserved: "bg-blue-100 text-blue-700",
  shipped: "bg-indigo-100 text-indigo-700",
  active: "bg-emerald-100 text-emerald-700",
  returned: "bg-amber-100 text-amber-700",
  refurbishing: "bg-orange-100 text-orange-700",
  ready: "bg-gray-100 text-gray-600",
  available: "bg-gray-100 text-gray-500",
  cancelled: "bg-red-100 text-red-600",
};

export default function DashboardPage() {
  const { data: session } = useSession();
  const [trials, setTrials] = useState<TrialResponse[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<string>("");
  const [actionLoading, setActionLoading] = useState<number | null>(null);

  const token = session?.accessToken as string | undefined;

  const fetchTrials = async () => {
    if (!token) return;
    setLoading(true);
    try {
      const params: { status?: string } = {};
      if (filter) params.status = filter;
      const data = await getMyTrials(token, params);
      setTrials(data.items);
      setTotal(data.total);
    } catch {
      setError("Failed to load trials");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTrials();
  }, [token, filter]);

  const handleCancel = async (trialId: number) => {
    if (!token || !confirm("Cancel this trial? A full refund will be issued.")) return;
    setActionLoading(trialId);
    try {
      await cancelMyTrial(trialId, token);
      await fetchTrials();
    } catch (err: unknown) {
      const apiErr = err as { detail?: string };
      alert(apiErr.detail || "Failed to cancel trial");
    } finally {
      setActionLoading(null);
    }
  };

  const handleReturnRequest = async (trialId: number) => {
    if (!token) return;
    setActionLoading(trialId);
    try {
      // Call the return request endpoint
      const { api } = await import("@/lib/api");
      await api<TrialResponse>(`/trials/my/${trialId}/return`, {
        method: "POST",
        token,
      });
      alert("Return request submitted. You'll receive return instructions via email.");
      await fetchTrials();
    } catch (err: unknown) {
      const apiErr = err as { detail?: string };
      alert(apiErr.detail || "Failed to request return");
    } finally {
      setActionLoading(null);
    }
  };

  if (!session) {
    return (
      <main className="mx-auto max-w-4xl px-4 py-8 text-center sm:px-6 lg:px-8">
        <h1 className="mb-2 text-xl font-bold text-gray-900">Sign in required</h1>
        <Link
          href="/auth/login"
          className="text-sm font-medium text-stone-600 underline hover:text-stone-800"
        >
          Sign in to view your dashboard
        </Link>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-4xl px-4 py-8 sm:px-6 lg:px-8">
      <h1 className="mb-6 text-2xl font-bold text-gray-900">My Dashboard</h1>

      {/* Status filter tabs */}
      <div className="mb-6 flex flex-wrap gap-2">
        {["", "reserved", "active", "returned", "cancelled"].map((s) => (
          <button
            key={s}
            onClick={() => setFilter(s)}
            className={`rounded-full px-3 py-1.5 text-xs font-medium transition-colors ${
              filter === s
                ? "bg-stone-800 text-white"
                : "bg-gray-100 text-gray-600 hover:bg-gray-200"
            }`}
          >
            {s || "All"}
          </button>
        ))}
      </div>

      {/* Error */}
      {error && (
        <div className="mb-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="space-y-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="animate-pulse rounded-xl border border-gray-200 bg-white p-5">
              <div className="flex items-center gap-4">
                <div className="h-14 w-14 rounded-lg bg-gray-100" />
                <div className="flex-1 space-y-2">
                  <div className="h-4 w-48 rounded bg-gray-100" />
                  <div className="h-3 w-32 rounded bg-gray-100" />
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Trial list */}
      {!loading && trials.length > 0 && (
        <div className="space-y-3">
          {trials.map((trial) => (
            <div
              key={trial.id}
              className="rounded-xl border border-gray-200 bg-white p-5 transition-shadow hover:shadow-sm"
            >
              <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                {/* Left: device info */}
                <div className="flex items-center gap-4">
                  <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-lg bg-gray-50 p-1">
                    <img
                      src={trial.device_image || "/placeholder-device.svg"}
                      alt={trial.device_name || "Device"}
                      className="max-h-full w-auto object-contain"
                    />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">
                      {trial.device_name || `Device #${trial.device_id}`}
                    </h3>
                    <p className="text-xs text-gray-500">
                      {trial.device_brand} · {trial.duration_days}-day trial
                    </p>
                    <div className="mt-1 flex items-center gap-2">
                      <span
                        className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                          STATUS_STYLES[trial.status] || "bg-gray-100 text-gray-600"
                        }`}
                      >
                        {trial.status}
                      </span>
                      {trial.start_date && trial.end_date && (
                        <span className="text-xs text-gray-400">
                          {trial.start_date} — {trial.end_date}
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                {/* Right: pricing + actions */}
                <div className="flex items-center gap-3 sm:flex-col sm:items-end">
                  <p className="text-sm font-semibold text-stone-800">
                    €{trial.trial_fee.toFixed(2)}
                    <span className="ml-1 text-xs font-normal text-gray-400">fee</span>
                  </p>

                  <div className="flex gap-2">
                    {/* Cancel — only for reserved trials */}
                    {trial.status === "reserved" && (
                      <button
                        onClick={() => handleCancel(trial.id)}
                        disabled={actionLoading === trial.id}
                        className="rounded-lg border border-red-200 px-3 py-1.5 text-xs font-medium text-red-600 transition-colors hover:bg-red-50 disabled:opacity-50"
                      >
                        {actionLoading === trial.id ? "Cancelling..." : "Cancel"}
                      </button>
                    )}

                    {/* Return — only for active trials */}
                    {trial.status === "active" && (
                      <button
                        onClick={() => handleReturnRequest(trial.id)}
                        disabled={actionLoading === trial.id}
                        className="rounded-lg border border-amber-200 px-3 py-1.5 text-xs font-medium text-amber-700 transition-colors hover:bg-amber-50 disabled:opacity-50"
                      >
                        {actionLoading === trial.id ? "Requesting..." : "Request return"}
                      </button>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Empty state */}
      {!loading && trials.length === 0 && (
        <div className="flex flex-col items-center justify-center rounded-xl border-2 border-dashed border-gray-200 py-16 text-center">
          <p className="text-lg font-medium text-gray-900">No trials yet</p>
          <p className="mt-1 text-sm text-gray-500">
            Browse our catalog and start your first device trial
          </p>
          <Link
            href="/devices"
            className="mt-4 rounded-lg bg-stone-800 px-6 py-2.5 text-sm font-medium text-white hover:bg-stone-700"
          >
            Browse devices
          </Link>
        </div>
      )}
    </main>
  );
}
