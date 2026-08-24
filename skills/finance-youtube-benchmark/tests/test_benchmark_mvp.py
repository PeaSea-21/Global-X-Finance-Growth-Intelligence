import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "benchmark_mvp.py"
SPEC = importlib.util.spec_from_file_location("benchmark_mvp", SCRIPT)
MVP = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MVP)


ATOM_FIXTURE = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns:yt="http://www.youtube.com/xml/schemas/2015" xmlns="http://www.w3.org/2005/Atom">
  <yt:channelId>UC_REAL_TEST</yt:channelId><title>測試頻道</title>
  <entry><yt:videoId>vid001</yt:videoId><title>真實標題格式測試</title><published>2026-08-01T00:00:00+00:00</published><updated>2026-08-01T00:00:00+00:00</updated><media:group xmlns:media="http://search.yahoo.com/mrss/"><media:thumbnail url="https://example.test/thumb.jpg"/><media:community><media:statistics views="1234"/></media:community></media:group></entry>
</feed>"""


class BenchmarkMvpTests(unittest.TestCase):
    def test_local_text_does_not_persist_body(self):
        source = "先看官方數據。問題是市場如何解讀？接下來拆成三點。"
        result = MVP.text_features(source)
        self.assertFalse(result["transcript"]["body_persisted"])
        self.assertNotIn(source, json.dumps(result, ensure_ascii=False))
        self.assertEqual(result["external_calls"], 0)

    def test_parse_public_atom(self):
        result = MVP.parse_youtube_atom(ATOM_FIXTURE)
        self.assertEqual(result["channel_id"], "UC_REAL_TEST")
        self.assertEqual(result["videos"][0]["video_id"], "vid001")
        self.assertEqual(result["videos"][0]["view_count"], 1234)

    def test_transcriptapi_is_disabled(self):
        result = MVP.adapter_status()["transcriptapi"]
        self.assertEqual(result["backend_status"], "DISABLED")
        self.assertEqual(result["actual_run_status"], "NOT_RUN")

    def test_schema_validator_accepts_channel_template(self):
        root = Path(__file__).parents[1]
        result = MVP.validate_document(root / "schemas" / "channel.schema.json", root / "templates" / "channel_record.json")
        self.assertEqual(result["status"], "PASS", result["errors"])

    def test_originality_blocks_long_copy(self):
        source = "官方資料顯示這是一段刻意重複而且長度足夠的測試文字"
        candidate = "開場不同，" + source + "，結尾也不同。"
        result = MVP.compare_text(candidate, source)
        self.assertEqual(result["status"], "BLOCKED")

    def test_originality_passes_distinct_text(self):
        result = MVP.compare_text("先拆解需求，再檢查供應鏈限制。", "利率決策公布後，市場重新估算資金成本。")
        self.assertEqual(result["status"], "PASS")

    def test_peer_mode_allows_shared_fact_but_not_long_draft(self):
        fact = "第二季营收新台币一兆二千七百零三点八亿元年增百分之三十六"
        first = (
            "先核对季度结果，再拆先进制程与高效能运算需求，最后列出下一季观察清单。"
            "开场解决一个决策问题，中段把增长引擎、成本限制和未知条件分开，结尾回到可验证指标。"
            + fact
            + "这只是历史结果，不能直接转换成价格预测；还要等待平台组合、节点占比与实际利润率。"
        )
        second = (
            "从客户地区出发，沿着运算平台走到制造节点，并把海外扩产成本放入反方情境。"
            "开头呈现传导链，中段解释需求如何进入制造结构，最后用情境而非单点结论处理未来。"
            + fact
            + "接下来要用实际毛利与营收区间继续复核，同时保留汇率、需求与执行层面的不确定性。"
        )
        self.assertEqual(MVP.compare_text(first, second, comparison_type="peer")["status"], "PASS")
        self.assertEqual(MVP.compare_text(first * 5, first * 5, comparison_type="peer")["status"], "BLOCKED")

    def test_credential_scan(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "safe.md").write_text("API key is not configured; status is DISABLED.", encoding="utf-8")
            self.assertEqual(MVP.credential_scan(root)["status"], "PASS")
            (root / "bad.txt").write_text('api_key="' + ("x" * 32) + '"', encoding="utf-8")
            self.assertEqual(MVP.credential_scan(root)["status"], "FAIL")

    def test_structure(self):
        root = Path(__file__).parents[1]
        self.assertEqual(MVP.check_structure(root)["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
