# P04 Event Cluster Gold Dataset 方法

## 数据来源

- 数据库：`data/taiwan-demo.db`。
- 时间范围：生成时向前 168 小时；数据库中实际进入财经相关性筛选的 Evidence 为 90 条。
- 只使用已有 `ben_news_items` 与 `ben_x_posts` 原始标题/正文、发布时间、URL、发布方和已提取实体；没有编造新闻文本。
- 固化文件：`research/ben_radar_p04/event_cluster_gold.jsonl`，共 45 对。
- 可复核生成命令：`python scripts/benchmark_ben_clusters.py build-gold --db data/taiwan-demo.db --hours 168`。脚本按明确 Evidence ID 取数；若任何来源行缺失会失败关闭。

## 标签定义

| 标签 | 数量 | 判定标准 |
|---|---:|---|
| `SAME_EVENT` | 6 | 核心主体、动作、对象与事实节点相同；允许不同标题、转载或 X 评论补充。 |
| `RELATED_BUT_DISTINCT` | 19 | 同一公司、产品、产业主题或事件链，但对象、数字、阶段或事实节点不同。 |
| `DIFFERENT_EVENT` | 20 | 只有宽泛关键词、来源、国家、行业或动作相同，核心事实没有交集。 |

## 覆盖的困难样本

- 同一事件的标题改写和转载。
- 同公司、同动作、不同金额或不同投资对象。
- 同主题但不同新闻。
- 计划/洽谈、宣布、获批、完成等不同事件阶段。
- 新闻与 X 的共同事件、独立报道、评论扩写。
- 同一媒体的滚动摘要与重复节目模板。
- 同一产品不同功能或不同里程碑。
- 同一国家、同一动作或同一宽泛主题造成的关键词碰撞。

## 人工标注原则

1. 先读完整原文片段与 URL slug，不以系统分数作为标签依据。
2. “同公司”不是同事件；必须检查 action、target/object、number 与时间。
3. X 评论可以与新闻属于同一事件，但 `publisher_group` 独立性另外计算。
4. 不能确认核心事实相同但明显有关联时标为 `RELATED_BUT_DISTINCT`，不强行二选一。
5. Gold 是当前 45 对真实小样本，不代表全市场分布；指标必须连同样本量一起报告。

## JSONL 结构

每行包含 `id`、`label`、`case_type`、`rationale`、`left` 与 `right`。左右 Evidence 均固化：ID、类型、真实文本、发布时间、URL、发布方、`publisher_group`、repost、实体、动作、主题与外链。
