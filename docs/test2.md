# 测试用例（第二阶段：Othello / AI / Accounts / Replay）

说明：
- 以下均在项目根目录运行 `python3 -m src.main`。
- 为避免输出过长，下面大多数用例会先执行 `hint off`；终端输出摘录核心内容（棋盘与部分提示文本略，除非该用例明确需要检查可视化/提示）。
- AI1/AI2 存在随机性（用于在同分情况下打破平局），因此 AI 的具体落子坐标可能与示例不同；测试时以“是否自动走子、是否始终落在合法位置”为准。
- `register/login` 会通过 `getpass` 读取密码（不回显），不适合用管道喂入；相关用例以“手动交互测试”形式给出。

---

## 1. 引导与帮助（Help / Hint）

输入：
```
help
help othello
help ai
help accounts
help replay
hint off
hint on
quit
```

实际输出摘录：
```
Board Game Platform - Help
...
Help - Othello (Reversi)
...
Help - AI (Othello only)
...
Help - Accounts (all games)
...
Help - Replay
...
[info] Hint off
[info] Hint on
```

---

## 2. Othello：开局与尺寸约束（偶数 8–18）

输入：
```
start othello
start othello 9
start othello 18
start othello 20
quit
```

实际输出摘录：
```
[info] Started othello size 8
Start failed: Othello size must be even between 8 and 18
[info] Started othello size 18
Start failed: Othello size must be even between 8 and 18
```

---

## 3. Othello：合法落子可视化（moves 显示 `*`）+ 翻转

输入：
```
start othello 8
hint off
moves
play 2 3
moves
quit
```

实际输出摘录（示例，棋盘略）：
```
[info] Legal moves for BLACK: 4
[info] Tip: play x y on a '*' cell
[info] Move (2,3); flipped 1
[info] Legal moves for WHITE: ...
```

检查点：
- `moves` 后棋盘中会用 `*` 标记当前行棋方的所有合法落子点。
- `play` 必须下在合法点，否则会提示非法（见下一用例）。

---

## 4. Othello：非法落子与 pass 提示（含补救指引）

输入：
```
start othello 8
hint off
play 0 0
pass
quit
```

实际输出摘录：
```
[info] Illegal move in Othello: must flip at least one disc
[info] Tip: use 'moves' to show legal moves ('*' on the board)
[info] Pass not allowed: you have legal moves
[info] Tip: Othello uses forced pass automatically; play a legal move (try 'moves')
```

---

## 5. Othello：forced pass（自动弃权）可复现用例（短序列）

目标：复现“某一方无合法落子时，系统自动执行 forced pass（无需输入 pass）”。

输入：
```
start othello 8
hint off
play 3 2
play 2 2
play 4 5
play 3 1
play 3 0
play 4 0
play 1 1
play 2 0
quit
```

实际输出摘录（中间落子过程略）：
```
...
[info] Move (2,0); flipped 1
...
[info] Forced pass (no legal moves)
```

检查点：
- 在最后一步后，应出现 `Forced pass (no legal moves)`，并自动轮到对方继续行棋。

---

## 6. seat：对弈双方配置（human / ai1 / ai2）与跨游戏限制

### 6.1 未开始游戏时设置 seat

输入：
```
seat white ai1
who
quit
```

实际输出摘录：
```
[info] WHITE set to AI1
[info] Tip: start othello 8 to play with AI (AI is Othello-only)
[info] Black=Guest | White=AI1
```

### 6.2 在非 Othello 游戏中尝试使用 AI（会被重置）

输入：
```
seat white ai1
start gomoku 8
who
quit
```

实际输出摘录：
```
[info] WHITE set to AI1
[info] Started gomoku size 8 (AI seats reset to human)
[info] Black=Guest | White=Guest
```

---

## 7. Othello：AI 自动走子（Human-AI）

输入：
```
start othello 8
hint off
seat white ai1
play 2 3
quit
```

实际输出摘录（示例）：
```
[info] WHITE set to AI1
[info] AI will move automatically on its turns.
...
[info] Move (2,3); flipped 1
[info] Move (...); flipped ...
```

检查点：
- 人类落子后，应立刻出现 AI 的落子信息（无需用户再次输入 `play`）。
- AI 的落子必须始终合法（可用 `moves` 辅助人工核对）。

---

## 8. 录像与回放：save + replay（next/prev/jump/exit）

输入：
```
start othello 8
hint off
play 2 3
save replay_othello
replay replay_othello
next
prev
jump 0
exit
quit
```

实际输出摘录：
```
[info] Saved to saves/replay_othello.json ...
[info] Tip: replay replay_othello
[info] Replay othello 0/...: start
[info] Replay othello 1/...: Black Move (2,3); flipped 1
[info] Exited replay mode
```

检查点：
- `replay` 进入回放模式后，命令集变为 `next/prev/jump/exit/quit`。
- 信息行会尽量显示每一步的坐标，以及 Othello 的翻转数（flipped N）。

---

## 9. replay：无参数回放上一局 + 非法存档名

输入：
```
start gomoku 8
hint off
play 0 0
save lastgame
replay
exit
replay no_such_name
quit
```

实际输出摘录：
```
[info] Saved to saves/lastgame.json ...
[info] Replay gomoku 0/...: start
[info] Exited replay mode
Replay failed: [Errno 2] No such file or directory: 'saves/no_such_name.json'
```

---

## 10. 用户账户：注册/登录/战绩更新/录像关联（手动交互测试）

说明：本节需要在交互终端中手动输入密码（不回显），建议不要用管道喂入。

### 10.1 注册 + 登录

步骤（示例）：
1) 运行：`python3 -m src.main`
2) `register black alice`（输入密码两次）
3) `register white bob`
4) `who`，应显示类似：`Black=alice (0/0) | White=bob (0/0)`

### 10.2 对局结束后战绩自动更新（用 Gomoku 快速结束）

步骤（示例）：
1) `start gomoku 8`
2) 依次输入（让黑方快速连五获胜）：
   - `play 0 0`
   - `play 0 1`
   - `play 1 0`
   - `play 1 1`
   - `play 2 0`
   - `play 2 1`
   - `play 3 0`
   - `play 3 1`
   - `play 4 0`
3) 结束后输入 `who`，应看到：
   - 黑方 `alice`：wins/games 至少为 `1/1`
   - 白方 `bob`：wins/games 至少为 `0/1`

### 10.3 存档与账号录像关联

步骤（示例）：
1) 在任意对局中执行：`save acc_demo`
2) 打开 `saves/accounts.json`，在对应用户条目中检查 `recordings` 是否包含 `saves/acc_demo.json`。

### 10.4 退出登录与错误密码

步骤（示例）：
1) `logout black`
2) `who`：黑方应回到 `Guest`
3) `login white bob` 并输入错误密码：应提示 `Login failed: invalid username or password`

