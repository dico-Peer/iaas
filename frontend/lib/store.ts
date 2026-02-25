import { create } from "zustand";
import { persist } from "zustand/middleware";

export interface User {
  id: string;
  email: string;
  name: string | null;
  role: string;
}

export interface Org {
  id: string;
  name: string;
}

interface AuthState {
  user: User | null;
  org: Org | null;
  token: string | null;
  setAuth: (user: User, org: Org, token: string) => void;
  clearAuth: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      org: null,
      token: null,
      setAuth: (user, org, token) => set({ user, org, token }),
      clearAuth: () => set({ user: null, org: null, token: null }),
    }),
    {
      name: "iaas-auth",
      partialize: (s) => ({ user: s.user, org: s.org, token: s.token }),
    }
  )
);
