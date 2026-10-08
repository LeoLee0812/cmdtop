# cmdtop

[![GitHub stars](https://img.shields.io/github/stars/LeoLee0812/cmdtop?style=flat-square)](https://github.com/LeoLee0812/cmdtop/stargazers)
[![Claude Code skill](https://img.shields.io/badge/Claude_Code-skill-D97757?style=flat-square&logo=claude&logoColor=white)](https://docs.claude.com/en/docs/claude-code/skills)
[![Python](https://img.shields.io/badge/python-3.8+-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/github/license/LeoLee0812/cmdtop?style=flat-square)](LICENSE)

看看你在 Claude Code 里到底最常敲哪个斜杠命令。

在 Claude Code 里输入 `/cmdtop`，直接给你一张排行榜：

```
  Claude Code 命令排行榜 · 全部历史
  共 13782 次输入，其中斜杠命令 3210 次，用过 105 种

   1. /usage                590  18.4%  ████████████████████████
   2. /clear                452  14.1%  ██████████████████
   3. /model                406  12.6%  █████████████████  ← sonnet×25, fable×25, opus×22
   4. /exit                 391  12.2%  ████████████████
   5. /resume               350  10.9%  ██████████████
   6. /goal                 131   4.1%  █████
   7. /rename               117   3.6%  █████
   8. /btw                   92   2.9%  ████
   9. /effort                88   2.7%  ████  ← max×39, medium×13, high×10
  10. /context               62   1.9%  ███
```

## 安装

**方式一：插件市场（推荐）**

```
/plugin marketplace add LeoLee0812/cmdtop
/plugin install cmdtop@cmdtop
```

**方式二：直接拷 skill**

```bash
git clone https://github.com/LeoLee0812/cmdtop.git
cp -r cmdtop/skills/cmdtop ~/.claude/skills/
```

装完重开一个会话就能用 `/cmdtop`。

## 用法

| 命令 | 效果 |
| --- | --- |
| `/cmdtop` | 全部历史 Top 15 |
| `/cmdtop -d 7` | 最近 7 天 |
| `/cmdtop -n 30` | 显示前 30 名 |
| `/cmdtop --builtin` | 只看内置命令，不算 skill / 插件 |
| `/cmdtop -p my-project` | 只看某个项目 |
| `/cmdtop --json` | 输出 JSON |

也可以直接说"我这周最常用哪些命令"，Claude 会自动调用。

不进 Claude Code，在终端直接跑也行：

```bash
python3 skills/cmdtop/scripts/cmdtop.py -d 30
```

## 原理

Claude Code 会把你每次回车的输入记在 `~/.claude/history.jsonl` 里。cmdtop 做三件事：

1. **建命令表**：内置命令清单 + 扫描本机装的 skill、自定义命令、插件命令
2. **正则提取**：用 `^/命令名(空白|结尾)` 匹配每条输入，`/Users/xxx` 这种路径不会误伤；`/quit`、`/reset` 这类别名归并到主命令，`/rsume`、`/exiut` 这类手误按最接近的命令算
3. **计数排序**：输出 Top N，`/model`、`/effort` 这种带选项的命令顺带统计你最常切到哪个参数

匹配不上任何已知命令的会单独列在"未识别"里，一般是卸掉的 skill。

## 隐私

纯本地运行，只用 Python 标准库，不联网、不上传。像 `/btw`、`/goal` 后面跟的自由文本不会被展示，只统计次数。

## License

MIT
