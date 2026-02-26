/**
 * US-2.02: Question Guide Editor
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

describe("Question Editor", () => {
  beforeEach(() => {
    mockFetch.mockReset();
    useAuthStore.setState({
      user: { id: "1", email: "admin@test.com", name: "Admin", role: "org_admin" },
      org: { id: "o1", name: "Test Org" },
      token: "fake-token",
    });
  });

  it("test_render_questions_in_order", async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: () =>
        Promise.resolve({
          questions: [
            { id: "q1", order_index: 0, question_text: "First?", question_type: "open", probing_depth: 1 },
            { id: "q2", order_index: 1, question_text: "Second?", question_type: "open", probing_depth: 2 },
          ],
        }),
    });
    render(<ProjectQuestionsPage />);
    await waitFor(() => {
      expect(screen.getByText("First?")).toBeInTheDocument();
    });
    expect(screen.getByText("Second?")).toBeInTheDocument();
    expect(screen.getByText("Q1")).toBeInTheDocument();
    expect(screen.getByText("Q2")).toBeInTheDocument();
  });

  it("test_add_question_open_ended", async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ questions: [] }),
    });
    render(<ProjectQuestionsPage />);
    await waitFor(() => {
      expect(screen.getByTestId("add-question")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByTestId("add-question"));
    await waitFor(() => {
      expect(screen.getByTestId("question-card-0")).toBeInTheDocument();
    });
    expect(screen.getByPlaceholderText("Question text (required)")).toBeInTheDocument();
    expect(mockFetch).toHaveBeenCalledTimes(1);
  });

  it("test_add_question_rating_shows_scale_fields", async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: () =>
        Promise.resolve({
          questions: [
            {
              id: "q1",
              order_index: 0,
              question_text: "Rate it",
              question_type: "scale",
              probing_depth: 3,
              scale_config: { min: 1, max: 10, min_label: "Not at all", max_label: "Extremely" },
            },
          ],
        }),
    });
    render(<ProjectQuestionsPage />);
    await waitFor(() => {
      expect(screen.getByText("Rate it")).toBeInTheDocument();
    });
    expect(screen.getByTestId("scale-min")).toBeInTheDocument();
    expect(screen.getByTestId("scale-max")).toBeInTheDocument();
    expect(screen.getByTestId("scale-min-label")).toBeInTheDocument();
    expect(screen.getByTestId("scale-max-label")).toBeInTheDocument();
  });

  it("test_add_question_mc_shows_options", async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: () =>
        Promise.resolve({
          questions: [
            {
              id: "q1",
              order_index: 0,
              question_text: "Choose one",
              question_type: "multiple_choice",
              probing_depth: 2,
              options_json: ["Option A", "Option B"],
            },
          ],
        }),
    });
    render(<ProjectQuestionsPage />);
    await waitFor(() => {
      expect(screen.getByText("Choose one")).toBeInTheDocument();
    });
    expect(screen.getByTestId("options-section")).toBeInTheDocument();
    expect(screen.getByDisplayValue("Option A")).toBeInTheDocument();
    expect(screen.getByDisplayValue("Option B")).toBeInTheDocument();
    expect(screen.getByTestId("option-0-branch-toggle")).toBeInTheDocument();
  });

  it("test_move_up_reorders_cards", async () => {
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: () =>
          Promise.resolve({
            questions: [
              { id: "q1", order_index: 0, question_text: "First", question_type: "open", probing_depth: 1 },
              { id: "q2", order_index: 1, question_text: "Second", question_type: "open", probing_depth: 1 },
            ],
          }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: () =>
          Promise.resolve({
            questions: [
              { id: "q2", order_index: 0, question_text: "Second", question_type: "open", probing_depth: 1 },
              { id: "q1", order_index: 1, question_text: "First", question_type: "open", probing_depth: 1 },
            ],
          }),
      });
    render(<ProjectQuestionsPage />);
    await waitFor(() => {
      expect(screen.getByText("First")).toBeInTheDocument();
    });
    const cards = screen.getAllByTestId(/^question-card-/);
    expect(cards[0]).toHaveTextContent("First");
    expect(cards[1]).toHaveTextContent("Second");
    const moveUpButtons = screen.getAllByTestId("move-up");
    fireEvent.click(moveUpButtons[0]);
    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/questions/reorder"),
        expect.objectContaining({ method: "PATCH" })
      );
    });
  });

  it("test_delete_with_undo_toast", async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: () =>
        Promise.resolve({
          questions: [{ id: "q1", order_index: 0, question_text: "Delete me", question_type: "open", probing_depth: 1 }],
        }),
    });
    render(<ProjectQuestionsPage />);
    await waitFor(() => {
      expect(screen.getByText("Delete me")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByText("Delete"));
    await waitFor(() => {
      expect(screen.getByText("Question deleted")).toBeInTheDocument();
      expect(screen.getByText("Undo")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByText("Undo"));
    await waitFor(() => {
      expect(screen.getByText("Delete me")).toBeInTheDocument();
    });
  });

  it("test_save_persists_all_questions", async () => {
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: () =>
          Promise.resolve({
            questions: [{ id: "q1", order_index: 0, question_text: "Edit me", question_type: "open", probing_depth: 2 }],
          }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: () =>
          Promise.resolve({
            questions: [{ id: "q1", order_index: 0, question_text: "Edited text", question_type: "open", probing_depth: 2 }],
          }),
      });
    render(<ProjectQuestionsPage />);
    await waitFor(() => {
      expect(screen.getByDisplayValue("Edit me")).toBeInTheDocument();
    });
    fireEvent.change(screen.getByPlaceholderText("Question text (required)"), {
      target: { value: "Edited text" },
    });
    fireEvent.click(screen.getByTestId("save-all"));
    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/projects/123/questions"),
        expect.objectContaining({ method: "PUT", body: expect.stringContaining("Edited text") })
      );
    });
  });

  it("test_validation_empty_text_inline_error", async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: () =>
        Promise.resolve({
          questions: [{ id: "q1", order_index: 0, question_text: "Has text", question_type: "open", probing_depth: 1 }],
        }),
    });
    render(<ProjectQuestionsPage />);
    await waitFor(() => {
      expect(screen.getByDisplayValue("Has text")).toBeInTheDocument();
    });
    const textarea = screen.getByPlaceholderText("Question text (required)");
    fireEvent.change(textarea, { target: { value: "" } });
    fireEvent.click(screen.getByTestId("save-all"));
    await waitFor(
      () => {
        expect(screen.getByTestId("inline-error")).toHaveTextContent("Question text is required");
      },
      { timeout: 2000 }
    );
  });
});
