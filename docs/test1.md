# 测试用例（第一阶段：Go / Gomoku）

说明：以下均在项目根目录运行 `python3 -m src.main`，将命令序列通过管道喂入；终端输出摘录核心内容（棋盘、启动首屏、Hints/Tip 文本等均略）。

## 通用/非法输入
输入：
```
play 1 1
foobar
start go 3
start gomoku 25
quit
```
实际输出摘录：
```
Start a game first: start go|gomoku|othello [size]
Tip: type 'help' for examples (e.g. start othello 8)
Start a game first: start go|gomoku|othello [size]
Tip: type 'help' for examples (e.g. start othello 8)
Start failed: Board size must be between 8 and 19
Start failed: Board size must be between 8 and 19
```

## Gomoku：连五取胜
输入：
```
start gomoku 8
play 0 0
play 0 1
play 1 0
play 0 2
play 2 0
play 0 3
play 3 0
play 0 4
play 4 0
quit
```
实际输出摘录：
```
[info] Started gomoku size 8
...
[info] Move (0,4)
...
[info] BLACK wins by five in a row
[result] BLACK wins by five in a row
```

## Gomoku：悔棋 + 存档/读档 + 认输
输入：
```
start gomoku 8
play 0 0
undo
play 0 0
save g1
load g1
resign
quit
```
实际输出摘录：
```
[info] Started gomoku size 8
[info] Move (0,0)
[info] Undone
[info] Move (0,0)
[info] Saved to saves/g1.json  (use 'load g1' or 'load' to restore)
[info] Loaded gomoku from saves/g1.json
[info] BLACK wins by resignation
[result] BLACK wins by resignation
```

## Gomoku：非法操作与 restart
输入：
```
start gomoku 8
undo
play -1 0
play 8 0
play 0 0
play 0 0
pass
quit
```
实际输出摘录：
```
[info] Started gomoku size 8
[info] No move to undo
[info] Move out of bounds
[info] Move out of bounds
[info] Move (0,0)
[info] Position already occupied
[info] Pass not allowed in Gomoku
```

输入：
```
start gomoku 8
play 0 0
restart
play 1 1
restart 10
quit
```
实际输出摘录：
```
[info] Started gomoku size 8
[info] Move (0,0)
[info] Started gomoku size 8
[info] Move (1,1)
[info] Started gomoku size 10
```

## Gomoku：满盘平局（Draw）
输入：
```
start gomoku 8
play 7 1
play 7 6
play 3 2
play 6 2
play 6 6
play 0 6
play 4 5
play 3 6
play 3 3
play 5 4
play 4 4
play 1 1
play 5 7
play 2 5
play 0 0
play 0 4
play 5 0
play 4 2
play 5 2
play 1 6
play 2 4
play 3 1
play 6 4
play 4 1
play 0 7
play 5 5
play 7 2
play 7 7
play 0 1
play 0 2
play 2 1
play 6 5
play 0 3
play 4 0
play 2 2
play 1 0
play 7 4
play 1 2
play 4 3
play 6 3
play 6 0
play 7 5
play 0 5
play 6 1
play 3 4
play 4 6
play 5 1
play 6 7
play 1 4
play 5 3
play 7 0
play 2 3
play 3 0
play 1 7
play 2 6
play 7 3
play 4 7
play 1 5
play 1 3
play 3 7
play 2 7
play 2 0
play 5 6
play 3 5
quit
```
实际输出摘录（省略棋盘中间过程）：
```
...
[info] Draw: board is full
[result] Draw: board is full
```

## Go：提子、双 pass 终局（数子胜局）
输入：
```
start go 8
play 1 1
play 0 1
play 2 1
play 1 0
play 1 2
play 2 0
play 0 0
play 1 3
play 0 2
play 2 2
pass
pass
quit
```
实际输出摘录（中间棋盘略）：
```
[info] Started go size 8
[info] Move (1,1); captured 0
...
[info] Move (0,2); captured 1   # (1,1) 被提
...
[info] Move (2,2); captured 0
[info] Pass
[info] Pass
[result] Black wins 6 vs 4
```

## Go：悔棋 + 存档/读档 + restart
输入：
```
start go 8
play 3 3
undo
play 3 3
save go1
load go1
restart
quit
```
实际输出摘录：
```
[info] Started go size 8
[info] Move (3,3); captured 0
[info] Undone
[info] Move (3,3); captured 0
[info] Saved to saves/go1.json  (use 'load go1' or 'load' to restore)
[info] Loaded go from saves/go1.json
[info] Started go size 8
```

## Go：非法加载与提示开关
输入：
```
load no_such
start go 8
play 0 0
hint off
hint on
quit
```
实际输出摘录：
```
Load failed: [Errno 2] No such file or directory: 'saves/no_such.json'
[info] Started go size 8
[info] Move (0,0); captured 0
[info] Hint off
[info] Hint on
```

## Go：非法操作（无棋可悔、越界、占用）
输入：
```
start go 8
undo
play -1 0
play 8 0
play 0 0
play 0 0
quit
```
实际输出摘录：
```
[info] Started go size 8
[info] No move to undo
[info] Move out of bounds
[info] Move out of bounds
[info] Move (0,0); captured 0
[info] Position already occupied
```
