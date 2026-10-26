# LangGraph 故障恢复实验

**并行节点出错后，已经成功的工作会不会再执行一次？**

[直接打开在线演示](https://111111tjb-cell.github.io/langgraph-recovery-lab/)，无需安装即可回放实测事件，并打开完整矩阵。页面展示已有记录；执行新的实验请使用下方 Python 命令。

本项目用两个节点和 SQLite 回答这个问题：先注入失败，再启动新的 Python 进程恢复，检查实际保存的结果和节点调用次数。实验不需要大模型、API key 或外部数据库。

这是 [111111tjb-cell](https://github.com/111111tjb-cell) 维护的独立实验。LangGraph 由 LangChain 与社区维护。候选修复来自实验性 fork，不代表官方发布或认可。

## 快速运行

推荐 Python 3.12。先获取代码，再在项目根目录执行准备和对照实验：

```sh
git clone https://github.com/111111tjb-cell/langgraph-recovery-lab.git
cd langgraph-recovery-lab
python -m recovery_lab prepare
python -m recovery_lab compare
```

第一条命令联网安装固定依赖，分别创建 `.venvs/baseline` 与 `.venvs/candidate`；第二条在本地运行实验。打开输出的 `index.html` 可以选择案例、回放记录的事件、查看源码指纹。旁边还有 JSON、Markdown 和 SVG 报告。

Windows 可以使用 `py -3.12` 替代 `python`。不必激活两套环境，驱动程序会分别调用解释器。

## 怎样理解结果

A（`flaky`）故意在第一次运行时失败，B（`slow`）稍后完成。调用次数保存在独立 SQLite 数据库，LangGraph 检查点保存在另一个数据库。最终状态可能都正确，但执行次数不同：

| 观察 | 含义 |
|---|---|
| `completed-result-lost` | B 已完成但结果没有保存，恢复后再次执行 |
| `completed-result-preserved` | B 的结果被保存，恢复时复用 |
| `unfinished-node-retried` | 异步 B 响应取消、没有完成；恢复时重试符合预期 |
| `unexpected-result` | 结果不属于以上情况，需要检查原始记录 |

`observed-fix` 只表示本次观察到原版丢失结果、候选版正确恢复。原版未复现、两边加载相同实现、运行时中途改变或候选版失败，都会给出其他结论。

## 完整矩阵

```sh
python -m recovery_lab compare --matrix --include-cancelled --repeat 3
```

这里有两个独立维度：

- `--mode sync/async`：用同步 `invoke` 还是异步 `ainvoke` 执行图。
- `--durability exit/sync/async`：在什么时候持久化检查点。

异步执行另有两种取消行为：`finish` 在收到取消后仍完成，`cancel` 响应取消。只有真正完成的工作才有结果可保留。

## 版本和证据

基线为 `langgraph==1.2.17`，候选版固定到 fork 的 `e3263b3742852d4e1576baa60d9307aa0e03f8df`。报告记录实际包版本、两个核心源码文件按 LF 规范化后的 SHA-256，以及是否匹配预期提交。

[首次 GitHub CI](https://github.com/111111tjb-cell/langgraph-recovery-lab/actions/runs/40259639626) 已全部通过：Linux、Windows、macOS 的格式检查和单元测试，以及 Linux、Windows 各 21 项含跨进程恢复的测试、各 18 个矩阵案例。macOS 尚未运行图恢复实验。详细范围见[验证记录](../VALIDATION.md)。

观察自己的环境可以运行：

```sh
python -m recovery_lab run --python /path/to/python --mode sync --durability exit
```

Windows 使用 `Scripts/python.exe`。输出目录必须是新的或空的，已有结果不会覆盖。

## 边界

- 这是并发恢复实验，不是性能基准。注入延迟不能用于宣称加速。
- 进程在保存前被强制结束，仍可能丢失工作。
- 检查点不保证外部操作“恰好一次”。
- 结果只适用于记录的版本、平台和情境。
- 子进程关闭 LangChain/LangSmith tracing。分享 stderr 前检查其中的本地绝对路径。

背景见 [实验解读](interpretation.md)，原问题见 [上游 #9397](https://github.com/langchain-ai/langgraph/issues/9397)。代码和文稿整理使用了 Codex 辅助，实际验证范围单独记录。
