"use client";

import { FilterOptions } from "@/lib/api";

export interface ActiveFilters {
  category: string;
  brand: string;
  search: string;
  min_price: string;
  max_price: string;
  available_only: boolean;
}

interface DeviceFiltersProps {
  filters: ActiveFilters;
  filterOptions: FilterOptions | null;
  onChange: (filters: ActiveFilters) => void;
  onReset: () => void;
}

/**
 * Sidebar filter panel for the device catalog.
 * Supports category, brand, price range, and availability filtering.
 */
export default function DeviceFilters({
  filters,
  filterOptions,
  onChange,
  onReset,
}: DeviceFiltersProps) {
  const update = (key: keyof ActiveFilters, value: string | boolean) => {
    onChange({ ...filters, [key]: value });
  };

  const hasActiveFilters =
    filters.category ||
    filters.brand ||
    filters.search ||
    filters.min_price ||
    filters.max_price ||
    filters.available_only;

  return (
    <aside className="space-y-6">
      {/* Search */}
      <div>
        <label htmlFor="search" className="mb-1.5 block text-sm font-medium text-gray-700">
          Search
        </label>
        <input
          id="search"
          type="text"
          placeholder="Search devices..."
          value={filters.search}
          onChange={(e) => update("search", e.target.value)}
          className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm placeholder-gray-400 focus:border-stone-500 focus:outline-none focus:ring-1 focus:ring-stone-500"
        />
      </div>

      {/* Category */}
      <div>
        <label htmlFor="category" className="mb-1.5 block text-sm font-medium text-gray-700">
          Category
        </label>
        <select
          id="category"
          value={filters.category}
          onChange={(e) => update("category", e.target.value)}
          className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-stone-500 focus:outline-none focus:ring-1 focus:ring-stone-500"
        >
          <option value="">All categories</option>
          {filterOptions?.categories.map((cat) => (
            <option key={cat} value={cat}>
              {cat}
            </option>
          ))}
        </select>
      </div>

      {/* Brand */}
      <div>
        <label htmlFor="brand" className="mb-1.5 block text-sm font-medium text-gray-700">
          Brand
        </label>
        <select
          id="brand"
          value={filters.brand}
          onChange={(e) => update("brand", e.target.value)}
          className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-stone-500 focus:outline-none focus:ring-1 focus:ring-stone-500"
        >
          <option value="">All brands</option>
          {filterOptions?.brands.map((b) => (
            <option key={b} value={b}>
              {b}
            </option>
          ))}
        </select>
      </div>

      {/* Price range */}
      <div>
        <span className="mb-1.5 block text-sm font-medium text-gray-700">
          Trial price range (7-day)
        </span>
        <div className="flex items-center gap-2">
          <input
            type="number"
            placeholder="Min"
            min={0}
            value={filters.min_price}
            onChange={(e) => update("min_price", e.target.value)}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm placeholder-gray-400 focus:border-stone-500 focus:outline-none focus:ring-1 focus:ring-stone-500"
          />
          <span className="text-gray-400">—</span>
          <input
            type="number"
            placeholder="Max"
            min={0}
            value={filters.max_price}
            onChange={(e) => update("max_price", e.target.value)}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm placeholder-gray-400 focus:border-stone-500 focus:outline-none focus:ring-1 focus:ring-stone-500"
          />
        </div>
      </div>

      {/* Available only */}
      <label className="flex cursor-pointer items-center gap-2 text-sm text-gray-700">
        <input
          type="checkbox"
          checked={filters.available_only}
          onChange={(e) => update("available_only", e.target.checked)}
          className="h-4 w-4 rounded border-gray-300 text-stone-800 focus:ring-stone-500"
        />
        Available now only
      </label>

      {/* Reset */}
      {hasActiveFilters && (
        <button
          onClick={onReset}
          className="w-full rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-600 transition-colors hover:bg-gray-50"
        >
          Clear all filters
        </button>
      )}
    </aside>
  );
}
