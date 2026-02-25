"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { useAuthStore } from "@/lib/store";
import { fetchProjects, type Project } from "@/lib/api";

function formatDate(s: string | null): string {
  if (!s) return "—";
  try {
    return new Date(s).toLocaleDateString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  } catch {
    return "—";
  }
}

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    draft: "bg-gray-200 text-gray-800",
    active: "bg-green-200 text-green-800",
    paused: "bg-yellow-200 text-yellow-800",
    completed: "bg-blue-200 text-blue-800",
    archived: "bg-gray-300 text-gray-600",
  };
  return (
    <span
      className={`rounded px-2 py-0.5 text-xs font-medium ${colors[status] ?? "bg-gray-200"}`}
    >
      {status}
    </span>
  );
}

export default function ProjectsPage() {
  const token = useAuthStore((s) => s.token);
  const [projects, setProjects] = useState<Project[]>([]);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Debounce search 300ms
  useEffect(() => {
    const t = setTimeout(() => setDebouncedSearch(search), 300);
    return () => clearTimeout(t);
  }, [search]);

  const load = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      const data = await fetchProjects(token, debouncedSearch || undefined);
      setProjects(data.projects);
      setTotal(data.total);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load");
    } finally {
      setLoading(false);
    }
  }, [token, debouncedSearch]);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold">Projects</h1>
      </div>
      <div className="mb-4">
        <input
          type="search"
          placeholder="Search projects..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full max-w-sm rounded border px-3 py-2"
          data-testid="project-search"
        />
      </div>
      {error && (
        <div className="mb-4 rounded border border-red-200 bg-red-50 p-3 text-red-700">
          {error}
        </div>
      )}
      {loading ? (
        <p>Loading...</p>
      ) : (
        <div className="overflow-x-auto rounded border">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">
                  Title
                </th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">
                  Status
                </th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">
                  Interviews
                </th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">
                  Completion %
                </th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">
                  Cost
                </th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">
                  Created
                </th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">
                  Last modified
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 bg-white">
              {projects.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-4 py-8 text-center text-gray-500">
                    No projects yet. Create one to get started.
                  </td>
                </tr>
              ) : (
                projects.map((p) => (
                  <tr key={p.id}>
                    <td className="px-4 py-3 font-medium">
                      <Link href={`/projects/${p.id}`} className="text-blue-600 hover:underline">
                        {p.title}
                      </Link>
                    </td>
                    <td className="px-4 py-3">
                      <StatusBadge status={p.status} />
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600">
                      {p.interview_count ?? 0}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600">
                      {p.completion_pct != null ? `${p.completion_pct}%` : "0%"}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600">
                      {p.cost ?? "—"}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600">
                      {formatDate(p.created_at)}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600">
                      {formatDate(p.updated_at)}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}
      {!loading && total > 0 && (
        <p className="mt-2 text-sm text-gray-500">{total} project(s)</p>
      )}
    </div>
  );
}
