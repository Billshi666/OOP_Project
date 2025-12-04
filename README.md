# 棋类对战平台（Go / Gomoku）

一个基于命令行的棋类对战平台，支持 **围棋** 和 **五子棋** 的双人对战，作为面向对象程序设计课程的大作业第一阶段实现。

> 本 README 用于开发者或日后维护者快速了解项目情况。  
> 面向玩家的使用说明见：`PLAYER_GUIDE.md`。  
> 详细设计与实验报告见：`docs/requirements.md`、`docs/architecture.md` 等。

## 功能概览

- 支持两种棋类：
  - 五子棋（Gomoku）：任意方向连五即胜，满盘平局。
  - 围棋（Go）：支持提子、虚着（pass）、双 pass 后数子判胜负。
- 双人对战（黑白轮流），黑棋先行。
- 基本对局控制：
  - 开始游戏：选择游戏类型和棋盘尺寸（8–19）。
  - 对局中重开（可调整尺寸）。
  - 落子 / 虚着（仅围棋）、悔棋一步、认输。
- 局面管理：
  - 棋盘实时显示，黑白棋清晰区分。
  - 存档与读档：支持多局命名存档，默认恢复上一局。
  - 处理非法操作并给出错误提示（越界、占用、无棋可悔、非法尺寸、非法命令等）。
- 文档与测试：
  - 需求说明、架构设计、UML（Mermaid）。
  - 命令级测试用例及真实终端输出记录。

## 运行环境与依赖

- Python 3.8+（项目只用到标准库，无第三方依赖）。
- 操作系统：Windows / macOS / Linux 均可（只要有 Python 3）。

## 快速开始

在项目根目录运行：

```bash
python3 -m src.main
```

在命令行内使用 `start go|gomoku [size]` 开始对局，更多玩家操作说明见 `PLAYER_GUIDE.md`。

## 目录结构

```text
.
├─ src/
│  ├─ main.py               # 程序入口（命令行循环）
│  ├─ controller.py         # 控制器，协调命令解析、游戏逻辑与渲染
│  ├─ command_parser.py     # 简单命令行解析
│  ├─ renderer.py           # CLI 渲染器（棋盘与消息显示）
│  ├─ serializer.py         # JSON 存档读写
│  ├─ core/                 # 领域核心模型
│  │  ├─ board.py           # 棋盘表示与基本操作
│  │  ├─ move.py            # 落子/操作表示
│  │  ├─ history.py         # 悔棋/快照历史（备忘录）
│  │  ├─ player.py          # 玩家颜色等
│  │  └─ snapshot.py        # 给 UI/存档使用的局面快照
│  ├─ game/                 # 游戏类型与模板
│  │  ├─ base_game.py       # Game 模板基类（生命周期与通用流程）
│  │  ├─ go_game.py         # 围棋具体游戏
│  │  ├─ gomoku_game.py     # 五子棋具体游戏
│  │  └─ factory.py         # 抽象工厂：按类型创建游戏
│  └─ rules/                # 规则引擎（策略）
│     ├─ base_rule.py       # RuleEngine 抽象、ApplyResult、GameResult
│     ├─ go_rule.py         # 围棋规则（提子、数子）
│     └─ gomoku_rule.py     # 五子棋规则（连五、满盘平局）
├─ docs/
│  ├─ requirements.md       # 需求说明
│  ├─ architecture.md       # 领域建模与架构分层 + UML
│  └─ tests.md              # 测试用例与实际输出记录
├─ PLAYER_GUIDE.md          # 玩家使用说明
├─ project_step1.md         # 课程作业原始说明（第一阶段）
└─ README.md                # 本文件
```

存档文件默认写入 `saves/` 目录，例如 `saves/game1.json`。

## 设计与模式概览（非完整设计文档）

代码整体遵循“后端逻辑与客户端界面分离”的思路，主要采用了以下设计模式（细节见 `docs/architecture.md`）：

- 抽象工厂（`GameFactory`）  
  根据玩家选择的游戏类型（Go / Gomoku）创建对应的 `Game` 实例及其配置，便于后续扩展更多棋类。

- 策略模式（`RuleEngine` 及其实现）  
  将围棋/五子棋的规则判定封装为独立的策略类：`GoRuleEngine`、`GomokuRuleEngine`，`Game` 通过统一接口调用规则逻辑。

- 模板方法（`Game` 基类）  
  在基类中定义对局流程骨架（落子检查、历史快照、终局判定等），具体规则委托给策略类实现。

- 备忘录模式（`History` + `Memento`）  
  通过保存局面快照支持悔棋与存档/读档，外部只需调用 `undo` 或 `save`/`load`，无需关心内部细节。

此外，还通过简单的分层结构实现了 UI 与业务逻辑解耦：

- `Controller`：应用服务层，负责处理命令、调用 `Game`、捕获错误并交给渲染器。
- `CliRenderer`：表现层，仅负责展示棋盘和消息，可在后续替换或增加 GUI 渲染器。
- `core` / `rules` / `game`：领域模型与规则实现，不依赖具体 UI。

## 围棋规则简化说明

项目中的围棋实现做了一些有意的简化（适合课程作业规模）：

- 支持：
  - 提子：将无气的对方棋链从棋盘上移除。
  - 虚着（pass）：当前回合选择不落子，并轮到对方。
  - 双 pass 后数子：两人连续 pass 后，系统自动数子并判定胜负。
  - 自杀禁手：若一手落子后本方棋链无气且未提到任何对方棋子，则视为自杀，判为非法并给出提示。
  - 数子方式：各方盘面实子数 + 控制空地数，较多者胜（接触单一颜色的空地归该方）。
- 未实现：
  - 劫争判定（Ko）与相关禁着规则（暂不检测重复局面）。

这些假设在课程背景下通常是可接受的，也便于专注在面向对象设计与代码结构上；若后续需要，可在现有规则引擎基础上继续扩展。

如需了解具体类/接口设计与 UML 图，请参考 `docs/architecture.md`。  
如需了解需求来源与评分标准，请参考 `project_step1.md`。 

## GUI 说明（可选扩展）

除命令行版本外，项目还实现了一个基于 Tkinter 的简单图形界面：

- 启动方式：
  - 在项目根目录运行：`python3 -m src.gui_main`
- 界面组成：
  - 左侧为棋盘网格（支持 8–19 的棋盘尺寸），鼠标点击棋盘格即可落子。
  - 右侧为控制区：游戏类型选择（Go / Gomoku）、棋盘尺寸输入，以及 Start / Restart / Undo / Pass(Go) / Resign / Save / Load 按钮。
  - 下方为信息栏：显示当前提示信息、对局结果和轮到哪一方行棋。
- 行为与命令行一致：
  - 所有按钮操作最终都会被映射为与命令行相同的命令（如 play/pass/undo/save/load 等），复用同一套 `Controller` 和规则引擎逻辑。
  - 存档仍保存在 `saves/` 目录；Save/Load 按钮通过简单对话框让用户输入/选择存档名称。

如需了解具体类/接口设计与 UML 图，请参考 `docs/architecture.md`。  
如需了解需求来源与评分标准，请参考 `project_step1.md`。 
