"""Auto-Ontology 语义层的 Django 集成：vendor 核心库 + 权限护栏。

- 核心库位于 backend/vendor/auto_ontology（从官方容器裁剪抽取，已含千问 patch）；
- 语义元数据/向量仍存于现有 postgres+pgvector 容器，编译结果直接复用；
- ask_for_user(user_id, question) 同步执行（agent 为同步生成器），
  调用方（ai_gateway 工具层）用 sync_to_async 包装；
- 数据权限 = 用户本人权限：self→仅本人，team→visible_ids(团队+本人)，all→不过滤。
"""

from __future__ import annotations

import logging
import os
import sys
import threading
from pathlib import Path
from typing import Any

from django.conf import settings

logger = logging.getLogger(__name__)

_VENDOR = Path(settings.BASE_DIR) / "vendor"
if _VENDOR.is_dir() and str(_VENDOR) not in sys.path:
    sys.path.insert(0, str(_VENDOR))

_env_lock = threading.Lock()
_env_ready = False
_retriever_lock = threading.Lock()
_retrievers: tuple | None = None

MAX_DISPLAY_ROWS = 50


def _setup_env() -> None:
    """把 Django 配置映射为 auto_ontology 需要的环境变量（幂等）。"""
    global _env_ready
    if _env_ready:
        return
    with _env_lock:
        if _env_ready:
            return
        mapping = {
            "POSTGRES_HOST": "ONTOLOGY_PG_HOST",
            "POSTGRES_PORT": "ONTOLOGY_PG_PORT",
            "POSTGRES_USER": "ONTOLOGY_PG_USER",
            "POSTGRES_PASSWORD": "ONTOLOGY_PG_PASSWORD",
            "POSTGRES_DATABASE": "ONTOLOGY_PG_DATABASE",
        }
        for target, source in mapping.items():
            value = os.environ.get(source)
            if value:
                os.environ.setdefault(target, value)
        os.environ.setdefault("POSTGRES_HOST", "127.0.0.1")
        os.environ.setdefault("POSTGRES_PORT", "5432")
        os.environ.setdefault("POSTGRES_USER", "postgres")
        os.environ.setdefault("POSTGRES_DATABASE", "auto_ontology")

        ai_key = os.environ.get("AI_API_KEY") or getattr(settings, "AI_API_KEY", "")
        ai_base = os.environ.get("AI_BASE_URL") or getattr(settings, "AI_BASE_URL", "")
        ai_model = os.environ.get("AI_MODEL") or getattr(settings, "AI_MODEL", "qwen-plus")
        if ai_key:
            os.environ.setdefault("DEFAULT_MODELS_API_KEY", ai_key)
        if ai_base:
            os.environ.setdefault("DEFAULT_MODELS_ENDPOINT", ai_base)
        os.environ.setdefault("DEFAULT_MODELS_MODEL", ai_model)
        os.environ.setdefault("REASONING_MODEL", ai_model)
        os.environ.setdefault("NON_REASONING_MODEL", ai_model)
        os.environ.setdefault("EMBED_MODEL", "text-embedding-v3")
        os.environ.setdefault("EMBED_BATCH_SIZE", "10")
        os.environ.setdefault("EMBED_DIMENSION", "1024")
        _env_ready = True


def _get_retrievers() -> tuple:
    """retriever 单例（内部连接池复用，懒加载）。"""
    global _retrievers
    if _retrievers is None:
        with _retriever_lock:
            if _retrievers is None:
                _setup_env()
                from auto_ontology.utils import (
                    get_data_objects_retriever,
                    get_semantic_objects_retriever,
                )

                _retrievers = (
                    get_data_objects_retriever(),
                    get_semantic_objects_retriever(),
                )
    return _retrievers


def _visible_employee_ids(user_id: int) -> list[int] | None:
    """当前用户可见的员工 ID 集合；None 表示全部可见（all scope）。"""
    from apps.accounts.models import UserAccount
    from apps.accounts.services.auth import get_user_roles
    from apps.accounts.services.managers import visible_ids

    best_role = None
    for role in get_user_roles(user_id):
        if role.scope == "all":
            return None
        if role.scope == "team":
            best_role = role.role_code
    if best_role is None:
        return [user_id]
    user = UserAccount.objects.filter(id=user_id).only("id").first()
    if user is None:
        return [user_id]
    return list(visible_ids(user, best_role))


def _ensure_llm_clients() -> None:
    """main.py 在 import 时初始化 LLM client；若此前 env 未就绪导致为 None，这里兜底重建。"""
    from auto_ontology.retrieval.text_to_sql import main as tts_main

    if tts_main.llm_client is None or tts_main.reasoning_llm_client is None:
        from auto_ontology.utils.llm_invoke import (
            get_llm_client,
            get_non_reasoning_llm_client,
        )

        tts_main.llm_client = get_non_reasoning_llm_client()
        tts_main.reasoning_llm_client = get_llm_client()


def ask_for_user(user_id: int, question: str) -> dict[str, Any]:
    """以指定用户的权限执行一次语义查询，返回答案 + SQL + 数据行。"""
    # 注意：必须先 _setup_env() 再 import main（其模块级 LLM client 依赖环境变量）
    _setup_env()
    from auto_ontology.connectors import get_connectors
    from auto_ontology.retrieval.text_to_sql.main import stream_agent_response

    from .guard import GuardedConnector, SqlGuardError

    _ensure_llm_clients()
    visible = _visible_employee_ids(user_id)
    data_retriever, semantic_retriever = _get_retrievers()
    raw_connectors = get_connectors()
    if not raw_connectors:
        return {"error": "语义层尚未配置业务数据库连接。"}
    connectors = [GuardedConnector(c, visible) for c in raw_connectors]

    payload = {
        "question": question,
        "evidence": "",
        "custom_prompts": "所有回答必须使用简体中文。",
        "data_retriever": data_retriever,
        "semantic_retriever": semantic_retriever,
        "connectors": connectors,
    }

    answer_text = ""
    sql_code = ""
    try:
        for event in stream_agent_response(payload):
            event_type = event.get("type")
            if event_type == "result":
                answer = event.get("answer", {}) or {}
                answer_text = str(answer.get("response") or "")
                sql_code = str(answer.get("sql_code") or "") or sql_code
            elif event_type == "sql":
                sql_code = str(event.get("sql") or "") or sql_code
            elif event_type == "error":
                return {"error": f"语义查询失败：{event.get('message')}"}
    except SqlGuardError as exc:
        return {"error": f"SQL 安全校验未通过：{exc}"}
    except Exception:
        logger.exception("ontology ask failed for user %s", user_id)
        return {"error": "语义查询执行失败，请稍后重试。"}

    if not answer_text and not sql_code:
        return {"error": "语义层未能生成有效回答，请换种问法或改用专用查询工具。"}

    # 展示用数据行：经同一护栏再执行一次最终 SQL，保证所见即权限内数据
    rows: list[dict[str, Any]] = []
    if sql_code:
        try:
            frame = connectors[0].execute(sql_code)
            rows = [
                {k: (str(v) if v is not None else "") for k, v in row.items()}
                for row in frame.head(MAX_DISPLAY_ROWS).to_dict(orient="records")
            ]
        except Exception:
            logger.warning("ontology display-query failed", exc_info=True)

    scope_text = "全部数据" if visible is None else f"可见员工 {len(visible)} 人范围内"
    result: dict[str, Any] = {
        "回答": answer_text,
        "SQL": sql_code,
        "数据行": rows,
        "权限说明": f"本次查询已自动限定在当前登录用户权限范围内（{scope_text}）。",
    }
    return result
