/**
 * US-2.03: Branching Logic Builder
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { useAuthStore } from "@/lib/store";
import ProjectQuestionsPage from "@/app/(dashboard)/projects/[id]/page";

const mockFetch = vi.fn();
vi.stubGlobal("fetch", mockFetch);

vi.mock("next/navigation", () => ({
  usePathname: () => "/projects/123",
  useParams: () => ({ id: "123" }),
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
}));

describe("Branching Builder", () => {
  beforeEach(() => {
    mockFetch.mockReset();
    useAuthStore.setState({
      user: { id: "1", email: "admin@test.com", name: "Admin", role: "org_admin" },
      org: { id: "o1", name: "Test Org" },
      token: "fake-token",
    });
  });

  it("test_add_branching_rule_panel_expands", async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: () =>
        Promise.resolve({
          questions: [
            { id: "q1", order_index: 0, question_text: "First", question_type: "open", probing_depth: 1 },
            { id: "q2", order_index: 1, question_text: "Second", question_type: "open", probing_depth: 1 },
          ],
        }),
    });
    render(<ProjectQuestionsPage />);
    await waitFor(() => {
      expect(screen.getByText("First")).toBeInTheDocument();
    });
    fireEvent.click(screen.getAllByTestId("add-branch")[0]);
    await waitFor(() => {
      expect(screen.getByTestId("branching-panel")).toBeInTheDocument();
    });
  });

  it("test_condition_types_dropdown", async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: () =>
        Promise.resolve({
          questions: [
            { id: "q1", order_index: 0, question_text: "First", question_type: "open", probing_depth: 1 },
            { id: "q2", order_index: 1, question_text: "Second", question_type: "open", probing_depth: 1 },
          ],
        }),
    });
    render(<ProjectQuestionsPage />);
    await waitFor(() => {
      expect(screen.getByText("First")).toBeInTheDocument();
    });
    fireEvent.click(screen.getAllByTestId("add-branch")[0]);
    await waitFor(() => {
      expect(screen.getByTestId("branching-panel")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByTestId("add-another-rule"));
    await waitFor(() => {
      const selects = screen.getAllByTestId("condition-type");
      expect(selects.length).toBeGreaterThan(0);
    });
    expect(screen.getByText("Answer contains text")).toBeInTheDocument();
    expect(screen.getByText("Selected option equals")).toBeInTheDocument();
    expect(screen.getByText("Rating ≥ value")).toBeInTheDocument();
    expect(screen.getByText("Rating ≤ value")).toBeInTheDocument();
  });

  it("test_and_or_logic_toggle", async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: () =>
        Promise.resolve({
          questions: [
            { id: "q1", order_index: 0, question_text: "A", question_type: "open", probing_depth: 1 },
            { id: "q2", order_index: 1, question_text: "B", question_type: "open", probing_depth: 1 },
          ],
        }),
    });
    render(<ProjectQuestionsPage />);
    await waitFor(() => {
      expect(screen.getByText("A")).toBeInTheDocument();
    });
    fireEvent.click(screen.getAllByTestId("add-branch")[0]);
    await waitFor(() => {
      expect(screen.getByTestId("branching-panel")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByTestId("add-another-rule"));
    fireEvent.click(screen.getByTestId("add-another-rule"));
    await waitFor(() => {
      const logicSelects = screen.getAllByTestId("logic-operator");
      expect(logicSelects.length).toBeGreaterThan(0);
    });
    const logicSelects = screen.getAllByTestId("logic-operator");
    expect(logicSelects[0]).toBeInTheDocument();
  });
});
