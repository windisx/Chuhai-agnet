# 结构化结果约定 v1

result.json 是本次产物的共同来源，不是对话记忆的替代物。UTF-8、合法JSON、不得有注释。所有自由文本字段写中文便于业务员阅读；ID/枚举英文。缺失信息使用“未知/未定位/未核实”，不得填造数值。兼容1.0结构；新增可选presentation字段用于业务摘要。

推荐额外顶层字段：`"presentation":{"summary":"120字以内的一句话业务摘要","next_actions":["C001：明确的下一步，80字以内"]}`。模板不重新推断事实；摘要和事项必须一致。不把报告里的长段落当摘要。

## 顶层结构

```json
{
  "schema_version": "1.0",
  "case_id": "export-demo-001",
  "version": 1,
  "previous_version": null,
  "context": {
    "product": "从材料提取的产品及型号",
    "market": "目标市场",
    "target_date": "用户指定的上市/交付日期或未知，注明含义",
    "checked_at": "实际核查日期",
    "purpose": "客户提交前资料预审",
    "role": "用户企业角色或未知",
    "scope": "本次已完成检查的范围",
    "limitations": "尚未覆盖的规则、解析限制和未知信息"
  },
  "files": [],
  "sources": [],
  "checks": [],
  "changes": [],
  "copy_suggestions": []
}
```

示例只展示格式，不可直接作为真实核查结果。context各值须为非空字符串。

## files 每项字段

`id`（如F001），`name`（原始文件名），`path`（本次真实可读路径），`role`（文件角色），`origin`（官方原文/公开供应商资料/模拟内部文件/用户口述等），`parse_status`（parsed/partial/failed），`notes`（身份线索、读取范围和解析限制）。

## sources 每项字段

`id`（如R001），`title`，`issuer`，`kind`（法规/非约束性官方指南等），`version`（核实的版本），`official_url`（原始官方链接；不能验证则“未核实”），`locator`（知识库file_id及章节/行号，或实际打开的来源），`applicability`（适用时间与本案范围、未知点），`checked_at`（本次实际日期）。未取得原文的来源不伪装成已查阅依据，写到context.limitations。

## checks 每项字段

```json
{
  "id": "C001",
  "title": "简明业务问题",
  "category": "身份对应/信息一致性/文案核对/资料范围",
  "status": "uncertain",
  "workflow": "open",
  "priority": "P1",
  "priority_reason": "为什么影响本次交付",
  "finding": "现有证据支持的事实和未知点",
  "impact": "对本次资料准备的影响，不直接推定违法",
  "evidence": [
    {"file_id": "F001", "quote": "准确原文或含行列信息的表格上下文", "locator": "经核实的PDF页/印刷页/章节/行号；否则未定位"}
  ],
  "source_ids": [],
  "search_limit": "实际查找范围/解析限制；不需要时填不适用",
  "next_action": "明确可执行的下一步",
  "recipient": "供应商/内部资料负责人/专业人员/无需补件",
  "requested_material": "应提供的具体材料；无需补件时注明",
  "acceptance": "后续需要核对哪些内容才能认定本事项解决",
  "review_note": "首次核查；或本次相对旧版本的复核依据"
}
```

核查状态：conflict=直接矛盾；missing=在已读取范围未发现所需资料；uncertain=信息/规则/归属待确认；unparsed=解析阻塞；consistent=本项有现有证据支持；not_applicable=有具体理由不适用。最后两类不表示整体合规。

办理状态：open=待处理；awaiting=待补件；review=已收到说明/修订待复核；closed=本事项已完成复核。首次consistent/not_applicable可以closed，但要写证据或不适用理由。conflict/missing/uncertain/unparsed不能closed。用户口述已改只能标review，不能据此将核查状态改为consistent。

优先级：P1=本次应优先确认/修订，P2=后续补齐/核实，P3=记录或本项已有支持。不是法律风险评级。前台计数由脚本按事项计算，不在JSON里另存统计数字。

conflict/consistent须有文件证据；其余状态也应附证据，若确无可用证据必须明确search_limit。每条引用的file_id/source_id必须存在。不得编造quote来通过校验。

## 补件复核

version为正整数。v1的previous_version为null，changes可为空；v2起previous_version为直接上个版本整数。必须读取旧版保留全部旧ID，沿用仍表示同一问题的ID，不能删除已解决事项。新增C编号续号。

changes每项：`check_id`、`before`、`after`、`basis`，均为非空字符串。每个新版本至少记一项变化（可以是状态保持不变、仅新增口述并待证据）；basis区分口述、内部修订、供应商新证据或专业书面复核。上版文件不可读取则停下自动版本比较，向用户说明并请提供旧记录或另建任务，禁止猜旧记录。

copy_suggestions每项：`check_id`、`original`、`suggested`、`reason`。建议文案只使用已被证据支持的内容，不编造认证、成分或供应商承诺；无文案任务时空数组。

## 看板与交付

脚本使用固定assets/dashboard.html生成交互HTML：数量卡、紧凑列表、搜索/状态和对象筛选、多选、证据侧栏、所选事项补件草稿、复核指令、文件依据与版本记录。离线可读，无外部脚本或远端接口。只用textContent展示输入，拒绝执行证据里的HTML。JSON路径用于工具审计，生成看板前删除文件登记中的内部path字段。复制与下载受宿主预览限制时保留可选中的文本。

本地命令：`python <skill目录>/scripts/render_review.py <result.json>`。脚本成功后再检查实际文件并调用present_artifacts。若选择手工生成同样产物，计数要按同一checks数组计算，不能报告脚本验证通过。
