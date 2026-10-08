---
name: cmdtop
description: 统计用户在 Claude Code 里最常用的斜杠命令（/resume、/model、/exit 等），读取本地 ~/.claude/history.jsonl，按命中次数输出 Top 排行榜。当用户执行 /cmdtop、问"我最常用哪些命令""统计一下我的命令使用""命令排行"时使用。
argument-hint: "[-n 条数] [-d 天数] [-p 项目] [--builtin]"
allowed-tools: Bash(python3:*)
---

# cmdtop：Claude Code 命令排行榜

直接运行统计脚本，把用户给的参数原样透传：

```bash
python3 "${CLAUDE_SKILL_DIR:-$HOME/.claude/skills/cmdtop}/scripts/cmdtop.py" $ARGUMENTS
```

参数说明（用户用自然语言说的，翻译成对应参数）：

- `-n 20`：显示前 20 名（默认 15）
- `-d 7`：只看最近 7 天（"这周""最近一个月"→ `-d 7` / `-d 30`）
- `-p 关键词`：只看某个项目路径
- `--builtin`：只看内置命令，不含 skill / 插件命令
- `--json`：输出 JSON

拿到输出后：

1. 把排行榜原样放进代码块展示给用户（保留柱状图对齐）
2. 下面用一两句话点评：前三名是谁、占比多少，有没有值得一提的习惯（比如 `/clear` 很多可以试试 `/compact`，`/model` 切得多可以在 settings 里设默认模型）
3. 不要编造脚本没给出的数字
