# HotScore method

`HotScore = price(25) + volume(25) + catalyst(30) + publisher breadth(20)`.

- Price uses absolute latest-session change versus the immediately prior close.
- Volume uses latest volume divided by the median of the prior 20 completed sessions.
- Catalyst counts linked news/X Evidence and linked events.
- Breadth counts independent publisher groups; reposts do not add breadth.
- Every component is capped and the total is capped at 100.
- No future row can enter the baseline: only rows before the current completed session are used.
- This score ranks editorial investigation opportunities; it is not a buy/sell score.
