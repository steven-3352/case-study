"""
PRD-009 §7.1 单元测试 · Phase 4 测试工程师

覆盖用例
========
(a)  角色命名 + 绑定 ─── 纯单元，无 mock
(a2) gate 读磁盘桶 ────── AsyncIO + patch stubs
(a3) 混合合唱处理 ─────── 直接调用 _split_character_names + 过滤逻辑
(b)  计费去重 ───────────── 真实 SQLite，INSERT OR IGNORE 幂等断言

依赖与 Mock 策略
================
(a)  直接导入 drafting._bind_director_cast；构造 Python 字典，
     不需要任何 mock 或磁盘文件。

(a2) 创建真实 ApplicationService（临时目录）；
     - patch service._run_lyrics_transcribe 写伪 .lrc 文件；
     - patch service._run_character_design 写伪 .png 文件；
     - MagicMock supervisor 捕获 director_intake 调用；
     - asyncio.run(_materialize_job(...)) 同步执行异步方法；
     - 断言 job.input_refs 在 materialize 后仍为建 job 时的 audio-only tuple。

(a3) 直接调用 intake._split_character_names 验证返回值
     （该测试按 PRD §7.1 规格编写；若当前实现行为与规格不符则测试失败）；
     另建独立测试验证 _CHORUS_MARKERS 集合减法过滤逻辑（不依赖 _split_character_names）；
     使用 patch mock parse_xlsx_director_sheet，调用
     service._extract_character_names_from_lyrics 验证"合"被剔除出生成名单。

(b)  创建真实 Database（临时 SQLite）；通过 create_project + submit_job 满足 FK；
     两次相同参数调用 service._record_cost；断言 cost_entries 行数 == 1。
"""

from __future__ import annotations

import asyncio
import sys
from decimal import Decimal
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ─────────────────────────────────────────────────────────────────────────────
# sys.path setup
# ─────────────────────────────────────────────────────────────────────────────
_REPO = Path(__file__).resolve().parents[4]
for _p in (_REPO / "src", _REPO):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from mv_platform.application.service import ApplicationService
from mv_platform.config import Settings
from mv_platform.infrastructure.database import Database
from mvstudio.director.drafting import MapDraftError, _bind_director_cast
from mvstudio.director.intake import (
    IntakeContractError,
    _CHORUS_MARKERS,
    _split_character_names,
)


# ─────────────────────────────────────────────────────────────────────────────
# Shared helper
# ─────────────────────────────────────────────────────────────────────────────

def _make_service(tmp_path, supervisor=None):
    settings = Settings()
    database = Database(tmp_path / settings.db_path)
    service = ApplicationService(
        settings,
        database,
        workspace_root=tmp_path,
        supervisor=supervisor,
    )
    service.initialize()
    return service


# ─────────────────────────────────────────────────────────────────────────────
# (a) 角色命名 + 绑定
# ─────────────────────────────────────────────────────────────────────────────

class TestCharacterBinding:
    """
    §7.1 (a) — XLSX binding 落名规则与 _bind_director_cast 命中断言

    _bind_director_cast.aliases() 的逻辑：
        aliases = {item["name"].strip(), Path(item["source_asset"]).stem}
        aliases 再加上各自 re.sub(r"-[0-9a-f]{10}$", "", v) 剥尾结果

    合法命中条件（缺一即崩）：
      1. stem == "<合约角色名>-<10位小写hex>"  →  剥尾后 == 合约名
      2. 哈希段恰好 10 位小写 hex（正则才会匹配）
    """

    @staticmethod
    def _chars(source_asset: str):
        # 关键：当 brief.characters 为空时，_characters() 将 name 设为 Path(source).stem
        # 这里复现该行为：name = stem（而非手动写死 "林渊"），
        # 以确保别名集合仅来自 stem / re.sub 剥尾，不受 name 字段干扰。
        stem = Path(source_asset).stem
        return [{"id": "C01", "name": stem, "source_asset": source_asset, "traits": []}]

    @staticmethod
    def _lines():
        return [{
            "id": "L01",
            "start_seconds": 0.0,
            "end_seconds": 3.0,
            "text": "测试歌词",
            "character_names": ["林渊"],
        }]

    def test_correct_stem_and_10hex_binds_successfully(self):
        """
        文件名 stem = 林渊-abc123def4（10 位小写 hex）
        → re.sub 剥尾 → '林渊'
        → 命中合约角色名 '林渊'
        → character_ids 正确绑定
        """
        lines = self._lines()
        _bind_director_cast(lines, self._chars("inputs/characters/林渊-abc123def4.png"))
        assert lines[0]["character_ids"] == ["C01"]

    def test_wrong_prefix_c01_fails_binding(self):
        """
        文件名 stem = C01-abc123def4
        → re.sub 剥尾 → 'C01'
        → 'C01' ≠ '林渊'  →  MapDraftError 包含 '林渊'
        """
        lines = self._lines()
        with pytest.raises(MapDraftError, match="林渊"):
            _bind_director_cast(lines, self._chars("inputs/characters/C01-abc123def4.png"))

    def test_short_hash_6hex_fails_binding(self):
        """
        文件名 stem = 林渊-abc123（只有 6 位 hex，正则 {10} 不匹配）
        → re.sub 不剥尾 → stem 仍是 '林渊-abc123' ≠ '林渊'
        → MapDraftError 包含 '林渊'
        """
        lines = self._lines()
        with pytest.raises(MapDraftError, match="林渊"):
            _bind_director_cast(lines, self._chars("inputs/characters/林渊-abc123.png"))


# ─────────────────────────────────────────────────────────────────────────────
# (a2) gate 读磁盘桶
# ─────────────────────────────────────────────────────────────────────────────

class TestMaterializeReadsDiskBucket:
    """
    §7.1 (a2) — audio-only job → materialize 只往磁盘桶写文件、不改 input_refs

    验证：
    · supervisor.submit 以 "director_intake" 被调用一次（intake 被触发）
    · job.input_refs 在 materialize 后仍为建 job 时的原始 tuple（不可变验证）
    """

    # 最小合法 1×1 PNG（18 字节 stub）
    _MIN_PNG = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
        b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00"
        b"\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18"
        b"\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
    )

    def test_input_refs_unchanged_after_materialize(self, tmp_path):
        supervisor = MagicMock()
        supervisor.submit.return_value = {"status": "queued"}
        service = _make_service(tmp_path, supervisor=supervisor)

        proj = service.create_project("test-proj", {"title": "测试"})
        project_id = proj.project_id
        # create_project 已创建 inputs/audio/ 等目录
        project_root = tmp_path / "projects" / "test-proj"

        # 放入唯一音频文件（stub 字节，不需要真实 mp3）
        audio_file = project_root / "inputs" / "audio" / "song.mp3"
        audio_file.write_bytes(b"\xff\xfb" + b"\x00" * 128)

        # 建 analyze job，input_refs 仅含 audio（audio-only 场景）
        job_result = service.submit_job(
            project_id,
            "analyze",
            "sha256:" + "a" * 64,
            input_refs=("inputs/audio/song.mp3",),
        )
        job_id = job_result.job_id
        original_refs = tuple(job_result.job_spec.input_refs)

        lyrics_dir = project_root / "inputs" / "lyrics"
        chars_dir = project_root / "inputs" / "characters"

        async def fake_transcribe(_project_id, _job_id):
            """写伪 .lrc 到 inputs/lyrics/"""
            (lyrics_dir / "auto-aabbccdd00.lrc").write_text(
                "[00:01.00]测试歌词\n", encoding="utf-8"
            )

        async def fake_char_design(_project_id, _job_id, char_name):
            """写最小 PNG 到 inputs/characters/"""
            name = char_name if char_name else "auto"
            (chars_dir / f"{name}-aabbccdd01.png").write_bytes(self._MIN_PNG)

        with (
            patch.object(service, "_run_lyrics_transcribe", side_effect=fake_transcribe),
            patch.object(service, "_run_character_design", side_effect=fake_char_design),
        ):
            asyncio.run(service._materialize_job(project_id, job_id, confirm_billing=True))

        # intake 通过 supervisor.submit 触发，且 executor = "director_intake"
        supervisor.submit.assert_called_once()
        call_pos_args = supervisor.submit.call_args[0]
        assert call_pos_args[0] == job_id, "supervisor.submit 的第一个参数应为 job_id"
        assert call_pos_args[1] == "director_intake", "executor 应为 'director_intake'"

        # input_refs 不可变：仍是建 job 时的 ("inputs/audio/song.mp3",)
        job_now = service.repository.get_job(job_id)
        assert tuple(job_now.input_refs) == original_refs, (
            f"input_refs 被修改：期望 {original_refs}，实际 {tuple(job_now.input_refs)}"
        )
        assert original_refs == ("inputs/audio/song.mp3",)


# ─────────────────────────────────────────────────────────────────────────────
# (a3) 混合合唱处理
# ─────────────────────────────────────────────────────────────────────────────

class TestMixedChorusHandling:
    """
    §7.1 (a3) — _split_character_names 拆分行为 + character_design 剔合逻辑

    注意：test_split_mixed_chorus_returns_list 按 PRD §7.1 规格编写，
    若当前实现对 "林渊+合" 抛 IntakeContractError 而非返回列表，该测试将失败，
    表明该行为与 PRD 规格不符。
    """

    def test_pure_chorus_marker_returns_list(self):
        """纯合唱标记 '合' → ['合']"""
        assert _split_character_names("合") == ["合"]

    def test_single_character_returns_list(self):
        """单角色 '林渊' → ['林渊']"""
        assert _split_character_names("林渊") == ["林渊"]

    def test_split_mixed_chorus_returns_list(self):
        """
        PRD §7.1 (a3) 规格：
        '林渊+合' → _split_character_names → ["林渊", "合"]

        若当前实现抛 IntakeContractError("chorus marker cannot be combined...")
        则此测试失败，说明实现与规格不符。
        """
        result = _split_character_names("林渊+合")
        assert result == ["林渊", "合"]

    def test_chorus_markers_constant_excludes_correctly(self):
        """
        _CHORUS_MARKERS 集合减法过滤逻辑：
        模拟 character_design 的核心过滤步骤——
          raw_names（拆分后全集）= {"林渊", "合"}
          to_generate = raw_names - _CHORUS_MARKERS = {"林渊"}
        断言 '合' 不在待生成集合，'林渊' 在。
        此测试不依赖 _split_character_names，验证过滤逻辑本身正确。
        """
        raw_names = {"林渊", "合"}
        to_generate = raw_names - _CHORUS_MARKERS
        assert "林渊" in to_generate
        assert "合" not in to_generate

    def test_extract_character_names_filters_chorus(self, tmp_path):
        """
        service._extract_character_names_from_lyrics 对 XLSX 路径：
        mock parse_xlsx_director_sheet 返回含 '合' / '林渊' / 混合行，
        断言返回名单中 '合' 已被剔除、'林渊' 保留。
        """
        supervisor = MagicMock()
        service = _make_service(tmp_path, supervisor=supervisor)
        proj = service.create_project("chorus-proj", {"title": "合唱测试"})
        project_root = tmp_path / "projects" / "chorus-proj"

        # 放一个 .xlsx 占位文件（让 iterdir 看到文件，后缀匹配）
        lyrics_dir = project_root / "inputs" / "lyrics"
        (lyrics_dir / "contract.xlsx").write_bytes(b"PK\x05\x06" + b"\x00" * 18)

        # 伪 XLSX 解析结果：含纯合唱行、纯角色行、混合行
        mock_sheet = {
            "kind": "timed_spreadsheet",
            "alignment_state": "aligned_director_contract",
            "timed_entries": [
                {
                    "character_names": ["合"],
                    "text": "副歌合唱",
                    "start_seconds": 0.0,
                    "end_seconds": 1.0,
                },
                {
                    "character_names": ["林渊"],
                    "text": "主角独唱",
                    "start_seconds": 1.0,
                    "end_seconds": 2.0,
                },
                {
                    "character_names": ["林渊", "合"],
                    "text": "混合演唱",
                    "start_seconds": 2.0,
                    "end_seconds": 3.0,
                },
            ],
            "plain_lines": [],
            "plain_line_count": 0,
            "director_contract": {"characters_are_binding": True},
        }

        with patch(
            "mvstudio.director.intake.parse_xlsx_director_sheet",
            return_value=mock_sheet,
        ):
            names = service._extract_character_names_from_lyrics(project_root)

        assert "合" not in names, f"'合' 不应出现在待生成名单中，实际得到 {names}"
        assert "林渊" in names, f"'林渊' 应出现在待生成名单中，实际得到 {names}"


# ─────────────────────────────────────────────────────────────────────────────
# (b) 计费去重
# ─────────────────────────────────────────────────────────────────────────────

class TestBillingDeduplication:
    """
    §7.1 (b) — 同一 (project_id, job_id, step_id) 调用 _record_cost 两次
    断言 cost_entries 行数 == 1（INSERT OR IGNORE 幂等）

    _record_cost 使用确定性哈希：
        entry_id = "cost-" + canonical_hash({project_id, job_id, step_id,
                                             resource_type, metadata})
    相同五元组 → 相同 entry_id → 第二次 INSERT OR IGNORE 静默跳过。
    """

    def test_duplicate_record_cost_inserts_only_once(self, tmp_path):
        service = _make_service(tmp_path)
        proj = service.create_project("billing-proj", {"title": "计费测试"})
        project_id = proj.project_id

        # 建 analyze job（FK 约束需要合法 job 行）
        job_result = service.submit_job(
            project_id,
            "analyze",
            "sha256:" + "b" * 64,
            input_refs=("inputs/audio/x.mp3",),
        )
        job_id = job_result.job_id

        step_id = "materialize:lyrics:aabbccdd01"
        common_kwargs = dict(
            project_id=project_id,
            job_id=job_id,
            step_id=step_id,
            resource_type="asr",
            quantity=1,
            unit_price=Decimal("0"),
            amount=Decimal("0"),
            metadata={},
        )

        # 第一次记账
        entry_id_1 = service._record_cost(**common_kwargs)
        # 第二次：完全相同参数 → INSERT OR IGNORE 应静默跳过
        entry_id_2 = service._record_cost(**common_kwargs)

        # 两次调用返回的 entry_id 应相同（确定性哈希）
        assert entry_id_1 == entry_id_2, (
            f"相同参数应产生相同 entry_id，但得到 {entry_id_1!r} vs {entry_id_2!r}"
        )

        # 数据库中该 step_id 只有 1 行
        with service.database.connect() as db:
            row = db.execute(
                "SELECT COUNT(*) FROM cost_entries "
                "WHERE project_id=? AND step_id=?",
                (project_id, step_id),
            ).fetchone()
        assert row[0] == 1, (
            f"期望 cost_entries 行数 == 1（INSERT OR IGNORE 幂等），"
            f"实际 {row[0]} 行"
        )
