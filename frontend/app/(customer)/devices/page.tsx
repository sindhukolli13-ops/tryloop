"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import {
  DeviceListParams,
  DeviceResponse,
  FilterOptions,
  getDevices,
  getFilterOptions,
} from "@/lib/api";
import DeviceCard from "@/components/devices/DeviceCard";
import DeviceFilters, { ActiveFilters } from "@/components/devices/DeviceFilters";

const DEFAULT_FILTERS: ActiveFilters = {
  category: "",
  brand: "",
  search: "",
  min_price: "",
  max_price: "",
  available_only: false,
};

const PAGE_SIZE = 12;

export default function DevicesPage() {
  const [devices, setDevices] = useState<DeviceResponse[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<ActiveFilters>(DEFAULT_FILTERS);
  const [filterOptions, setFilterOptions] = useState<FilterOptions | null>(null);
  // Track which device IDs are selected for comparison
  const [compareIds, setCompareIds] = useState<Set<number>>(new Set());
  // Mobile filter drawer toggle
  const [showMobileFilters, setShowMobileFilters] = useState(false);

  // Load filter options (categories, brands) once on mount
  useEffect(() => {
    getFilterOptions()
      .then(setFilterOptions)
      .catch(() => {}); // non-critical — filters still work without options
  }, []);

  // Fetch devices whenever filters or page changes
  const fetchDevices = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params: DeviceListParams = {
        page,
        page_size: PAGE_SIZE,
      };
      if (filters.category) params.category = filters.category;
      if (filters.brand) params.brand = filters.brand;
      if (filters.search) params.search = filters.search;
      if (filters.min_price) params.min_price = parseFloat(filters.min_price);
      if (filters.max_price) params.max_price = parseFloat(filters.max_price);
      if (filters.available_only) params.available_only = true;

      const data = await getDevices(params);
      setDevices(data.items);
      setTotal(data.total);
    } catch {
      setError("Failed to load devices. Please try again.");
    } finally {
      setLoading(false);
    }
  }, [page, filters]);

  useEffect(() => {
    fetchDevices();
  }, [fetchDevices]);

  // Reset to page 1 when filters change
  const handleFilterChange = (newFilters: ActiveFilters) => {
    setPage(1);
    setFilters(newFilters);
  };

  const handleFilterReset = () => {
    setPage(1);
    setFilters(DEFAULT_FILTERS);
  };

  // Comparison selection (max 3)
  const toggleCompare = (id: number) => {
    setCompareIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else if (next.size < 3) {
        next.add(id);
      }
      return next;
    });
  };

  const totalPages = Math.ceil(total / PAGE_SIZE);

  return (
    <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900 sm:text-3xl">Device Catalog</h1>
        <p className="mt-1 text-sm text-gray-500">
          Browse our collection of electronics available for trial
        </p>
      </div>

      {/* Comparison bar — shown when devices are selected */}
      {compareIds.size > 0 && (
        <div className="mb-6 flex items-center justify-between rounded-lg border border-stone-200 bg-stone-50 px-4 py-3">
          <p className="text-sm text-stone-700">
            <span className="font-medium">{compareIds.size}</span> of 3 devices selected for
            comparison
          </p>
          <div className="flex gap-2">
            <button
              onClick={() => setCompareIds(new Set())}
              className="rounded-lg px-3 py-1.5 text-sm font-medium text-gray-600 hover:bg-gray-100"
            >
              Clear
            </button>
            {compareIds.size >= 2 && (
              <Link
                href={`/devices/compare?ids=${Array.from(compareIds).join(",")}`}
                className="rounded-lg bg-stone-800 px-4 py-1.5 text-sm font-medium text-white transition-colors hover:bg-stone-700"
              >
                Compare now
              </Link>
            )}
          </div>
        </div>
      )}

      {/* Mobile filter toggle */}
      <button
        onClick={() => setShowMobileFilters(!showMobileFilters)}
        className="mb-4 flex items-center gap-2 rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 lg:hidden"
      >
        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
        </svg>
        Filters
      </button>

      <div className="flex gap-8">
        {/* Sidebar filters — hidden on mobile unless toggled */}
        <div
          className={`w-64 shrink-0 ${showMobileFilters ? "block" : "hidden"} lg:block`}
        >
          <DeviceFilters
            filters={filters}
            filterOptions={filterOptions}
            onChange={handleFilterChange}
            onReset={handleFilterReset}
          />
        </div>

        {/* Main content */}
        <div className="flex-1">
          {/* Result count */}
          {!loading && (
            <p className="mb-4 text-sm text-gray-500">
              {total} device{total !== 1 ? "s" : ""} found
            </p>
          )}

          {/* Error state */}
          {error && (
            <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
              {error}
            </div>
          )}

          {/* Loading state */}
          {loading && (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
              {Array.from({ length: 6 }).map((_, i) => (
                <div key={i} className="animate-pulse rounded-xl border border-gray-200 bg-white">
                  <div className="h-48 rounded-t-xl bg-gray-100" />
                  <div className="space-y-2 p-4">
                    <div className="h-3 w-24 rounded bg-gray-100" />
                    <div className="h-4 w-40 rounded bg-gray-100" />
                    <div className="h-5 w-28 rounded bg-gray-100" />
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Device grid */}
          {!loading && !error && devices.length > 0 && (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
              {devices.map((device) => (
                <DeviceCard
                  key={device.id}
                  device={device}
                  selectable
                  selected={compareIds.has(device.id)}
                  onToggleSelect={toggleCompare}
                />
              ))}
            </div>
          )}

          {/* Empty state */}
          {!loading && !error && devices.length === 0 && (
            <div className="flex flex-col items-center justify-center rounded-xl border-2 border-dashed border-gray-200 py-16 text-center">
              <p className="text-lg font-medium text-gray-900">No devices found</p>
              <p className="mt-1 text-sm text-gray-500">
                Try adjusting your filters or search terms
              </p>
              <button
                onClick={handleFilterReset}
                className="mt-4 rounded-lg bg-stone-800 px-4 py-2 text-sm font-medium text-white hover:bg-stone-700"
              >
                Clear all filters
              </button>
            </div>
          )}

          {/* Pagination */}
          {totalPages > 1 && (
            <nav className="mt-8 flex items-center justify-center gap-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="rounded-lg border border-gray-300 px-3 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-40"
              >
                Previous
              </button>
              <span className="px-3 text-sm text-gray-600">
                Page {page} of {totalPages}
              </span>
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="rounded-lg border border-gray-300 px-3 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-40"
              >
                Next
              </button>
            </nav>
          )}
        </div>
      </div>
    </main>
  );
}
