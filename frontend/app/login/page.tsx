"use client";

import { useRouter } from "next/navigation";
import { useAuthStore } from "@/lib/store";
import { useEffect } from "react";

export default function LoginPage() {
  const token = useAuthStore((s) => s.token);
  const router = useRouter();

  useEffect(() => {
    if (token) {
      router.replace("/dashboard");
    }
  }, [token, router]);

  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="w-full max-w-md rounded border p-6">
        <h1 className="mb-4 text-2xl font-bold">Login</h1>
        <p className="text-gray-600">
          Login form placeholder. Connect to /api/v1/auth/login.
        </p>
      </div>
    </div>
  );
}
