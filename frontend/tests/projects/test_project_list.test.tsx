/**
 * US-2.01: Project list - search debounce and filter by title
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { useAuthStore } from "@/lib/store";
import ProjectsPage from "@/app/(dashboard)/projects/page";

const mockFetch = vi.fn();
vi.stubGlobal("fetch", mockFetch);

vi.mock("next/navigation", () => ({
  usePathname: () => "/projects",
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
}));

describe("Project List", () => {
  beforeEach(() => {
    mockFetch.mockReset();
    useAuthStore.setState({
      user: { id: "1", email: "admin@test.com", name: "Admin", role: "org_admin" },
      org: { id: "o1", name: "Test Org" },
      token: "fake-token",
    });
  });

  it("test_search_projects_debounced_300ms", async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ projects: [], total: 0 }),
    });
    vi.useFakeTimers();
    render(<ProjectsPage />);
    await vi.advanceTimersByTimeAsync(500);
    mockFetch.mockClear();
    const search = screen.getByTestId("project-search");
    fireEvent.change(search, { target: { value: "A" } });
    vi.advanceTimersByTime(100);
    expect(mockFetch).not.toHaveBeenCalled();
    await vi.advanceTimersByTimeAsync(250);
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining("search=A"),
      expect.any(Object)
    );
    vi.useRealTimers();
  });

  it("test_search_filters_by_title", async () => {
    const projectData = {
      projects: [
        {
          id: "1",
          title: "AI Research",
          status: "draft",
          created_at: null,
          updated_at: null,
          interview_count: 0,
          completion_pct: 0,
          cost: null,
        },
      ],
      total: 1,
    };
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(projectData),
    });
    render(<ProjectsPage />);
    await waitFor(
      () => {
        expect(screen.getByText("AI Research")).toBeInTheDocument();
      },
      { timeout: 2000 }
    );
    const search = screen.getByTestId("project-search");
    fireEvent.change(search, { target: { value: "AI" } });
    await waitFor(
      () => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining("search=AI"),
          expect.any(Object)
        );
      },
      { timeout: 2000 }
    );
  });
});
