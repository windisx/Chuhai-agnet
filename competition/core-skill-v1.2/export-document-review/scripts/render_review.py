"""Render one review record. Standard library only; no legal/factual validation."""
import argparse
from collections import Counter
import json
from pathlib import Path
import re

STATUSES = {"conflict": "存在矛盾", "missing": "已读范围未发现", "uncertain": "待确认", "unparsed": "解析受阻", "consistent": "本项有支持", "not_applicable": "本项不适用"}
WORKFLOWS = {"open": "待处理", "awaiting": "待补件", "review": "待复核", "closed": "已完成复核"}
OUTPUTS = ("预审看板.html", "核查清单.md", "补件请求.md", "文案修订建议.md")


def require(ok, message):
    if not ok:
        raise ValueError(message)


def fields(obj, keys):
    require(isinstance(obj, dict), "记录必须为对象")
    for key in keys.split():
        require(isinstance(obj.get(key), str) and obj[key].strip(), f"缺少非空文本字段 {key}")


def index(items, prefix):
    result = {}
    require(isinstance(items, list), f"{prefix}记录必须为数组")
    for item in items:
        fields(item, "id")
        require(re.fullmatch(prefix + r"\d{3,}", item["id"]), f"非法编号 {item['id']}")
        require(item["id"] not in result, f"重复编号 {item['id']}")
        result[item["id"]] = item
    return result


def validate(data, path):
    require(data.get("schema_version") == "1.0", "schema_version必须为1.0")
    require(re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", data.get("case_id", "")), "case_id格式错误")
    version = data.get("version")
    require(type(version) is int and version > 0, "version须为正整数")
    require(path.parent.name == f"v{version}" and path.parent.parent.name == data["case_id"], "目录必须为<case_id>/v<N>/result.json")
    fields(data.get("context"), "product market target_date checked_at purpose role scope limitations")
    if "presentation" in data:
        fields(data["presentation"], "summary")
        require(len(data["presentation"]["summary"]) <= 120, "摘要须在120字以内")
        actions = data["presentation"].get("next_actions")
        require(isinstance(actions, list) and 0 <= len(actions) <= 3 and all(isinstance(a, str) and 0 < len(a) <= 80 for a in actions), "下一步须为0至3条，每条80字以内；存在未完成事项时不能为空")
    presentation = data.get("presentation", {})
    for key in ("summary_cards", "action_cards"):
        if key not in presentation:
            continue
        cards = presentation[key]
        require(isinstance(cards, list) and 1 <= len(cards) <= 3, f"{key}须为1至3张卡片")
        for card in cards:
            fields(card, "title detail")
            require(len(card["title"]) <= 20 and len(card["detail"]) <= 60, "卡片标题/说明过长")
            ids = card.get("check_ids")
            require(isinstance(ids, list) and all(isinstance(cid, str) for cid in ids), "check_ids须为编号数组")
            if key == "summary_cards":
                require(card.get("tone") in {"warning", "info", "success", "danger"}, "非法卡片语义色")
            else:
                fields(card, "recipient")
                require(len(card["recipient"]) <= 50 and bool(ids), "动作卡须有简短责任对象和关联事项")
    files = index(data.get("files"), "F")
    sources = index(data.get("sources"), "R")
    checks = index(data.get("checks"), "C")
    require(not presentation or bool(presentation["next_actions"]) or all(c["workflow"] == "closed" for c in checks.values()), "存在未完成事项时下一步不能为空")
    for key in ("summary_cards", "action_cards"):
        for card in presentation.get(key, []):
            require(all(cid in checks for cid in card["check_ids"]), "卡片关联未知事项")
            if key == "action_cards":
                require(any(checks[cid]["workflow"] != "closed" for cid in card["check_ids"]), "动作卡不能仅关联已关闭事项")
            if key == "summary_cards" and card["tone"] in {"success", "danger"}:
                allowed = {"consistent", "not_applicable"} if card["tone"] == "success" else {"conflict"}
                require(bool(card["check_ids"]) and all(checks[cid]["status"] in allowed for cid in card["check_ids"]), "卡片颜色与关联事项状态不符")
    for item in files.values():
        fields(item, "name path role origin parse_status notes")
        require(item["parse_status"] in {"parsed", "partial", "failed"}, "非法解析状态")
    for item in sources.values():
        fields(item, "title issuer kind version official_url locator applicability checked_at")
    for item in checks.values():
        fields(item, "title category status workflow priority priority_reason finding impact search_limit next_action recipient requested_material acceptance review_note")
        require(item["status"] in STATUSES and item["workflow"] in WORKFLOWS, "非法事项状态")
        require(item["priority"] in {"P1", "P2", "P3"}, "非法优先级")
        require(item["workflow"] != "closed" or item["status"] in {"consistent", "not_applicable"}, "未解决事项不能关闭")
        if "display" in item:
            display = item["display"]
            fields(display, "summary")
            require(len(display["summary"]) <= 80, "事项展示摘要过长")
            for key in ("finding_points", "next_steps", "materials", "acceptance_points"):
                points = display.get(key)
                require(isinstance(points, list) and 1 <= len(points) <= 6 and all(isinstance(p, str) and p.strip() and len(p) <= 120 for p in points), f"{key}须为1至6条短要点")
        evidence = item.get("evidence")
        require(isinstance(evidence, list), "evidence必须为数组")
        require(evidence or item["status"] not in {"conflict", "consistent"}, "矛盾/有支持状态必须有文件证据")
        for e in evidence:
            fields(e, "file_id quote locator")
            require(e["file_id"] in files, "引用了不存在的文件")
            if "summary" in e:
                fields(e, "summary")
                require(len(e["summary"]) <= 120, "证据摘要过长")
        refs = item.get("source_ids")
        require(isinstance(refs, list) and all(isinstance(r, str) and r in sources for r in refs), "来源引用错误")
    for key, required in [("changes", "check_id before after basis"), ("copy_suggestions", "check_id original suggested reason")]:
        require(isinstance(data.get(key), list), f"{key}必须为数组")
        for item in data[key]:
            fields(item, required)
            require(item["check_id"] in checks, f"{key}引用未知事项")
    if version == 1:
        require(data.get("previous_version") is None, "v1的previous_version须为null")
    else:
        require(data.get("previous_version") == version - 1, "previous_version须为直接上版")
        old_path = path.parent.parent / f"v{version-1}" / "result.json"
        require(old_path.is_file(), "缺少旧版result.json，不能自动比较")
        old = json.loads(old_path.read_text(encoding="utf-8-sig"))
        require(old.get("case_id") == data["case_id"] and old.get("version") == version - 1, "上版身份不符")
        old_checks = index(old.get("checks"), "C")
        require(old_checks.keys() <= checks.keys(), "新版不能删除旧事项ID")
        require(bool(data["changes"]), "新版需记录变化或未解决原因")
        changed = {c["check_id"] for c in data["changes"]}
        for cid, item in checks.items():
            if cid not in old_checks or item != old_checks[cid]:
                require(cid in changed, f"{cid}变化没有记录")
        maximum = max((int(cid[1:]) for cid in old_checks), default=0)
        require(all(int(cid[1:]) > maximum for cid in checks.keys() - old_checks.keys()), "新事项须续号")


def render(data):
    ctx = data["context"]
    checks = sorted(data["checks"], key=lambda c: (c["workflow"] == "closed", c["priority"], c["id"]))
    counts = Counter(c["status"] for c in checks)
    heading = f"{ctx['product']} · {ctx['market']} · v{data['version']}"
    summary = "；".join(f"{label} {counts[key]}项" for key, label in STATUSES.items())
    intro = ["# 出海资料预审", heading, "辅助核查，待人工确认；本项有支持不等于产品整体合规。", summary]
    intro += [f"{k}：{ctx[k]}" for k in ctx]
    lines = intro.copy()
    requests = ["# 补件请求草稿", heading, "请人工核对收件对象和内容后使用；本工具未发送任何消息。"]
    for c in checks:
        title = f"{c['id']} {c['title']}"
        state = f"{STATUSES[c['status']]} · {WORKFLOWS[c['workflow']]} · {c['priority']}"
        details = [state, f"类别：{c['category']}", f"优先级理由：{c['priority_reason']}", f"发现：{c['finding']}", f"交付影响：{c['impact']}", f"下一步：{c['next_action']}", f"补件对象：{c['recipient']}", f"所需材料：{c['requested_material']}", f"复核标准：{c['acceptance']}", f"复核说明：{c['review_note']}", f"查找限制：{c['search_limit']}"]
        proof = [f"{e['file_id']} | {e['locator']} | {e['quote']}" for e in c['evidence']]
        proof.append("规则来源：" + ("、".join(c['source_ids']) or "未关联规则；详见核查范围与查找限制"))
        lines += ["\n## " + title, *details, "\n证据：", *proof]
    for recipient in sorted({c['recipient'] for c in checks if c['workflow'] != 'closed'}):
        requests.append("\n## " + recipient)
        for c in checks:
            if c['recipient'] == recipient and c['workflow'] != 'closed':
                requests += [f"\n### {c['id']} {c['title']}", f"为完成本次资料预审，请协助提供：{c['requested_material']}", f"核对背景：{c['finding']}", f"请确认/需核对的内容：{c['acceptance']}"]
    if all(c['workflow'] == 'closed' for c in checks):
        requests.append("本次记录没有待办理事项；不表示其他范围无资料需求。")
    copies = ["# 文案修订建议", heading, "仅针对本次内部草稿，不代表供应商声明。"]
    for c in data['copy_suggestions']:
        copies += [f"\n## {c['check_id']}", f"原文：{c['original']}", f"建议：{c['suggested']}", f"理由：{c['reason']}"]
    if not data['copy_suggestions']:
        copies.append("本次未形成具体文案修订建议；原因以核查范围和事项记录为准。")
    registry = ["\n## 文件登记"]
    for f in data['files']:
        registry.append(f"{f['id']} | {f['name']} | {f['role']} | {f['origin']} | {f['parse_status']} | {f['notes']}")
    registry.append("\n## 规则依据")
    for s in data['sources']:
        registry.append(" | ".join(f"{k}：{s[k]}" for k in s))
    if not data['sources']:
        registry.append("未记录已核实规则来源，不作法律要求判定。")
    registry.append("\n## 版本变化")
    registry.extend(f"{c['check_id']} | {c['before']} → {c['after']} | 依据：{c['basis']}" for c in data['changes'])
    if not data['changes']:
        registry.append("首次核查。")
    lines += registry
    template = Path(__file__).resolve().parent.parent / "assets" / "dashboard.html"
    view = {**data, "files": [{k: v for k, v in f.items() if k != "path"} for f in data["files"]]}
    payload = json.dumps(view, ensure_ascii=False).replace("&", "\\u0026").replace("<", "\\u003c").replace(">", "\\u003e").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    html = template.read_text(encoding="utf-8").replace("__REVIEW_DATA__", payload)
    return dict(zip(OUTPUTS, [html, "\n\n".join(lines), "\n\n".join(requests), "\n\n".join(copies)]))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", type=Path)
    path = parser.parse_args().record.resolve()
    require(path.name == "result.json", "输入文件须为result.json")
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    validate(data, path)
    for name in OUTPUTS:
        require(not (path.parent / name).exists(), f"拒绝覆盖已有交付文件：{name}；请使用新版本")
    outputs = render(data)
    for name, content in outputs.items():
        with (path.parent / name).open("x", encoding="utf-8") as file:
            file.write(content)
    print(json.dumps({"status": "ok", "validation": "structure_only", "outputs": [str(path.parent / n) for n in OUTPUTS]}, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, TypeError, KeyError) as exc:
        raise SystemExit(f"校验/生成失败：{exc}") from exc
