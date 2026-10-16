# 本地运行

CI 使用 Python 3.12 与 Node.js 24。后端声明 Python ≥3.10，前端声明 Node.js ≥20.9；优先使用 CI 版本复现。所有命令均从仓库根目录开始，除非明确切换目录。

## Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ./apps/api
npm.cmd ci
npm.cmd --prefix apps/web ci
if (!(Test-Path apps/api/.env)) { Copy-Item apps/api/.env.example apps/api/.env }
```

编辑已有 `apps/api/.env`，填入模型服务配置。配置项说明见 [API 示例](../apps/api/.env.example)。示例不含可用密钥；不要覆盖已有配置或提交 `.env`。

分别在两个终端运行 `npm.cmd run dev:api`、`npm.cmd run dev:web`，打开 [Web](http://127.0.0.1:3000)。

如需 Web 改用 3100，API 终端应在启动前设置：

```powershell
$env:CORS_ORIGINS='http://127.0.0.1:3100,http://localhost:3100'
npm.cmd run dev:api
```

Web 终端运行：

```powershell
npm.cmd --prefix apps/web run dev -- --hostname 127.0.0.1 --port 3100
```

API 地址默认 `http://127.0.0.1:8000`。仅当更换 API 地址时，才需要修改前端 `NEXT_PUBLIC_API_BASE_URL`；在 `apps/web/.env.local` 中维护并重启前端。

## Linux / macOS

根目录的部分 npm 脚本调用 Windows 的 `npm.cmd`。其他系统使用以下分步命令：

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e ./apps/api
npm ci
npm --prefix apps/web ci
test -f apps/api/.env || cp apps/api/.env.example apps/api/.env
```

配置模型后，在两个终端分别运行：

```sh
cd apps/api
python -m uvicorn app.main:app --reload --port 8000
```

```sh
npm --prefix apps/web run dev
```

## 配置与数据

| 配置 | 用途 |
| --- | --- |
| `LLM_PROVIDER` / `LLM_BASE_URL` / `LLM_MODEL` / `LLM_API_KEY` | 聊天模型连接；模型名称以实际供应商可用配置为准 |
| `DATABASE_URL` / `COURSE_STORE_PATH` | 学生库与课程库路径，API 从 `apps/api` 启动时相对该目录解析 |
| `CORS_ORIGINS` | 允许访问 API 的 Web 来源，须包含实际协议、主机和端口 |
| `NEXT_PUBLIC_API_BASE_URL` | 浏览器使用的 API 地址；浏览器可见，不能放密钥 |
| `AUTH_REQUIRED` / `AUTH_TOKEN_SECRET` | 身份认证；本地示例不构成生产配置 |

无密钥时，可体验本地数值实验与静态任务，模型生成请求会缺少可用服务。文档解析、语义服务和外部可视化可能还需各自凭证，按实际使用配置。

本地 SQLite 文件、上传资料和密钥都属于忽略内容。正式部署前须在隔离环境验收鉴权、数据迁移、备份和恢复，见[限制](limitations.md)。

## 测试与构建

Windows 使用 README 中的验证命令。其他系统按 CI 分步运行：

```sh
node scripts/validate-json.js
node scripts/export_intelligent_ui_catalog.mjs --check
cd apps/api
python -m pytest -q
cd ../..
npm run test:web:ui
npm --prefix apps/web run typecheck
npm --prefix apps/web run lint
npm --prefix apps/web run build
python scripts/check_docs.py
```

从 `apps/api` 运行 pytest，避免根目录误收集其他脚本；CI 也在该目录执行。运行 `next build` 前先停止使用相同构建目录的开发服务。
