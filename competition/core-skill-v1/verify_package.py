"""Local package tests with artificial fixtures; never bundled in the Skill ZIP."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from zipfile import ZipFile, ZIP_DEFLATED

BASE = Path(__file__).resolve().parent
SKILL = BASE / "export-document-review"
spec = importlib.util.spec_from_file_location("review_renderer", SKILL / "scripts/render_review.py")
renderer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(renderer)


def fixture():
    return {"schema_version": "1.0", "case_id": "fixture-only", "version": 1, "previous_version": None,
            "context": {k: "人工测试占位，非业务证据" for k in "product market target_date checked_at purpose role scope limitations".split()},
            "files": [{"id": "F001", "name": "fixture.txt", "path": "fixture.txt", "role": "内部草稿", "origin": "人工脚本测试", "parse_status": "parsed", "notes": "无业务用途"}],
            "sources": [], "checks": [{"id": "C001", "title": "<script>alert(1)</script>", "category": "信息一致性", "status": "conflict", "workflow": "open", "priority": "P1", "priority_reason": "测试", "finding": "测试", "impact": "测试", "search_limit": "测试", "next_action": "测试", "recipient": "内部", "requested_material": "测试", "acceptance": "测试", "review_note": "首次测试", "source_ids": [], "evidence": [{"file_id": "F001", "quote": "测试原文", "locator": "测试行号"}]}], "changes": [], "copy_suggestions": []}


passed = []
with tempfile.TemporaryDirectory(prefix="chuhai-skill-check-") as tmp:
    path = Path(tmp) / "fixture-only/v1/result.json"
    path.parent.mkdir(parents=True)
    data = fixture()
    renderer.validate(data, path)
    passed.append("合法记录通过结构校验")
    out = renderer.render(data)
    assert len(out) == 4
    assert "<script>" not in out["预审看板.html"] and "&lt;script&gt;" in out["预审看板.html"]
    assert "存在矛盾 1项" in out["预审看板.html"]
    passed.append("四项交付生成、HTML转义及计数一致")
    for label, mutate in [
        ("拒绝无证据的矛盾状态", lambda d: d['checks'][0].update(evidence=[])),
        ("拒绝关闭未解决事项", lambda d: d['checks'][0].update(workflow='closed')),
        ("拒绝悬空证据引用", lambda d: d['checks'][0]['evidence'][0].update(file_id='F999')),
        ("拒绝重复事项ID", lambda d: d['checks'].append(deepcopy(d['checks'][0]))),
    ]:
        bad = deepcopy(data)
        mutate(bad)
        try:
            renderer.validate(bad, path)
        except ValueError:
            passed.append(label)
        else:
            raise AssertionError(label)
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    command = [sys.executable, str(SKILL / "scripts/render_review.py"), str(path)]
    assert subprocess.run(command, capture_output=True).returncode == 0
    old_text = path.read_bytes()
    assert subprocess.run(command, capture_output=True).returncode != 0
    passed.append("命令行生成成功并拒绝覆盖已有交付物")
    v2path = path.parent.parent / "v2/result.json"
    new = deepcopy(data)
    new.update(version=2, previous_version=1, changes=[{"check_id": "C001", "before": "待处理", "after": "待复核", "basis": "用户口述，无新文件"}])
    new['checks'][0].update(workflow='review', review_note='用户口述，无新证据')
    renderer.validate(new, v2path)
    assert new['checks'][0]['status'] == 'conflict' and path.read_bytes() == old_text
    passed.append("补充口述版本可保持原核查状态且不改旧版")
    bad = deepcopy(new)
    bad['checks'] = []
    bad['changes'] = []
    try:
        renderer.validate(bad, v2path)
    except ValueError:
        passed.append("拒绝删除旧版事项")
    else:
        raise AssertionError("删除未被拒绝")

# Validate metadata with the actual project parser if PyYAML is available.
metadata_result = "未运行平台解析器（当前Python缺PyYAML）；ZIP内容和引用已检查"
try:
    import yaml
except ImportError:
    pass
else:
    package = BASE.parents[1] / "backend/package/yuxi/services/skills/package.py"
    pspec = importlib.util.spec_from_file_location("skill_package", package)
    pm = importlib.util.module_from_spec(pspec)
    pspec.loader.exec_module(pm)
    meta = pm.parse_skill_dir_metadata(SKILL)
    assert meta['slug'] == 'export-document-review' and meta['skill_dependencies'] == ['knowledge-base']
    metadata_result = "ChuHai-agent实际Skill元数据解析器校验通过"

zip_path = BASE / "export-document-review.zip"
with ZipFile(zip_path, "w", ZIP_DEFLATED) as archive:
    for file in sorted(SKILL.rglob("*")):
        if file.is_file() and "__pycache__" not in file.parts:
            archive.write(file, file.relative_to(BASE).as_posix())
with ZipFile(zip_path) as archive:
    assert len(archive.namelist()) == 4
    assert all(name.startswith('export-document-review/') for name in archive.namelist())
    assert not any('fixture' in name or 'verify' in name for name in archive.namelist())
passed.append("ZIP仅含四个Skill文件，无测试答案/缓存/个人配置")
report = "# 本地验证记录\n\n" + "\n".join(f"- 通过：{line}" for line in passed)
report += f"\n- 平台格式：{metadata_result}。\n\n以上只验证包、结构和模板，不验证模型会遵循指令、证据事实正确性、法规准确性或当前实例端到端效果。尚未自动安装、调用付费模型或运行实际预审。请按安装与测试.md完成真实附件测试。\n"
(BASE / "本地验证记录.md").write_text(report, encoding="utf-8")
print(report)
print(f"ZIP: {zip_path}")
