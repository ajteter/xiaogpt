# xiaogpt 启动验证记录

日期：2026-04-07

## 目标

使用当前项目中的 `xiao_config.yaml`，在本地机器上做一次最小启动验证，确认：

- `xiaogpt` 是否能正常启动
- 当前配置是否存在明显字段错误
- 阻塞点是在配置、模型、小米登录，还是运行环境

## 本次使用的关键配置

来自项目根目录 `xiao_config.yaml` 的核心信息：

- `hardware: LX05A`
- `mi_did: 384696888`
- `bot: gemini`
- `gemini_model: gemini-3-flash-preview`
- `gemini_api_domain: https://generativelanguage.googleapis.com`
- `tts: mi`

目标音箱：

- 设备名称：`客厅小爱`
- 局域网 IP：`192.168.50.40`
- 云端模型：`xiaomi.wifispeaker.lx5a`

## 已确认的前置结论

### 1. `mi_did` 已拿到

之前已经通过 `passToken` 路线成功拉取 Xiaomi 设备列表，并确认：

- `192.168.50.40` 对应 DID：`384696888`

因此，本次启动验证不再卡在 “拿 DID” 这一步。

### 2. Gemini 配置字段本身没有明显问题

检查了本机安装的 `xiaogpt` 代码后，确认当前版本支持这些 Gemini 字段：

- `gemini_key`
- `gemini_model`
- `gemini_api_domain`

并且 Gemini 默认模型已经不是旧的 `gemini-pro`，而是：

- `gemini-2.0-flash-lite`

因此，从字段名角度看，当前 YAML 中的 Gemini 配置方向是合理的。

## 实际启动尝试

### 尝试 1：直接调用本机全局 `xiaogpt`

执行：

- `xiaogpt --help`

结果：

- 启动失败
- 失败位置甚至早于配置加载

错误：

```text
ModuleNotFoundError: No module named 'langchain.memory'
```

### 尝试 2：检查本机全局 Python 包状态

确认到本机全局环境中：

- `xiaogpt 3.10`
- `miservice_fork 2.9.3`
- `langchain 1.2.15`
- `langchain-community 0.4.1`

问题在于：

- `xiaogpt 3.10` 代码仍然依赖老版 `langchain` API
- 当前机器上的 `langchain` 已升级到 1.x
- 两者不兼容

### 尝试 3：用临时虚拟环境安装 `xiaogpt[locked]`

目的：

- 避免污染全局环境
- 尝试用上游推荐的锁定依赖方式跑起来

结果：

- 在 Python 3.13 下安装旧依赖时失败
- 失败点出现在旧版 `grpcio` 构建阶段

典型报错：

```text
ModuleNotFoundError: No module named 'pkg_resources'
```

### 尝试 4：用临时虚拟环境手动组合旧版 `langchain`

思路：

- 单独安装 `xiaogpt==3.10`
- 同时强制限制 `langchain<0.1` 和 `langchain-community<0.1`

结果：

- 依赖解析大量回溯
- 老版本栈在 Python 3.13 上兼容性很差
- 没有进入真正的 `xiaogpt` 启动阶段

## 根因判断

本次阻塞点不是 `xiao_config.yaml` 配置本身，而是运行环境。

更准确地说：

- 当前本机是 `Python 3.13.6`
- `xiaogpt 3.10` 属于更老的依赖栈
- 它依赖的 `langchain`、`grpcio`、`numpy` 等旧包与 Python 3.13 的兼容性不理想

因此，这次启动失败的主因是：

- `xiaogpt 3.10 + Python 3.13` 组合不稳定

而不是：

- `hardware` 配错
- `mi_did` 配错
- Gemini 字段写错

## 关于 `cookie` 的额外确认

本次顺手确认了一个很重要的边界：

- `xiaogpt` 配置里的 `cookie` 不是单独的 `passToken`
- 它期待的是可被解析的完整 cookie 字符串

`xiaogpt` 代码里如果走 `cookie` 路线，会从 cookie 中解析至少这些信息：

- `deviceId`
- `serviceToken`
- `userId`

这和我们之前为了“拿设备列表”使用的：

- `passToken -> .mi.json -> mi-service-lite`

不是同一条链路。

## 当前可下的结论

### 已确认可用的部分

- `mi_did` 已确认
- 目标音箱信息已确认
- Gemini 配置字段方向正确
- `passToken` 路线可用于设备发现

### 当前未通过的部分

- `xiaogpt` 本体尚未在本机真正启动成功

### 当前最可能的主阻塞

- 本机 Python 版本过新
- 本机全局依赖与 `xiaogpt 3.10` 不兼容

## 建议的下一步

如果继续验证 `xiaogpt`，推荐优先采用以下路线之一：

1. 在树莓派上单独准备 `Python 3.11` 或 `Python 3.12` 环境
2. 在该环境里安装 `xiaogpt[locked]`
3. 再使用当前项目里的 `xiao_config.yaml` 做启动测试

或者：

1. 在本机额外安装 `Python 3.11` 或 `Python 3.12`
2. 单独创建全新虚拟环境
3. 再重新安装 `xiaogpt[locked]`

## 本次不建议继续做的事

- 不建议继续在本机全局 `Python 3.13` 环境里硬修 `xiaogpt`
- 不建议把启动失败误判为 `Gemini` 配置错误
- 不建议把 `passToken` 直接填进 `xiao_config.yaml` 的 `cookie`

## 参考代码位置

本机已安装的 `xiaogpt` 代码中，和本次判断直接相关的文件包括：

- `xiaogpt` 的旧版 `langchain` 依赖：
  - `/Library/Frameworks/Python.framework/Versions/3.13/lib/python3.13/site-packages/xiaogpt/bot/langchain_bot.py`
- Gemini 配置与模型初始化：
  - `/Library/Frameworks/Python.framework/Versions/3.13/lib/python3.13/site-packages/xiaogpt/bot/gemini_bot.py`
- 小米登录与 `cookie` 处理：
  - `/Library/Frameworks/Python.framework/Versions/3.13/lib/python3.13/site-packages/xiaogpt/xiaogpt.py`
- 配置字段定义：
  - `/Library/Frameworks/Python.framework/Versions/3.13/lib/python3.13/site-packages/xiaogpt/config.py`
