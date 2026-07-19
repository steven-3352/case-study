# 动效技术计划 · W30D03

- 适用性：HTML+GSAP 适合确定性轨道位移和闸门开合，服务 3s、理解与完播；无需 Three/Web 3D。
- 可读性：过程镜最长句 48px 起；出口票九问正文不低于 30px，执行规则不低于 24px，并做手机尺寸停帧核验。1.0×/1.5× duration 压测，真实 VO 结束前持续有语义动作。
- 资产：8 个 D03 专属 HTML、共享 GSAP runtime、CC0 SFX；不依赖真人录音或外部素材。
- 导出：1080×1920、30fps；runtime storyboard 从 seg timing 生成，场景 ID 使用 `w30d03__*` 命名空间。
- 风险：轨道微动不能掩盖长静止；机器 `freezedetect` >4.00s fail。文字过密则先删次级说明，不缩小主问。

高级动效只服务看懂顺序、收藏 Prompt 和中段第十问回报，不为装饰。
