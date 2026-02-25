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
  createQuestion,
  updateQuestion,
  reorderQuestions,
  deleteQuestion,
  type Question,
} from "@/lib/api";

const QUESTION_TYPES = [
  { value: "open", label: "Open-ended" },
  { value: "scale", label: "Rating" },
  { value: "multiple_choice", label: "Multiple choice" },
  { value: "ranking", label: "Ranking" },
] as const;

function SortableQuestionCard({
  q,
  index,
  onUpdate,
  onDeleteRequest,
  onMoveUp,
  token,
  projectId,
}: {
  q: Question;
  index: number;
  onUpdate: () => void;
  onDeleteRequest: (questionId: string) => void;
  onMoveUp?: (questionId: string) => void;
  token: string;
  projectId: string;
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
        onUpdate={onUpdate}
        onDeleteRequest={onDeleteRequest}
        onMoveUp={onMoveUp}
        token={token}
        projectId={projectId}
        dragHandleProps={{ ...attributes, ...listeners }}
      />
    </div>
  );
}

function QuestionCard({
  q,
  index,
  onUpdate,
  onDeleteRequest,
  onMoveUp,
  token,
  projectId,
  dragHandleProps,
}: {
  q: Question;
  index: number;
  onUpdate: () => void;
  onDeleteRequest: (questionId: string) => void;
  onMoveUp?: (questionId: string) => void;
  token: string;
  projectId: string;
  dragHandleProps?: Record<string, unknown>;
}) {
  const [text, setText] = useState(q.question_text);
  const [type, setType] = useState(q.question_type);
  const [depth, setDepth] = useState(q.probing_depth);
  const [helpText, setHelpText] = useState(q.help_text ?? "");
  const [scaleMin, setScaleMin] = useState(
    (q.scale_config as { min?: number })?.min ?? 1
  );
  const [scaleMax, setScaleMax] = useState(
    (q.scale_config as { max?: number })?.max ?? 10
  );
  const [scaleMinLabel, setScaleMinLabel] = useState(
    (q.scale_config as { min_label?: string })?.min_label ?? "Not at all"
  );
  const [scaleMaxLabel, setScaleMaxLabel] = useState(
    (q.scale_config as { max_label?: string })?.max_label ?? "Extremely"
  );
  const [options, setOptions] = useState<string[]>(
    Array.isArray(q.options_json) ? [...q.options_json] : ["", ""]
  );
  const [saving, setSaving] = useState(false);
  const [inlineError, setInlineError] = useState<string | null>(null);

  const handleSave = useCallback(async () => {
    if (!token || !projectId) return;
    const trimmed = text.trim();
    if (!trimmed) {
      setInlineError("Question text is required");
      return;
    }
    setInlineError(null);
    setSaving(true);
    try {
      const payload: Parameters<typeof updateQuestion>[3] = {
        question_text: trimmed,
        question_type: type,
        probing_depth: depth,
        help_text: helpText || undefined,
      };
      if (type === "scale") {
        payload.scale_config = {
          min: scaleMin,
          max: scaleMax,
          min_label: scaleMinLabel,
          max_label: scaleMaxLabel,
        };
      }
      if (type === "multiple_choice") {
        const opts = options.filter((o) => o.trim().length > 0);
        if (opts.length < 2) {
          setInlineError("At least 2 options required for multiple choice");
          setSaving(false);
          return;
        }
        payload.options_json = opts;
      }
      await updateQuestion(token, projectId, q.id, payload);
      onUpdate();
    } catch {
      setInlineError("Failed to save");
    } finally {
      setSaving(false);
    }
  }, [
    token,
    projectId,
    q.id,
    text,
    type,
    depth,
    helpText,
    scaleMin,
    scaleMax,
    scaleMinLabel,
    scaleMaxLabel,
    options,
    onUpdate,
  ]);

  const handleDeleteClick = useCallback(() => {
    onDeleteRequest(q.id);
  }, [q.id, onDeleteRequest]);

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
        <span className="rounded bg-gray-100 px-2 py-0.5 text-xs">{type}</span>
        <span className="text-xs text-gray-500">Depth: {depth}</span>
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
        value={text}
        onChange={(e) => {
          setText(e.target.value);
          setInlineError(null);
        }}
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
          value={helpText}
          onChange={(e) => setHelpText(e.target.value)}
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
            value={type}
            onChange={(e) => setType(e.target.value)}
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
            value={depth}
            onChange={(e) => setDepth(Number(e.target.value))}
            className="w-24"
          />
          <span>{depth}</span>
        </label>
      </div>
      {type === "scale" && (
        <div className="mt-3 rounded border border-gray-200 bg-gray-50 p-3" data-testid="scale-fields">
          <div className="grid grid-cols-2 gap-2 text-sm">
            <label>
              Min value:
              <input
                type="number"
                min={0}
                max={100}
                value={scaleMin}
                onChange={(e) => setScaleMin(Number(e.target.value))}
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
                value={scaleMax}
                onChange={(e) => setScaleMax(Number(e.target.value))}
                className="ml-1 w-16 rounded border"
                data-testid="scale-max"
              />
            </label>
            <label className="col-span-2">
              Min label:
              <input
                type="text"
                value={scaleMinLabel}
                onChange={(e) => setScaleMinLabel(e.target.value)}
                className="ml-1 w-full rounded border"
                data-testid="scale-min-label"
              />
            </label>
            <label className="col-span-2">
              Max label:
              <input
                type="text"
                value={scaleMaxLabel}
                onChange={(e) => setScaleMaxLabel(e.target.value)}
                className="ml-1 w-full rounded border"
                data-testid="scale-max-label"
              />
            </label>
          </div>
        </div>
      )}
      {type === "multiple_choice" && (
        <div className="mt-3 rounded border border-gray-200 bg-gray-50 p-3" data-testid="options-section">
          <div className="mb-2 text-sm font-medium">Options (2-10)</div>
          {options.map((opt, i) => (
            <div key={i} className="mb-2 flex gap-2">
              <input
                type="text"
                value={opt}
                onChange={(e) => {
                  const next = [...options];
                  next[i] = e.target.value;
                  setOptions(next);
                }}
                placeholder={`Option ${i + 1}`}
                className="flex-1 rounded border"
                data-testid={`option-${i}`}
              />
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
              onClick={() => setOptions([...options, ""])}
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
          onClick={handleSave}
          disabled={saving}
          className="rounded bg-blue-600 px-3 py-1 text-white disabled:opacity-50"
        >
          Save
        </button>
        <button
          type="button"
          onClick={handleDeleteClick}
          className="rounded border px-3 py-1 text-red-600"
        >
          Delete
        </button>
      </div>
    </div>
  );
}

export default function ProjectQuestionsPage() {
  const params = useParams();
  const projectId = params?.id as string;
  const token = useAuthStore((s) => s.token);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
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
      setQuestions(data.questions);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load");
    } finally {
      setLoading(false);
    }
  }, [token, projectId]);

  useEffect(() => {
    load();
  }, [load]);

  const handleDeleteRequest = useCallback(
    (questionId: string) => {
      const q = questions.find((x) => x.id === questionId);
      if (!q || !token || !projectId) return;
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

  const handleAddQuestion = useCallback(async () => {
    if (!token || !projectId) return;
    try {
      await createQuestion(token, projectId, {
        question_text: "New question",
        question_type: "open",
        probing_depth: 3,
      });
      load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to add");
    }
  }, [token, projectId, load]);

  const handleDragEnd = useCallback(
    async (event: DragEndEvent) => {
      const { active, over } = event;
      if (!over || active.id === over.id || !token || !projectId) return;
      const oldIndex = questions.findIndex((q) => q.id === active.id);
      const newIndex = questions.findIndex((q) => q.id === over.id);
      if (oldIndex === -1 || newIndex === -1) return;
      try {
        await reorderQuestions(token, projectId, String(active.id), newIndex);
        const next = arrayMove(questions, oldIndex, newIndex);
        setQuestions(next);
      } catch {
        setError("Failed to reorder");
      }
    },
    [questions, token, projectId]
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
                    onUpdate={load}
                    onDeleteRequest={handleDeleteRequest}
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
                    token={token!}
                    projectId={projectId}
                  />
                ))}
              </div>
            </SortableContext>
          </DndContext>
          <button
            type="button"
            onClick={handleAddQuestion}
            className="rounded border border-dashed border-gray-400 px-4 py-2 text-gray-600 hover:bg-gray-50"
            data-testid="add-question"
          >
            Add Question
          </button>
        </>
      )}
    </div>
  );
}
