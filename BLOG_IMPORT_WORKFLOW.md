# 博客更新快速指南（Import Workflow）

> 配套文档：`BLOG_DOCUMENTATION.md` 定义"文章格式规则"；本文定义"如何把 `_pre_docs/` 的新草稿落地成已发布文章"。  
> 适用场景：在 `_pre_docs/` 增加了一批新的 Markdown 草稿，要批量导入 `_posts/` 并推送到 GitHub Pages。

------

## 0. 一行命令版（确认环境正常时直接跑）

```bash
cd /home/white/Desktop/2-github/github.io

# 1. 看哪些是新的，哪些已经导入过（按 display_filename 判定）
for f in _pre_docs/*.md; do
  name=$(basename "$f")
  grep -lFq "display_filename: \"$name\"" _posts/*.md 2>/dev/null \
    && echo "SKIP $name" || echo "NEW  $name"
done

# 2. 取下一个可用编号
ls _posts/ | grep -oE '\b[0-9]{3}\b' | sort -n | tail -1 | awk '{print $1+1}'

# 3. 创建 _posts/YYYY-MM-DD-NNN-slug.md（按 §3 模板补 front matter + 清洗正文）

# 4. 验证：必须无输出
grep -RInE "<font|</font>|style=|<span|</span>|<u>|</u>" _posts

# 5. 提交 & 推送
git add _posts/2026-MM-DD-*.md
git commit -m "Import new posts: <简短主题列表>"
git push https://niuteng5618:<PAT>@github.com/niuteng5618/niuteng5618.github.io.git main
```

详细步骤、决策点、常见坑见下文。

------

## 1. 处理流程总览

```
_pre_docs/*.md  ──①盘点──▶  待导入清单
                              │
                              ②按 BLOG_DOCUMENTATION.md 分配 NNN / 选分类
                              │
                              ③在 _posts/ 写入新文件（前置 front matter + 清洗正文）
                              │
                              ④grep 校验 + 前置字段校验
                              │
                              ⑤git add / commit
                              │
                              ⑥git push（HTTPS + PAT）
                              │
                              ▼
                       GitHub Pages 自动构建（30–90s）
                              │
                              ▼
                  https://niuteng5618.github.io/<title-slug>/
```

`_pre_docs/` 里的原始文件**导入后保留**，不删除、不重命名 — 这是历史草稿归档，每篇 `_posts/*.md` 通过 `display_filename` 反向指向它。

------

## 2. Step 1 — 盘点：新草稿 vs 已导入

唯一可靠的判定方式：用 `display_filename` 字段反查 `_posts/`，**不要靠标题猜**。

```bash
cd /home/white/Desktop/2-github/github.io
for f in _pre_docs/*.md; do
  name=$(basename "$f")
  if grep -lFq "display_filename: \"$name\"" _posts/*.md 2>/dev/null; then
    echo "SKIP (已导入): $name"
  else
    echo "NEW  (待导入): $name"
  fi
done
```

输出 `NEW` 的就是这次要处理的草稿。

------

## 3. Step 2 — 分配编号 & 选分类

### 3.1 取下一个可用编号

```bash
ls _posts/ | grep -oE '\b[0-9]{3}\b' | sort -n | tail -1 | awk '{print $1+1}'
```

- 编号**只增不复用**，即便中间有删除留下空号。
- 同一批多篇导入：按草稿顺序连续递增（例如本次 076 / 077 / 078）。

### 3.2 选 primary / secondary / series

参照 `BLOG_DOCUMENTATION.md` 的"分类与标签规范"和已有文章的 `*_order` 字段。归类原则：

| 内容方向 | 推荐归类 |
| --- | --- |
| Claude Code / Codex 内部机制（system prompt、compact、memory、hook、todo、熔断器…） | `智能体应用开发 / AI 编程工具 / Claude Code / Codex` → 5/3/1 |
| MCP / Skill / Agent 通用工具链 | `智能体应用开发 / Agent 工具链 / MCP` 或 `Skill` → 5/1/x |
| 多智能体（MetaGPT 等） | `智能体应用开发 / 多智能体框架 / MetaGPT` → 5/2/1 |
| RAG 检索 / 排序 / 评测 / 框架 | `RAG / …` → 3/x/x |
| LLM 推理（KV Cache / 量化 / vLLM / SGLang） | `大模型技术 / 推理与部署 / …` → 2/5/x |
| LLM 训练（预训练 / LoRA / FSDP） | `大模型技术 / 训练与微调` 或 `训练基础设施` → 2/3/x、2/4/x |
| Attention / LLaMA / MoE / Embedding 等架构 | `大模型技术 / 模型架构与基础 / …` → 2/2/x |
| RL（PPO / DPO / GRPO / Q-learning） | `强化学习与对齐 / …` → 4/x/x |
| 序列模型 / 激活函数 / 正则化 / PyTorch | `传统深度学习 / …` → 1/x/x |

复用现有 `series` 时，`*_order` 三个字段必须与同 series 已有文章完全一致；新建 series 时，`series_order` 取该 `secondary_category` 下当前最大值 +1。

> 完整的分类表保存在 memory：`~/.claude/projects/-home-white-Desktop-2-github-github-io/memory/blog-taxonomy.md`。需要全量刷新时跑该文件末尾的 shell 片段即可重新生成。

### 3.3 起 slug

- 全小写 ASCII + 连字符。
- 不要直接搬中文文件名。
- 示例：`circuit-breaker`、`claude-code-context-compact`、`claude-code-memory`。

------

## 4. Step 3 — 创建文章

文件名：`_posts/YYYY-MM-DD-NNN-slug.md`（日期 = 今天；NNN = `post_order`；slug 见 §3.3）。

### 4.1 Front matter 模板

```yaml
---
layout: post
title: "文章标题"                       # ⚠ 一旦发布勿改 — 改了 URL 也会变
display_title: "显示标题"                # 仅页面显示用，可随时改
display_filename: "原始草稿名.md"        # 必须与 _pre_docs/ 下源文件一致（含中文/空格）
date: 2026-MM-DD                         # 与文件名日期一致
primary_category: "..."
secondary_category: "..."
series: "..."
primary_category_order: N
secondary_category_order: N
series_order: N
post_order: NNN                          # 必须等于文件名里的 NNN
categories:
  - <primary_category>                   # 三项必须完全等于上面 primary/secondary/series
  - <secondary_category>
  - <series>
tags:
  - tag1
  - tag2                                  # 2–5 个，优先复用已有 tag
toc: true
comments: false
author: niuteng5618
---
```

### 4.2 正文处理

- 直接把 `_pre_docs/` 的正文复制到 front matter 下面。
- 保留作者原始 `# H1` 标题（已有导入文章就是这种风格）。
- **不要**改写技术内容。

### 4.3 清洗内联 HTML（强制）

外部导入的 Markdown 经常带 `<font color>`、`<span style>`、`<u>`、内联 `style="..."`，会在浅色/深色模式下出现白字黄底等 bug。

- 删 `<font ...>` `</font>` `<span ...>` `</span>` `<u>` `</u>` —— 只保留内部文本。
- 删所有 `style="..."` 属性。
- `<br/>`、`<sub>` 等排版/公式标签可保留。

------

## 5. Step 4 — 验证

```bash
# A. 不能有残留的内联 HTML（必须无输出）
grep -RInE "<font|</font>|style=|<span|</span>|<u>|</u>" _posts

# B. 检查新文章的关键 front matter
for f in _posts/2026-MM-DD-*.md; do
  echo "=== $f ==="
  grep -E "^(layout|title|display_filename|date|primary_category|secondary_category|series|primary_category_order|secondary_category_order|series_order|post_order):" "$f"
done

# C. 确认文件名里的 NNN 等于 post_order
for f in _posts/2026-MM-DD-*.md; do
  fn_n=$(basename "$f" | grep -oE '\b[0-9]{3}\b')
  fm_n=$(grep -m1 "^post_order:" "$f" | awk '{print $2}')
  printf "%s | filename=%s post_order=%s %s\n" "$f" "$fn_n" "$fm_n" \
    "$([ "$fn_n" = "0$fm_n" ] || [ "$fn_n" = "$fm_n" ] && echo OK || echo MISMATCH)"
done
```

A 项必须零输出；B 项必须每篇都看到完整字段；C 项必须全 OK。

------

## 6. Step 5 — 提交

```bash
git add _posts/2026-MM-DD-*.md
git commit -m "Import new posts: <简短主题，多个用 / 分隔>"
```

模仿历史 commit 风格：

- `Import new blog posts and reorganize taxonomy`
- `Import new Claude Code mechanism posts`
- `Polish imported posts and article UI`

> ⚠ 永远不要 `git add _pre_docs/`。`_pre_docs/` 是工作目录中的本地草稿区，不进版本库（截至目前历史上未 commit 过任何 `_pre_docs/` 文件）。

------

## 7. Step 6 — 推送（HTTPS + PAT）

```bash
git push https://niuteng5618:<PAT>@github.com/niuteng5618/niuteng5618.github.io.git main
```

- **PAT 只在命令行临时使用**，不要写入 `.git/config`、不要落到任何文件、不要进 commit message。
- 默认 `origin` 已经是 HTTPS（`https://github.com/niuteng5618/niuteng5618.github.io.git`），保持不动。
- 推完后 GitHub Pages 30–90 秒自动构建，新文章出现在 `https://niuteng5618.github.io/<title-slug>/`。

------

## 8. 已踩过的坑与解决方案

记录的是实际遇到过的失败模式（非理论上的），便于下次秒解。

### 8.1 `Failed to connect to github.com port 443: Connection refused`

**症状**：

```
fatal: unable to access 'https://github.com/...': Failed to connect to github.com port 443 after 21082 ms: Connection refused
```

`ping github.com` 通，`curl -I https://github.com` 也 timeout / connection refused，但 `curl https://api.github.com`、`https://codeload.github.com` 正常。

**根因**：本地网络对 `github.com:443` 间歇性丢/挡，TCP 握手被 reset，不是 DNS、不是 PAT、也不是仓库权限问题。

**解决**：

1. 先确认是不是真的网络问题：
   ```bash
   curl -s -o /dev/null -m 8 -w "code=%{http_code} time=%{time_total}\n" https://github.com/
   ```
   `code=000` = 连不上；`code=200` = 通。
2. 如果是 000，连续探测 5 次（间隔几秒），通常几十秒到一两分钟会自行恢复：
   ```bash
   for i in 1 2 3 4 5; do
     curl -s -o /dev/null -m 8 -w "attempt $i code=%{http_code}\n" https://github.com/
     sleep 4
   done
   ```
3. 一旦看到 `code=200`，立刻重跑 `git push`，一般一次就过。

不要因为这个错把 `origin` 改成 SSH（除非账号已配 SSH key，本仓库当前未配 → 见 §8.2）。

### 8.2 SSH fallback 失败：`git@github.com: Permission denied (publickey)`

**症状**：把 remote 改成 `git@github.com:...` 后推送报 publickey denied。

**根因**：本机没有给该 GitHub 账号配置 SSH key。

**解决**：

- **回退到 HTTPS + PAT**，不要尝试现场配 SSH key（那是另一条独立的事，应单独做）：
  ```bash
  git remote set-url origin https://github.com/niuteng5618/niuteng5618.github.io.git
  ```
- 仍然按 §7 用 PAT 推送。

### 8.3 `_pre_docs/` 一直出现在 `git status` 的 untracked

不是 bug，是预期行为。`_pre_docs/` 历史上从未被 commit，也不应该被 commit。`git status` 显示 untracked 完全正常 — `git add` 时只点名 `_posts/2026-MM-DD-*.md` 即可，不要用 `git add .`。

### 8.4 PAT 不能写入仓库

如果不小心把 PAT 写进了任何文件（`.git/config` 的 remote URL、commit message、文档），即使后续删除，GitHub 也可能因检测到 secret 而**自动吊销该 token**。

预防：

- 推送时 PAT 只出现在 shell 命令行参数里。
- 命令跑完，必要时 `history -d` 删掉对应行（或不在乎本地 shell 历史就忽略，关键是别让它进 git）。

如果已经误提交：

1. 立刻在 GitHub 上 revoke 这个 PAT，重新生成。
2. 更新 memory `blog-identity.md`。
3. 用新 PAT 推送修正 commit。

### 8.5 GitHub Pages 没出现新文章

可能原因：

- 推送时 commit 没真正上去 → 看 `git push` 输出有没有 `<old>..<new>  main -> main`。
- front matter 缺字段 → 文章被 Jekyll 跳过；本地用 `bundle exec jekyll serve` 跑一次能定位。
- `categories` 列表项与 `primary_category` / `secondary_category` / `series` 三项不一致 → 分类页/目录页错位，文章本身仍会出现但目录里找不到。

------

## 9. 完整 checklist（提交前过一遍）

- [ ] `_pre_docs/` 草稿没有被删除或重命名
- [ ] 编号是 `ls _posts/ | grep -oE '\b[0-9]{3}\b' | sort -n | tail -1` + 1 起步，且未与现有文件冲突
- [ ] 文件名 `YYYY-MM-DD-NNN-slug.md`，日期等于今天
- [ ] Front matter 必填字段齐全（§4.1）
- [ ] `categories:` 三项 == `primary_category` / `secondary_category` / `series`
- [ ] `post_order` == 文件名里的 NNN
- [ ] `display_filename` == `_pre_docs/` 下源文件名（包含中文/空格）
- [ ] `tags` 2–5 个，技术性 tag，优先复用
- [ ] `grep -RInE "<font|</font>|style=|<span|</span>|<u>|</u>" _posts` 无输出
- [ ] 无平台宣传内容（语雀 / CSDN / 平台迁移说明）
- [ ] commit 信息描述清晰，符合历史 commit 风格
- [ ] 推送命令里 PAT 没有写进任何会被 commit 的文件
- [ ] `git push` 输出中包含 `main -> main` 行

------

**最后更新**：2026-06-22  
**维护者**：niuteng5618  
**配套**：`BLOG_DOCUMENTATION.md`（文章格式规则）、`~/.claude/projects/-home-white-Desktop-2-github-github-io/memory/`（跨会话 memory）
