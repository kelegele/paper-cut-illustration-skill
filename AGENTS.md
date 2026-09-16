# AGENTS.md

本仓库用于维护 `paper-cut-illustration` skill（剪纸插画）。不是应用程序：无构建系统、无 package 清单，核心资产是 skill 包与抠图脚本。

## 结构

- `paper-cut-illustration/` — skill 包本体（与仓库同名）：
  - `SKILL.md` — skill 主指令：执行流程、生成前选项（比例 1:1/4:3/16:9；背景纯色/其他色/透明）、检查与交付规则。
  - `references/original-prompt.txt` — 英文基础提示词，生成时的唯一内容来源。
  - `references/transparent-workflow.md` — 透明 PNG 工作流：纯色底图 + 本地抠图。
  - `scripts/remove_background.py` — Pillow 色键抠图脚本，PEP 723 内联依赖（Python >=3.10，Pillow >=10,<13）。
  - `agents/openai.yaml` — 界面元数据。
- `tests/test_remove_background.py` — 抠图脚本行为测试（unittest，合成小图，不依赖真实图片）。
- `docs/superpowers/specs/` — 设计文档，命名 `YYYY-MM-DD-<topic>-design.md`。
- `output/` — 成品输出目录，已 gitignore。

## 常用命令

```bash
# 测试（仓库根执行；无 pyproject，用 --with 提供 Pillow）
uv run --with "Pillow>=10,<13" python -m unittest discover -s tests -v

# 抠图脚本（可从任意目录用绝对/相对路径调用；输出必须是新的 .png 路径）
uv run paper-cut-illustration/scripts/remove_background.py input.png output/cutout.png --key "#00FF00" [--tolerance 35] [--feather 65] [--seed "x,y"]
```

所有 Python 一律经 `uv` 执行，不用系统 Python/pip；脚本依赖由 PEP 723 头自动解析。

## 硬性约束

- **`references/original-prompt.txt` 不可修改**：不翻译、不缩写、不润色、不重排段落；执行时全文读取并传给生图工具。用户的本次定制只作为独立补充指令追加，不改原文文件（设计文档记录其 SHA256 不应变）。
- 项目与 skill 名称固定为 `paper-cut-illustration`（剪纸插画）；原文针对人物服饰插画，不得改名或宣称支持任意题材。
- 不覆盖已有成品：保留源图，新输出用不同文件名写入 `output/` 或用户指定位置；脚本本身拒绝覆盖任何已存在文件。
- 抠图脚本边界：仅删除与画布边缘连通的均匀背景色，非语义分割；封闭背景孔用 `--seed "x,y"` 显式指定，禁止全局删除同色像素；棋盘格、复杂背景不适用，应要求重做纯色底图。
- 文档与规则用简体中文；唯一例外是 `original-prompt.txt` 保持英文原文。
