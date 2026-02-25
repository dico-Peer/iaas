/**
 * US-1.05: Application Shell & Navigation
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useAuthStore } from "@/lib/store";
import { Sidebar } from "@/components/Sidebar";
import { TopBar } from "@/components/TopBar";

vi.mock("next/navigation", () => ({
  usePathname: () => "/dashboard",
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
}));

describe("App Shell", () => {
  beforeEach(() => {
    useAuthStore.setState({
      user: { id: "1", email: "admin@test.com", name: "Admin User", role: "org_admin" },
      org: { id: "o1", name: "Test Org" },
      token: "fake-token",
    });
  });

  it("test_renders_sidebar_with_all_items", () => {
    render(<Sidebar />);
    expect(screen.getByText("Dashboard")).toBeInTheDocument();
    expect(screen.getByText("Projects")).toBeInTheDocument();
    expect(screen.getByText("Templates")).toBeInTheDocument();
    expect(screen.getByText("Team")).toBeInTheDocument();
    expect(screen.getByText("Settings")).toBeInTheDocument();
  });

  it("test_hides_team_for_designer_role", () => {
    useAuthStore.setState({
      user: { id: "1", email: "d@test.com", name: "Designer", role: "designer" },
      org: { id: "o1", name: "Test Org" },
      token: "fake-token",
    });
    render(<Sidebar />);
    expect(screen.getByText("Dashboard")).toBeInTheDocument();
    expect(screen.queryByText("Team")).not.toBeInTheDocument();
  });

  it("test_hides_team_for_analyst_role", () => {
    useAuthStore.setState({
      user: { id: "1", email: "a@test.com", name: "Analyst", role: "analyst" },
      org: { id: "o1", name: "Test Org" },
      token: "fake-token",
    });
    render(<Sidebar />);
    expect(screen.queryByText("Team")).not.toBeInTheDocument();
  });

  it("test_route_change_updates_url", async () => {
    const user = userEvent.setup();
    render(<Sidebar />);
    const projectsLink = screen.getByRole("link", { name: /projects/i });
    expect(projectsLink).toHaveAttribute("href", "/projects");
    await user.click(projectsLink);
  });

  it("test_route_renders_component_in_200ms", () => {
    const t0 = performance.now();
    render(<Sidebar />);
    expect(screen.getByText("Dashboard")).toBeInTheDocument();
    const t1 = performance.now();
    expect(t1 - t0).toBeLessThan(200);
  });

  it("test_mobile_hamburger_shows_on_small_viewport", () => {
    render(<Sidebar />);
    const hamburger = screen.getByTestId("hamburger-menu");
    expect(hamburger).toBeInTheDocument();
    expect(hamburger).toHaveClass("md:hidden");
    const sidebar = screen.getByTestId("sidebar");
    expect(sidebar).toHaveClass("-translate-x-full");
  });

  it("test_top_bar_shows_org_name_and_user", () => {
    render(<TopBar />);
    expect(screen.getByText("Test Org")).toBeInTheDocument();
    expect(screen.getByText("Admin User")).toBeInTheDocument();
    expect(screen.getByTitle("admin@test.com")).toHaveTextContent("AU");
  });

  it("test_preview_as_interviewee_button_present", () => {
    render(<TopBar />);
    const btn = screen.getByRole("button", { name: /preview as interviewee/i });
    expect(btn).toBeInTheDocument();
    expect(btn).not.toBeDisabled();
  });
});
