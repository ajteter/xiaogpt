# Raspberry Pi Deployment

本文档面向当前仓库：

- `https://github.com/ajteter/xiaogpt`

目标链路：

1. GitHub Actions 自动构建镜像
2. 树莓派在局域网内拉取镜像
3. 挂载本地配置文件运行

## 前提

- 树莓派系统建议为 `64-bit`
- Docker 已安装
- Docker Compose 插件已安装
- 树莓派能访问外网
- 树莓派与小爱设备处于可互通的局域网环境

建议先确认架构：

```bash
uname -m
```

常见结果：

- `aarch64`：对应 `linux/arm64`
- `armv7l`：不是当前默认目标，建议尽量使用 64 位系统

## GitHub Action 出镜像

当前仓库工作流：

- `.github/workflows/ci.yml`
- `.github/workflows/docker.yml`

默认镜像发布目标：

- `ghcr.io/ajteter/xiaogpt`

如果你配置了 Docker Hub secrets，还会额外附加发布到：

- `docker.io/<DOCKERHUB_USERNAME>/xiaogpt`

## GitHub 侧需要做的事

### 1. 启用 Actions

确保仓库 Actions 没被禁用。

### 2. 默认不需要 Docker Hub secrets

如果你只用 GHCR，可以跳过 Docker Hub 配置。

### 3. 如果还要同步推 Docker Hub，再配置 secrets

仓库 Secrets and variables -> Actions：

- `DOCKERHUB_USERNAME`
- `DOCKERHUB_TOKEN`

### 4. 触发构建

以下任意一种都会触发：

- push 到 `main`
- push 到 `master`
- push `v*` tag
- 手动运行 `docker.yml`

## 树莓派拉取镜像

### 方案 A：直接用 GHCR

如果镜像是公开的：

```bash
docker pull ghcr.io/ajteter/xiaogpt:latest
```

如果镜像是私有的，需要先登录：

```bash
echo "<YOUR_GITHUB_TOKEN>" | docker login ghcr.io -u <YOUR_GITHUB_USERNAME> --password-stdin
docker pull ghcr.io/ajteter/xiaogpt:latest
```

### 方案 B：用 Docker Hub

```bash
docker pull <DOCKERHUB_USERNAME>/xiaogpt:latest
```

## 准备配置目录

在树莓派上创建目录：

```bash
mkdir -p ~/xiaogpt/config
cd ~/xiaogpt
```

把仓库里的示例配置复制过去：

```bash
cp xiao_config.yaml.example ~/xiaogpt/config/xiao_config.yaml
```

然后编辑：

- `~/xiaogpt/config/xiao_config.yaml`

建议至少填这些：

- `hardware`
- `mi_did`
- `mi_user_id`
- `mi_device_id`
- `pass_token`
- `bot`
- `gemini_key`
- `gemini_model`
- `gemini_google_search`
- `tts`
- `poll_interval`

推荐：

- `tts: "mi"`
- `poll_interval: 3`

## 在树莓派本地校验配置

如果你本地仓库也在树莓派上，可以直接跑：

```bash
python3 scripts/healthcheck.py --config ~/xiaogpt/config/xiao_config.yaml
```

如果树莓派上没有源码仓库，只拉了镜像，可以直接先运行容器验证挂载：

```bash
docker run --rm \
  -v ~/xiaogpt/config:/config \
  ghcr.io/ajteter/xiaogpt:latest \
  python3 scripts/healthcheck.py --config /config/xiao_config.yaml
```

## 运行方式 1：docker run

```bash
docker run -d \
  --name xiaogpt \
  --restart unless-stopped \
  --network host \
  -v ~/xiaogpt/config:/config \
  -e XIAOGPT_PORT=9527 \
  ghcr.io/ajteter/xiaogpt:latest
```

看日志：

```bash
docker logs -f xiaogpt
```

停止：

```bash
docker stop xiaogpt
docker rm xiaogpt
```

## 运行方式 2：docker compose

在树莓派创建 `docker-compose.yml`：

```yaml
services:
  xiaogpt:
    image: ghcr.io/ajteter/xiaogpt:latest
    container_name: xiaogpt
    restart: unless-stopped
    network_mode: host
    init: true
    volumes:
      - ./config:/config
    environment:
      XIAOGPT_PORT: "9527"
```

启动：

```bash
docker compose up -d
```

查看日志：

```bash
docker compose logs -f
```

停止：

```bash
docker compose down
```

## 树莓派上的建议

1. 优先使用 64 位 Raspberry Pi OS。
2. 优先使用 `tts: mi`，这样最少依赖局域网音频回放转发。
3. 如果树莓派和小爱不在同一稳定网络环境，先不要切到非 `mi` 的 TTS。
4. 先用 `poll_interval: 3`，再根据实际体验调整。
5. 如果你通过 GHCR 拉取，建议固定 tag，而不是长期只用 `latest`。

## 常见问题

### 1. 拉不到镜像

先检查：

- Actions 是否真的构建成功
- 镜像是否公开
- GHCR 或 Docker Hub 是否登录

### 2. 容器起来了但服务没监听

检查：

- 配置文件是否真的挂到了 `/config/xiao_config.yaml`
- `pass_token` 是否仍有效
- `mi_did` / `hardware` 是否正确

### 3. 服务能启动但问话常被截断

当前更像是：

- 小爱本身语音输入窗口较短
- 或语音分段比较激进

项目侧可通过 `poll_interval` 调慢轮询，但这不是唯一根因。

## 推荐发布方式

如果这是你自己的长期项目，建议：

1. GHCR 作为默认镜像源
2. Docker Hub 仅作为可选附加镜像源
3. 树莓派固定用 `linux/arm64`
4. `main` 分支推 `latest`
5. 正式版本推 `v*` tag
6. 树莓派上线时优先拉 tag 镜像，而不是长期只跟 `latest`
