"use client";

import { useEffect, useState, useCallback } from "react";
import { useSession } from "next-auth/react";
import {
  DeviceResponse,
  DeviceListResponse,
  DeviceUnitResponse,
  DeviceUnitListResponse,
  getDevices,
  adminCreateDevice,
  adminUpdateDevice,
  adminDeleteDevice,
  adminGetUnits,
  adminCreateUnit,
  adminUpdateUnit,
  adminDeleteUnit,
} from "@/lib/api";

// ── Tabs ──

type Tab = "devices" | "units";

// ── Condition grade + status labels ──

const CONDITION_GRADES = ["new", "like_new", "refurb_a", "refurb_b"];
const UNIT_STATUSES = [
  "available",
  "reserved",
  "shipped",
  "active",
  "returned",
  "refurbishing",
  "retired",
  "sold",
];

const STATUS_COLORS: Record<string, string> = {
  available: "bg-emerald-100 text-emerald-700",
  reserved: "bg-blue-100 text-blue-700",
  shipped: "bg-indigo-100 text-indigo-700",
  active: "bg-emerald-100 text-emerald-700",
  returned: "bg-amber-100 text-amber-700",
  refurbishing: "bg-orange-100 text-orange-700",
  retired: "bg-gray-200 text-gray-600",
  sold: "bg-purple-100 text-purple-700",
};

// ── Main page ──

export default function InventoryPage() {
  const { data: session } = useSession();
  const token = session?.accessToken as string | undefined;
  const [tab, setTab] = useState<Tab>("devices");

  if (!session) {
    return (
      <main className="mx-auto max-w-6xl px-4 py-8">
        <p className="text-gray-500">Sign in as admin to access inventory.</p>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-6xl px-4 py-8 sm:px-6 lg:px-8">
      <h1 className="mb-6 text-2xl font-bold text-gray-900">
        Inventory Management
      </h1>

      {/* Tab switcher */}
      <div className="mb-6 flex gap-1 rounded-lg bg-gray-100 p-1">
        {(["devices", "units"] as Tab[]).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`flex-1 rounded-md px-4 py-2 text-sm font-medium transition-colors ${
              tab === t
                ? "bg-white text-gray-900 shadow-sm"
                : "text-gray-500 hover:text-gray-700"
            }`}
          >
            {t === "devices" ? "Device Catalog" : "Physical Units"}
          </button>
        ))}
      </div>

      {tab === "devices" && token && <DevicesTab token={token} />}
      {tab === "units" && token && <UnitsTab token={token} />}
    </main>
  );
}

// ══════════════════════════════════════════════════════════════
// DEVICES TAB — catalog CRUD with pricing and featured toggle
// ══════════════════════════════════════════════════════════════

function DevicesTab({ token }: { token: string }) {
  const [devices, setDevices] = useState<DeviceResponse[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingDevice, setEditingDevice] = useState<DeviceResponse | null>(
    null
  );

  const fetchDevices = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getDevices({ page, page_size: 20 });
      setDevices(data.items);
      setTotal(data.total);
    } catch {
      /* ignore */
    } finally {
      setLoading(false);
    }
  }, [page]);

  useEffect(() => {
    fetchDevices();
  }, [fetchDevices]);

  const handleDelete = async (id: number, name: string) => {
    if (!confirm(`Deactivate "${name}"? It will be hidden from customers.`))
      return;
    try {
      await adminDeleteDevice(id, token);
      await fetchDevices();
    } catch (err: unknown) {
      alert((err as { detail?: string }).detail || "Failed to delete");
    }
  };

  const handleToggleFeatured = async (device: DeviceResponse) => {
    try {
      await adminUpdateDevice(
        device.id,
        { is_featured: !device.is_featured },
        token
      );
      await fetchDevices();
    } catch {
      /* ignore */
    }
  };

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <p className="text-sm text-gray-500">{total} devices in catalog</p>
        <button
          onClick={() => {
            setEditingDevice(null);
            setShowForm(true);
          }}
          className="rounded-lg bg-stone-800 px-4 py-2 text-sm font-medium text-white hover:bg-stone-700"
        >
          + Add device
        </button>
      </div>

      {/* Device form modal */}
      {showForm && (
        <DeviceForm
          token={token}
          device={editingDevice}
          onClose={() => {
            setShowForm(false);
            setEditingDevice(null);
          }}
          onSaved={() => {
            setShowForm(false);
            setEditingDevice(null);
            fetchDevices();
          }}
        />
      )}

      {/* Loading skeleton */}
      {loading && (
        <div className="space-y-2">
          {Array.from({ length: 5 }).map((_, i) => (
            <div
              key={i}
              className="animate-pulse rounded-lg border border-gray-200 bg-white p-4"
            >
              <div className="h-4 w-64 rounded bg-gray-100" />
            </div>
          ))}
        </div>
      )}

      {/* Device table */}
      {!loading && (
        <div className="overflow-x-auto rounded-xl border border-gray-200 bg-white">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-gray-100 bg-gray-50">
              <tr>
                <th className="px-4 py-3 font-medium text-gray-600">Device</th>
                <th className="px-4 py-3 font-medium text-gray-600">
                  Category
                </th>
                <th className="px-4 py-3 font-medium text-gray-600">
                  Trial 7d / 14d
                </th>
                <th className="px-4 py-3 font-medium text-gray-600">
                  Deposit
                </th>
                <th className="px-4 py-3 font-medium text-gray-600">Units</th>
                <th className="px-4 py-3 font-medium text-gray-600">
                  Featured
                </th>
                <th className="px-4 py-3 font-medium text-gray-600">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {devices.map((d) => (
                <tr key={d.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3">
                    <div className="font-medium text-gray-900">{d.name}</div>
                    <div className="text-xs text-gray-400">{d.brand}</div>
                  </td>
                  <td className="px-4 py-3 text-gray-600">{d.category}</td>
                  <td className="px-4 py-3 text-gray-600">
                    €{d.trial_price_7d.toFixed(2)} / €
                    {d.trial_price_14d.toFixed(2)}
                  </td>
                  <td className="px-4 py-3 text-gray-600">
                    €{d.deposit_amount.toFixed(2)}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`text-sm font-medium ${
                        d.available_units > 0
                          ? "text-emerald-600"
                          : "text-gray-400"
                      }`}
                    >
                      {d.available_units}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <button
                      onClick={() => handleToggleFeatured(d)}
                      className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                        d.is_featured
                          ? "bg-amber-100 text-amber-700"
                          : "bg-gray-100 text-gray-400"
                      }`}
                    >
                      {d.is_featured ? "Featured" : "—"}
                    </button>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex gap-2">
                      <button
                        onClick={() => {
                          setEditingDevice(d);
                          setShowForm(true);
                        }}
                        className="text-xs font-medium text-stone-600 hover:text-stone-800"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => handleDelete(d.id, d.name)}
                        className="text-xs font-medium text-red-500 hover:text-red-700"
                      >
                        Delete
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Pagination */}
      {total > 20 && (
        <div className="mt-4 flex items-center justify-center gap-2">
          <button
            disabled={page <= 1}
            onClick={() => setPage((p) => p - 1)}
            className="rounded border px-3 py-1 text-sm disabled:opacity-40"
          >
            Prev
          </button>
          <span className="text-sm text-gray-500">
            Page {page} of {Math.ceil(total / 20)}
          </span>
          <button
            disabled={page >= Math.ceil(total / 20)}
            onClick={() => setPage((p) => p + 1)}
            className="rounded border px-3 py-1 text-sm disabled:opacity-40"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}

// ── Device create/edit form ──

function DeviceForm({
  token,
  device,
  onClose,
  onSaved,
}: {
  token: string;
  device: DeviceResponse | null;
  onClose: () => void;
  onSaved: () => void;
}) {
  const isEdit = !!device;
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form fields
  const [name, setName] = useState(device?.name ?? "");
  const [brand, setBrand] = useState(device?.brand ?? "");
  const [category, setCategory] = useState(device?.category ?? "");
  const [description, setDescription] = useState(device?.description ?? "");
  const [trialPrice7d, setTrialPrice7d] = useState(
    device?.trial_price_7d?.toString() ?? ""
  );
  const [trialPrice14d, setTrialPrice14d] = useState(
    device?.trial_price_14d?.toString() ?? ""
  );
  const [purchasePrice, setPurchasePrice] = useState(
    device?.purchase_price?.toString() ?? ""
  );
  const [depositAmount, setDepositAmount] = useState(
    device?.deposit_amount?.toString() ?? ""
  );
  const [isFeatured, setIsFeatured] = useState(device?.is_featured ?? false);
  const [isActive, setIsActive] = useState(device?.is_active ?? true);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError(null);

    const data = {
      name,
      brand,
      category,
      description: description || undefined,
      trial_price_7d: parseFloat(trialPrice7d),
      trial_price_14d: parseFloat(trialPrice14d),
      purchase_price: parseFloat(purchasePrice),
      deposit_amount: parseFloat(depositAmount),
      is_featured: isFeatured,
      is_active: isActive,
    };

    try {
      if (isEdit && device) {
        await adminUpdateDevice(device.id, data, token);
      } else {
        await adminCreateDevice(data, token);
      }
      onSaved();
    } catch (err: unknown) {
      setError((err as { detail?: string }).detail || "Failed to save");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="mb-6 rounded-xl border border-gray-200 bg-white p-6">
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">
          {isEdit ? "Edit Device" : "Add New Device"}
        </h3>
        <button
          onClick={onClose}
          className="text-sm text-gray-400 hover:text-gray-600"
        >
          Cancel
        </button>
      </div>

      {error && (
        <div className="mb-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Row 1: name, brand, category */}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <label className="block">
            <span className="text-xs font-medium text-gray-600">Name *</span>
            <input
              type="text"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-stone-500 focus:outline-none focus:ring-1 focus:ring-stone-500"
            />
          </label>
          <label className="block">
            <span className="text-xs font-medium text-gray-600">Brand *</span>
            <input
              type="text"
              required
              value={brand}
              onChange={(e) => setBrand(e.target.value)}
              className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-stone-500 focus:outline-none focus:ring-1 focus:ring-stone-500"
            />
          </label>
          <label className="block">
            <span className="text-xs font-medium text-gray-600">
              Category *
            </span>
            <input
              type="text"
              required
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              placeholder="phones, laptops, tablets..."
              className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-stone-500 focus:outline-none focus:ring-1 focus:ring-stone-500"
            />
          </label>
        </div>

        {/* Description */}
        <label className="block">
          <span className="text-xs font-medium text-gray-600">Description</span>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={2}
            className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-stone-500 focus:outline-none focus:ring-1 focus:ring-stone-500"
          />
        </label>

        {/* Row 2: pricing */}
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          <label className="block">
            <span className="text-xs font-medium text-gray-600">
              Trial 7d (€) *
            </span>
            <input
              type="number"
              required
              step="0.01"
              min="0.01"
              value={trialPrice7d}
              onChange={(e) => setTrialPrice7d(e.target.value)}
              className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-stone-500 focus:outline-none focus:ring-1 focus:ring-stone-500"
            />
          </label>
          <label className="block">
            <span className="text-xs font-medium text-gray-600">
              Trial 14d (€) *
            </span>
            <input
              type="number"
              required
              step="0.01"
              min="0.01"
              value={trialPrice14d}
              onChange={(e) => setTrialPrice14d(e.target.value)}
              className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-stone-500 focus:outline-none focus:ring-1 focus:ring-stone-500"
            />
          </label>
          <label className="block">
            <span className="text-xs font-medium text-gray-600">
              Purchase (€) *
            </span>
            <input
              type="number"
              required
              step="0.01"
              min="0.01"
              value={purchasePrice}
              onChange={(e) => setPurchasePrice(e.target.value)}
              className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-stone-500 focus:outline-none focus:ring-1 focus:ring-stone-500"
            />
          </label>
          <label className="block">
            <span className="text-xs font-medium text-gray-600">
              Deposit (€) *
            </span>
            <input
              type="number"
              required
              step="0.01"
              min="0.01"
              value={depositAmount}
              onChange={(e) => setDepositAmount(e.target.value)}
              className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-stone-500 focus:outline-none focus:ring-1 focus:ring-stone-500"
            />
          </label>
        </div>

        {/* Toggles */}
        <div className="flex items-center gap-6">
          <label className="flex items-center gap-2 text-sm text-gray-700">
            <input
              type="checkbox"
              checked={isFeatured}
              onChange={(e) => setIsFeatured(e.target.checked)}
              className="rounded border-gray-300"
            />
            Featured on homepage
          </label>
          <label className="flex items-center gap-2 text-sm text-gray-700">
            <input
              type="checkbox"
              checked={isActive}
              onChange={(e) => setIsActive(e.target.checked)}
              className="rounded border-gray-300"
            />
            Active (visible to customers)
          </label>
        </div>

        {/* Submit */}
        <div className="flex justify-end">
          <button
            type="submit"
            disabled={saving}
            className="rounded-lg bg-stone-800 px-6 py-2 text-sm font-medium text-white hover:bg-stone-700 disabled:opacity-50"
          >
            {saving ? "Saving..." : isEdit ? "Update Device" : "Create Device"}
          </button>
        </div>
      </form>
    </div>
  );
}

// ══════════════════════════════════════════════════════════════
// UNITS TAB — physical unit management with serial tracking
// ══════════════════════════════════════════════════════════════

function UnitsTab({ token }: { token: string }) {
  const [units, setUnits] = useState<DeviceUnitResponse[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState("");
  const [conditionFilter, setConditionFilter] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [editingUnit, setEditingUnit] = useState<DeviceUnitResponse | null>(
    null
  );

  // We need device list for the "device_id" dropdown in the create form
  const [deviceOptions, setDeviceOptions] = useState<
    { id: number; name: string; brand: string }[]
  >([]);

  const fetchUnits = useCallback(async () => {
    setLoading(true);
    try {
      const params: Record<string, string | number> = { page, page_size: 20 };
      if (statusFilter) params.status = statusFilter;
      if (conditionFilter) params.condition_grade = conditionFilter;
      const data = await adminGetUnits(token, params);
      setUnits(data.items);
      setTotal(data.total);
    } catch {
      /* ignore */
    } finally {
      setLoading(false);
    }
  }, [token, page, statusFilter, conditionFilter]);

  // Fetch device options for dropdown (once)
  useEffect(() => {
    getDevices({ page: 1, page_size: 200 }).then((data) => {
      setDeviceOptions(
        data.items.map((d) => ({ id: d.id, name: d.name, brand: d.brand }))
      );
    });
  }, []);

  useEffect(() => {
    fetchUnits();
  }, [fetchUnits]);

  const handleDelete = async (unitId: number, serial: string) => {
    if (!confirm(`Delete unit "${serial}"? Only works if it has no rental history.`))
      return;
    try {
      await adminDeleteUnit(unitId, token);
      await fetchUnits();
    } catch (err: unknown) {
      alert((err as { detail?: string }).detail || "Failed to delete");
    }
  };

  return (
    <div>
      {/* Filters */}
      <div className="mb-4 flex flex-wrap items-center gap-3">
        <p className="text-sm text-gray-500">{total} units total</p>
        <div className="ml-auto flex gap-2">
          <select
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value);
              setPage(1);
            }}
            className="rounded-lg border border-gray-300 px-3 py-1.5 text-sm"
          >
            <option value="">All statuses</option>
            {UNIT_STATUSES.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
          <select
            value={conditionFilter}
            onChange={(e) => {
              setConditionFilter(e.target.value);
              setPage(1);
            }}
            className="rounded-lg border border-gray-300 px-3 py-1.5 text-sm"
          >
            <option value="">All conditions</option>
            {CONDITION_GRADES.map((g) => (
              <option key={g} value={g}>
                {g.replace("_", " ")}
              </option>
            ))}
          </select>
          <button
            onClick={() => {
              setEditingUnit(null);
              setShowForm(true);
            }}
            className="rounded-lg bg-stone-800 px-4 py-1.5 text-sm font-medium text-white hover:bg-stone-700"
          >
            + Add unit
          </button>
        </div>
      </div>

      {/* Unit form */}
      {showForm && (
        <UnitForm
          token={token}
          unit={editingUnit}
          deviceOptions={deviceOptions}
          onClose={() => {
            setShowForm(false);
            setEditingUnit(null);
          }}
          onSaved={() => {
            setShowForm(false);
            setEditingUnit(null);
            fetchUnits();
          }}
        />
      )}

      {/* Loading */}
      {loading && (
        <div className="space-y-2">
          {Array.from({ length: 5 }).map((_, i) => (
            <div
              key={i}
              className="animate-pulse rounded-lg border border-gray-200 bg-white p-4"
            >
              <div className="h-4 w-64 rounded bg-gray-100" />
            </div>
          ))}
        </div>
      )}

      {/* Units table */}
      {!loading && (
        <div className="overflow-x-auto rounded-xl border border-gray-200 bg-white">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-gray-100 bg-gray-50">
              <tr>
                <th className="px-4 py-3 font-medium text-gray-600">
                  Serial #
                </th>
                <th className="px-4 py-3 font-medium text-gray-600">
                  Device
                </th>
                <th className="px-4 py-3 font-medium text-gray-600">
                  Condition
                </th>
                <th className="px-4 py-3 font-medium text-gray-600">
                  Status
                </th>
                <th className="px-4 py-3 font-medium text-gray-600">
                  Rentals
                </th>
                <th className="px-4 py-3 font-medium text-gray-600">
                  Revenue
                </th>
                <th className="px-4 py-3 font-medium text-gray-600">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {units.map((u) => {
                const deviceName =
                  deviceOptions.find((d) => d.id === u.device_id)?.name ??
                  `#${u.device_id}`;
                return (
                  <tr key={u.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 font-mono text-xs text-gray-800">
                      {u.serial_number}
                    </td>
                    <td className="px-4 py-3 text-gray-600">{deviceName}</td>
                    <td className="px-4 py-3">
                      <span className="rounded bg-gray-100 px-2 py-0.5 text-xs text-gray-600">
                        {u.condition_grade.replace("_", " ")}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                          STATUS_COLORS[u.status] || "bg-gray-100 text-gray-600"
                        }`}
                      >
                        {u.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-gray-600">
                      {u.rental_count}
                    </td>
                    <td className="px-4 py-3 text-gray-600">
                      €{u.total_lifecycle_revenue.toFixed(2)}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex gap-2">
                        <button
                          onClick={() => {
                            setEditingUnit(u);
                            setShowForm(true);
                          }}
                          className="text-xs font-medium text-stone-600 hover:text-stone-800"
                        >
                          Edit
                        </button>
                        <button
                          onClick={() =>
                            handleDelete(u.id, u.serial_number)
                          }
                          className="text-xs font-medium text-red-500 hover:text-red-700"
                        >
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Pagination */}
      {total > 20 && (
        <div className="mt-4 flex items-center justify-center gap-2">
          <button
            disabled={page <= 1}
            onClick={() => setPage((p) => p - 1)}
            className="rounded border px-3 py-1 text-sm disabled:opacity-40"
          >
            Prev
          </button>
          <span className="text-sm text-gray-500">
            Page {page} of {Math.ceil(total / 20)}
          </span>
          <button
            disabled={page >= Math.ceil(total / 20)}
            onClick={() => setPage((p) => p + 1)}
            className="rounded border px-3 py-1 text-sm disabled:opacity-40"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}

// ── Unit create/edit form ──

function UnitForm({
  token,
  unit,
  deviceOptions,
  onClose,
  onSaved,
}: {
  token: string;
  unit: DeviceUnitResponse | null;
  deviceOptions: { id: number; name: string; brand: string }[];
  onClose: () => void;
  onSaved: () => void;
}) {
  const isEdit = !!unit;
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [deviceId, setDeviceId] = useState(unit?.device_id?.toString() ?? "");
  const [serialNumber, setSerialNumber] = useState(unit?.serial_number ?? "");
  const [conditionGrade, setConditionGrade] = useState(
    unit?.condition_grade ?? "new"
  );
  const [unitStatus, setUnitStatus] = useState(unit?.status ?? "available");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError(null);

    try {
      if (isEdit && unit) {
        await adminUpdateUnit(
          unit.id,
          {
            serial_number: serialNumber,
            condition_grade: conditionGrade,
            status: unitStatus,
          },
          token
        );
      } else {
        await adminCreateUnit(
          {
            device_id: parseInt(deviceId, 10),
            serial_number: serialNumber,
            condition_grade: conditionGrade,
          },
          token
        );
      }
      onSaved();
    } catch (err: unknown) {
      setError((err as { detail?: string }).detail || "Failed to save");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="mb-6 rounded-xl border border-gray-200 bg-white p-6">
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">
          {isEdit ? "Edit Unit" : "Register New Unit"}
        </h3>
        <button
          onClick={onClose}
          className="text-sm text-gray-400 hover:text-gray-600"
        >
          Cancel
        </button>
      </div>

      {error && (
        <div className="mb-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {/* Device picker — only on create */}
          {!isEdit && (
            <label className="block">
              <span className="text-xs font-medium text-gray-600">
                Device *
              </span>
              <select
                required
                value={deviceId}
                onChange={(e) => setDeviceId(e.target.value)}
                className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-stone-500 focus:outline-none focus:ring-1 focus:ring-stone-500"
              >
                <option value="">Select device...</option>
                {deviceOptions.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.brand} {d.name}
                  </option>
                ))}
              </select>
            </label>
          )}

          <label className="block">
            <span className="text-xs font-medium text-gray-600">
              Serial Number *
            </span>
            <input
              type="text"
              required
              value={serialNumber}
              onChange={(e) => setSerialNumber(e.target.value)}
              className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm font-mono focus:border-stone-500 focus:outline-none focus:ring-1 focus:ring-stone-500"
            />
          </label>

          <label className="block">
            <span className="text-xs font-medium text-gray-600">
              Condition
            </span>
            <select
              value={conditionGrade}
              onChange={(e) => setConditionGrade(e.target.value)}
              className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-stone-500 focus:outline-none focus:ring-1 focus:ring-stone-500"
            >
              {CONDITION_GRADES.map((g) => (
                <option key={g} value={g}>
                  {g.replace("_", " ")}
                </option>
              ))}
            </select>
          </label>

          {/* Status — only on edit */}
          {isEdit && (
            <label className="block">
              <span className="text-xs font-medium text-gray-600">Status</span>
              <select
                value={unitStatus}
                onChange={(e) => setUnitStatus(e.target.value)}
                className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-stone-500 focus:outline-none focus:ring-1 focus:ring-stone-500"
              >
                {UNIT_STATUSES.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
            </label>
          )}
        </div>

        <div className="flex justify-end">
          <button
            type="submit"
            disabled={saving}
            className="rounded-lg bg-stone-800 px-6 py-2 text-sm font-medium text-white hover:bg-stone-700 disabled:opacity-50"
          >
            {saving
              ? "Saving..."
              : isEdit
                ? "Update Unit"
                : "Register Unit"}
          </button>
        </div>
      </form>
    </div>
  );
}
