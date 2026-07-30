#!/usr/bin/env python3

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "skills"
    / "chat-distill"
    / "scripts"
    / "knowledge_note.py"
)


def load_script_module():
    spec = importlib.util.spec_from_file_location("knowledge_note_test_module", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load script module: {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class KnowledgeNoteTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.vault = Path(self.temporary.name) / "Vault"
        self.folder = self.vault / "AI Knowledge"
        (self.vault / ".obsidian").mkdir(parents=True)
        self.folder.mkdir()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def run_cli(
        self, *arguments: str, check: bool = True
    ) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), *arguments],
            capture_output=True,
            text=True,
            check=False,
        )
        if check and result.returncode != 0:
            self.fail(
                f"command failed ({result.returncode}): {result.stderr or result.stdout}"
            )
        return result

    def common(self) -> list[str]:
        return ["--vault", str(self.vault), "--folder", "AI Knowledge"]

    def content_file(self, name: str, content: str) -> Path:
        path = Path(self.temporary.name) / name
        path.write_text(content, encoding="utf-8")
        return path

    def write_note(self, title: str, content: str) -> Path:
        source = self.content_file(f"{title}.input.md", content)
        result = self.run_cli(
            "write",
            *self.common(),
            "--title",
            title,
            "--content",
            str(source),
            "--date",
            "2026-07-29",
        )
        return Path(result.stdout.strip())

    def test_write_is_atomic_and_leaves_no_temporary_file(self) -> None:
        target = self.write_note(
            "方法-工具-原子写入",
            "# 原子写入\n\n只有完整内容才能成为正式笔记。\n",
        )
        saved = target.read_text(encoding="utf-8")
        self.assertIn("只有完整内容才能成为正式笔记", saved)
        self.assertIn("created: 2026-07-29", saved)
        self.assertIn("topic: 原子写入", saved)
        self.assertIn("domain: 工具", saved)
        self.assertIn("type: 方法", saved)
        self.assertIn("# 原子写入", saved)
        self.assertNotIn("# 方法-工具-原子写入", saved)
        self.assertEqual(list(self.folder.glob(".*.tmp")), [])
        self.assertTrue((self.folder / ".knowledge-note-locks").is_dir())

        target.chmod(0o640)
        replacement = self.content_file(
            "atomic-replacement.md", "# 原子写入\n\n更新后的完整内容。\n"
        )
        self.run_cli(
            "write",
            *self.common(),
            "--title",
            "方法-工具-原子写入",
            "--target",
            str(target),
            "--content",
            str(replacement),
        )
        self.assertEqual(target.stat().st_mode & 0o777, 0o640)

    def test_new_atomic_file_stays_private_under_restrictive_umask(self) -> None:
        module = load_script_module()
        target = self.folder / "方法-工具-私有写入.md"
        previous_umask = os.umask(0o077)
        try:
            module.atomic_write_text(target, "private knowledge\n")
        finally:
            os.umask(previous_umask)

        self.assertEqual(target.stat().st_mode & 0o777, 0o600)

    def test_configure_writes_private_config_and_doctor_uses_it(self) -> None:
        config = Path(self.temporary.name) / "config" / "config.json"
        configured = self.run_cli(
            "configure",
            "--vault",
            str(self.vault),
            "--folder",
            "AI Knowledge",
            "--config",
            str(config),
        )
        report = json.loads(configured.stdout)
        self.assertTrue(report["configured"])
        self.assertEqual(config.stat().st_mode & 0o777, 0o600)

        doctor = self.run_cli("doctor", "--config", str(config))
        diagnosis = json.loads(doctor.stdout)
        self.assertTrue(diagnosis["ok"])
        self.assertEqual(diagnosis["vault"], str(self.vault.resolve()))
        self.assertEqual(diagnosis["folder"], "AI Knowledge")
        self.assertEqual(diagnosis["notes_read"], 0)

    def test_write_derives_yaml_for_all_naming_patterns(self) -> None:
        module = load_script_module()
        cases = [
            (
                "用户习惯-写作-表达与篇幅",
                {"type": "用户习惯", "domain": "写作", "topic": "表达与篇幅"},
            ),
            (
                "方法-工具-原子写入",
                {"type": "方法", "domain": "工具", "topic": "原子写入"},
            ),
            (
                "模板-邮件-课程申请",
                {"type": "模板", "domain": None, "topic": "邮件-课程申请"},
            ),
            (
                "资料-合同-风险条款",
                {"type": "资料", "domain": None, "topic": "合同-风险条款"},
            ),
            (
                "索引-工具",
                {"type": "索引", "domain": "工具", "topic": "工具"},
            ),
            (
                "工具-Obsidian-知识记录规则",
                {"type": None, "domain": "工具", "topic": "Obsidian-知识记录规则"},
            ),
        ]
        for title, expected in cases:
            with self.subTest(title=title):
                note = self.write_note(title, f"# {expected['topic']}\n\n测试正文。\n")
                metadata = module.parse_frontmatter(note.read_text(encoding="utf-8"))
                for field, value in expected.items():
                    if value is None:
                        self.assertNotIn(field, metadata)
                    else:
                        self.assertEqual(metadata.get(field), value)

    def test_script_generated_note_passes_classification_audit(self) -> None:
        note = self.write_note(
            "方法-工具-分类联动",
            "# 分类联动\n\n脚本生成的元数据应当通过自身的分类审计。\n",
        )
        report = json.loads(self.run_cli("audit", *self.common()).stdout)
        classification_issues = [
            issue
            for issue in report["issues"]
            if issue["path"].endswith(note.name)
            and str(issue["code"]).startswith("classification_")
        ]
        self.assertEqual(classification_issues, [])

    def test_update_requires_title_to_match_existing_filename(self) -> None:
        target = self.write_note("方法-工具-更新保护", "# 更新保护\n\n原内容。\n")
        replacement = self.content_file(
            "update-mismatch.md", "# 另一个主题\n\n不应覆盖。\n"
        )
        before = target.read_text(encoding="utf-8")
        result = self.run_cli(
            "write",
            *self.common(),
            "--title",
            "方法-工具-错误名称",
            "--target",
            str(target),
            "--content",
            str(replacement),
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("must match the existing target filename", result.stderr)
        self.assertEqual(target.read_text(encoding="utf-8"), before)

    def test_candidates_prioritize_the_matching_topic(self) -> None:
        expected = self.write_note(
            "方法-工具-浏览器超时回退",
            "# 浏览器超时回退\n\n浏览器自动化超时后使用有限重试和手动回退。\n",
        )
        self.write_note(
            "方法-写作-批注驱动修订",
            "# 批注驱动修订\n\n使用批注完成异步审阅和修改确认。\n",
        )
        result = self.run_cli(
            "candidates",
            *self.common(),
            "--query",
            "浏览器超时",
            "--limit",
            "2",
        )
        candidates = json.loads(result.stdout)
        self.assertGreaterEqual(len(candidates), 1)
        self.assertEqual(Path(candidates[0]["path"]), expected)
        self.assertEqual(candidates[0]["topic"], "浏览器超时回退")

    def test_refuses_unconfirmed_overwrite_and_preserves_original(self) -> None:
        target = self.write_note("方法-工具-覆盖保护", "# 覆盖保护\n\n原始内容。\n")
        before = target.read_text(encoding="utf-8")
        replacement = self.content_file("replacement.md", "# 覆盖保护\n\n替换内容。\n")
        result = self.run_cli(
            "write",
            *self.common(),
            "--title",
            "方法-工具-覆盖保护",
            "--content",
            str(replacement),
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Refusing to overwrite", result.stderr)
        self.assertEqual(target.read_text(encoding="utf-8"), before)

    def test_concurrent_updates_never_interleave_content(self) -> None:
        target = self.write_note("方法-工具-并发写入", "# 并发写入\n\n初始内容。\n")
        marker_a = "alpha_atomic_payload_"
        marker_b = "beta_atomic_payload_"
        source_a = self.content_file(
            "concurrent-a.md", "# 并发写入\n\n" + marker_a * 20000 + "\n"
        )
        source_b = self.content_file(
            "concurrent-b.md", "# 并发写入\n\n" + marker_b * 20000 + "\n"
        )

        base = [
            sys.executable,
            str(SCRIPT),
            "write",
            *self.common(),
            "--title",
            "方法-工具-并发写入",
            "--target",
            str(target),
        ]
        process_a = subprocess.Popen(
            [*base, "--content", str(source_a)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        process_b = subprocess.Popen(
            [*base, "--content", str(source_b)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        stdout_a, stderr_a = process_a.communicate(timeout=20)
        stdout_b, stderr_b = process_b.communicate(timeout=20)
        self.assertEqual(process_a.returncode, 0, stderr_a or stdout_a)
        self.assertEqual(process_b.returncode, 0, stderr_b or stdout_b)

        final = target.read_text(encoding="utf-8")
        has_a = marker_a in final
        has_b = marker_b in final
        self.assertNotEqual(has_a, has_b)
        self.assertEqual(list(self.folder.glob(".*.tmp")), [])

    def test_audit_reports_actionable_issues_without_changing_notes(self) -> None:
        duplicate_body = (
            "这是一段用于检查重复知识的完整正文。"
            "它包含足够多的内容，能够稳定触发完全重复检测，"
            "但审计只能报告候选项，不能自动合并笔记。"
        )
        managed_template = """---
created: 2026-07-20
updated: 2026-07-21
source: chat-distill
topic: {topic}
aliases: []
tags: [chat-distill, ai-knowledge]
domain: 工具
type: 方法
status: active
---

# {heading}

{body}

[[不存在的页面]]
"""
        (self.folder / "方法-工具-重复检查一.md").write_text(
            managed_template.format(
                topic="重复检查一", heading="重复检查一", body=duplicate_body
            ),
            encoding="utf-8",
        )
        (self.folder / "方法-工具-重复检查二.md").write_text(
            managed_template.format(
                topic="重复检查二", heading="重复检查二", body=duplicate_body
            ),
            encoding="utf-8",
        )
        (self.folder / "方法-工具-主题错位.md").write_text(
            managed_template.format(
                topic="错误主题", heading="主题错位", body="用于检查 topic 对齐。"
            ),
            encoding="utf-8",
        )
        (self.folder / "生活-杂项-未管理.md").write_text(
            "# 未管理笔记\n\n## 空章节\n", encoding="utf-8"
        )
        (self.folder / "用户习惯-写作-篇幅.md").write_text(
            """---
created: 2026-07-20
updated: 2026-07-21
topic: 篇幅
aliases: []
tags: [chat-distill, ai-knowledge]
domain: 写作
type: 用户习惯
status: uncertain
---

# 篇幅习惯

默认保持紧凑，但仍需用户确认。
""",
            encoding="utf-8",
        )
        (self.folder / "工具-安全-敏感字段.md").write_text(
            """---
created: 2026-07-20
updated: 2026-07-21
topic: 敏感字段
aliases: []
tags: [chat-distill, ai-knowledge]
domain: 工具
type: 风险清单
status: active
---

# 敏感字段

api_key: test-secret-value-that-must-never-be-reported
""",
            encoding="utf-8",
        )
        outside = Path(self.temporary.name) / "outside-private.md"
        outside.write_text("api_key: should-not-be-read-through-symlink\n", encoding="utf-8")
        (self.folder / "方法-工具-外部链接.md").symlink_to(outside)
        before = {
            path: path.read_text(encoding="utf-8")
            for path in self.folder.glob("*.md")
            if not path.is_symlink()
        }

        result = self.run_cli("audit", *self.common())
        report = json.loads(result.stdout)
        codes = {issue["code"] for issue in report["issues"]}
        self.assertIn("exact_duplicate", codes)
        self.assertIn("dead_wikilink", codes)
        self.assertIn("missing_frontmatter", codes)
        self.assertIn("empty_section", codes)
        self.assertIn("habit_status_review", codes)
        self.assertIn("sensitive_key", codes)
        self.assertIn("symlink_note", codes)
        self.assertIn("classification_topic", codes)
        self.assertGreaterEqual(report["summary"]["notes_scanned"], 5)
        self.assertNotIn("test-secret-value", result.stdout)
        self.assertNotIn("should-not-be-read", result.stdout)

        after = {
            path: path.read_text(encoding="utf-8")
            for path in self.folder.glob("*.md")
            if not path.is_symlink()
        }
        self.assertEqual(before, after)

    def test_rejects_folder_escape(self) -> None:
        source = self.content_file("escape.md", "# Escape\n")
        result = self.run_cli(
            "write",
            "--vault",
            str(self.vault),
            "--folder",
            "../outside",
            "--title",
            "方法-工具-路径保护",
            "--content",
            str(source),
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--folder must be a relative folder", result.stderr)

    def test_rename_preserves_old_title_as_alias(self) -> None:
        original = self.write_note("方法-工具-旧名称", "# 旧名称\n\n可复用内容。\n")
        result = self.run_cli(
            "rename",
            *self.common(),
            "--target",
            str(original),
            "--title",
            "方法-工具-新名称",
            "--date",
            "2026-07-29",
        )
        payload = json.loads(result.stdout)
        renamed = Path(payload["renamed"])
        self.assertFalse(original.exists())
        self.assertTrue(renamed.exists())
        renamed_content = renamed.read_text(encoding="utf-8")
        self.assertIn("方法-工具-旧名称", renamed_content)
        self.assertIn("topic: 新名称", renamed_content)
        self.assertIn("# 新名称", renamed_content)
        self.assertNotIn("# 方法-工具-新名称", renamed_content)

    def test_merge_atomically_updates_target_and_removes_source(self) -> None:
        target = self.write_note("方法-工具-合并目标", "# 合并目标\n\n目标内容。\n")
        source = self.write_note("方法-工具-合并来源", "# 合并来源\n\n来源内容。\n")
        consolidated = self.content_file(
            "consolidated.md", "# 合并目标\n\n目标内容与来源内容均已保留。\n"
        )
        result = self.run_cli(
            "merge",
            *self.common(),
            "--target",
            str(target),
            "--sources",
            str(source),
            "--content",
            str(consolidated),
            "--date",
            "2026-07-29",
        )
        payload = json.loads(result.stdout)
        self.assertEqual(Path(payload["merged"]), target)
        self.assertFalse(source.exists())
        merged_content = target.read_text(encoding="utf-8")
        self.assertIn("目标内容与来源内容均已保留", merged_content)
        self.assertIn("topic: 合并目标", merged_content)
        self.assertIn("# 合并目标", merged_content)
        self.assertNotIn("# 方法-工具-合并目标", merged_content)

    def test_split_writes_all_outputs_before_removing_source(self) -> None:
        broad = self.write_note("方法-工具-宽泛主题", "# 宽泛主题\n\n主题一与主题二。\n")
        first = self.content_file("split-one.md", "# 主题一\n\n第一部分。\n")
        second = self.content_file("split-two.md", "# 主题二\n\n第二部分。\n")
        result = self.run_cli(
            "split",
            *self.common(),
            "--target",
            str(broad),
            "--outputs",
            f"方法-工具-主题一={first}",
            f"方法-工具-主题二={second}",
            "--date",
            "2026-07-29",
        )
        payload = json.loads(result.stdout)
        outputs = [Path(path) for path in payload["written"]]
        self.assertFalse(broad.exists())
        self.assertEqual(len(outputs), 2)
        self.assertTrue(all(path.exists() for path in outputs))
        self.assertIn("topic: 主题一", outputs[0].read_text(encoding="utf-8"))
        self.assertIn("# 主题一", outputs[0].read_text(encoding="utf-8"))

    def test_move_section_updates_both_notes_without_partial_text(self) -> None:
        source = self.write_note(
            "方法-工具-章节来源",
            "# 章节来源\n\n## 保留章节\n\n保留内容。\n\n## 移动章节\n\n移动内容。\n",
        )
        target = self.write_note("方法-工具-章节目标", "# 章节目标\n\n原目标内容。\n")
        target_after = self.content_file(
            "target-after.md", "# 章节目标\n\n原目标内容。\n\n## 移动章节\n\n移动内容。\n"
        )
        self.run_cli(
            "move-section",
            *self.common(),
            "--source",
            str(source),
            "--target",
            str(target),
            "--heading",
            "移动章节",
            "--content",
            str(target_after),
            "--date",
            "2026-07-29",
        )
        self.assertNotIn("移动内容", source.read_text(encoding="utf-8"))
        target_content = target.read_text(encoding="utf-8")
        self.assertIn("移动内容", target_content)
        self.assertIn("topic: 章节目标", target_content)
        self.assertIn("# 章节目标", target_content)
        self.assertEqual(list(self.folder.glob(".*.tmp")), [])

    def test_move_section_accepts_prepared_source_and_target_rewrites(self) -> None:
        source = self.write_note("方法-工具-重写来源", "# 重写来源\n\n旧来源。\n")
        target = self.write_note("方法-工具-重写目标", "# 重写目标\n\n旧目标。\n")
        source_after = self.content_file(
            "rewrite-source-after.md", "# 重写来源\n\n保留后的来源。\n"
        )
        target_after = self.content_file(
            "rewrite-target-after.md", "# 重写目标\n\n包含迁移后的内容。\n"
        )
        self.run_cli(
            "move-section",
            *self.common(),
            "--source",
            str(source),
            "--target",
            str(target),
            "--source-content",
            str(source_after),
            "--target-content",
            str(target_after),
            "--date",
            "2026-07-29",
        )
        source_content = source.read_text(encoding="utf-8")
        target_content = target.read_text(encoding="utf-8")
        self.assertIn("保留后的来源", source_content)
        self.assertIn("包含迁移后的内容", target_content)
        self.assertIn("topic: 重写来源", source_content)
        self.assertIn("topic: 重写目标", target_content)

    def test_move_section_keeps_source_when_target_write_fails(self) -> None:
        module = load_script_module()
        source = self.write_note(
            "方法-工具-失败来源",
            "# 失败来源\n\n## 保留章节\n\n保留内容。\n\n## 移动章节\n\n移动内容。\n",
        )
        target = self.write_note("方法-工具-失败目标", "# 失败目标\n\n原目标内容。\n")
        target_after = self.content_file(
            "failed-target-after.md",
            "# 失败目标\n\n原目标内容。\n\n## 移动章节\n\n移动内容。\n",
        )
        source_before = source.read_text(encoding="utf-8")
        target_before = target.read_text(encoding="utf-8")
        original_atomic_write = module.atomic_write_text
        attempted_paths: list[Path] = []

        def fail_target_write(path: Path, content: str) -> None:
            attempted_paths.append(path.resolve())
            if path.resolve() == target.resolve():
                raise OSError("injected target write failure")
            original_atomic_write(path, content)

        module.atomic_write_text = fail_target_write
        args = argparse.Namespace(
            vault=str(self.vault),
            folder="AI Knowledge",
            date="2026-07-29",
            source=str(source),
            target=str(target),
            heading="移动章节",
            content=str(target_after),
            source_content=None,
            target_content=None,
            source_title=None,
            target_title=None,
        )
        with self.assertRaisesRegex(OSError, "injected target write failure"):
            module.run_move_section(args)

        self.assertEqual(attempted_paths, [target.resolve()])
        self.assertEqual(source.read_text(encoding="utf-8"), source_before)
        self.assertEqual(target.read_text(encoding="utf-8"), target_before)


if __name__ == "__main__":
    unittest.main()
