# Skill 使用说明

项目级 Skill 位于：`skills/finance-youtube-benchmark/`。它没有全局安装，也不接入 P02。

## 常用命令

以下命令使用 Python 标准库；在本机可把 `<python>` 替换为 Codex 随附 Python 的完整路径。

```powershell
<python> skills/finance-youtube-benchmark/scripts/benchmark_mvp.py check-structure --skill-root skills/finance-youtube-benchmark
<python> skills/finance-youtube-benchmark/scripts/benchmark_mvp.py adapter-status
<python> skills/finance-youtube-benchmark/scripts/benchmark_mvp.py ingest-text --input <用户提供文本> --output <特征JSON>
<python> skills/finance-youtube-benchmark/scripts/benchmark_mvp.py public-feed --channel-id <频道ID> --cache-dir <缓存目录> --ledger <调用账本>
<python> skills/finance-youtube-benchmark/scripts/benchmark_mvp.py select-feed --input <feed.json> --output <selection.json>
<python> skills/finance-youtube-benchmark/scripts/benchmark_mvp.py validate-list --schema <schema.json> --input <records.json>
<python> skills/finance-youtube-benchmark/scripts/benchmark_mvp.py originality --comparison-type source --candidate <原创稿> --sources <临时来源文本>
<python> skills/finance-youtube-benchmark/scripts/benchmark_mvp.py credential-scan --path <运行目录>
```

## 安全用法

1. 先读 `SKILL.md`，再按需读取 `references/governance.md`、`adapters.md`、`workflow.md`、`analysis.md`。
2. 优先使用 `local_text`；完整字幕只能作为临时输入，输出只保留哈希和特征。
3. 没有审批与密钥时，TranscriptAPI 必须保持 `DISABLED`。
4. 频道视频只能提供风格观察；FactPack 必须来自独立权威来源。
5. 生成只使用去身份化结构参数，不使用频道名、口头禅或个人经历。
6. Skill 不登录、不发布、不互动，也不产生投资建议。
