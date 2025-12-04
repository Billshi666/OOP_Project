# 棋类对战平台 玩家使用说明

本平台支持在命令行中或简单图形界面中进行 **围棋** 和 **五子棋** 的双人对战，提供落子、悔棋、认输、存档/读档等功能。本说明面向玩家，只介绍如何运行和操作游戏。

## 一、如何运行游戏

### 1.1 命令行版本

在项目根目录下执行：

```bash
python3 -m src.main
```

看到提示：

```text
Board Game Platform (Go / Gomoku). Type 'start go|gomoku [size]' to begin. 'quit' to exit.
```

表示程序启动成功。

### 1.2 GUI 图形界面版本

在项目根目录下执行：

```bash
python3 -m src.gui_main
```

将打开一个简单的窗口：

- 左侧为棋盘网格，点击格子即可落子。
- 右侧为控制区：
  - 选择游戏类型（Go / Gomoku）。
  - 输入棋盘尺寸（8–19）。
  - 按钮：Start / Restart / Undo / Pass(Go) / Resign / Save / Load。
- 下方为状态栏：显示当前提示信息、对局结果和轮到哪一方行棋。

## 二、基本概念

- 棋盘大小：8～19 之间的整数。
  - 五子棋默认棋盘：15×15
  - 围棋默认棋盘：19×19
- 黑棋与白棋轮流行棋：
  - 黑棋用符号 `●`
  - 白棋用符号 `○`
  - 空位用符号 `+`

## 三、常用命令一览

命令提示行（可用 `hint on/off` 控制显示）：

```text
Commands: start go|gomoku [size] | play x y | pass (go only) | undo | resign | restart [size] | save name | load [name] | hint on/off | quit
```

各命令说明：

- `start go [size]`：开始一局围棋，对局未开始或已结束时可使用。
  - 例：`start go`（使用默认 19×19）
  - 例：`start go 9`（使用 9×9）
- `start gomoku [size]`：开始一局五子棋。
  - 例：`start gomoku`（默认 15×15）
  - 例：`start gomoku 10`
- `play x y`：在坐标 `(x, y)` 处落子，当前行棋方自动使用自己的棋子。
  - 例：`play 3 4`
- `pass`（仅围棋）：虚着，不落子但轮换行棋方。
- `undo`：悔棋一步，回到上一手之前的局面。若当前无棋可悔，会提示错误信息。
- `resign`：当前一方认输，对方立即获胜。
- `restart [size]`：在对局过程中重新开始当前游戏类型，可选择新棋盘大小。
  - 例：`restart`（沿用当前大小）
  - 例：`restart 13`
- `save name`：将当前对局存档为 `saves/name.json`。
  - 例：`save game1`
  - 成功后会提示存档路径，并说明可使用 `load game1` 或 `load` 恢复。
- `load [name]`：读取存档并覆盖当前局面。
  - `load name`：从 `saves/name.json` 读取。
  - `load`：若之前成功 `save` 过，会自动载入最近一次存档（“上一局”）。
- `hint on` / `hint off`：打开/关闭命令提示行。
- `quit` / `exit`：退出程序。

## 四、围棋规则简要说明（本平台实现）

- 支持落子、提子、虚着、数子判胜负：
  - 当你在一个位置落子时，如果把对方一整串相连的棋子（棋链）的“气”全部占满，该棋链会被提走。
  - 若某一手落子后，本方棋链没有任何气，而且没有提到对方任何棋子，则视为“自杀”，该手不被允许，系统会提示 `Suicide move is not allowed in Go`。
  - 两位玩家可以在自己的回合输入 `pass` 选择虚着。
  - 当双方连续各虚着一次（双 pass），系统会自动数子并判定胜负：
    - 黑、白棋盘上的实子数量 + 各自控制的空地数量更多者获胜；
    - 若双方数目相同，则为平局。
- 为简化实现，暂不考虑劫争（Ko）等复杂规则；但基本下法和终局判断与常见业余对局一致。

## 五、五子棋规则简要说明

- 两位玩家轮流在棋盘上落子，先形成 **任一方向连续五子** 的一方获胜（横、竖、斜均可）。
- 若棋盘被完全下满仍无人形成五连，则判定为平局。
- 五子棋中 **不允许 `pass`**，输入 `pass` 会提示错误。

## 六、简单示例

五子棋快速示例：

```text
start gomoku 8
play 0 0
play 1 0
play 2 0
play 3 0
play 4 0
```

当黑方在 (4,0) 形成连续五子后，系统会提示黑方获胜并结束对局。

围棋数子示例（简要）：

```text
start go 8
...（若干步落子与提子）
pass    # 黑虚着
pass    # 白虚着
```

当出现双 pass，系统会输出类似 `Black wins 6 vs 4` 的结果，表示黑方以 6:4 的目数获胜。

## 七、错误提示示例

常见错误场景和系统反馈：

- 未开始游戏就下子：`Start a game first: start go|gomoku [size]`
- 棋盘大小不合法：`Start failed: Board size must be between 8 and 19`
- 落子越界：`Move out of bounds`
- 落子到已有棋子的位置：`Position already occupied`
- 无棋可悔：`No move to undo`
- 载入不存在的存档：`Load failed: [Errno 2] No such file or directory: 'saves/xxx.json'`

根据这些提示调整操作即可。祝你对局愉快！
