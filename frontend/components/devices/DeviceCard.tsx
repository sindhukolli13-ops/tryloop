"use client";

import Link from "next/link";
import { DeviceResponse } from "@/lib/api";

interface DeviceCardProps {
  device: DeviceResponse;
  /** When true, shows a checkbox for comparison selection */
  selectable?: boolean;
  selected?: boolean;
  onToggleSelect?: (id: number) => void;
}

/**
 * Product card shown in the device catalog grid.
 * Displays image, name, brand, price, and availability status.
 */
export default function DeviceCard({
  device,
  selectable = false,
  selected = false,
  onToggleSelect,
}: DeviceCardProps) {
  // Pick the first image or use a placeholder
  const imageUrl =
    device.images && device.images.length > 0
      ? device.images[0]
      : "/placeholder-device.svg";

  // Availability badge color
  const availabilityLabel =
    device.available_units > 0
      ? `${device.available_units} available`
      : "Out of stock";
  const availabilityColor =
    device.available_units > 0 ? "bg-emerald-100 text-emerald-700" : "bg-gray-100 text-gray-500";

  return (
    <div className="group relative rounded-xl border border-gray-200 bg-white shadow-sm transition-shadow hover:shadow-md">
      {/* Comparison checkbox */}
      {selectable && (
        <label className="absolute left-3 top-3 z-10 flex cursor-pointer items-center gap-1.5 rounded-full bg-white/90 px-2.5 py-1 text-xs font-medium shadow-sm backdrop-blur-sm">
          <input
            type="checkbox"
            checked={selected}
            onChange={() => onToggleSelect?.(device.id)}
            className="h-3.5 w-3.5 rounded border-gray-300 text-stone-800 focus:ring-stone-500"
          />
          Compare
        </label>
      )}

      {/* Featured badge */}
      {device.is_featured && (
        <span className="absolute right-3 top-3 z-10 rounded-full bg-amber-100 px-2.5 py-1 text-xs font-medium text-amber-700">
          Featured
        </span>
      )}

      <Link href={`/devices/${device.id}`} className="block">
        {/* Image */}
        <div className="flex h-48 items-center justify-center overflow-hidden rounded-t-xl bg-gray-50 p-4">
          <img
            src={imageUrl}
            alt={device.name}
            className="h-full max-h-40 w-auto object-contain transition-transform group-hover:scale-105"
          />
        </div>

        {/* Content */}
        <div className="p-4">
          {/* Category & brand */}
          <div className="mb-1 flex items-center gap-2 text-xs text-gray-500">
            <span>{device.category}</span>
            <span className="text-gray-300">·</span>
            <span>{device.brand}</span>
          </div>

          {/* Name */}
          <h3 className="mb-2 text-sm font-semibold text-gray-900 line-clamp-2">
            {device.name}
          </h3>

          {/* Pricing */}
          <div className="mb-3 space-y-0.5">
            <p className="text-base font-bold text-stone-800">
              €{device.trial_price_7d.toFixed(2)}{" "}
              <span className="text-xs font-normal text-gray-400">/ 7-day trial</span>
            </p>
            <p className="text-xs text-gray-500">
              14-day trial: €{device.trial_price_14d.toFixed(2)}
            </p>
          </div>

          {/* Availability */}
          <span
            className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-medium ${availabilityColor}`}
          >
            {availabilityLabel}
          </span>
        </div>
      </Link>
    </div>
  );
}
