#!/usr/bin/env python3
"""cmdtop：统计你在 Claude Code 里最常敲的斜杠命令，输出 Top 排行榜。

数据来源是 Claude Code 自己记下的输入历史 ~/.claude/history.jsonl，
每敲一次回车就会追加一行 {"display": "...", "timestamp": ..., "project": ...}。
这个文件会被 Claude Code 按 cleanupPeriodDays 裁剪，所以每次运行都会顺手归档一份。
纯标准库，无任何依赖，数据只在本地读，不上传。
"""
import argparse
import difflib
import json
import os
import re
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

CLAUDE_DIR = Path(os.environ.get("CLAUDE_CONFIG_DIR", Path.home() / ".claude"))
ARCHIVE = CLAUDE_DIR / "cmdtop" / "archive.jsonl"

# Claude Code 内置斜杠命令（含历代版本出现过的，旧命令留着不影响统计）
BUILTIN = {
    "add-dir", "agents", "artifacts", "bashes", "bg", "branch", "btw", "buddy", "bug",
    "chrome", "clear", "code-review", "color", "compact", "config", "context", "continue",
    "copy", "cost", "desktop", "doctor", "effort", "exit", "export", "extra-usage", "fast",
    "feedback", "fewer-permission-prompts", "fork", "goal", "help", "hooks", "ide", "init",
    "insights", "install-github-app", "install-slack-app", "keybindings", "login", "logout",
    "loop", "mcp", "memory", "migrate-installer", "mobile", "model", "new", "output-style",
    "passes", "permissions", "plan", "plugin", "plugins", "pr-comments", "privacy-settings",
    "quit", "release-notes", "reload-plugins", "remote-control", "remote-env", "rename",
    "reset", "resume", "review", "rewind", "sandbox", "schedule", "security-review",
    "simplify", "skills", "stats", "status", "statusline", "tag", "tasks", "teleport",
    "terminal-setup", "theme", "todos", "ultrareview", "upgrade", "usage", "usage-credits",
    "vim", "voice", "workflows",
}
# 别名归并到主命令
ALIASES = {"quit": "exit", "reset": "clear", "new": "clear", "continue": "resume",
           "plugins": "plugin", "cost": "usage"}

# 只对这些「参数是选项」的命令统计参数分布，其他命令后面跟的是自由文本，不展示以免泄露内容
ARG_CMDS = {"model", "effort", "fast", "theme", "output-style", "vim", "plugin", "mcp"}

# 一条输入以 /命令 开头；命令名后面紧跟空白或结束，排除 /Users/xxx 这类路径
CMD_RE = re.compile(r"^/([A-Za-z][\w.-]*(?::[\w.-]+)?)(?=\s|$)(.*)", re.S)


def scan_skills(projects):
    """收集本机装的 skill / 自定义命令名（用户级、项目级、插件）。"""
    names = set()
    roots = [CLAUDE_DIR] + [Path(p) / ".claude" for p in projects]
    for root in roots:
        for sub in ("skills", "commands"):
            d = root / sub
            if not d.is_dir():
                continue
            for p in d.iterdir():
                names.add(p.stem if p.suffix == ".md" else p.name)
    cache = CLAUDE_DIR / "plugins" / "cache"
    if cache.is_dir():
        for d in cache.glob("*/*/*/*"):
            if d.name in ("skills", "commands") and d.is_dir():
                plugin = d.parent.parent.name
                for p in d.iterdir():
                    n = p.stem if p.suffix == ".md" else p.name
                    names.add(f"{plugin}:{n}")
                    names.add(n)
    return names


def read_jsonl(path):
    if not path.exists():
        return []
    out = []
    with open(path, encoding="utf-8", errors="ignore") as f:
        for line in f:
            try:
                out.append(json.loads(line))
            except ValueError:
                continue
    return out


def slim(d):
    """归档只留统计要用的字段：普通输入清空正文，斜杠命令只留第一行前 60 字。"""
    text = d.get("display", "").strip()
    text = text.split("\n", 1)[0][:60] if text.startswith("/") else ""
    return {"display": text, "timestamp": d.get("timestamp", 0),
            "project": d.get("project", ""), "sessionId": d.get("sessionId", "")}


def sync_archive():
    """新版 Claude Code 会按 cleanupPeriodDays（默认 30 天）裁剪 history.jsonl，
    所以每次运行都把新记录并入 cmdtop 自己的归档，旧数据被裁掉也还在。"""
    live = read_jsonl(CLAUDE_DIR / "history.jsonl")
    archive = read_jsonl(ARCHIVE)
    key = lambda d: (d.get("timestamp", 0), d.get("sessionId", ""))
    seen = {key(d) for d in archive}
    fresh = [slim(d) for d in live if key(d) not in seen]
    if fresh:
        try:
            ARCHIVE.parent.mkdir(parents=True, exist_ok=True)
            with open(ARCHIVE, "a", encoding="utf-8") as f:
                for d in fresh:
                    f.write(json.dumps(d, ensure_ascii=False) + "\n")
        except OSError:
            pass  # 写不了归档不影响本次统计
    if not live and not archive:
        sys.exit(f"找不到 {CLAUDE_DIR / 'history.jsonl'}，确认装过并用过 Claude Code")
    return archive + fresh


def load(days, project, no_archive=False):
    rows = [slim(d) for d in read_jsonl(CLAUDE_DIR / "history.jsonl")] if no_archive else sync_archive()
    since = (time.time() - days * 86400) * 1000 if days else 0
    return [d for d in rows
            if d["timestamp"] >= since and (not project or project in d["project"])]


def bar(n, top, width=24):
    return "█" * max(1, round(n / top * width)) if top else ""


def main():
    ap = argparse.ArgumentParser(description="统计 Claude Code 斜杠命令使用排行")
    ap.add_argument("-n", "--top", type=int, default=15, help="显示前几名（默认 15）")
    ap.add_argument("-d", "--days", type=int, default=0, help="只看最近 N 天（默认全部）")
    ap.add_argument("-p", "--project", default="", help="只看路径包含该字符串的项目")
    ap.add_argument("--builtin", action="store_true", help="只看内置命令，不含 skill")
    ap.add_argument("--no-archive", action="store_true", help="不读写归档，只看当前 history.jsonl")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    a = ap.parse_args()

    rows = load(a.days, a.project, a.no_archive)
    skills = scan_skills({r.get("project", "") for r in rows if r.get("project")})

    hits, args_of, unknown = Counter(), defaultdict(Counter), Counter()
    kind = {}
    for r in rows:
        m = CMD_RE.match(r.get("display", "").strip())
        if not m:
            continue
        name, rest = m.group(1), m.group(2).strip()
        name = ALIASES.get(name, name)
        if name not in BUILTIN and name not in skills and ":" not in name:
            # 手误（/rsume、/exiut）按最接近的已知命令算
            near = difflib.get_close_matches(name, BUILTIN | skills, n=1, cutoff=0.8)
            if near:
                name = near[0]
        if name in BUILTIN:
            kind[name] = "内置"
        elif name in skills or ":" in name:
            kind[name] = "skill"
        else:
            unknown[name] += 1
            continue
        if a.builtin and kind[name] != "内置":
            continue
        hits[name] += 1
        if rest and name in ARG_CMDS and len(rest) <= 30:
            args_of[name][rest] += 1

    ranked = hits.most_common(a.top)
    if a.json:
        print(json.dumps({
            "total_inputs": len(rows), "total_commands": sum(hits.values()),
            "top": [{"rank": i + 1, "command": "/" + n, "type": kind[n], "count": c,
                     "args": dict(args_of[n].most_common(3))}
                    for i, (n, c) in enumerate(ranked)],
            "unrecognized": dict(unknown.most_common(10)),
        }, ensure_ascii=False, indent=2))
        return

    total = sum(hits.values())
    scope = f"最近 {a.days} 天" if a.days else "全部历史"
    print(f"\n  Claude Code 命令排行榜 · {scope}")
    print(f"  共 {len(rows)} 次输入，其中斜杠命令 {total} 次，用过 {len(hits)} 种\n")
    if not ranked:
        print("  还没有敲过斜杠命令")
        return
    top = ranked[0][1]
    for i, (n, c) in enumerate(ranked, 1):
        pct = c / total * 100
        extra = ""
        if args_of[n]:
            extra = "  ← " + ", ".join(f"{k}×{v}" for k, v in args_of[n].most_common(3))
        print(f"  {i:>2}. /{n:<18} {c:>5}  {pct:4.1f}%  {bar(c, top)}{extra}")
    if unknown and not a.builtin:
        u = ", ".join(f"/{k}×{v}" for k, v in unknown.most_common(6))
        print(f"\n  未识别（可能是已卸载的 skill 或手误）：{u}")
    print()


if __name__ == "__main__":
    main()
