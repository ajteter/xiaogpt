# xiaogpt

用小爱音箱接入大模型对话。这个仓库基于 `xiaogpt 3.23` 做了实际可运行和可部署的整理，重点围绕以下目标：

- Gemini 可用
- Gemini 原生 Google Search 可用
- 小米登录更现实，优先支持 `passToken`
- 本地监听能长期跑，不因单次异常直接退出
- Docker 常驻部署可用

## 当前实现

- Gemini 原生 Google Search grounding
- bot 懒加载，避免未使用依赖拖垮启动
- `cookie` 真正参与登录，而不是只做轮询 cookie
- 新增 `passToken` 登录路径
- 为 `aiohttp` 显式挂 `certifi`
- 小米设备控制加了异常兜底和熔断降级
- Gemini 请求加了超时和有限重试
- 提供配置健康检查脚本，适配本地和 Docker

## 推荐登录方式

优先级：

1. `passToken`
2. `cookie`
3. `account/password`

### passToken

需要：

- `mi_user_id`
- `mi_device_id`
- `pass_token`
- `mi_did`
- `hardware`

这是当前实际跑通监听和播报的推荐路径。

### cookie

需要：

- `cookie`
- `mi_did`
- `hardware`

并且 `cookie` 至少包含：

- `deviceId`
- `userId`
- `serviceToken`

### account/password

代码仍支持，但小米风控经常导致失败。除非你明确验证过这条链路可用，否则不建议作为生产配置。

## 运行要求

- Python `>=3.9,<3.13`
- 一台已联网、可被小米云控制的小爱设备
- 已确认的 `hardware`
- 已确认的 `mi_did`
- 对应模型 API key

## 安装

```bash
pip install -r requirements.txt
```

## 配置

从示例文件开始：

```bash
cp xiao_config.yaml.example xiao_config.yaml
```

### passToken 示例

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
gemini_google_search: true
gemini_api_domain: "https://generativelanguage.googleapis.com"

tts: "mi"
stream: true
mute_xiaoai: true
keyword:
  - "请"
```

### cookie 示例

```yaml
hardware: "LX05A"
mi_did: "384696888"

cookie: "deviceId=...; userId=...; serviceToken=..."

bot: "gemini"
gemini_key: "your-gemini-key"
gemini_google_search: true
tts: "mi"
stream: true
mute_xiaoai: true
```

## 配置自检

启动前建议先跑：

```bash
python3 scripts/healthcheck.py --config xiao_config.yaml
```

通过时输出：

```text
ok
```

## 本地启动

```bash
python3 xiaogpt.py --config xiao_config.yaml
```

或：

```bash
python3 -m xiaogpt --config xiao_config.yaml
```

## Gemini Search

启用 Gemini 原生搜索：

```yaml
bot: "gemini"
gemini_key: "your-key"
gemini_google_search: true
```

如果没显式指定 `gemini_model`：

- 普通模式默认 `gemini-2.0-flash-lite`
- 搜索模式默认 `gemini-2.0-flash`

如果你自己已经确认更高版本模型支持搜索，也可以直接在配置里指定，例如：

```yaml
gemini_model: "gemini-3-flash-preview"
```

## 稳定性说明

当前代码已补这些加固：

- 单轮处理失败不会退出整个监听进程
- 后台轮询失败会自动继续重试
- 小米播放状态/静音/唤醒失败会自动降级，避免持续打挂
- Gemini 非 4xx 网络错误会做有限重试
- 空流式响应不会导致崩溃
- `verbose` 日志不再直接打印明文凭证

## Docker

### 准备配置

```bash
mkdir -p config
cp xiao_config.yaml.example config/xiao_config.yaml
python3 scripts/healthcheck.py --config xiao_config.yaml.example --allow-template
```

### 构建

```bash
docker build -t xiaogpt:local .
```

### 运行

```bash
docker run --rm \
  --network host \
  -v "$(pwd)/config:/config" \
  -e XIAOGPT_PORT=9527 \
  xiaogpt:local
```

### Compose

```bash
docker compose up --build -d
```

看日志：

```bash
docker compose logs -f
```

停止：

```bash
docker compose down
```

## Docker 注意事项

1. 推荐 `tts: mi`，最省事，不依赖容器内音频文件 HTTP 服务暴露给音箱。
2. 如果你用 `edge` / `fish` / `openai` 这类本地 HTTP 音频转发 TTS，要确认音箱能访问容器地址和端口。
3. `network_mode: host` 在 Linux 上最直接；在 macOS Docker Desktop 上要额外确认局域网访问链路。
4. 镜像和 compose 都带了健康检查，但它只校验配置完整性，不代表你的小米登录态一定有效。

## 常见排查顺序

1. `scripts/healthcheck.py` 是否通过
2. `pass_token` / `cookie` 是否仍有效
3. `mi_user_id` / `mi_device_id` / `pass_token` 是否同源
4. `mi_did` 是否正确
5. `hardware` 是否正确
6. `gemini_key` 是否可用
7. Python 是否为 `3.9` 到 `3.12`

## 安全建议

不要提交这些文件或内容到仓库：

- `xiao_config.yaml`
- `config/`
- `cookie`
- `pass_token`
- API key
