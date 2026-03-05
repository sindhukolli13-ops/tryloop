"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { DeviceResponse, compareDevices } from "@/lib/api";

export default function DeviceComparePage() {
  const searchParams = useSearchParams();
  const [devices, setDevices] = useState<DeviceResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const idsParam = searchParams.get("ids");
    if (!idsParam) {
      setError("No devices selected for comparison");
      setLoading(false);
      return;
    }

    const ids = idsParam.split(",").map(Number).filter((n) => !isNaN(n));
    if (ids.length < 2 || ids.length > 3) {
      setError("Please select 2 or 3 devices to compare");
      setLoading(false);
      return;
    }

    compareDevices(ids)
      .then((data) => {
        setDevices(data.devices);
        setLoading(false);
      })
      .catch(() => {
        setError("Failed to load comparison. One or more devices may not exist.");
        setLoading(false);
      });
  }, [searchParams]);

  if (loading) {
    return (
      <main className="mx-auto max-w-6xl px-4 py-8 sm:px-6 lg:px-8">
        <div className="animate-pulse space-y-4">
          <div className="h-6 w-48 rounded bg-gray-200" />
          <div className="h-96 rounded-xl bg-gray-100" />
        </div>
      </main>
    );
  }

  if (error || devices.length === 0) {
    return (
      <main className="mx-auto max-w-6xl px-4 py-8 text-center sm:px-6 lg:px-8">
        <h1 className="mb-2 text-xl font-bold text-gray-900">{error || "No devices to compare"}</h1>
        <Link
          href="/devices"
          className="text-sm font-medium text-stone-600 underline hover:text-stone-800"
        >
          Back to catalog
        </Link>
      </main>
    );
  }

  // Collect all unique spec keys across all devices for the comparison table
  const allSpecKeys = Array.from(
    new Set(devices.flatMap((d) => (d.specs ? Object.keys(d.specs) : [])))
  );

  // Column width based on device count (2 or 3)
  const colClass = devices.length === 2 ? "w-1/2" : "w-1/3";

  return (
    <main className="mx-auto max-w-6xl px-4 py-8 sm:px-6 lg:px-8">
      {/* Breadcrumb */}
      <nav className="mb-6 text-sm text-gray-500">
        <Link href="/devices" className="hover:text-stone-700">
          Devices
        </Link>
        <span className="mx-2">/</span>
        <span className="text-gray-900">Compare</span>
      </nav>

      <h1 className="mb-8 text-2xl font-bold text-gray-900">Compare Devices</h1>

      <div className="overflow-x-auto">
        <table className="w-full min-w-[600px] border-collapse text-sm">
          {/* Device images + names header */}
          <thead>
            <tr>
              <th className="w-40 border-b border-gray-200 p-4 text-left text-xs font-semibold uppercase tracking-wide text-gray-400">
                Device
              </th>
              {devices.map((d) => (
                <th key={d.id} className={`${colClass} border-b border-gray-200 p-4 text-center`}>
                  <Link href={`/devices/${d.id}`} className="group">
                    <div className="mx-auto mb-3 flex h-32 w-32 items-center justify-center rounded-lg bg-gray-50 p-2">
                      <img
                        src={d.images?.[0] || "/placeholder-device.svg"}
                        alt={d.name}
                        className="max-h-full w-auto object-contain transition-transform group-hover:scale-105"
                      />
                    </div>
                    <p className="font-semibold text-gray-900 group-hover:text-stone-600">
                      {d.name}
                    </p>
                    <p className="text-xs text-gray-500">
                      {d.brand} · {d.category}
                    </p>
                  </Link>
                </th>
              ))}
            </tr>
          </thead>

          <tbody>
            {/* Pricing rows */}
            <CompareRow label="7-day trial" values={devices.map((d) => `€${d.trial_price_7d.toFixed(2)}`)} highlight />
            <CompareRow label="14-day trial" values={devices.map((d) => `€${d.trial_price_14d.toFixed(2)}`)} />
            <CompareRow label="Deposit" values={devices.map((d) => `€${d.deposit_amount.toFixed(2)}`)} />
            <CompareRow label="Purchase price" values={devices.map((d) => `€${d.purchase_price.toFixed(2)}`)} />
            <CompareRow
              label="Availability"
              values={devices.map((d) =>
                d.available_units > 0 ? `${d.available_units} available` : "Out of stock"
              )}
            />

            {/* Spec rows */}
            {allSpecKeys.length > 0 && (
              <tr>
                <td
                  colSpan={devices.length + 1}
                  className="border-b border-gray-200 bg-gray-50 px-4 py-2 text-xs font-semibold uppercase tracking-wide text-gray-500"
                >
                  Specifications
                </td>
              </tr>
            )}
            {allSpecKeys.map((key) => (
              <CompareRow
                key={key}
                label={key}
                values={devices.map((d) =>
                  d.specs && d.specs[key] ? String(d.specs[key]) : "—"
                )}
              />
            ))}
          </tbody>
        </table>
      </div>

      {/* CTA buttons */}
      <div className="mt-8 flex flex-wrap justify-center gap-3">
        {devices.map((d) => (
          <Link
            key={d.id}
            href={`/devices/${d.id}`}
            className="rounded-lg border border-stone-800 px-5 py-2.5 text-sm font-medium text-stone-800 transition-colors hover:bg-stone-800 hover:text-white"
          >
            View {d.name}
          </Link>
        ))}
      </div>
    </main>
  );
}

/** A single row in the comparison table */
function CompareRow({
  label,
  values,
  highlight = false,
}: {
  label: string;
  values: string[];
  highlight?: boolean;
}) {
  return (
    <tr className="border-b border-gray-100">
      <td className="px-4 py-3 text-sm font-medium text-gray-700">{label}</td>
      {values.map((val, idx) => (
        <td
          key={idx}
          className={`px-4 py-3 text-center ${
            highlight ? "font-bold text-stone-800" : "text-gray-600"
          }`}
        >
          {val}
        </td>
      ))}
    </tr>
  );
}
