#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
定时刷新量化数据 → data/snapshot.json

设计原则
--------
- 只做「量化数据」刷新：行情、估值、资金流、筛选池规模。
- 不做「分析师判断」：评级、情景区间、触发/推翻条件属于人工判断，
  必须手工维护在 assets/data.js 中（见 README 第六节）。
- 凭据只从环境变量 EM_API_KEY 读取（GitHub Actions Secret），
  绝不写入前端产物，绝不落盘到仓库。

用法
----
    EM_API_KEY=xxx python scripts/refresh.py

输出
----
    data/snapshot.json
"""

import json
import os
import sys
import uuid
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta
from pathlib import Path

MCP_URL = "https://ai-saas.eastmoney.com/proxy/b/mcp/tool/selectSecurity"
CST = timezone(timedelta(hours=8))
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "snapshot.json"

# 与研究报告第四章「筛选漏斗」一一对应的查询条件
QUERIES = [
    {"key": "capital_inflow", "system": "全体系·资金",
     "query": "今日主力资金净流入排名前50的股票", "selectType": "A股"},
    {"key": "limit_up_ladder", "system": "短线·情绪",
     "query": "今日涨停的股票，按连续涨停天数从多到少排序，最多40只", "selectType": "A股"},
    {"key": "trend_bullish", "system": "中线·趋势",
     "query": "股价在60日均线上方，5日均线大于20日均线大于60日均线，近20日涨幅大于5%，总市值大于100亿，市盈率小于60",
     "selectType": "A股"},
    {"key": "deep_value", "system": "长线·价值",
     "query": "市净率低于1.2倍，市盈率低于12倍，总市值大于200亿，近3年净利润均为正", "selectType": "A股"},
    {"key": "quality_value", "system": "长线·价值",
     "query": "市盈率低于15倍，净资产收益率大于15%，股息率大于3%，总市值大于100亿", "selectType": "A股"},
]


def build_meta(query: str, select_type: str) -> dict:
    return {
        "query": query,
        "selectType": select_type,
        "toolContext": {
            "callId": f"call_{uuid.uuid4().hex[:8]}",
            "userInfo": {"userId": f"user_{uuid.uuid4().hex[:8]}"},
        },
    }


def call_mcp(api_key: str, query: str, select_type: str, retries: int = 2) -> dict:
    payload = json.dumps(build_meta(query, select_type)).encode("utf-8")
    req = urllib.request.Request(
        MCP_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "em_api_key": api_key,
            "x-open-id-vendor": "tencent",
            "x-open-id-app": "workbuddy",
        },
        method="POST",
    )
    last = None
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=45) as resp:
                body = json.loads(resp.read().decode("utf-8"))
            code = body.get("code")
            status = body.get("status")
            if code in (401, "401", 403, "403") or status in (401, "401", 403, "403"):
                raise RuntimeError(f"鉴权失败（HTTP 业务码 {code}/{status}），请检查 EM_API_KEY")
            return body.get("data") or {}
        except urllib.error.HTTPError as e:
            if e.code in (401, 403):
                raise RuntimeError(f"鉴权失败（HTTP {e.code}），请检查 EM_API_KEY") from e
            last = e
        except Exception as e:  # noqa: BLE001
            last = e
        if attempt < retries:
            print(f"    重试 {attempt + 1}/{retries} …")
    raise RuntimeError(f"调用失败：{last}")


def norm_rows(data: dict) -> list:
    """把 MCP 返回的 columns + dataList 归一成 [{中文列名: 值}]"""
    cols = data.get("columns") or []
    rows = data.get("dataList") or []
    if not cols or not rows:
        return []
    cmap = {}
    for c in cols:
        en = c.get("field") or c.get("name") or c.get("key")
        cn = c.get("title") or c.get("label") or c.get("name") or en
        if en:
            cmap[en] = cn
    out = []
    for r in rows:
        if isinstance(r, dict):
            out.append({cmap.get(k, k): v for k, v in r.items()})
        elif isinstance(r, list):
            out.append({cmap.get(cols[i].get("field", i), i): v
                        for i, v in enumerate(r) if i < len(cols)})
    return out


def main() -> int:
    api_key = os.environ.get("EM_API_KEY", "").strip()
    if not api_key:
        print("ERROR: 未设置环境变量 EM_API_KEY", file=sys.stderr)
        return 2

    snapshot = {
        "generatedAt": datetime.now(CST).strftime("%Y-%m-%d %H:%M"),
        "generatedAtISO": datetime.now(CST).isoformat(),
        "source": "东方财富妙想选股",
        "note": "仅含量化数据；评级与情景区间属人工判断，维护于 assets/data.js",
        "pools": [],
    }

    ok = 0
    for q in QUERIES:
        print(f"[{q['system']}] {q['query'][:38]}…")
        try:
            data = call_mcp(api_key, q["query"], q["selectType"])
            rows = norm_rows(data)
            snapshot["pools"].append({
                "key": q["key"],
                "system": q["system"],
                "query": q["query"],
                "count": len(rows),
                "rows": rows,
            })
            print(f"    ✓ {len(rows)} 行")
            ok += 1
        except Exception as e:  # noqa: BLE001
            print(f"    ✗ {e}", file=sys.stderr)
            snapshot["pools"].append({
                "key": q["key"], "system": q["system"], "query": q["query"],
                "count": 0, "rows": [], "error": str(e),
            })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n已写入 {OUT.relative_to(ROOT)}（成功 {ok}/{len(QUERIES)} 个筛选池）")

    # 全部失败视为异常，让 Actions 变红以便察觉
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
