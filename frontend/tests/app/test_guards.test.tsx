/**
 * US-1.05: Route guards - unauthenticated redirect to login
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { useAuthStore } from "@/lib/store";

const mockReplace = vi.fn();
vi.mock("next/navigation", () => ({
  usePathname: () => "/dashboard",
  useRouter: () => ({ push: vi.fn(), replace: mockReplace }),
}));

describe("Route Guards", () => {
  beforeEach(() => {
    mockReplace.mockClear();
    useAuthStore.setState({ user: null, org: null, token: null });
  });

  it("test_unauthenticated_redirect_to_login", async () => {
    const DashboardLayout = (await import("@/app/(dashboard)/layout")).default;
    render(<DashboardLayout><div>Dashboard content</div></DashboardLayout>);
    expect(mockReplace).toHaveBeenCalledWith("/login");
  });

  it("test_login_page_accessible_without_token", async () => {
    const LoginPage = (await import("@/app/login/page")).default;
    render(<LoginPage />);
    expect(screen.getByText("Login")).toBeInTheDocument();
  });
});
