"""Hybrid retrieval over the carrier internal incident KB.

Sources: operational runbooks + a ServiceNow ITSM historical-incident export.
Deterministic keyword/code overlap is the runnable baseline when no retriever is injected;
a real retriever (dense multilingual-e5 + BM25 for device/error codes) is injected via
config in production.
"""

from __future__ import annotations

from typing import Any, cast
import re

# Seed internal KB (deterministic fallback when no retriever is injected).
_SEED_KB: list[dict[str, Any]] = [
    {
        "doc_id": "RUNBOOK-BGP-FLAP-001",
        "source": "runbook",
        "device": "core_router",
        "incident_type": "bgp_flap",
        "text": "BGPセッションフラップ発生時: 1) 対向ルータの到達性をping/tracerouteで確認, 2) interface error counterを確認, 3) BGP neighbor logを採取, 4) 物理層(光レベル)を確認。復旧しない場合はTier2へエスカレーション。",
        "escalation": ["NOC-Tier2", "Core-Network-Engineering"],
    },
    {
        "doc_id": "ITSM-INC0048213",
        "source": "itsm",
        "device": "core_router",
        "incident_type": "bgp_flap",
        "text": "過去事例: 光モジュール劣化によるBGPフラップ。SFPを交換し復旧。MTTR 45分。",
        "escalation": ["NOC-Tier2"],
    },
    {
        "doc_id": "RUNBOOK-CELL-DOWN-014",
        "source": "runbook",
        "device": "enodeb",
        "incident_type": "cell_outage",
        "text": "セル停止時: 1) OSS/EMSでアラーム種別を確認, 2) 伝送路(バックホール)断を確認, 3) 電源・環境アラームを確認, 4) リモートリセットを実施。改善なければ現地保守へエスカレーション。",
        "escalation": ["Field-Maintenance", "RAN-Engineering"],
    },
    {
        "doc_id": "ITSM-INC0051902",
        "source": "itsm",
        "device": "enodeb",
        "incident_type": "cell_outage",
        "text": "過去事例: バックホール光ファイバ断によるセル停止。伝送ベンダ手配で復旧。MTTR 3時間。",
        "escalation": ["Field-Maintenance"],
    },
    {
        "doc_id": "RUNBOOK-CORE-CPU-022",
        "source": "runbook",
        "device": "packet_core",
        "incident_type": "high_cpu",
        "text": "パケットコアCPU高負荷時: 1) トラフィック異常(DDoS等)を確認, 2) 該当ノードのプロセス使用率を確認, 3) 必要に応じ負荷分散・トラフィック制御。継続時はコアエンジニアリングへエスカレーション。",
        "escalation": ["Core-Network-Engineering"],
    },
]

_CODE = re.compile(r"[A-Za-z]+[-_/]?\d+")


def hybrid_retrieve(
    query: str, top_k: int = 8, hybrid_search: bool = True, retriever: Any = None
) -> list[dict[str, Any]]:
    """Retrieve candidate resolution passages for an incident query.

    If ``retriever`` is injected it must expose ``search(query, top_k, hybrid_search)``.
    Otherwise a deterministic keyword + device/error-code overlap over the seed KB is used.
    """
    if retriever is not None:
        return cast(list[dict[str, Any]], retriever.search(query, top_k=top_k, hybrid_search=hybrid_search))

    q = (query or "").lower()
    codes = {c.lower() for c in _CODE.findall(query or "")}
    keywords = (
        "bgp",
        "flap",
        "セル",
        "停止",
        "cpu",
        "高負荷",
        "光",
        "バックホール",
        "ルータ",
        "router",
        "outage",
        "down",
    )
    scored = []
    for doc in _SEED_KB:
        text = doc["text"].lower()
        overlap = sum(1 for kw in keywords if kw in q or kw in text)
        overlap += sum(1 for c in codes if c in doc["doc_id"].lower())
        # soft device/incident-type signal
        if doc["device"] in q or doc["incident_type"].replace("_", " ") in q:
            overlap += 1
        scored.append((overlap, doc))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [dict(d, score=round(0.5 + 0.05 * s, 3)) for s, d in scored[:top_k] if s > 0] or [
        dict(d, score=0.4) for _s, d in scored[:top_k]
    ]
