# Local MV Studio · 目录与产品边界合同

状态：M2 开工前置合同
日期：2026-07-31

## 1. 决策

Local MV Studio 是给普通用户使用的产品，不是要求用户修改仓库脚本的开发框架。

- 应用源码和内置资源视为只读。
- 普通用户只选择素材、填写项目配置、运行功能和查看结果。
- 用户项目、运行状态、缓存、日志和输出不得写入源码目录。
- 公共能力必须进入可安装的代码包；单片脚本和单片配置不得进入公共代码目录。
- pipeline/ 是待迁移的 legacy 混合目录，不再作为新项目根或新输出根。

## 2. 三类根目录

### 2.1 应用代码根

目标安装结构：

~~~text
src/mvstudio/
  domain/
  application/
  infrastructure/
  interfaces/
  engines/
  providers/
  workflows/
  resources/
tests/
docs/
pyproject.toml
~~~

其中 engines/ 接收可复用的确定性渲染能力，providers/ 接收 GPT-image、TTS 和视频服务适配器，resources/ 只放随产品发布的 schema、模板、CSS、JS 和默认配置。

代码根禁止出现运行日志、下载素材、帧序列、TTS、生成图片、视频、项目 YAML 或用户凭证。

### 2.2 应用状态根

应用状态根由操作系统规范或 MV_WORKSPACE_ROOT 决定，默认不在 Git 仓库内：

~~~text
<workspace>/
  .mvstudio/
    app.sqlite3
    jobs/
    cache/
    service-logs/
  projects/
~~~

SQLite、全局任务队列、共享缓存和服务级日志属于应用状态，不属于源码。

### 2.3 用户项目根

每个普通用户项目位于 <workspace>/projects/<slug>/：

~~~text
brief.json
inputs/
  audio/
  lyrics/
  characters/
creative/
assets/
  source/
  generated/
outputs/
.mvstudio/
  jobs/
  work/
  logs/
~~~

inputs/ 是用户提供的只读原料；creative/ 是 maps、visual score 和 shots 等可编辑项目合同；assets/ 是项目专属素材；outputs/ 是 Animatic、final video 和质量报告；项目内 .mvstudio/ 是可清理的运行细节。

## 3. 写入矩阵

| 写入者 | 允许写入 | 禁止写入 |
|---|---|---|
| API / CLI / Codex 入口 | Application Service | 直接写文件、直接调用片级 renderer |
| Application Service | 用户工作区、应用状态根 | 应用代码根 |
| Job Supervisor | .mvstudio/jobs、事件数据库 | 项目合同和应用代码 |
| Stage Executor | 当前 Job staging、当前项目 outputs/assets | 其他项目、公共引擎目录 |
| Provider adapter | 当前 Job staging | 仓库、其他 Job、用户输入原件 |

所有正式产物先写 Job staging，完成 schema、hash 和 QC 后再原子发布到项目目录。

## 4. M2 迁移门禁

M2 Legacy adapter 开工前必须满足：

1. Project.root 不含 pipeline/voice_room。
2. CLI/API 无参数启动时不会以当前仓库为工作区。
3. 显式把源码根设为工作区时 fail-closed，且源码树零新增文件。
4. 创建项目只写 <workspace>/projects/<slug>/ 和 <workspace>/.mvstudio/。
5. 《明月天涯》作为只读 golden fixture，由 adapter 消费，不作为运行时工作目录。
6. 任一测试运行前后，受保护源码树的 tracked-file hash 不变。
7. 新增公共能力不得继续放入 pipeline/voice_room 或片名目录。

## 5. pipeline/ 迁移分类

迁移时逐文件归类，禁止整目录搬运：

- 可复用 Python 引擎、provider、公共模板：迁入 src/mvstudio/ 对应模块。
- golden reference 和反例 fixture：迁入 tests/fixtures/，只读。
- 单片 YAML、prompt、字幕、TTS 配置：迁入对应用户项目。
- 临时文件、日志、帧和生成结果：迁入项目 .mvstudio/ 或清理。
- 已废弃的一次性脚本：验证无调用后归档或删除，不包装成公共 API。

迁移期间旧 import 可由 adapter 兼容；新入口不得直接 import pipeline.*。M2 完成后再决定何时删除 legacy 路径，不能为了目录好看破坏 golden 对齐。
