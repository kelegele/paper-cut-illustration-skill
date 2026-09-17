# paper-cut-illustration · 剪纸插画 Skill

把一张人物照片变成温暖、精致、有分层卡纸质感的剪纸插画的 agent skill。生成本体走图片编辑工具，透明背景由本地色键脚本完成，不依赖付费 API 或模型下载。

## 功能

- 以 [references/original-prompt.txt](paper-cut-illustration/references/original-prompt.txt) 的英文原文为唯一基础提示词，全文传给生图工具；用户的本次定制只作为独立补充指令追加，不改原文。
- 生成前收集选项：
  - **比例**：1:1 / 4:3 / 16:9（画布宽高比，无默认值）。
  - **背景**：纯色（默认暖米色/奶油色纸质底）/ 其他色（描述或色值）/ 透明（RGBA PNG）。
- 透明背景：先生成与主体颜色不冲突的均匀纯色底图，再用仓库自带脚本抠图输出透明 PNG，保留内部纸纹、层间阴影与暖白模切边。

## 仓库结构

```
paper-cut-illustration/          # skill 包本体
├── SKILL.md                     # 主指令：执行流程、生成前选项、检查与交付
├── references/
│   ├── original-prompt.txt      # 英文基础提示词（不可修改）
│   └── transparent-workflow.md  # 透明 PNG 工作流
└── scripts/
    └── remove_background.py     # Pillow 色键抠图脚本（PEP 723）
tests/                           # 抠图脚本行为测试（unittest）
docs/superpowers/specs/          # 设计文档
output/                          # 成品输出目录（已 gitignore）
```

## 安装

### 发给 Agent 的安装提示词（推荐）

skill 由 Agent 安装。把下面整段发给 ZCode / Claude Code / Codex 等：

```text
请安装 paper-cut-illustration skill：
1. 克隆 https://github.com/kelegele/paper-cut-illustration-skill 到本地持久目录，位置自选并告知。
2. 把仓库内的 paper-cut-illustration/ 目录链入你读取的用户级 skills 目录（如 ~/.zcode/skills/、~/.claude/skills/、~/.agents/skills/，按你自己的规则选）：Windows 用 junction（mklink /J），Linux/macOS 用软链（ln -s）。不复制文件，保持仓库为唯一源，仓库更新即生效。
3. 完成后确认 <skills 目录>/paper-cut-illustration/SKILL.md 可读，报告安装位置。
```

### skills CLI

```bash
npx skills add kelegele/paper-cut-illustration-skill -a claude-code --copy -y
```

装到当前项目 `.claude/skills/`，为真实文件：`--copy` 直接复制成真身，不在 `.agents/skills/` 留源建软链；`-a` 指定目标 agent；`-y` 跳过确认。安装来源记录在 `skills-lock.json`，便于还原。

## 使用

对支持 skill 的 agent 说：

> 使用 $paper-cut-illustration，把这张照片变成剪纸插画。

按提示选择比例与背景即可；同图修正沿用原选项。

## 抠图脚本

```bash
uv run paper-cut-illustration/scripts/remove_background.py input.png output/cutout.png --key "#00FF00" [--tolerance 35] [--feather 65] [--seed "x,y"]
```

- 仅删除与画布边缘连通的均匀背景色，非语义分割。
- 封闭背景孔用 `--seed "x,y"` 显式指定，不做全局同色删除。
- 棋盘格、复杂背景不适用，请重做纯色底图。
- 输出必须是新的 `.png` 路径，脚本拒绝覆盖已存在文件。

依赖由 PEP 723 头声明（Python >=3.10，Pillow >=10,<13），`uv run` 自动解析，无需手动配置环境。

## 测试

```bash
uv run --with "Pillow>=10,<13" python -m unittest discover -s tests -v
```

## 约束

- 项目与 skill 名称固定 `paper-cut-illustration`；原文针对人物服饰插画，不宣称支持任意题材。
- `references/original-prompt.txt` 不可修改：不翻译、不缩写、不润色、不重排段落。
- 不覆盖已有成品：新输出用不同文件名写入 `output/` 或用户指定位置。
