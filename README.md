# Irys Eligibility 批量查询脚本

基于多线程与可选代理池的 Irys Eligibility 批量查询工具。读取地址列表，调用 `https://registration.irys.xyz/api/eligibility`，将标准化结果写入 `eligibility_result.jsonl`。

## 安装

- 安装 Python 3.9+
- 安装依赖：

```bash
pip install -r requirements.txt
```

## 使用

1. 在项目根目录准备地址文件 `wallets.txt`，每行一个地址：

```
0x1111...
0x2222...
```

2. 可选：准备代理池 `proxy.txt`（支持两种格式）：

- NST 格式：`ip:port:user:pass`
- 完整代理 URL：`http://user:pass@ip:port`

3. 运行：

```bash
python bot.py
```

## 说明

- 并发默认 `30`，可在代码中调整 `ThreadPoolExecutor(max_workers=30)`。
- 结果输出到 `eligibility_result.jsonl`，每行一条 JSON。
- 代理池为空时自动直连；存在时随机轮询代理。
- 返回数据统一解析为：
  - `status=normal` 正常结构
  - `status=fallback_format` 兼容格式
  - `status=unknown_format` 未知结构
  - `status=network_failed` 网络失败

## 安全

- 请勿将 `wallets.txt`、`proxy.txt` 上传到公共仓库。
- 已在 `.gitignore` 中默认忽略上述敏感文件与运行输出。

## 输出文件

- `eligibility_result.jsonl`：查询结果（地址、代理、解析后的字段）。

## 常见问题

- 代理池为空或不可用：脚本会自动直连并重试。
- 接口返回非 200 或非 JSON：会进入 `unknown_format` 并写入原始数据供复查。
