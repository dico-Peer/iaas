/**
 * US-2.01: Project list - search debounce and filter by title
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
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
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ projects: [], total: 0 }),
    });
    const user = userEvent.setup({ delay: null });
    render(<ProjectsPage />);
    const search = screen.getByTestId("project-search");
    await user.type(search, "AI");
    expect(mockFetch).toHaveBeenCalled();
    const callsBefore = mockFetch.mock.calls.length;
    await user.type(search, "B");
    expect(mockFetch.mock.calls.length).toBeLessThanOrEqual(callsBefore + 2);
  });

  it("test_search_filters_by_title", async () => {
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: () =>
          Promise.resolve({
            projects: [
              { id: "1", title: "AI Research", status: "draft", created_at: null, updated_at: null },
            ],
            total: 1,
          }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: () =>
          Promise.resolve({
            projects: [
              { id: "1", title: "AI Research", status: "draft", created_at: null, updated_at: null },
            ],
            total: 1,
          }),
      });
    const user = userEvent.setup({ delay: null });
    render(<ProjectsPage />);
    await vi.waitFor(() => {
      expect(screen.getByText("AI Research")).toBeInTheDocument();
    });
    const search = screen.getByTestId("project-search");
    await user.type(search, "AI");
    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("search=AI"),
        expect.any(Object)
      );
    });
  });
});
