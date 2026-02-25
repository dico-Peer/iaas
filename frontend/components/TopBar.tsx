"use client";

import { useAuthStore } from "@/lib/store";

function getInitials(name: string | null, email: string): string {
  if (name?.trim()) {
    return name
      .split(/\s+/)
      .map((n) => n[0])
      .join("")
      .toUpperCase()
      .slice(0, 2);
  }
  return email.slice(0, 2).toUpperCase();
}

export function TopBar() {
  const user = useAuthStore((s) => s.user);
  const org = useAuthStore((s) => s.org);

  return (
    <header className="flex h-14 items-center justify-between border-b bg-white px-6">
      <span className="font-medium">{org?.name ?? "Organization"}</span>
      <div className="flex items-center gap-4">
        <button
          type="button"
          className="rounded border px-3 py-1 text-sm"
        >
          Preview as Interviewee
        </button>
        <div className="flex items-center gap-2">
          <div
            className="flex h-8 w-8 items-center justify-center rounded-full bg-gray-200 text-sm font-medium"
            title={user?.email}
          >
            {user ? getInitials(user.name, user.email) : "?"}
          </div>
          <span className="text-sm">{user?.name ?? user?.email ?? "User"}</span>
        </div>
      </div>
    </header>
  );
}
