"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState, useRef } from "react";
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  type DragEndEvent,
} from "@dnd-kit/core";
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  useSortable,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { useAuthStore } from "@/lib/store";
import {
  fetchQuestions,
  batchPutQuestions,
  reorderQuestions,
  deleteQuestion,
  updateQuestionBranching,
  type Question,
  type BranchingRule,
} from "@/lib/api";

const QUESTION_TYPES = [
  { value: "open", label: "Open-ended" },
  { value: "scale", label: "Rating" },
  { value: "multiple_choice", label: "Multiple choice" },
  { value: "ranking", label: "Ranking" },
  { value: "branching_gate", label: "Branching gate" },
] as const;

export type EditableQuestion = Question & {
  _local?: boolean;
};

type McOption = { text: string; add_follow_up_branch: boolean };

function normalizeOptions(
  raw: string[] | { text: string; add_follow_up_branch?: boolean }[] | null | undefined
): McOption[] {
  if (!raw || !Array.isArray(raw)) return [{ text: "", add_follow_up_branch: false }, { text: "", add_follow_up_branch: false }];
  return raw.map((o) =>
    typeof o === "string"
      ? { text: o, add_follow_up_branch: false }
      : { text: o.text ?? "", add_follow_up_branch: !!o.add_follow_up_branch }
  );
}

function SortableQuestionCard({
  q,
  index,
  onChange,
  onDeleteRequest,
  onMoveUp,
  inlineError,
  otherQuestions,
  allQuestions,
  token,
  projectId,
  onBranchingSaved,
}: {
  q: EditableQuestion;
  index: number;
  onChange: (updated: EditableQuestion) => void;
  onDeleteRequest: (questionId: string) => void;
  onMoveUp?: (questionId: string) => void;
  inlineError?: string | null;
  otherQuestions: EditableQuestion[];
  allQuestions: EditableQuestion[];
  token: string | null;
  projectId: string;
  onBranchingSaved?: () => void;
}) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: q.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  return (
    <div ref={setNodeRef} style={style} className={isDragging ? "opacity-50" : ""}>
      <QuestionCard
        q={q}
        index={index}
        onChange={onChange}
        onDeleteRequest={onDeleteRequest}
        onMoveUp={onMoveUp}
        dragHandleProps={{ ...attributes, ...listeners }}
        inlineError={inlineError}
        otherQuestions={otherQuestions}
        allQuestions={allQuestions}
        token={token}
        projectId={projectId}
        onBranchingSaved={onBranchingSaved}
      />
    </div>
  );
}

const BRANCHING_CONDITION_TYPES = [
  { value: "answer_contains_text", label: "Answer contains text" },
  { value: "selected_option_equals", label: "Selected option equals" },
  { value: "rating_gte", label: "Rating ≥ value" },
  { value: "rating_lte", label: "Rating ≤ value" },
] as const;

function QuestionCard({
  q,
  index,
  onChange,
  onDeleteRequest,
  onMoveUp,
  dragHandleProps,
  inlineError,
  otherQuestions,
  allQuestions,
  token,
  projectId,
  onBranchingSaved,
}: {
  q: EditableQuestion;
  index: number;
  onChange: (updated: EditableQuestion) => void;
  onDeleteRequest: (questionId: string) => void;
  onMoveUp?: (questionId: string) => void;
  dragHandleProps?: Record<string, unknown>;
  inlineError?: string | null;
  otherQuestions: EditableQuestion[];
  allQuestions: EditableQuestion[];
  token: string | null;
  projectId: string;
  onBranchingSaved?: () => void;
}) {
  const [branchPanelOpen, setBranchPanelOpen] = useState(false);
  const [branchRules, setBranchRules] = useState<BranchingRule[]>([]);
  const [defaultNextId, setDefaultNextId] = useState<string | null>(null);
  const [savingBranching, setSavingBranching] = useState(false);

  useEffect(() => {
    const br = q.branching_rules as { rules?: BranchingRule[]; default_next_question_id?: string } | null;
    if (br?.rules && Array.isArray(br.rules) && br.rules.length > 0) {
      setBranchRules([...br.rules]);
    } else {
      setBranchRules([]);
    }
    setDefaultNextId(br?.default_next_question_id ?? null);
  }, [q.id, q.branching_rules]);
  const update = useCallback(
    (patch: Partial<EditableQuestion>) => {
      onChange({ ...q, ...patch });
    },
    [q, onChange]
  );

  const options = normalizeOptions(q.options_json as McOption[] | string[] | null);

  const handleDeleteClick = useCallback(() => {
    onDeleteRequest(q.id);
  }, [q.id, onDeleteRequest]);

  const setOptions = useCallback(
    (next: McOption[]) => {
      update({ options_json: next });
    },
    [update]
  );

  return (
    <div
      className="rounded border bg-white p-4 shadow-sm"
      data-testid={`question-card-${index}`}
    >
      <div className="mb-2 flex items-center gap-2">
        <span
          className="cursor-grab font-mono text-sm text-gray-500"
          data-testid="drag-handle"
          {...dragHandleProps}
        >
          ⋮⋮
        </span>
        <span className="font-medium">Q{index + 1}</span>
        <span className="rounded bg-gray-100 px-2 py-0.5 text-xs">{q.question_type}</span>
        <span className="text-xs text-gray-500">Depth: {q.probing_depth}</span>
        {index > 0 && onMoveUp && (
          <button
            type="button"
            data-testid="move-up"
            onClick={() => onMoveUp(q.id)}
            className="ml-2 text-xs text-blue-600"
          >
            Move up
          </button>
        )}
      </div>
      <textarea
        value={q.question_text}
        onChange={(e) => update({ question_text: e.target.value })}
        placeholder="Question text (required)"
        maxLength={1000}
        className="mb-2 w-full rounded border p-2"
        rows={2}
      />
      {inlineError && (
        <div
          className="mb-2 rounded border border-red-200 bg-red-50 p-2 text-sm text-red-700"
          data-testid="inline-error"
        >
          {inlineError}
        </div>
      )}
      <div className="mb-2">
        <label className="block text-sm text-gray-600">Help text (optional)</label>
        <textarea
          value={q.help_text ?? ""}
          onChange={(e) => update({ help_text: e.target.value || undefined })}
          placeholder="Optional help text"
          maxLength={500}
          className="mt-1 w-full rounded border p-2 text-sm"
          rows={1}
        />
      </div>
      <div className="flex flex-wrap gap-4">
        <label className="flex items-center gap-2">
          Type:
          <select
            value={q.question_type}
            onChange={(e) => update({ question_type: e.target.value })}
            className="rounded border"
          >
            {QUESTION_TYPES.map((t) => (
              <option key={t.value} value={t.value}>
                {t.label}
              </option>
            ))}
          </select>
        </label>
        <label className="flex items-center gap-2">
          Probing depth (1-10):
          <input
            type="range"
            min={1}
            max={10}
            value={q.probing_depth}
            onChange={(e) => update({ probing_depth: Number(e.target.value) })}
            className="w-24"
          />
          <span>{q.probing_depth}</span>
        </label>
      </div>
      {q.question_type === "scale" && (
        <div className="mt-3 rounded border border-gray-200 bg-gray-50 p-3" data-testid="scale-fields">
          <div className="grid grid-cols-2 gap-2 text-sm">
            <label>
              Min value:
              <input
                type="number"
                min={0}
                max={100}
                value={(q.scale_config as { min?: number })?.min ?? 1}
                onChange={(e) =>
                  update({
                    scale_config: {
                      ...(q.scale_config as object),
                      min: Number(e.target.value),
                    },
                  })
                }
                className="ml-1 w-16 rounded border"
                data-testid="scale-min"
              />
            </label>
            <label>
              Max value:
              <input
                type="number"
                min={0}
                max={100}
                value={(q.scale_config as { max?: number })?.max ?? 10}
                onChange={(e) =>
                  update({
                    scale_config: {
                      ...(q.scale_config as object),
                      max: Number(e.target.value),
                    },
                  })
                }
                className="ml-1 w-16 rounded border"
                data-testid="scale-max"
              />
            </label>
            <label className="col-span-2">
              Min label:
              <input
                type="text"
                value={(q.scale_config as { min_label?: string })?.min_label ?? "Not at all"}
                onChange={(e) =>
                  update({
                    scale_config: {
                      ...(q.scale_config as object),
                      min_label: e.target.value,
                    },
                  })
                }
                className="ml-1 w-full rounded border"
                data-testid="scale-min-label"
              />
            </label>
            <label className="col-span-2">
              Max label:
              <input
                type="text"
                value={(q.scale_config as { max_label?: string })?.max_label ?? "Extremely"}
                onChange={(e) =>
                  update({
                    scale_config: {
                      ...(q.scale_config as object),
                      max_label: e.target.value,
                    },
                  })
                }
                className="ml-1 w-full rounded border"
                data-testid="scale-max-label"
              />
            </label>
          </div>
        </div>
      )}
      {q.question_type === "multiple_choice" && (
        <div className="mt-3 rounded border border-gray-200 bg-gray-50 p-3" data-testid="options-section">
          <div className="mb-2 text-sm font-medium">Options (2-10)</div>
          {options.map((opt, i) => (
            <div key={i} className="mb-2 flex items-center gap-2">
              <input
                type="text"
                value={opt.text}
                onChange={(e) => {
                  const next = [...options];
                  next[i] = { ...next[i], text: e.target.value };
                  setOptions(next);
                }}
                placeholder={`Option ${i + 1}`}
                className="flex-1 rounded border"
                data-testid={`option-${i}`}
              />
              <label className="flex items-center gap-1 text-xs">
                <input
                  type="checkbox"
                  checked={opt.add_follow_up_branch}
                  onChange={(e) => {
                    const next = [...options];
                    next[i] = { ...next[i], add_follow_up_branch: e.target.checked };
                    setOptions(next);
                  }}
                  data-testid={`option-${i}-branch-toggle`}
                />
                Add follow-up branch
              </label>
              <button
                type="button"
                onClick={() => {
                  if (options.length > 2) {
                    setOptions(options.filter((_, j) => j !== i));
                  }
                }}
                className="rounded border px-2 text-red-600"
              >
                Remove
              </button>
            </div>
          ))}
          {options.length < 10 && (
            <button
              type="button"
              onClick={() => setOptions([...options, { text: "", add_follow_up_branch: false }])}
              className="rounded border border-dashed px-3 py-1 text-sm text-gray-600"
            >
              Add option
            </button>
          )}
        </div>
      )}
      <div className="mt-2 flex gap-2">
        <button
          type="button"
          onClick={() => setBranchPanelOpen((v) => !v)}
          className="rounded border px-3 py-1 text-blue-600"
          data-testid="add-branch"
        >
          {branchPanelOpen ? "Hide Branch" : "Add Branch"}
        </button>
        <button
          type="button"
          onClick={handleDeleteClick}
          className="rounded border px-3 py-1 text-red-600"
        >
          Delete
        </button>
      </div>
      {branchPanelOpen && (
        <div className="mt-3 rounded border border-blue-200 bg-blue-50 p-3" data-testid="branching-panel">
          <div className="mb-2 text-sm font-medium">Branching rules</div>
          {branchRules.map((rule, ri) => (
            <div key={ri} className="mb-2 flex flex-wrap items-center gap-2 rounded border bg-white p-2">
              {ri > 0 && (
                <select
                  value={rule.logic_operator}
                  onChange={(e) => {
                    const next = [...branchRules];
                    next[ri] = { ...next[ri], logic_operator: e.target.value };
                    setBranchRules(next);
                  }}
                  className="rounded border text-xs"
                  data-testid="logic-operator"
                >
                  <option value="AND">AND</option>
                  <option value="OR">OR</option>
                </select>
              )}
              <select
                value={rule.condition_type}
                onChange={(e) => {
                  const next = [...branchRules];
                  next[ri] = { ...next[ri], condition_type: e.target.value };
                  setBranchRules(next);
                }}
                className="rounded border text-sm"
                data-testid="condition-type"
              >
                {BRANCHING_CONDITION_TYPES.map((t) => (
                  <option key={t.value} value={t.value}>
                    {t.label}
                  </option>
                ))}
              </select>
              <input
                type="text"
                value={String(rule.condition_value)}
                onChange={(e) => {
                  const next = [...branchRules];
                  const val = e.target.value;
                  next[ri] = {
                    ...next[ri],
                    condition_value: /^\d+$/.test(val) ? parseInt(val, 10) : val,
                  };
                  setBranchRules(next);
                }}
                placeholder="Value"
                className="w-24 rounded border text-sm"
                data-testid="condition-value"
              />
              <span className="text-xs">→</span>
              <select
                value={rule.target_question_id}
                onChange={(e) => {
                  const next = [...branchRules];
                  next[ri] = { ...next[ri], target_question_id: e.target.value };
                  setBranchRules(next);
                }}
                className="rounded border text-sm"
                data-testid="target-question"
              >
                <option value="">—</option>
                {otherQuestions.map((oq) => (
                  <option key={oq.id} value={oq.id}>
                    Q{allQuestions.findIndex((x) => x.id === oq.id) + 1}: {(oq.question_text || "").slice(0, 30)}…
                  </option>
                ))}
              </select>
              <button
                type="button"
                onClick={() => setBranchRules(branchRules.filter((_, j) => j !== ri))}
                className="text-xs text-red-600"
              >
                Remove
              </button>
            </div>
          ))}
          <div className="mb-2">
            <label className="text-xs">Default next: </label>
            <select
              value={defaultNextId ?? ""}
              onChange={(e) => setDefaultNextId(e.target.value || null)}
              className="rounded border text-sm"
            >
              <option value="">Next by order</option>
              {otherQuestions.map((oq) => (
                <option key={oq.id} value={oq.id}>
                  Q{allQuestions.findIndex((x) => x.id === oq.id) + 1}: {(oq.question_text || "").slice(0, 30)}…
                </option>
              ))}
            </select>
          </div>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() =>
                setBranchRules([
                  ...branchRules,
                  {
                    condition_type: "answer_contains_text",
                    condition_value: "",
                    logic_operator: "AND",
                    target_question_id: otherQuestions[0]?.id ?? "",
                  },
                ])
              }
              className="rounded border border-dashed px-2 py-1 text-xs text-gray-600"
              data-testid="add-another-rule"
            >
              {branchRules.length === 0 ? "Add rule" : "Add another rule"}
            </button>
            {token && !q._local && (
              <button
                type="button"
                disabled={savingBranching}
                onClick={async () => {
                  setSavingBranching(true);
                  try {
                    await updateQuestionBranching(token, projectId, q.id, {
                      rules: branchRules.filter((r) => r.target_question_id),
                      default_next_question_id: defaultNextId,
                    });
                    onChange({ ...q, branching_rules: { rules: branchRules, default_next_question_id: defaultNextId } });
                    onBranchingSaved?.();
                  } finally {
                    setSavingBranching(false);
                  }
                }}
                className="rounded bg-blue-600 px-2 py-1 text-xs text-white disabled:opacity-50"
              >
                Save Branching
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default function ProjectQuestionsPage() {
  const params = useParams();
  const projectId = params?.id as string;
  const token = useAuthStore((s) => s.token);
  const [questions, setQuestions] = useState<EditableQuestion[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saveToast, setSaveToast] = useState(false);
  const [deleteToast, setDeleteToast] = useState<{
    questionId: string;
    questionText: string;
  } | null>(null);
  const deleteTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const load = useCallback(async () => {
    if (!token || !projectId) return;
    setLoading(true);
    setError(null);
    try {
      const data = await fetchQuestions(token, projectId);
      setQuestions(data.questions.map((q) => ({ ...q, _local: false })));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load");
    } finally {
      setLoading(false);
    }
  }, [token, projectId]);

  useEffect(() => {
    load();
  }, [load]);

  const [inlineErrors, setInlineErrors] = useState<Map<string, string>>(new Map());

  const handleQuestionChange = useCallback((index: number, updated: EditableQuestion) => {
    setQuestions((prev) => {
      const next = [...prev];
      next[index] = updated;
      return next;
    });
    setInlineErrors((prev) => {
      const next = new Map(prev);
      next.delete(updated.id);
      return next;
    });
  }, []);

  const handleDeleteRequest = useCallback(
    (questionId: string) => {
      const q = questions.find((x) => x.id === questionId);
      if (!q) return;
      if (q._local) {
        setQuestions((prev) => prev.filter((x) => x.id !== questionId));
        return;
      }
      if (!token || !projectId) return;
      setDeleteToast({ questionId, questionText: q.question_text });
      if (deleteTimeoutRef.current) clearTimeout(deleteTimeoutRef.current);
      deleteTimeoutRef.current = setTimeout(() => {
        deleteQuestion(token, projectId, questionId).then(() => {
          load();
        });
        setDeleteToast(null);
        deleteTimeoutRef.current = null;
      }, 5000);
    },
    [questions, token, projectId, load]
  );

  const handleUndoDelete = useCallback(() => {
    if (deleteTimeoutRef.current) {
      clearTimeout(deleteTimeoutRef.current);
      deleteTimeoutRef.current = null;
    }
    setDeleteToast(null);
  }, []);

  useEffect(() => {
    return () => {
      if (deleteTimeoutRef.current) clearTimeout(deleteTimeoutRef.current);
    };
  }, []);

  const handleAddQuestion = useCallback(() => {
    const newId = `new-${crypto.randomUUID()}`;
    setQuestions((prev) => [
      ...prev,
      {
        id: newId,
        order_index: prev.length,
        question_text: "",
        question_type: "open",
        probing_depth: 3,
        help_text: null,
        options_json: null,
        scale_config: null,
        branching_rules: null,
        created_at: null,
        updated_at: null,
        _local: true,
      } as EditableQuestion,
    ]);
  }, []);

  const handleSaveAll = useCallback(async () => {
    if (!token || !projectId) return;
    const errs = new Map<string, string>();
    for (let i = 0; i < questions.length; i++) {
      const q = questions[i];
      const trimmed = (q.question_text || "").trim();
      if (!trimmed) {
        errs.set(q.id, "Question text is required");
      }
      if (q.question_type === "multiple_choice") {
        const opts = normalizeOptions(q.options_json as McOption[] | string[] | null);
        const filled = opts.filter((o) => o.text.trim().length > 0);
        if (filled.length < 2) {
          errs.set(q.id, "At least 2 options required for multiple choice");
        }
      }
    }
    if (errs.size > 0) {
      setInlineErrors(errs);
      return;
    }
    setInlineErrors(new Map());
    setSaving(true);
    setError(null);
    try {
      const payload = questions.map((q, i) => {
        const scale =
          q.question_type === "scale" && q.scale_config
            ? q.scale_config
            : undefined;
        let opts: string[] | { text: string; add_follow_up_branch: boolean }[] | undefined;
        if (q.question_type === "multiple_choice" && q.options_json) {
          const normalized = normalizeOptions(q.options_json as McOption[] | string[]);
          const filled = normalized.filter((o) => o.text.trim().length > 0);
          opts = filled.map((o) =>
            o.add_follow_up_branch ? { text: o.text, add_follow_up_branch: true } : o.text
          );
        } else {
          opts = undefined;
        }
        return {
          order_index: i,
          question_text: (q.question_text || "").trim(),
          question_type: q.question_type,
          probing_depth: q.probing_depth,
          help_text: (q.help_text || "").trim() || undefined,
          options_json: opts,
          scale_config: scale,
        };
      });
      await batchPutQuestions(token, projectId, payload);
      setSaveToast(true);
      setTimeout(() => setSaveToast(false), 3000);
      load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to save");
    } finally {
      setSaving(false);
    }
  }, [questions, token, projectId, load]);

  const handleDragEnd = useCallback(
    async (event: DragEndEvent) => {
      const { active, over } = event;
      if (!over || active.id === over.id || !token || !projectId) return;
      const oldIndex = questions.findIndex((q) => q.id === active.id);
      const newIndex = questions.findIndex((q) => q.id === over.id);
      if (oldIndex === -1 || newIndex === -1) return;
      const next = arrayMove(questions, oldIndex, newIndex);
      setQuestions(next);
      try {
        await reorderQuestions(token, projectId, String(active.id), newIndex);
        load();
      } catch {
        setError("Failed to reorder");
      }
    },
    [questions, token, projectId, load]
  );

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 2 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates })
  );

  if (!projectId) return null;

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <Link href="/projects" className="text-blue-600 hover:underline">
          ← Back to projects
        </Link>
        <h1 className="text-2xl font-bold">Question Guide</h1>
      </div>
      {error && (
        <div className="mb-4 rounded border border-red-200 bg-red-50 p-3 text-red-700">
          {error}
        </div>
      )}
      {saveToast && (
        <div
          className="mb-4 rounded border border-green-200 bg-green-50 p-3 text-green-800"
          data-testid="save-toast"
        >
          Questions saved.
        </div>
      )}
      {deleteToast && (
        <div
          className="mb-4 flex items-center justify-between rounded border border-amber-200 bg-amber-50 p-3 text-amber-800"
          data-testid="delete-toast"
        >
          <span>Question deleted</span>
          <button
            type="button"
            onClick={handleUndoDelete}
            className="rounded bg-amber-200 px-3 py-1 font-medium hover:bg-amber-300"
          >
            Undo
          </button>
        </div>
      )}
      {loading ? (
        <p>Loading...</p>
      ) : (
        <>
          <DndContext
            sensors={sensors}
            collisionDetection={closestCenter}
            onDragEnd={handleDragEnd}
          >
            <SortableContext
              items={questions.map((q) => q.id)}
              strategy={verticalListSortingStrategy}
            >
              <div className="mb-4 flex flex-col gap-4">
                {questions.map((q, i) => (
                  <SortableQuestionCard
                    key={q.id}
                    q={q}
                    index={i}
                    onChange={(updated) => handleQuestionChange(i, updated)}
                    onDeleteRequest={handleDeleteRequest}
                    inlineError={inlineErrors.get(q.id)}
                    otherQuestions={questions.filter((_, j) => j !== i)}
                    allQuestions={questions}
                    token={token}
                    projectId={projectId}
                    onBranchingSaved={load}
                    onMoveUp={async (id) => {
                      const idx = questions.findIndex((x) => x.id === id);
                      if (idx <= 0 || !token || !projectId) return;
                      try {
                        await reorderQuestions(token, projectId, id, idx - 1);
                        load();
                      } catch {
                        setError("Failed to reorder");
                      }
                    }}
                  />
                ))}
              </div>
            </SortableContext>
          </DndContext>
          <div className="flex gap-4">
            <button
              type="button"
              onClick={handleAddQuestion}
              className="rounded border border-dashed border-gray-400 px-4 py-2 text-gray-600 hover:bg-gray-50"
              data-testid="add-question"
            >
              Add Question
            </button>
            <button
              type="button"
              onClick={handleSaveAll}
              disabled={saving}
              className="rounded bg-blue-600 px-4 py-2 text-white disabled:opacity-50"
              data-testid="save-all"
            >
              Save
            </button>
          </div>
        </>
      )}
    </div>
  );
}
