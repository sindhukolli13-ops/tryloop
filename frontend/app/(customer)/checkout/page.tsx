"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { useSession } from "next-auth/react";
import Link from "next/link";
import {
  DeviceResponse,
  createTrialCheckout,
  getDevice,
} from "@/lib/api";

export default function CheckoutPage() {
  const searchParams = useSearchParams();
  const { data: session } = useSession();

  const deviceId = Number(searchParams.get("device_id"));
  const [device, setDevice] = useState<DeviceResponse | null>(null);
  const [duration, setDuration] = useState<7 | 14>(7);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load device info
  useEffect(() => {
    if (!deviceId || isNaN(deviceId)) {
      setError("No device selected");
      setLoading(false);
      return;
    }
    getDevice(deviceId)
      .then((d) => {
        setDevice(d);
        setLoading(false);
      })
      .catch(() => {
        setError("Device not found");
        setLoading(false);
      });
  }, [deviceId]);

  const trialFee = device
    ? duration === 7
      ? device.trial_price_7d
      : device.trial_price_14d
    : 0;
  const deposit = device?.deposit_amount ?? 0;
  const totalDue = trialFee + deposit;

  const handleCheckout = async () => {
    if (!device || !session?.accessToken) return;

    setSubmitting(true);
    setError(null);
    try {
      const result = await createTrialCheckout(
        { device_id: device.id, duration_days: duration },
        session.accessToken as string
      );
      // Redirect to Stripe Checkout
      window.location.href = result.checkout_url;
    } catch (err: unknown) {
      const apiErr = err as { detail?: string };
      setError(apiErr.detail || "Failed to start checkout. Please try again.");
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <main className="mx-auto max-w-2xl px-4 py-8 sm:px-6 lg:px-8">
        <div className="animate-pulse space-y-4">
          <div className="h-6 w-48 rounded bg-gray-200" />
          <div className="h-64 rounded-xl bg-gray-100" />
        </div>
      </main>
    );
  }

  if (error && !device) {
    return (
      <main className="mx-auto max-w-2xl px-4 py-8 text-center sm:px-6 lg:px-8">
        <h1 className="mb-2 text-xl font-bold text-gray-900">{error}</h1>
        <Link
          href="/devices"
          className="text-sm font-medium text-stone-600 underline hover:text-stone-800"
        >
          Browse devices
        </Link>
      </main>
    );
  }

  if (!session) {
    return (
      <main className="mx-auto max-w-2xl px-4 py-8 text-center sm:px-6 lg:px-8">
        <h1 className="mb-2 text-xl font-bold text-gray-900">Sign in required</h1>
        <p className="mb-4 text-sm text-gray-500">
          You need to be signed in to start a trial.
        </p>
        <Link
          href="/auth/login"
          className="rounded-lg bg-stone-800 px-6 py-3 text-sm font-semibold text-white hover:bg-stone-700"
        >
          Sign in
        </Link>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-2xl px-4 py-8 sm:px-6 lg:px-8">
      {/* Breadcrumb */}
      <nav className="mb-6 text-sm text-gray-500">
        <Link href="/devices" className="hover:text-stone-700">Devices</Link>
        <span className="mx-2">/</span>
        <Link href={`/devices/${device?.id}`} className="hover:text-stone-700">
          {device?.name}
        </Link>
        <span className="mx-2">/</span>
        <span className="text-gray-900">Checkout</span>
      </nav>

      <h1 className="mb-6 text-2xl font-bold text-gray-900">Start a Trial</h1>

      <div className="rounded-xl border border-gray-200 bg-white p-6">
        {/* Device summary */}
        <div className="mb-6 flex gap-4">
          <div className="flex h-20 w-20 shrink-0 items-center justify-center rounded-lg bg-gray-50 p-2">
            <img
              src={device?.images?.[0] || "/placeholder-device.svg"}
              alt={device?.name}
              className="max-h-full w-auto object-contain"
            />
          </div>
          <div>
            <h2 className="font-semibold text-gray-900">{device?.name}</h2>
            <p className="text-sm text-gray-500">
              {device?.brand} · {device?.category}
            </p>
            {device && device.available_units > 0 ? (
              <span className="mt-1 inline-block rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-medium text-emerald-700">
                {device.available_units} available
              </span>
            ) : (
              <span className="mt-1 inline-block rounded-full bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-500">
                Out of stock
              </span>
            )}
          </div>
        </div>

        {/* Duration selection */}
        <div className="mb-6">
          <h3 className="mb-3 text-sm font-semibold text-gray-700">Select trial duration</h3>
          <div className="flex gap-3">
            {[7, 14].map((days) => (
              <button
                key={days}
                onClick={() => setDuration(days as 7 | 14)}
                className={`flex-1 rounded-lg border-2 px-4 py-3 text-center transition-colors ${
                  duration === days
                    ? "border-stone-800 bg-stone-50 text-stone-800"
                    : "border-gray-200 text-gray-600 hover:border-gray-300"
                }`}
              >
                <span className="block text-lg font-bold">{days} days</span>
                <span className="text-sm">
                  €{(days === 7 ? device?.trial_price_7d : device?.trial_price_14d)?.toFixed(2)}
                </span>
              </button>
            ))}
          </div>
        </div>

        {/* Price breakdown */}
        <div className="mb-6 rounded-lg bg-gray-50 p-4">
          <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-gray-500">
            Price breakdown
          </h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">
                {duration}-day trial fee
                <span className="ml-1 text-xs text-gray-400">(non-refundable)</span>
              </span>
              <span className="font-medium text-gray-900">€{trialFee.toFixed(2)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">
                Refundable deposit
                <span className="ml-1 text-xs text-gray-400">(returned on device return)</span>
              </span>
              <span className="font-medium text-gray-900">€{deposit.toFixed(2)}</span>
            </div>
            <hr className="my-2 border-gray-200" />
            <div className="flex justify-between text-base font-bold">
              <span className="text-gray-900">Total due today</span>
              <span className="text-stone-800">€{totalDue.toFixed(2)}</span>
            </div>
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="mb-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            {error}
          </div>
        )}

        {/* CTA */}
        <button
          onClick={handleCheckout}
          disabled={submitting || !device || device.available_units === 0}
          className="w-full rounded-lg bg-stone-800 px-6 py-3 text-sm font-semibold text-white transition-colors hover:bg-stone-700 disabled:cursor-not-allowed disabled:bg-gray-300 disabled:text-gray-500"
        >
          {submitting ? "Redirecting to payment..." : `Pay €${totalDue.toFixed(2)} and start trial`}
        </button>

        <p className="mt-3 text-center text-xs text-gray-400">
          You'll be redirected to Stripe for secure payment. The trial fee is non-refundable.
          Your deposit is fully refunded when you return the device in acceptable condition.
        </p>
      </div>
    </main>
  );
}
