# 多租户服务器部署说明 · MVStudio Multi-Tenant Deployment

> 把单用户本地 app 改成对外多租户服务器的部署记录。代码在仓库,系统级配置
> (`/etc/nginx`、`/etc/systemd/system`、`ufw`)不在仓库,以本文为准。
> 最近更新:2026-08-04。

---

## 架构一句话

```
公网 :80  ──►  nginx (0.0.0.0:80, 唯一公网监听)  ──►  uvicorn (127.0.0.1:8787, 仅回环)
                                                        └─ create_app() 多用户工厂模式
```

app **只**监听 `127.0.0.1:8787`,永不直接对外;nginx 是唯一公网入口。

## 五条需求 → 实现映射

| 需求 | 实现 |
|---|---|
| ① 注册界面(用户名+密码) | 前端登录门 `apps/mv_api/static/index.html#auth-gate`;`POST /api/v1/auth/register` |
| ② 每用户自己配 key(不共享) | 每用户 `ApplicationService`,`registry.py` 建服务时 `read_process_env=False`;`control_plane.default_runtime_config` 不再从 `os.environ` 播种 key |
| ③ 每用户独立数据区 | `~/.local/share/mvstudio/users/<user_id>/` 每人一个 workspace |
| ④ 并发 | 单进程单事件循环,阻塞调用走 `run_in_threadpool`;每用户 supervisor 一把 `RLock` |
| ⑤ 对外 80 端口 | nginx 反代 + ufw 放行 |

## 鉴权硬约束(务必保持)

**不读本地 `.env`,provider key 只来自用户自己在设置页填的配置。** 新用户 key 为空,
系统绝不回退到 `.env` 或任何共享公钥。实现:多用户模式下 `read_process_env=False`,
凭据只从各用户 workspace 配置读;`control_plane.config_to_environ()` 返回的 dict 只含
用户填了值的 key。

**注册邀请码:硬编码 `jenny`**(`apps/mv_api/auth.py`)。错码/缺码一律拒绝注册。
临时方案,不做成可配置。

---

## 数据位置

- BASE:`~/.local/share/mvstudio/`(`default_workspace_root()`,可被 `MV_WORKSPACE_ROOT` 覆盖)
- 鉴权库:`BASE/auth.sqlite3`(用户 scrypt 哈希 + 会话 token;**已 gitignore,绝不入库**)
- 每用户 workspace:`BASE/users/<user_id>/`
- 旧单用户遗留 `BASE/projects/`、`BASE/models/` 与多用户互不相干,保留未动

---

## systemd 服务

`/etc/systemd/system/mvstudio.service`:

```ini
[Unit]
Description=MVStudio multi-user API (uvicorn on loopback:8787, public via nginx:80)
After=network.target

[Service]
Type=simple
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/case-study
Environment=PYTHONUNBUFFERED=1
Environment=PYTHONPATH=/home/ubuntu/case-study
ExecStart=/home/ubuntu/case-study/.venv/bin/python -m uvicorn apps.mv_api:create_app --factory --host 127.0.0.1 --port 8787
Restart=always
RestartSec=2

[Install]
WantedBy=multi-user.target
```

`create_app()` 不带参数即多用户模式(鉴权中间件开启)。`--factory` 让 uvicorn 调用它。

## nginx 反向代理

`/etc/nginx/sites-available/mvstudio`(软链到 `sites-enabled/`,已删 `default` 站点):

```nginx
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _;

    client_max_body_size 1g;          # 项目素材/文件夹上传走请求体

    location / {
        proxy_pass http://127.0.0.1:8787;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # SSE (/api/v1/jobs/*/events):不缓冲,保持长连接
        proxy_buffering off;
        proxy_cache off;
        proxy_set_header Connection '';
        proxy_read_timeout 3600s;
        proxy_send_timeout 3600s;
    }
}
```

## 防火墙

ufw 默认 DROP,已放行:`sudo ufw allow 80/tcp`(原本只放行 22)。

---

## 运维命令

```bash
sudo journalctl -u mvstudio -f          # 看 app 日志(排查用)
sudo systemctl restart mvstudio         # 重启 app
sudo systemctl stop mvstudio            # 停 app
sudo nginx -t && sudo systemctl reload nginx   # 改 nginx 配后
```

访问:`http://192.144.235.54/`,注册邀请码 `jenny`。

---

## 未决 / 注意事项

- **云厂商安全组**:VM 之外的防火墙是否放行 80,需在控制台确认(机器内无法验证)。
- **HTTP 明文**:当前裸 HTTP,密码/key 明文传输。临时方案可接受;长期用应加 HTTPS。
- **restart 端点**:app 的 `/api/v1/system/restart` 用 `os.execv` 原地替换进程镜像,
  PID 不变,systemd 无感;真崩溃则 `Restart=always` 拉起。
- 停用的 MoneyPrinterTurbo 遗留 ufw 规则 `8080/tcp # MPT backend` 现无进程监听,无害,未清理。
