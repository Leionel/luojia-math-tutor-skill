# U12 获准的小规模模型运行有真实准入和预算

状态：升级计划草案；本轮只写计划，尚未实施。后续按用户选择的切片开始。

**对应目标：** A5/A7 + S5.3

**优先级：** 条件启动

**Blocked by：** 无；真实供应商、计费上界与消费授权为外部gate

**工程投入情景：** 3–5开发日＋供应商/复核等待；不是交付保证，不含外部等待。

## What to build

指定模型/endpoint用最多3次隔离协议probe，获准的最多8个单run smoke有发送前限额和可核对回执。

## 选择的实现范围

- 复用S4 call/span和S5 offline ledger理念，但不删除Mock-only检查伪装支持live；新增明确验证的live profile与薄transport注入。
- 先核对实际model/endpoint、计费输入/输出/cache/reasoning/按次项上界与权限；未知费用硬上限模式不运行。
- 只有批准host/path/model/run清单；禁redirect/embedding/联网搜索/后台/自动重试；失败取消恢复不返额度。
- protocol probe只证明schema/续轮/usage能力，不证明数学质量；S5.2材料复核状态保持。

## Acceptance criteria

- [ ] 费用/能力未知或profile缺失不发送；请求52上界仅适用于3probe+8单run×6，episode按真实run重算。
- [ ] 并发额度、错目标、取消/重启/unknown usage保护在真实transport边界再次通过。
- [ ] 实际usage/已知金额与未知部分分别报告，不能以字节数估算计费token上界。
- [ ] 一次获准小smoke有原始运行绑定和人工逐题证据；无授权不自动用.env消费。

## 回滚与恢复

关闭live profile与发送入口，保留已预留/消费/未运行记录，不换provider续跑。

## STOP conditions

未核实可计费上界/供应商能力、消费授权或密钥归属时只停live；离线可继续。

## 验收与记录

使用母计划§验收合同：先对本切片反例/状态/权限/恢复做针对性测试，再跑适用完整回归；UI变化做桌面/390px、键盘/主题/取消/刷新/空/错误态实际验证。条件项必须有对应真实环境回执；源码、fixture、live、教师审核和学生研究分别记录。实现偏离写母目录implementation-notes.md的Deviations；不是STOP的保守选择可自行完成并记录。
