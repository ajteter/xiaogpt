# xiaogpt

用小爱音箱接入大模型对话。本仓库当前已经实测跑通：

- `Gemini`
- `Gemini + 原生 Google Search grounding`
- 小米音箱真实监听
- `passToken` 登录路径

## 当前状态

这份代码不是原样上游，而是基于 `xiaogpt 3.23` 做了以下实用修正：

- 保留 Gemini 原生 Google Search 能力
- 启动时按需懒加载 bot，避免全局 `langchain` 导入导致启动失败
- 支持 `passToken` 登录
- `cookie` 路径改为真正优先，不再强制先走账号密码登录
- 修复浏览器导出 cookie 的解析问题
- 为 `aiohttp` 显式挂 `certifi`，避免部分本机 Python 环境证书链异常

## 已实测可用的登录方式

当前项目支持三种小米登录方式，推荐优先级如下：

1. `passToken`
2. `cookie`
3. `account/password`

### 1. passToken 登录，当前最推荐

这是这次本地真实跑通使用的方式。

需要提供：

- `mi_user_id`
- `pass_token`
- `mi_device_id`

说明：

- `mi_user_id`：小米账号的 `userId`
- `pass_token`：浏览器 cookie 里的 `passToken`
- `mi_device_id`：浏览器 cookie 里的 `deviceId`

这条路径会先用 `passToken` 向 `account.xiaomi.com` 换取 `micoapi` 的真实登录态，然后再访问小爱音箱相关接口。

### 2. cookie 登录

如果不用 `passToken`，也可以直接提供完整 cookie 字符串。

注意：

- 这里不是任意小米网页 cookie 都行
- 必须是能用于小爱接口的完整 cookie
- 当前代码要求其中至少包含：
  - `deviceId`
  - `userId`
  - `serviceToken`

最稳妥的来源是 README 原方法里那条请求：

- `https://userprofile.mina.mi.com/device_profile/v2/conversation`

### 3. account/password 登录

代码仍然支持，但现实里经常被小米安全验证拦住。

如果你遇到：

- `Exception on login ...: 'userId'`
- `Login failed`

通常不是你密码写错，而是这条旧登录链被风控拦截了。此时直接改走 `passToken` 更现实。

## 运行要求

- Python `>=3.9,<3.13`
- 一台已联网且可正常被小米云控制的小爱音箱
- 音箱 `hardware`
- 音箱 `mi_did`
- 对应模型的 API key

项目当前 `pyproject.toml` 里声明的是：

- `requires-python = ">=3.9,<3.13"`

如果你本机是 Python 3.13，虽然这次仓库代码已经尽量兼容启动，但依赖层面仍不建议把 3.13 当作官方推荐环境。

## 安装

建议在干净虚拟环境里安装依赖。

```bash
pip install -r requirements.txt
```

或者：

```bash
pip install -U --force-reinstall xiaogpt[locked]
```

## 获取 `mi_did`

你需要先确认音箱的 DID。

上游原方法是：

```bash
pip install miservice_fork
export MI_USER=你的小米账号
export MI_PASS=你的小米密码
micli list
```

但现实里这条链路经常因为小米安全验证失败。

当前更实际的做法是：

- 用 `passToken` 路线的工具链拿设备列表
- 或者先从你已有环境里确认 DID

本项目运行时只需要最终把 `mi_did` 填进配置即可。

## 最小配置

推荐从示例文件开始：

```bash
cp xiao_config.yaml.example xiao_config.yaml
```

### passToken 方式示例

```yaml
hardware: "LX05A"
mi_did: "384696888"

mi_user_id: "123456789"
mi_device_id: "wb_xxx"
pass_token: "V1:xxxx"

cookie: ""
account: ""
password: ""

bot: "gemini"
gemini_key: "your-gemini-key"
gemini_model: "gemini-3-flash-preview"
gemini_api_domain: "https://generativelanguage.googleapis.com"
gemini_google_search: true

tts: "mi"
stream: true
mute_xiaoai: true
keyword:
  - "请"
```

### cookie 方式示例

```yaml
hardware: "LX05A"
mi_did: "384696888"

cookie: "deviceId=...; userId=...; serviceToken=..."

bot: "gemini"
gemini_key: "your-gemini-key"
tts: "mi"
stream: true
mute_xiaoai: true
```

## 启动

```bash
python3 xiaogpt.py --config xiao_config.yaml
```

如果安装了入口脚本，也可以：

```bash
xiaogpt --config xiao_config.yaml
```

## 真实运行效果

这次本地实测，项目已能正常进入监听状态：

```text
Running xiaogpt now, 用 你个渣渣 开头来提问
或用 开始持续对话 开始持续对话
```

实测对话流程也已成功：

- 小爱收到语音
- 项目抓到问题
- Gemini 返回回答
- 小爱播报回答

## 触发词与持续对话

- 普通触发词由 `keyword` 决定
- 开始持续对话：`start_conversation`
- 结束持续对话：`end_conversation`

例如：

- `你个渣渣 今天天气怎么样`
- `开始持续对话`

## Gemini 配置

### 基础 Gemini

```yaml
bot: gemini
gemini_key: "your-key"
gemini_model: "gemini-3-flash-preview"
gemini_api_domain: "https://generativelanguage.googleapis.com"
```

### 启用 Gemini 原生 Google Search

```yaml
bot: gemini
gemini_key: "your-key"
gemini_google_search: true
```

说明：

- 未显式指定 `gemini_model` 时
- 普通模式默认是 `gemini-2.0-flash-lite`
- 开启原生搜索时默认是 `gemini-2.0-flash`

也可以通过 `gpt_options` 传生成参数：

```yaml
gpt_options:
  temperature: 0.7
  top_p: 0.9
  max_output_tokens: 1024
```

## 命令行参数

除了原有参数，当前仓库额外支持：

- `--mi_user_id`
- `--mi_device_id`
- `--pass_token`
- `--gemini_google_search`

例如：

```bash
python3 xiaogpt.py \
  --hardware LX05A \
  --mi_did 384696888 \
  --mi_user_id 123456789 \
  --mi_device_id wb_xxx \
  --pass_token 'V1:xxxx' \
  --use_gemini \
  --gemini_key 'your-key' \
  --gemini_google_search \
  --stream \
  --mute_xiaoai
```

## 主要配置项

| 参数 | 说明 |
| --- | --- |
| `hardware` | 小爱音箱型号 |
| `mi_did` | 音箱 DID |
| `account` | 小米账号 |
| `password` | 小米密码 |
| `mi_user_id` | `passToken` 登录所需的 `userId` |
| `mi_device_id` | `passToken` 登录所需的浏览器 `deviceId` |
| `pass_token` | `passToken` 登录所需的 `passToken` |
| `cookie` | 完整小爱接口 cookie，至少要有 `deviceId`、`userId`、`serviceToken` |
| `bot` | 使用的模型类型 |
| `gemini_key` | Gemini API key |
| `gemini_model` | Gemini 模型名 |
| `gemini_google_search` | 是否启用 Gemini 原生 Google Search |
| `gemini_api_domain` | 自定义 Gemini API 域名 |
| `tts` | TTS 类型，默认 `mi` |
| `stream` | 是否启用流式响应 |
| `mute_xiaoai` | 是否先打断小爱原有回答 |
| `keyword` | 唤起词列表 |
| `prompt` | 追加给模型的提示词 |
| `gpt_options` | 传给模型 API 的额外参数 |
| `proxy` | HTTP 代理地址 |

## 当前推荐排错顺序

如果启动失败，优先按这个顺序排查：

1. `passToken` 是否有效
2. `mi_user_id` / `mi_device_id` 是否和 `passToken` 同源
3. `mi_did` 是否正确
4. `hardware` 是否正确
5. `gemini_key` 是否可用
6. Python 版本是否在 `3.9` 到 `3.12`

典型现象：

- `Exception on login ...: 'userId'`
  - 多半是账号密码登录被小米安全验证拦住
- `cookie missing required fields ...`
  - 说明 cookie 里缺 `deviceId`、`userId`、`serviceToken`
- `Login failed`
  - 多半是小米登录态本身无效，不是 Gemini 配置问题

## 与旧版行为的差异

当前仓库相对原始 3.23 的差异主要有：

- Gemini 原生 Google Search 已接入
- bot 改为懒加载，避免未使用 bot 的依赖导入直接拖垮启动
- `cookie` 不再只是“轮询接口 cookie”，而是真正参与启动登录
- 新增 `passToken` 登录路径
- 本机 Python 证书链问题已在代码里兜底

## 示例配置文件

见：

- `xiao_config.yaml.example`

## Docker 部署

当前仓库已经按 Docker 部署做了整理：

- 运行镜像基于 `python:3.12-slim`
- 默认入口是 `python3 xiaogpt.py --config /config/xiao_config.yaml`
- 配置文件通过 volume 挂载到容器内 `/config`

### 1. 准备配置目录

```bash
mkdir -p config
cp xiao_config.yaml.example config/xiao_config.yaml
```

然后编辑：

- `config/xiao_config.yaml`

推荐直接填 `passToken` 路线所需配置：

- `mi_user_id`
- `mi_device_id`
- `pass_token`
- `hardware`
- `mi_did`
- `gemini_key`

### 2. 构建镜像

```bash
docker build -t xiaogpt:local .
```

### 3. 运行容器

```bash
docker run --rm \
  --network host \
  -v "$(pwd)/config:/config" \
  -e XIAOGPT_PORT=9527 \
  xiaogpt:local
```

### 4. 使用 docker compose

仓库已提供：

- `docker-compose.yml`

启动：

```bash
docker compose up --build -d
```

查看日志：

```bash
docker compose logs -f
```

停止：

```bash
docker compose down
```

### Docker 注意事项

1. 建议优先使用 `tts: mi`，这样不依赖容器对外暴露本地音频 HTTP 服务。
2. 如果你使用 `edge` / `fish` / `openai` 这类本地 HTTP 音频转发 TTS，需要确保音箱能访问到容器对外提供的地址与端口。
3. `network_mode: host` 在 Linux 上最直接；如果是 macOS Docker Desktop，请额外确认网络可达性。
4. 不要把真实的 `xiao_config.yaml`、`pass_token`、`cookie` 提交进仓库。

## 注意

1. `passToken`、`cookie`、`account/password` 都属于敏感凭证，不建议直接提交到仓库。
2. 如果你的设备型号不支持当前默认 TTS 方式，可以尝试 `use_command: true`。
3. 当前项目已经实测可运行，但小米侧风控策略随时可能变化。
4. 如果你在全局 Python 环境里跑，依赖污染仍可能影响结果，建议优先用虚拟环境。
