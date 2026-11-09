"""创建与真实预审分开的、明确标注为模拟的界面演示文件。"""
import importlib.util
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('renderer', BASE / 'export-document-review/scripts/render_review.py')
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)
data = {
    'schema_version': '1.0', 'case_id': 'demo-interface-only', 'version': 1, 'previous_version': None,
    'context': {'product': 'MO6738 卫衣小熊 · 界面演示', 'market': '欧盟 · 德国', 'target_date': '2027-01-15（模拟计划）', 'checked_at': '2026-11-06', 'purpose': '固定模板交互演示，非真实预审记录', 'role': '模拟内部资料负责人，法律角色未核实', 'scope': '演示文案、报告对应关系、标签和补件流程的界面层次', 'limitations': '本页数据为人工模拟，仅用于界面与交互测试；不代表对原始PDF的核查结论，不可作为真实产品证明。'},
    'presentation': {'summary': '模拟结果：内部文案存在一处材质表述矛盾，建议先修订；报告归属、标签和声明时间线仍需补充确认。', 'next_actions': ['C001：删去内部草稿中无依据的“100%纯棉”表述', 'C002、C003：向供应商索取目标国语言标签和测试点对应资料', 'C004：补充声明与报告日期之间的解释材料']},
    'files': [{'id': 'F001', 'name': '模拟内部文案.md', 'path': '/hidden/fixture-only', 'role': '内部草稿', 'origin': '人工模拟界面数据', 'parse_status': 'parsed', 'notes': '只为验证界面，不作为真实业务证据'}],
    'sources': [], 'checks': [], 'changes': [], 'copy_suggestions': []}
items = [
    ('内部文案中的纯棉表述与现有资料矛盾', 'conflict', 'open', 'P1', '内部资料负责人', '模拟旧稿包含“100%纯棉”，本次示意资料无法支持该表述。', '上传删去无依据材质声明的内部修订稿。'),
    ('目标国语言标签与包装样稿待补充', 'missing', 'awaiting', 'P1', '供应商', '本次演示材料未包含德语标签或包装样稿。', '提供对应型号的德语标签与包装样稿。'),
    ('化学测试点与目标型号的对应关系待确认', 'uncertain', 'awaiting', 'P1', '供应商 / 实验室', '多型号报告中的测试点是否覆盖本型号及部件仍不明确。', '提供逐测试点、逐部件的对应说明。'),
    ('声明签署日与报告日期之间的关系待解释', 'uncertain', 'open', 'P2', '供应商', '日期先后是待确认线索，本页不推定声明无效。', '说明声明所依据的资料及是否有后续版本。'),
    ('制造商信息的载体位置待核对', 'uncertain', 'open', 'P2', '供应商', '需要结合实物、包装和随附文件核对；本页没有实物。', '提交相关实物照片或随附文件。'),
    ('实际订单与批次追溯资料尚未提供', 'missing', 'open', 'P2', '内部资料负责人', '演示资料不是实际订单，不能据此推定追溯义务不满足。', '如进入实际订单阶段，提供相应追溯资料。'),
    ('企业在目标市场的法律角色尚待确认', 'uncertain', 'open', 'P2', '内部资料负责人', '尚未确认制造商、进口商与分销商分工。', '确认各经营者身份和本企业角色。'),
    ('本次草稿的产品型号对应已记录', 'consistent', 'closed', 'P3', '无需补件', '本演示的内部草稿明确标注MO6738，仅支持该文本中的型号对应。', '本项无需补件，其他证据范围另行核查。')]
for n, (title, status, workflow, priority, recipient, finding, action) in enumerate(items, 1):
    data['checks'].append({'id': f'C{n:03d}', 'title': title, 'category': '界面模拟事项', 'status': status, 'workflow': workflow, 'priority': priority, 'priority_reason': '按模拟资料交付的办理顺序安排，不是法律评级', 'finding': finding, 'impact': '影响资料提交前的准备与确认', 'evidence': [{'file_id': 'F001', 'quote': '界面模拟原文：' + finding, 'locator': '模拟章节，非真实PDF页码'}], 'source_ids': [], 'search_limit': '此界面测试没有执行真实法规或原PDF核查', 'next_action': action, 'recipient': recipient, 'requested_material': action, 'acceptance': '核对实际补充文件的型号、来源、版本和所需字段；模拟资料只验证流程', 'review_note': '人工模拟界面数据'})
for c in data['checks']:
    c['display'] = {'summary': c['finding'], 'finding_points': [c['finding'], '本项仅为模拟界面数据，不代表真实产品核查。'], 'next_steps': [c['next_action']], 'materials': [c['requested_material']], 'acceptance_points': ['核对型号、来源和版本', '核对实际需要的字段；模拟资料只验证流程']}
    c['evidence'][0]['summary'] = '人工模拟内容，用于验证证据摘要与原文分开展示。'
def presentation(status, title, detail):
    return {'summary': detail, 'next_actions': ['C002：索取目标国语言标签', 'C003：确认测试点归属'],
            'summary_cards': [{'title': title, 'detail': detail, 'tone': status, 'check_ids': ['C001']}, {'title': '资料仍待补充', 'detail': '语言标签、测试点对应与其他信息仍需确认。', 'tone': 'warning', 'check_ids': ['C002', 'C003']}, {'title': '仅作界面演示', 'detail': '未核查真实PDF和法规，不代表产品事实或合规结论。', 'tone': 'info', 'check_ids': []}],
            'action_cards': [{'title': '索取目标国语言标签', 'recipient': '供应商', 'detail': '提供对应型号标签和包装样稿', 'check_ids': ['C002']}, {'title': '确认测试点归属', 'recipient': '供应商 / 实验室', 'detail': '逐型号、逐部件说明对应关系', 'check_ids': ['C003']}, {'title': '补充版本沿革说明', 'recipient': '供应商', 'detail': '说明声明依据与后续版本', 'check_ids': ['C004']}]}
data['presentation'] = presentation('danger', '草稿表述存在矛盾', '模拟草稿中的材质表述缺少支持，需先修订。')
target = BASE / 'preview' / data['case_id'] / 'v1' / 'result.json'
target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
r.validate(data, target)
for name, content in r.render(data).items():
    (target.parent / name).write_text(content, encoding='utf-8')
# A second preview shows the precise change expected from an internal text revision.
data['version'] = 2
data['previous_version'] = 1
c = data['checks'][0]
c.update(status='consistent', workflow='closed', finding='模拟内部修订稿已删去原无依据材质表述；仅该份草稿文本得到修订，不证明产品材质。', review_note='依据实际上传的模拟内部修订文本，对比后仅关闭文本矛盾')
data['files'].append({'id': 'F002', 'name': '模拟内部文案修订稿.md', 'path': '/hidden/revision-fixture', 'role': '内部修订稿', 'origin': '人工模拟界面数据', 'parse_status': 'parsed', 'notes': '仅示意文本变化，不代表真实材质证明'})
c['evidence'] = [{'file_id': 'F002', 'quote': '模拟新稿：具体材料请以已核实的正式产品资料为准；未保留纯棉声明。', 'locator': '模拟修订稿产品介绍章节'}]
data['changes'] = [{'check_id': 'C001', 'before': '存在矛盾 · 待处理', 'after': '本项有支持 · 已复核（仅限该文本）', 'basis': '模拟内部修订稿删去无依据声明，不是供应商或实验室的新证据'}]
data['presentation'] = {'summary': '模拟复核结果：内部草稿的材质表述已修订；标签、测试点对应和其他待确认事项仍保留。', 'next_actions': ['C002：继续索取目标国语言标签与包装样稿', 'C003：请供应商或实验室确认测试点与部件的对应关系', 'C004：继续补充声明与报告日期的说明']}
c['display']['summary'] = c['finding']
c['display']['finding_points'] = [c['finding'], '其他材料、标签及测试事项未因此解决。']
c['evidence'][0]['summary'] = '模拟新稿删除材质声明，仅支持该份草稿的文字变化。'
data['presentation'] = presentation('success', '内部文本已修订', '仅支持该份模拟内部草稿修订，不能证明产品材质。')
v2 = target.parent.parent / 'v2' / 'result.json'
v2.parent.mkdir(exist_ok=True)
v2.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
r.validate(data, v2)
for name, content in r.render(data).items():
    (v2.parent / name).write_text(content, encoding='utf-8')
print('Created clearly labeled v1/v2 interface previews under competition/core-skill-v1.2/preview')

# 兼容性演示使用同一模拟数据，不进入上传ZIP。
from copy import deepcopy
for mode in ('legacy', 'closed'):
    sample = deepcopy(data)
    sample.update(version=1, previous_version=None, case_id='demo-' + mode, changes=[])
    sample['presentation'] = {'summary': '人工模拟兼容性测试，不代表真实核查。', 'next_actions': ['请核对模拟事项']} if mode == 'legacy' else {'summary': '人工模拟全部完成，仅验证无待办分支。', 'next_actions': []}
    for check in sample['checks']:
        if mode == 'legacy':
            check.pop('display', None)
            for evidence in check['evidence']:
                evidence.pop('summary', None)
        else:
            check.update(status='consistent', workflow='closed')
    record = BASE / 'preview' / sample['case_id'] / 'v1/result.json'
    record.parent.mkdir(parents=True, exist_ok=True)
    record.write_text(json.dumps(sample, ensure_ascii=False, indent=2), encoding='utf-8')
    r.validate(sample, record)
    for name, content in r.render(sample).items():
        (record.parent / name).write_text(content, encoding='utf-8')
