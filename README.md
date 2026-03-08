# error-memory-memory
An automatically running error memory system that can be used with any AI, such as Claude Code or Kimi Code.
第 1 层: Shell 自动捕获 (终端级)
  ↓ source shell_integration.sh → 任何失败命令自动记录
  ↓ 不依赖任何 AI 工具

第 2 层: AI Hook 自动捕获 (AI 工具级)
  ↓ Claude Code: PostToolUse hook 自动触发
  ↓ 其他 AI: 复制 AI_INSTRUCTIONS.md 到对应配置

第 3 层: AI 指令驱动 (对话级)
  ↓ 遇到错误 → 先查询历史 → 解决后记录 → 形成闭环


把 AI_INSTRUCTIONS.md 的内容复制到 你使用的ai工具的 的指令配置/自定义指令设置里即可。

在终端中启用自动捕获
source error-memory-memory/shell_integration.sh

加到 ~/.bashrc 中就永久生效。


自动工作流规则：
规则 1: 遇到错误时 → 先查询历史
规则 2: 解决错误后 → 记录到知识库
规则 3: 已有记录但方案更好 → 更新记录



已修复bug
hook 对成功命令误报	Bash exit_code=0 时不再检查 error keywords；新增 _has_structured_error() 只匹配 Traceback 等明确错误结构
2	NOISE_PATTERNS 永远不匹配	重构为 is_noise_command() 匹配命令名（grep/test/diff）+ is_noise_response() 匹配响应内容
3	query 污染 entry 对象	使用 entry.copy() 避免修改原始数据
4	delete 后空标签残留	delete() 现在自动清除空标签数组；清理了 index.json 中的 4 个空标签
5	Zsh 语法在 Bash 中报错	用 $ZSH_VERSION 变量检测替代 Zsh 专属 ${(%):-%x} 语法
6	并发写入数据损坏	memory_store.py 的 _save_index 和 _save_entry 添加了 file_lock() 文件锁
7	去重 load/save 竞态	合并为原子操作 check_and_mark_duplicate()，一次读写
8	CLI 与 auto_record_v2 去重不共享	统一使用 .recent_hashes.json 文件，两个系统共享去重状态，避免同一错误双重记录
9	exec 不支持管道/重定向	命令列表拼接为字符串，shell=True 执行
10	缺少 delete 命令	新增 delete/rm 子命令，带确认提示
11	查询太弱	支持多关键词 AND 搜索（"blender render" → 两个词都必须匹配），按相关度得分排序
12	exit code 检测不健壮	多位置检测（顶层字段、tool_response 内、文本正则），Bash 还额外检测 Python Traceback
