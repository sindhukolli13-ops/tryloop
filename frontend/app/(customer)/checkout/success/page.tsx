"use client";

import { useSearchParams } from "next/navigation";
import Link from "next/link";

export default function CheckoutSuccessPage() {
  const searchParams = useSearchParams();
  const trialId = searchParams.get("trial_id");

  return (
    <main className="mx-auto max-w-lg px-4 py-16 text-center sm:px-6 lg:px-8">
      {/* Success icon */}
      <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-full bg-emerald-100">
        <svg className="h-8 w-8 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
        </svg>
      </div>

      <h1 className="mb-2 text-2xl font-bold text-gray-900">Trial confirmed!</h1>
      <p className="mb-6 text-sm text-gray-500">
        Your payment was successful and your device is being prepared for shipment.
        You&apos;ll receive a confirmation email with tracking details.
      </p>

      {trialId && (
        <p className="mb-6 text-xs text-gray-400">Trial ID: {trialId}</p>
      )}

      <div className="flex flex-col items-center gap-3">
        <Link
          href="/dashboard"
          className="rounded-lg bg-stone-800 px-6 py-3 text-sm font-semibold text-white transition-colors hover:bg-stone-700"
        >
          View my trials
        </Link>
        <Link
          href="/devices"
          className="text-sm font-medium text-stone-600 underline hover:text-stone-800"
        >
          Continue browsing
        </Link>
      </div>
    </main>
  );
}
