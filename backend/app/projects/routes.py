"""Projects API routes - Interview Project CRUD (US-2.01)."""
import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query

from app.auth.dependencies import get_current_designer_or_admin
from app.branching.logic import detect_circular_reference
from app.database import get_connection
from app.projects.schemas import (
    BatchPutQuestionsRequest,
    BranchingRulesRequest,
    CreateProjectRequest,
    CreateQuestionRequest,
    ReorderRequest,
    UpdateProjectRequest,
    UpdateQuestionRequest,
)

router = APIRouter(prefix="/projects", tags=["projects"])


def _project_row_to_dict(row, settings_json=None):
    """Convert DB row to API response dict."""
    if settings_json is None:
        raw = row.get("settings_json")
        settings_json = raw if isinstance(raw, dict) else (json.loads(raw) if raw else {})
    elif isinstance(settings_json, str):
        settings_json = json.loads(settings_json) if settings_json else {}
    result = {
        "id": str(row["id"]),
        "title": row["title"],
        "description": row["description"],
        "research_objectives": row["research_objectives"],
        "target_audience": settings_json.get("target_audience"),
        "language": settings_json.get("language", "en"),
        "modality": row["modality_type"] or "text",
        "status": row["status"],
        "created_at": row["created_at"].isoformat() if row["created_at"] else None,
        "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None,
    }
    if "interview_count" in row:
        result["interview_count"] = row["interview_count"]
    if "completed_count" in row and "interview_count" in row:
        cnt = row["interview_count"] or 0
        result["completion_pct"] = round(100.0 * (row["completed_count"] or 0) / cnt, 1) if cnt > 0 else 0
    if "cost" in row:
        result["cost"] = row["cost"]
    return result


@router.post("", status_code=201)
def create_project(
    req: CreateProjectRequest,
    current_user: dict = Depends(get_current_designer_or_admin),
):
    """Create interview project. Designer/Admin only."""
    org_id = current_user.get("org_id")
    user_id = current_user.get("sub")
    if not org_id or not user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    settings = {"target_audience": req.target_audience, "language": req.language}
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO interview_projects
                   (org_id, created_by, title, description, research_objectives, status, settings_json, modality_type)
                   VALUES (%s, %s, %s, %s, %s, 'draft', %s, %s)
                   RETURNING id, title, description, research_objectives, status, settings_json, modality_type, created_at, updated_at""",
                (
                    org_id,
                    user_id,
                    req.title,
                    req.description,
                    req.research_objectives,
                    json.dumps(settings),
                    req.modality,
                ),
            )
            row = cur.fetchone()
    return _project_row_to_dict(row, settings)


@router.get("")
def list_projects(
    current_user: dict = Depends(get_current_designer_or_admin),
    search: str = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
):
    """List projects in org. Sorted by updated_at DESC."""
    org_id = current_user.get("org_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    offset = (page - 1) * limit
    with get_connection() as conn:
        with conn.cursor() as cur:
            if search:
                cur.execute(
                    """SELECT p.id, p.title, p.description, p.research_objectives, p.status, p.settings_json, p.modality_type, p.created_at, p.updated_at,
                              (SELECT COUNT(*)::int FROM conversations c WHERE c.project_id = p.id) AS interview_count,
                              (SELECT COUNT(*)::int FROM conversations c WHERE c.project_id = p.id AND c.status = 'completed') AS completed_count,
                              NULL::text AS cost
                       FROM interview_projects p
                       WHERE p.org_id = %s AND p.deleted_at IS NULL AND p.title ILIKE %s
                       ORDER BY p.updated_at DESC
                       LIMIT %s OFFSET %s""",
                    (org_id, f"%{search}%", limit, offset),
                )
            else:
                cur.execute(
                    """SELECT p.id, p.title, p.description, p.research_objectives, p.status, p.settings_json, p.modality_type, p.created_at, p.updated_at,
                              (SELECT COUNT(*)::int FROM conversations c WHERE c.project_id = p.id) AS interview_count,
                              (SELECT COUNT(*)::int FROM conversations c WHERE c.project_id = p.id AND c.status = 'completed') AS completed_count,
                              NULL::text AS cost
                       FROM interview_projects p
                       WHERE p.org_id = %s AND p.deleted_at IS NULL
                       ORDER BY p.updated_at DESC
                       LIMIT %s OFFSET %s""",
                    (org_id, limit, offset),
                )
            rows = cur.fetchall()
        with conn.cursor() as cur:
            if search:
                cur.execute(
                    "SELECT COUNT(*) as total FROM interview_projects WHERE org_id = %s AND deleted_at IS NULL AND title ILIKE %s",
                    (org_id, f"%{search}%"),
                )
            else:
                cur.execute(
                    "SELECT COUNT(*) as total FROM interview_projects WHERE org_id = %s AND deleted_at IS NULL",
                    (org_id,),
                )
            total = cur.fetchone()["total"]
    projects = [_project_row_to_dict(r) for r in rows]
    return {"projects": projects, "total": total}


@router.get("/{project_id}")
def get_project(
    project_id: str,
    current_user: dict = Depends(get_current_designer_or_admin),
):
    """Get single project."""
    org_id = current_user.get("org_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT id, title, description, research_objectives, status, settings_json, modality_type, created_at, updated_at
                   FROM interview_projects
                   WHERE id = %s AND org_id = %s AND deleted_at IS NULL""",
                (project_id, org_id),
            )
            row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Project not found")
    return _project_row_to_dict(row)


@router.put("/{project_id}")
def update_project(
    project_id: str,
    req: UpdateProjectRequest,
    current_user: dict = Depends(get_current_designer_or_admin),
):
    """Update project. Partial update. Creates audit log."""
    org_id = current_user.get("org_id")
    user_id = current_user.get("sub")
    if not org_id or not user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT id, title, description, research_objectives, status, settings_json, modality_type, created_at, updated_at
                   FROM interview_projects
                   WHERE id = %s AND org_id = %s AND deleted_at IS NULL""",
                (project_id, org_id),
            )
            row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Project not found")
        before = _project_row_to_dict(row)
        updates = []
        params = []
        if req.title is not None:
            updates.append("title = %s")
            params.append(req.title)
        if req.description is not None:
            updates.append("description = %s")
            params.append(req.description)
        if req.research_objectives is not None:
            updates.append("research_objectives = %s")
            params.append(req.research_objectives)
        raw = row["settings_json"]
        settings = raw if isinstance(raw, dict) else (json.loads(raw) if raw else {})
        if req.target_audience is not None:
            settings["target_audience"] = req.target_audience
        if req.language is not None:
            settings["language"] = req.language
        if req.target_audience is not None or req.language is not None:
            updates.append("settings_json = %s")
            params.append(json.dumps(settings))
        if req.modality is not None:
            updates.append("modality_type = %s")
            params.append(req.modality)
        if not updates:
            return before
        updates.append("updated_at = NOW()")
        params.append(project_id)
        with conn.cursor() as cur:
            cur.execute(
                f"UPDATE interview_projects SET {', '.join(updates)} WHERE id = %s AND org_id = %s",
                params + [org_id],
            )
            cur.execute(
                """SELECT id, title, description, research_objectives, status, settings_json, modality_type, created_at, updated_at
                   FROM interview_projects WHERE id = %s""",
                (project_id,),
            )
            row = cur.fetchone()
            after = _project_row_to_dict(row)
            cur.execute(
                """INSERT INTO audit_logs (org_id, user_id, action, resource_type, resource_id, details_json)
                   VALUES (%s, %s, 'project_updated', 'project', %s, %s)""",
                (org_id, user_id, project_id, json.dumps({"before": before, "after": after})),
            )
    return after


@router.delete("/{project_id}", status_code=204)
def delete_project(
    project_id: str,
    current_user: dict = Depends(get_current_designer_or_admin),
):
    """Soft delete project. Only draft allowed. Active returns 409."""
    org_id = current_user.get("org_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, status FROM interview_projects WHERE id = %s AND org_id = %s AND deleted_at IS NULL",
                (project_id, org_id),
            )
            row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Project not found")
        if row["status"] == "active":
            raise HTTPException(
                status_code=409,
                detail="Active projects cannot be deleted. Pause or complete first.",
            )
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE interview_projects SET deleted_at = NOW() WHERE id = %s AND org_id = %s",
                (project_id, org_id),
            )
    return None


@router.post("/{project_id}/clone", status_code=201)
def clone_project(
    project_id: str,
    current_user: dict = Depends(get_current_designer_or_admin),
):
    """Clone project with questions and agents. New title '[Original] — Copy'."""
    org_id = current_user.get("org_id")
    user_id = current_user.get("sub")
    if not org_id or not user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT id, title, description, research_objectives, settings_json, modality_type
                   FROM interview_projects
                   WHERE id = %s AND org_id = %s AND deleted_at IS NULL""",
                (project_id, org_id),
            )
            row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Project not found")
        new_id = str(uuid.uuid4())
        new_title = f"[{row['title']}] — Copy"
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO interview_projects
                   (id, org_id, created_by, title, description, research_objectives, status, settings_json, modality_type)
                   VALUES (%s, %s, %s, %s, %s, %s, 'draft', %s, %s)""",
                (
                    new_id,
                    org_id,
                    user_id,
                    new_title,
                    row["description"],
                    row["research_objectives"],
                    row["settings_json"] or "{}",
                    row["modality_type"] or "text",
                ),
            )
            cur.execute(
                """INSERT INTO interview_questions (id, project_id, order_index, question_text, question_type, probing_depth, help_text, options_json, scale_config, branching_rules)
                   SELECT gen_random_uuid(), %s, order_index, question_text, question_type, probing_depth, help_text, options_json, scale_config, branching_rules
                   FROM interview_questions WHERE project_id = %s""",
                (new_id, project_id),
            )
            cur.execute(
                """INSERT INTO agents (id, project_id, name, system_prompt, version, is_active)
                   SELECT gen_random_uuid(), %s, name, system_prompt, version, is_active
                   FROM agents WHERE project_id = %s""",
                (new_id, project_id),
            )
            cur.execute(
                """SELECT id, title, description, research_objectives, status, settings_json, modality_type, created_at, updated_at
                   FROM interview_projects WHERE id = %s""",
                (new_id,),
            )
            new_row = cur.fetchone()
    return _project_row_to_dict(new_row)


def _ensure_project_org(cur, project_id: str, org_id: str) -> None:
    """Raise 404 if project not found or not in org. Uses provided cursor."""
    cur.execute(
        "SELECT id FROM interview_projects WHERE id = %s AND org_id = %s AND deleted_at IS NULL",
        (project_id, org_id),
    )
    if not cur.fetchone():
        raise HTTPException(status_code=404, detail="Project not found")


def _question_row_to_dict(row):
    raw_opts = row.get("options_json")
    opts = raw_opts if isinstance(raw_opts, list) else (raw_opts or [])
    raw_scale = row.get("scale_config")
    scale = raw_scale if isinstance(raw_scale, dict) else (raw_scale or {})
    raw_br = row.get("branching_rules")
    br = (
        raw_br
        if isinstance(raw_br, dict)
        else (json.loads(raw_br) if isinstance(raw_br, str) else None)
    )
    return {
        "id": str(row["id"]),
        "order_index": row["order_index"],
        "question_text": row["question_text"],
        "question_type": row["question_type"],
        "probing_depth": row["probing_depth"],
        "help_text": row.get("help_text"),
        "options_json": opts if opts else None,
        "scale_config": scale if scale else None,
        "branching_rules": br,
        "created_at": row["created_at"].isoformat() if row.get("created_at") else None,
        "updated_at": row["updated_at"].isoformat() if row.get("updated_at") else None,
    }


@router.get("/{project_id}/questions")
def list_questions(
    project_id: str,
    current_user: dict = Depends(get_current_designer_or_admin),
):
    """List questions for project. Ordered by order_index."""
    org_id = current_user.get("org_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    with get_connection() as conn:
        with conn.cursor() as cur:
            _ensure_project_org(cur, project_id, org_id)
            cur.execute(
                """SELECT id, order_index, question_text, question_type, probing_depth, help_text, options_json, scale_config, branching_rules, created_at, updated_at
                   FROM interview_questions WHERE project_id = %s ORDER BY order_index""",
                (project_id,),
            )
            rows = cur.fetchall()
    questions = [_question_row_to_dict(r) for r in rows]
    return {"questions": questions}


@router.put("/{project_id}/questions")
def batch_put_questions(
    project_id: str,
    req: BatchPutQuestionsRequest,
    current_user: dict = Depends(get_current_designer_or_admin),
):
    """Replace all questions for project. AC #7: batch persist."""
    org_id = current_user.get("org_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    with get_connection() as conn:
        with conn.cursor() as cur:
            _ensure_project_org(cur, project_id, org_id)
            cur.execute("DELETE FROM interview_questions WHERE project_id = %s", (project_id,))
            for i, q in enumerate(req.questions):
                opts = json.dumps(q.options_json) if q.options_json else None
                scale = json.dumps(q.scale_config) if q.scale_config else None
                cur.execute(
                    """INSERT INTO interview_questions (project_id, order_index, question_text, question_type, probing_depth, help_text, options_json, scale_config)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                    (
                        project_id,
                        i,
                        q.question_text,
                        q.question_type,
                        q.probing_depth,
                        q.help_text,
                        opts,
                        scale,
                    ),
                )
            cur.execute(
                """SELECT id, order_index, question_text, question_type, probing_depth, help_text, options_json, scale_config, branching_rules, created_at, updated_at
                   FROM interview_questions WHERE project_id = %s ORDER BY order_index""",
                (project_id,),
            )
            rows = cur.fetchall()
    return {"questions": [_question_row_to_dict(r) for r in rows]}


@router.post("/{project_id}/questions", status_code=201)
def create_question(
    project_id: str,
    req: CreateQuestionRequest,
    current_user: dict = Depends(get_current_designer_or_admin),
):
    """Create question. Appends to end."""
    org_id = current_user.get("org_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    with get_connection() as conn:
        with conn.cursor() as cur:
            _ensure_project_org(cur, project_id, org_id)
            cur.execute(
                "SELECT COALESCE(MAX(order_index), -1) + 1 AS next_idx FROM interview_questions WHERE project_id = %s",
                (project_id,),
            )
            next_idx = cur.fetchone()["next_idx"]
            cur.execute(
                """INSERT INTO interview_questions (project_id, order_index, question_text, question_type, probing_depth, help_text, options_json, scale_config)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                   RETURNING id, order_index, question_text, question_type, probing_depth, help_text, options_json, scale_config, branching_rules, created_at, updated_at""",
                (
                    project_id,
                    next_idx,
                    req.question_text,
                    req.question_type,
                    req.probing_depth,
                    req.help_text,
                    json.dumps(req.options_json) if req.options_json else None,
                    json.dumps(req.scale_config) if req.scale_config else None,
                ),
            )
            row = cur.fetchone()
    return _question_row_to_dict(row)


@router.patch("/{project_id}/questions/reorder")
def reorder_questions(
    project_id: str,
    req: ReorderRequest,
    current_user: dict = Depends(get_current_designer_or_admin),
):
    """Reorder question. Recalculates all order_index values."""
    org_id = current_user.get("org_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    with get_connection() as conn:
        with conn.cursor() as cur:
            _ensure_project_org(cur, project_id, org_id)
            cur.execute(
                "SELECT id, order_index FROM interview_questions WHERE project_id = %s ORDER BY order_index",
                (project_id,),
            )
            rows = cur.fetchall()
        q_ids = [str(r["id"]) for r in rows]
        if req.question_id not in q_ids:
            raise HTTPException(status_code=404, detail="Question not found")
        old_idx = q_ids.index(req.question_id)
        new_idx = min(req.new_index, len(q_ids) - 1)
        if old_idx == new_idx:
            with conn.cursor() as cur:
                cur.execute(
                    """SELECT id, order_index, question_text, question_type, probing_depth, help_text, options_json, scale_config, branching_rules, created_at, updated_at
                       FROM interview_questions WHERE project_id = %s ORDER BY order_index""",
                    (project_id,),
                )
                rows = cur.fetchall()
            return {"questions": [_question_row_to_dict(r) for r in rows]}
        q_ids.pop(old_idx)
        q_ids.insert(new_idx, req.question_id)
        with conn.cursor() as cur:
            for i, qid in enumerate(q_ids):
                cur.execute(
                    "UPDATE interview_questions SET order_index = %s, updated_at = NOW() WHERE id = %s AND project_id = %s",
                    (i, qid, project_id),
                )
            cur.execute(
                """SELECT id, order_index, question_text, question_type, probing_depth, help_text, options_json, scale_config, branching_rules, created_at, updated_at
                   FROM interview_questions WHERE project_id = %s ORDER BY order_index""",
                (project_id,),
            )
            rows = cur.fetchall()
    return {"questions": [_question_row_to_dict(row) for row in rows]}


@router.patch("/{project_id}/questions/{question_id}")
def update_question(
    project_id: str,
    question_id: str,
    req: UpdateQuestionRequest,
    current_user: dict = Depends(get_current_designer_or_admin),
):
    """Update question. Partial update."""
    org_id = current_user.get("org_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    with get_connection() as conn:
        with conn.cursor() as cur:
            _ensure_project_org(cur, project_id, org_id)
            cur.execute(
                "SELECT id, order_index, question_text, question_type, probing_depth, help_text, options_json, scale_config, branching_rules, created_at, updated_at FROM interview_questions WHERE id = %s AND project_id = %s",
                (question_id, project_id),
            )
            row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Question not found")
        updates = []
        params = []
        if req.question_text is not None:
            updates.append("question_text = %s")
            params.append(req.question_text)
        if req.question_type is not None:
            updates.append("question_type = %s")
            params.append(req.question_type)
        if req.probing_depth is not None:
            updates.append("probing_depth = %s")
            params.append(req.probing_depth)
        if req.help_text is not None:
            updates.append("help_text = %s")
            params.append(req.help_text)
        if req.options_json is not None:
            updates.append("options_json = %s")
            params.append(json.dumps(req.options_json))
        if req.scale_config is not None:
            updates.append("scale_config = %s")
            params.append(json.dumps(req.scale_config))
        if not updates:
            return _question_row_to_dict(row)
        updates.append("updated_at = NOW()")
        params.extend([question_id, project_id])
        with conn.cursor() as cur:
            cur.execute(
                f"UPDATE interview_questions SET {', '.join(updates)} WHERE id = %s AND project_id = %s",
                params,
            )
            cur.execute(
                "SELECT id, order_index, question_text, question_type, probing_depth, help_text, options_json, scale_config, branching_rules, created_at, updated_at FROM interview_questions WHERE id = %s",
                (question_id,),
            )
            row = cur.fetchone()
    return _question_row_to_dict(row)


def _build_rules_by_question(cur, project_id: str, question_id: str, new_rules_data: dict) -> dict:
    """Build rules_by_question including the pending update for circular detection."""
    cur.execute(
        """SELECT id, branching_rules FROM interview_questions WHERE project_id = %s""",
        (project_id,),
    )
    rows = cur.fetchall()
    rules_by_question: dict[str, list[dict]] = {}
    for r in rows:
        qid = str(r["id"])
        raw = r.get("branching_rules")
        br = raw if isinstance(raw, dict) else (json.loads(raw) if isinstance(raw, str) else None)
        rules = br.get("rules", []) if br else []
        if qid == question_id:
            rules = new_rules_data.get("rules", [])
        filtered = [x for x in rules if x.get("target_question_id")]
        if filtered:
            rules_by_question[qid] = filtered
    return rules_by_question


@router.patch("/{project_id}/questions/{question_id}/branching")
def update_question_branching(
    project_id: str,
    question_id: str,
    req: BranchingRulesRequest,
    current_user: dict = Depends(get_current_designer_or_admin),
):
    """Update branching rules for question. US-2.03. Rejects circular branches (AC6)."""
    org_id = current_user.get("org_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    with get_connection() as conn:
        with conn.cursor() as cur:
            _ensure_project_org(cur, project_id, org_id)
            cur.execute(
                "SELECT id FROM interview_questions WHERE id = %s AND project_id = %s",
                (question_id, project_id),
            )
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Question not found")
            rules_data = {
                "rules": [
                    {
                        "condition_type": r.condition_type,
                        "condition_value": r.condition_value,
                        "logic_operator": r.logic_operator,
                        "target_question_id": r.target_question_id,
                    }
                    for r in req.rules
                ],
                "default_next_question_id": req.default_next_question_id,
            }
            rules_by_question = _build_rules_by_question(cur, project_id, question_id, rules_data)
            cycles = detect_circular_reference(rules_by_question)
            if cycles:
                a, b = cycles[0]
                cur.execute(
                    "SELECT id, order_index FROM interview_questions WHERE project_id = %s ORDER BY order_index",
                    (project_id,),
                )
                order_map = {str(r["id"]): i + 1 for i, r in enumerate(cur.fetchall())}
                qa = order_map.get(a, a)
                qb = order_map.get(b, b)
                raise HTTPException(
                    status_code=400,
                    detail=f"Circular branch detected between Q{qa} and Q{qb}.",
                )
            cur.execute(
                "UPDATE interview_questions SET branching_rules = %s, updated_at = NOW() WHERE id = %s AND project_id = %s",
                (json.dumps(rules_data), question_id, project_id),
            )
            cur.execute(
                "SELECT id, order_index, question_text, question_type, probing_depth, help_text, options_json, scale_config, branching_rules, created_at, updated_at FROM interview_questions WHERE id = %s",
                (question_id,),
            )
            row = cur.fetchone()
    return _question_row_to_dict(row)


@router.delete("/{project_id}/questions/{question_id}", status_code=204)
def delete_question(
    project_id: str,
    question_id: str,
    current_user: dict = Depends(get_current_designer_or_admin),
):
    """Delete question. Reorders remaining questions."""
    org_id = current_user.get("org_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    with get_connection() as conn:
        with conn.cursor() as cur:
            _ensure_project_org(cur, project_id, org_id)
            cur.execute(
                "DELETE FROM interview_questions WHERE id = %s AND project_id = %s",
                (question_id, project_id),
            )
            if cur.rowcount == 0:
                raise HTTPException(status_code=404, detail="Question not found")
            cur.execute(
                """SELECT id, order_index FROM interview_questions WHERE project_id = %s ORDER BY order_index""",
                (project_id,),
            )
            rows = cur.fetchall()
            for i, r in enumerate(rows):
                cur.execute(
                    "UPDATE interview_questions SET order_index = %s WHERE id = %s",
                    (i, r["id"]),
                )
    return None
