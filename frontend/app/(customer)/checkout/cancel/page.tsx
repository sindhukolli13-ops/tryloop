"use client";

import { useSearchParams } from "next/navigation";
import Link from "next/link";

export default function CheckoutCancelPage() {
  const searchParams = useSearchParams();
  const trialId = searchParams.get("trial_id");

  return (
    <main className="mx-auto max-w-lg px-4 py-16 text-center sm:px-6 lg:px-8">
      {/* Cancel icon */}
      <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-full bg-gray-100">
        <svg className="h-8 w-8 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
        </svg>
      </div>

      <h1 className="mb-2 text-2xl font-bold text-gray-900">Checkout cancelled</h1>
      <p className="mb-6 text-sm text-gray-500">
        Your payment was not processed and no charges were made.
        The device reservation will be automatically released.
      </p>

      <div className="flex flex-col items-center gap-3">
        <Link
          href="/devices"
          className="rounded-lg bg-stone-800 px-6 py-3 text-sm font-semibold text-white transition-colors hover:bg-stone-700"
        >
          Browse devices
        </Link>
      </div>
    </main>
  );
}
