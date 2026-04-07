# xiaogpt

用小爱音箱接入大模型对话。

这个仓库当前不是原样上游，而是基于 `xiaogpt 3.23` 做了实际可运行、可部署、可继续产品化的整理版本。本文档内容截至 `2026-04-07`，以当前仓库代码和本地实测结果为准。

## 当前状态

这份代码当前已经完成并验证了这些事情：

- Gemini 可用
- Gemini 原生 Google Search 可用
- 小米设备真实监听可启动
- `passToken` 登录路径已真实跑通
- 本地服务已能进入稳定监听状态
- Docker 运行文件已整理
- 仓库已具备后续接 GitHub Actions 构建镜像的基础

## 已实测结论

### 1. 小米登录

当前最推荐的登录方式是：

1. `passToken`
2. `cookie`
3. `account/password`

本次真实跑通使用的是 `passToken` 路线。
获取 `passToken` 方法： https://github.com/Yonsm/MiService/issues/57

需要的字段：

- `mi_user_id`
- `mi_device_id`
- `pass_token`
- `mi_did`
- `hardware`

已经确认：

- 账号密码登录经常被小米风控拦截，不适合作为默认生产方案
- 浏览器普通 cookie 不一定够，真正稳定的依然是 `passToken` 路线
- 当前代码已强制要求只启用一种登录方式，避免配置互相冲突

### 2. Gemini

当前仓库保留并支持 Gemini 原生搜索能力。

配置核心字段：

- `bot: gemini`
- `gemini_key`
- `gemini_model`
- `gemini_google_search`
- `gemini_api_domain`

已经确认：

- `gemini_google_search: true` 时，日志里会输出 `Gemini Google Search queries`
- 多轮 Gemini 历史消息格式已按 Gemini 原生格式修正
- Gemini 请求已补超时和有限重试

### 3. 本地监听服务

当前代码已经真实启动并进入监听状态，出现过如下正常启动日志：

```text
Running xiaogpt now, 用 你个渣渣 开头来提问
或用 开始持续对话 开始持续对话
```

实际对话日志也已确认过：

- 小爱能收到问题
- 项目能拿到 query
- Gemini 能返回回答
- 搜索模式能被触发
- 服务可被正常停止

### 4. 关于“说到一半被打断”

截至目前的判断：

- 这不太像单纯是本项目轮询间隔过短
- 更像是小爱本身的语音输入窗口较短，或者语音分段策略偏激进
- 项目侧确实会在检测到新记录时尽快处理，所以如果小爱把一句话拆成多段，体感上会像“中途被截断”

当前这个结论已经写进文档，但还没有为此进一步改代码策略。

## 当前代码里已经补过的稳定性加固

- bot 懒加载，避免未使用依赖拖垮启动
- `cookie` 不再只是轮询 cookie，而是真正参与登录
- 新增 `passToken` 登录路径
- `aiohttp` 显式使用 `certifi`
- Gemini 请求加超时和有限重试
- 空流式回答不会直接打崩
- 单轮处理异常不会退出整个监听主循环
- 后台轮询异常会继续重试
- 小米播放状态/静音/唤醒/TTS 加了异常兜底
- 小米设备控制加了熔断降级，避免连续超时反复打设备
- `verbose` 日志不再直接打印敏感凭证
- 提供配置健康检查脚本
- 入口支持更干净的停止和退出

## 运行要求

- Python `>=3.9,<3.13`
- 一台已联网且可被小米云控制的小爱设备
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

### 推荐配置示例

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
poll_interval: 3
keyword:
  - "你个渣渣"
```

说明：

- 登录方式三选一，只保留一种，其他留空
- 当前最推荐 `tts: "mi"`
- `mute_xiaoai: true` 适合减少和小爱原回答重叠，但也会让“被新记录打断”的体感更明显
- `poll_interval` 是小爱会话轮询间隔，默认建议可以调到 `3`

## 配置自检

真实配置：

```bash
python3 scripts/healthcheck.py --config xiao_config.yaml
```

示例模板：

```bash
python3 scripts/healthcheck.py --config xiao_config.yaml.example --allow-template
```

通过时输出：

```text
ok
```

## 本地运行

```bash
python3 xiaogpt.py --config xiao_config.yaml
```

或：

```bash
python3 -m xiaogpt --config xiao_config.yaml
```

## Docker

当前仓库已经做了这些 Docker 准备：

- `Dockerfile`
- `docker-compose.yml`
- `.dockerignore`
- 容器健康检查
- 配置挂载目录 `/config`

### 准备配置

```bash
mkdir -p config
cp xiao_config.yaml.example config/xiao_config.yaml
```

编辑：

- `config/xiao_config.yaml`

建议在启动前先本地检查配置：

```bash
python3 scripts/healthcheck.py --config config/xiao_config.yaml
```

### 构建镜像

```bash
docker build -t xiaogpt:local .
```

### 运行容器

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

查看日志：

```bash
docker compose logs -f
```

停止：

```bash
docker compose down
```

## Docker 注意事项

1. 推荐优先使用 `tts: mi`，这样不依赖容器对外提供本地音频文件 HTTP 服务。
2. 如果使用 `edge` / `fish` / `openai` 这类本地 HTTP 音频转发 TTS，要保证音箱能访问容器提供的地址和端口。
3. `network_mode: host` 在 Linux 上最直接。
4. 如果你后面要部署到树莓派，最终目标应优先以 `linux/arm64` 镜像为准。
5. 镜像健康检查当前只检查配置结构，不代表小米登录态一定有效。

## GitHub 与镜像构建现状

当前仓库 `.github/workflows/` 下已经整理为两套面向当前 fork 项目的工作流：

- [ci.yml](/Users/huxiao/Public/GitHub/xiaogpt/.github/workflows/ci.yml)
- [docker.yml](/Users/huxiao/Public/GitHub/xiaogpt/.github/workflows/docker.yml)

它们当前已经具备这些基础：

- 使用 `docker/setup-qemu-action`
- 使用 `docker/setup-buildx-action`
- 支持多架构构建
- 已包含 `linux/amd64,linux/arm64`
- 默认主发布目标是 `GHCR`
- 配置好 Docker Hub secrets 后，可选附加推送到 Docker Hub

这意味着：

- 后续把仓库推到 GitHub 后
- 不需要再保留上游硬编码镜像名
- 可以直接按当前仓库名自动生成镜像标签
- 可以通过 GitHub Actions 自动生成多架构镜像

当前仓库地址：

- `https://github.com/ajteter/xiaogpt`

### GitHub Actions 当前行为

- `ci.yml`
  - 检查格式
  - 安装依赖
  - 校验 CLI
  - 校验模板配置
  - 做一次 Docker build 校验
- `docker.yml`
  - 在 `main/master` push 时发布镜像
  - 在 `v*` tag push 时发布镜像
  - 默认发布到 `ghcr.io/ajteter/xiaogpt`
  - 如果配置了 Docker Hub secrets，额外再发布到 `docker.io/<DOCKERHUB_USERNAME>/<repo-name>`

### 需要配置的 secrets

如果你只用 GHCR：

- GitHub Actions 不需要额外 Docker Hub 凭证
- 推荐直接把 GHCR 作为默认镜像源

如果你还要同时推 Docker Hub：

- `DOCKERHUB_USERNAME`
- `DOCKERHUB_TOKEN`

## 后续目标：GitHub Action -> 镜像 -> 树莓派

你后面的目标链路是：

1. 把当前仓库整理好后推到 GitHub
2. 用 GitHub Action 自动构建 Docker 镜像
3. 生成适用于树莓派的 `arm64` 镜像
4. 在局域网本地树莓派上拉取镜像
5. 通过挂载配置文件运行服务

这个目标和当前仓库状态是对齐的，现阶段还缺的主要不是代码能力，而是发布和部署侧的最后整理：

- 根据树莓派系统确认 `arm64` 还是 `arm/v7`
- 决定树莓派上是否继续使用 `network_mode: host`
- 准备树莓派上的 `config/xiao_config.yaml`

树莓派部署文档见：

- [DEPLOY-RPI.md](/Users/huxiao/Public/GitHub/xiaogpt/DEPLOY-RPI.md)

## 常见排查顺序

1. `scripts/healthcheck.py` 是否通过
2. `pass_token` / `cookie` 是否仍有效
3. `mi_user_id` / `mi_device_id` / `pass_token` 是否同源
4. `mi_did` 是否正确
5. `hardware` 是否正确
6. `gemini_key` 是否可用
7. Python 是否为 `3.9` 到 `3.12`
8. 是否是小爱本身语音输入窗口过短导致 query 被提前截断

## 安全建议

不要提交这些内容到仓库：

- `xiao_config.yaml`
- `config/`
- `cookie`
- `pass_token`
- API key
- 任何真实的小米账号信息

## 接下来建议

如果下一步是为 GitHub 和树莓派做最终准备，推荐顺序是：

1. 先把 README、Docker、健康检查、配置示例全部定稿
2. 再整理 GitHub Actions 的镜像发布策略
3. 最后补一份树莓派部署说明

如果你要，我下一步可以直接继续做这两件事：

- 把 GitHub Actions 调整成适合你自己仓库的镜像发布方案
- 再补一份专门给树莓派用的部署文档
