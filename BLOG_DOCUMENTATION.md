# 博客文档规范

本文档定义博客文章的创建、修改、删除规范。**在进行任何文档操作前必须阅读本规范。**

## 文件命名规范

### 文件名格式
```
2026-05-30-NNN-slug.md
```

- **日期部分** (`2026-05-30`): 文档最后修改日期
  - 新建文档: 使用创建日期
  - 修改文档: 更新为修改日期
  - 格式: `YYYY-MM-DD`
  
- **编号部分** (`NNN`): 三位数字编号，对应 `post_order` 字段
  - 从 `001` 开始递增
  - 新增文档使用下一个可用编号
  - 删除文档后编号不回收（保持历史连续性）
  
- **slug 部分**: URL 友好的短标识
  - 小写字母、数字、连字符
  - 简洁描述文章主题
  - 示例: `llama`, `attention`, `rag-system`

### 示例
```
2026-05-30-001-attention.md
2026-05-30-004-llama.md
2026-06-15-073-new-topic.md  (新增文档，使用新日期)
```

## Front Matter 必填字段

每篇文章开头必须包含以下 YAML front matter:

```yaml
---
layout: post
title: "文章标题"
display_title: "显示标题"
display_filename: "原始文件名.md"
date: 2026-05-30
primary_category: "一级分类"
secondary_category: "二级分类"
series: "系列名称"
primary_category_order: 1
secondary_category_order: 2
series_order: 1
post_order: 1
categories:
  - 一级分类
  - 二级分类
  - 系列名称
tags:
  - 标签1
  - 标签2
toc: true
word_count: 1234
reading_time: 4
comments: false
author: niuteng5618
---
```

### 字段说明

| 字段 | 必填 | 说明 |
|------|------|------|
| `layout` | ✅ | 固定为 `post` |
| `title` | ✅ | 文章标题（用于 SEO） |
| `display_title` | ✅ | 页面显示标题 |
| `display_filename` | ✅ | 原始文件名（记录来源） |
| `date` | ✅ | 最后修改日期 `YYYY-MM-DD` |
| `primary_category` | ✅ | 一级分类（如"人工智能技术"） |
| `secondary_category` | ✅ | 二级分类（如"大模型基础"） |
| `series` | ✅ | 系列名称（如"Attention"） |
| `primary_category_order` | ✅ | 一级分类排序号 |
| `secondary_category_order` | ✅ | 二级分类排序号 |
| `series_order` | ✅ | 系列内排序号 |
| `post_order` | ✅ | 全局文章编号（与文件名编号一致） |
| `categories` | ✅ | 分类列表（包含三级分类） |
| `tags` | ✅ | 标签列表（2-5个） |
| `toc` | ✅ | 是否显示目录（`true`/`false`） |
| `word_count` | ✅ | 正文字数（中文按字符、英文按单词计，剔除代码），由 `_scripts/update_reading_stats.py` 生成 |
| `reading_time` | ✅ | 预计阅读分钟数（`ceil(word_count / 400)`），由同一脚本生成 |
| `comments` | ✅ | 是否开启评论（当前统一 `false`） |
| `author` | ✅ | 作者名（固定 `niuteng5618`） |

## 分类与标签规范

### 分类层级
```
一级分类 (primary_category)
  └─ 二级分类 (secondary_category)
      └─ 系列 (series)
```

### 现有分类体系

#### 人工智能技术 (primary_category_order: 1)
- **大模型基础** (secondary_category_order: 2)
  - Attention, KV Cache, 量化, RAG系统, Embedding模型, MoE, 并行策略...
- **深度学习基础** (secondary_category_order: 3)
  - 激活函数, 正则化, RNN/LSTM, 知识蒸馏...
- **强化学习** (secondary_category_order: 7)
  - PPO, DPO, GRPO, Q-learning...
- **智能体应用开发** (secondary_category_order: 8)
  - Agent, MCP, Skill, 智能体框架, 上下文压缩...

#### 计算机基础 (primary_category_order: 2)
- **Linux基础** (文件管理, 磁盘管理)
- **数据库** (MySQL)
- **计算机网络** (面试基础)

### 标签规范
- 每篇文章 2-5 个标签
- 标签应具体、可检索
- 优先使用已有标签（查看 `/tags` 页面）
- 新标签应有明确技术含义

## 图片资源规范

### 存放位置
```
/images/posts/NNN-slug/
```

示例:
```
/images/posts/004-llama/architecture.png
/images/posts/025-embeddingrerank/comparison.jpg
```

### 引用格式
```markdown
![图片描述](/images/posts/004-llama/architecture.png)
```

### 命名规范
- 小写字母、数字、连字符
- 描述性命名（如 `architecture.png`, `workflow-diagram.jpg`）
- 避免中文文件名

## 操作流程

### 新增文章

1. **确定编号**: 查看 `_posts/` 目录，使用下一个可用编号
   ```bash
   ls _posts/ | tail -1  # 查看最后一篇
   # 假设最后是 072，新文章用 073
   ```

2. **创建文件**: `2026-MM-DD-073-new-topic.md`（使用当前日期）

3. **填写 front matter**: 复制现有文章的 front matter，修改所有字段

4. **分配分类排序号**:
   - 查看同分类文章，确定 `primary_category_order`, `secondary_category_order`, `series_order`
   - 新系列从 `series_order: 1` 开始

5. **添加图片**: 创建 `/images/posts/073-new-topic/` 目录

6. **验证**: 本地运行 `bundle exec jekyll serve` 检查显示

### 修改文章

1. **更新日期**: 修改文件名和 front matter 的 `date` 字段为当前日期
   ```bash
   # 重命名文件
   git mv _posts/2026-05-30-004-llama.md _posts/2026-06-15-004-llama.md
   ```

2. **更新内容**: 修改正文

3. **保持编号**: `post_order` 和文件名编号不变

4. **提交**: 
   ```bash
   git add _posts/2026-06-15-004-llama.md
   git commit -m "Update: LLaMA基础 - 新增推理优化章节"
   ```

### 删除文章

1. **删除文件**: 
   ```bash
   git rm _posts/2026-05-30-050-old-topic.md
   ```

2. **删除图片**: 
   ```bash
   git rm -r images/posts/050-old-topic/
   ```

3. **不回收编号**: 编号 050 不再使用，下一篇新文章用 073（假设当前最大 072）

4. **提交**: 
   ```bash
   git commit -m "Remove: 旧主题文章（已过时）"
   ```

## 日期语义

**当前所有文章日期统一为 `2026-05-30`**，表示博客初始化日期。

**未来修改文章时**:
- 更新文件名日期: `2026-05-30-004-llama.md` → `2026-06-15-004-llama.md`
- 更新 front matter: `date: 2026-05-30` → `date: 2026-06-15`
- 日期含义: **文档最后修改日期**（非学习日期、非发布日期）

## URL 规则

博客使用 `permalink: /:title/`，URL 由 `title` 字段生成，**与文件名日期无关**。

示例:
- 文件: `2026-05-30-004-llama.md`
- Title: `"LLaMA基础"`
- URL: `https://niuteng5618.github.io/llama/` (自动转换为 slug)

**重要**: 修改 `title` 会改变 URL，导致旧链接失效。如需修改标题，只改 `display_title`。

## 内容规范

### 文本清理规范

从外部文档或富文本编辑器导入 Markdown 时，必须先清理会破坏前端显示的内联 HTML 样式。尤其要处理以下内容：

- 删除 `<font ...>` 与 `</font>`，只保留内部文本。
- 删除 `<span ...>` 与 `</span>`，只保留内部文本。
- 删除 `<u>` 与 `</u>`，只保留内部文本。
- 删除 `style="..."` 这类内联样式，避免浅色/深色模式下出现白字黄底、灰字灰底等视觉 bug。
- 不要把清理动作变成改写原文；只移除展示层样式标签，不新增额外语义、不重写技术内容。
- `<br/>`、`<sub>` 等确实用于排版或公式说明的标签可以保留，但应尽量用标准 Markdown 替代。

清理后必须执行检查：

```bash
grep -RIn "<font\|</font>\|style=\|<span\|</span>\|<u>\|</u>" _posts
```

如果仍有结果，必须逐项确认并清理，直到没有会影响前端显示的残留样式标签。

### 禁止内容
- ❌ 提及其他平台（语雀、GitHub、CSDN 等）作为平台宣传
- ❌ 平台迁移说明
- ✅ 技术资源链接（GitHub 仓库、文档）允许

### 推荐内容
- ✅ 技术原理讲解
- ✅ 代码示例与注释
- ✅ 实践经验总结
- ✅ 问题解决方案
- ✅ 学习资源链接（论文、文档、教程）

### 写作风格
- 初学者友好：清晰的概念解释
- 实践导向：可复现的代码和步骤
- 结构化：使用标题、列表、代码块
- 视觉化：适当使用图表、流程图

## 工具脚本

### 批量更新日期
```bash
# 更新所有文章日期为今天
for f in _posts/*.md; do
  new_date=$(date +%Y-%m-%d)
  new_name=$(echo "$f" | sed "s/[0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\}/$new_date/")
  git mv "$f" "$new_name"
  sed -i "s/^date: [0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\}/date: $new_date/" "$new_name"
done
```

### 查找下一个可用编号
```bash
ls _posts/ | grep -oE '[0-9]{3}' | sort -n | tail -1 | awk '{print $1+1}'
```

### 验证 front matter 完整性
```bash
# 检查缺失必填字段的文章
for f in _posts/*.md; do
  if ! grep -q "^post_order:" "$f"; then
    echo "Missing post_order: $f"
  fi
done
```

## 常见问题

### Q: 为什么所有文章日期都是 2026-05-30?
A: 这是博客初始化日期。未来修改文章时，更新为实际修改日期。

### Q: 删除文章后编号能重用吗?
A: 不能。编号一旦分配就永久占用，保持历史连续性。

### Q: 如何调整文章在目录中的顺序?
A: 修改 `primary_category_order`, `secondary_category_order`, `series_order` 字段。

### Q: 修改 title 会影响 URL 吗?
A: 会。只修改显示标题时，改 `display_title` 而非 `title`。

### Q: 图片路径写错了怎么办?
A: 本地运行 `jekyll serve` 会显示 404 错误，检查路径是否匹配 `/images/posts/NNN-slug/`。

## 检查清单

### 新增文章前
- [ ] 确定下一个可用编号
- [ ] 准备好所有图片资源
- [ ] 确定分类和系列归属
- [ ] 准备 2-5 个标签

### 提交前
- [ ] Front matter 所有必填字段已填写
- [ ] 日期格式正确 `YYYY-MM-DD`
- [ ] `post_order` 与文件名编号一致
- [ ] 图片路径正确且文件存在
- [ ] 无平台宣传内容（技术资源链接允许）
- [ ] 本地预览无错误

### 修改文章前
- [ ] 更新文件名日期
- [ ] 更新 front matter `date` 字段
- [ ] 保持 `post_order` 不变
- [ ] 保持 `title` 不变（避免 URL 变化）

---

**最后更新**: 2026-05-30  
**维护者**: niuteng5618
