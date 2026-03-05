"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { DeviceResponse, getDevice } from "@/lib/api";

export default function DeviceDetailPage() {
  const params = useParams();
  const deviceId = Number(params.id);

  const [device, setDevice] = useState<DeviceResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedImage, setSelectedImage] = useState(0);

  useEffect(() => {
    if (!deviceId || isNaN(deviceId)) {
      setError("Invalid device ID");
      setLoading(false);
      return;
    }

    getDevice(deviceId)
      .then((data) => {
        setDevice(data);
        setLoading(false);
      })
      .catch(() => {
        setError("Device not found");
        setLoading(false);
      });
  }, [deviceId]);

  if (loading) {
    return (
      <main className="mx-auto max-w-5xl px-4 py-8 sm:px-6 lg:px-8">
        <div className="animate-pulse">
          <div className="mb-6 h-4 w-48 rounded bg-gray-200" />
          <div className="grid gap-8 md:grid-cols-2">
            <div className="h-80 rounded-xl bg-gray-100" />
            <div className="space-y-4">
              <div className="h-6 w-32 rounded bg-gray-200" />
              <div className="h-8 w-64 rounded bg-gray-200" />
              <div className="h-4 w-full rounded bg-gray-100" />
              <div className="h-4 w-3/4 rounded bg-gray-100" />
            </div>
          </div>
        </div>
      </main>
    );
  }

  if (error || !device) {
    return (
      <main className="mx-auto max-w-5xl px-4 py-8 text-center sm:px-6 lg:px-8">
        <h1 className="mb-2 text-xl font-bold text-gray-900">{error || "Device not found"}</h1>
        <Link
          href="/devices"
          className="text-sm font-medium text-stone-600 underline hover:text-stone-800"
        >
          Back to catalog
        </Link>
      </main>
    );
  }

  const images = device.images && device.images.length > 0 ? device.images : ["/placeholder-device.svg"];
  const specs = device.specs ? Object.entries(device.specs) : [];

  // Availability label
  const isAvailable = device.available_units > 0;

  return (
    <main className="mx-auto max-w-5xl px-4 py-8 sm:px-6 lg:px-8">
      {/* Breadcrumb */}
      <nav className="mb-6 text-sm text-gray-500">
        <Link href="/devices" className="hover:text-stone-700">
          Devices
        </Link>
        <span className="mx-2">/</span>
        <span className="text-gray-900">{device.name}</span>
      </nav>

      <div className="grid gap-8 md:grid-cols-2">
        {/* Image gallery */}
        <div>
          <div className="mb-3 flex h-72 items-center justify-center rounded-xl bg-gray-50 p-6 sm:h-80">
            <img
              src={images[selectedImage]}
              alt={device.name}
              className="max-h-full w-auto object-contain"
            />
          </div>
          {images.length > 1 && (
            <div className="flex gap-2 overflow-x-auto">
              {images.map((img, idx) => (
                <button
                  key={idx}
                  onClick={() => setSelectedImage(idx)}
                  className={`h-16 w-16 shrink-0 overflow-hidden rounded-lg border-2 p-1 transition-colors ${
                    idx === selectedImage
                      ? "border-stone-800"
                      : "border-gray-200 hover:border-gray-400"
                  }`}
                >
                  <img src={img} alt="" className="h-full w-full object-contain" />
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Details */}
        <div>
          <div className="mb-1 flex items-center gap-2 text-sm text-gray-500">
            <span>{device.category}</span>
            <span className="text-gray-300">·</span>
            <span>{device.brand}</span>
          </div>

          <h1 className="mb-3 text-2xl font-bold text-gray-900">{device.name}</h1>

          {/* Availability badge */}
          <span
            className={`mb-4 inline-block rounded-full px-3 py-1 text-xs font-medium ${
              isAvailable
                ? "bg-emerald-100 text-emerald-700"
                : "bg-gray-100 text-gray-500"
            }`}
          >
            {isAvailable ? `${device.available_units} available` : "Out of stock"}
          </span>

          {/* Description */}
          {device.description && (
            <p className="mb-6 text-sm leading-relaxed text-gray-600">{device.description}</p>
          )}

          {/* Pricing card */}
          <div className="mb-6 rounded-xl border border-gray-200 bg-gray-50 p-5">
            <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-gray-500">
              Trial Pricing
            </h2>
            <div className="space-y-2">
              <div className="flex items-baseline justify-between">
                <span className="text-sm text-gray-600">7-day trial</span>
                <span className="text-lg font-bold text-stone-800">
                  €{device.trial_price_7d.toFixed(2)}
                </span>
              </div>
              <div className="flex items-baseline justify-between">
                <span className="text-sm text-gray-600">14-day trial</span>
                <span className="text-lg font-bold text-stone-800">
                  €{device.trial_price_14d.toFixed(2)}
                </span>
              </div>
              <hr className="my-2 border-gray-200" />
              <div className="flex items-baseline justify-between">
                <span className="text-sm text-gray-600">Refundable deposit</span>
                <span className="text-base font-semibold text-gray-700">
                  €{device.deposit_amount.toFixed(2)}
                </span>
              </div>
              <div className="flex items-baseline justify-between">
                <span className="text-sm text-gray-600">Purchase price (new)</span>
                <span className="text-base font-semibold text-gray-700">
                  €{device.purchase_price.toFixed(2)}
                </span>
              </div>
            </div>
          </div>

          {/* CTA — links to checkout (to be built in Step 5) */}
          <button
            disabled={!isAvailable}
            className="w-full rounded-lg bg-stone-800 px-6 py-3 text-sm font-semibold text-white transition-colors hover:bg-stone-700 disabled:cursor-not-allowed disabled:bg-gray-300 disabled:text-gray-500"
          >
            {isAvailable ? "Start a Trial" : "Currently Unavailable"}
          </button>
          <p className="mt-2 text-center text-xs text-gray-400">
            Trial fee is non-refundable. Deposit is fully refunded on return.
          </p>
        </div>
      </div>

      {/* Specs table */}
      {specs.length > 0 && (
        <section className="mt-10">
          <h2 className="mb-4 text-lg font-semibold text-gray-900">Specifications</h2>
          <div className="overflow-hidden rounded-xl border border-gray-200">
            <table className="w-full text-sm">
              <tbody>
                {specs.map(([key, value], idx) => (
                  <tr
                    key={key}
                    className={idx % 2 === 0 ? "bg-white" : "bg-gray-50"}
                  >
                    <td className="px-4 py-3 font-medium text-gray-700">{key}</td>
                    <td className="px-4 py-3 text-gray-600">{String(value)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </main>
  );
}
