# 班级德育学分座次选择系统部署指南

本文档覆盖本项目在 Windows 本地开发环境和基础生产环境下的部署方式，包含后端、前端、数据库初始化、默认账号、构建发布和常见故障排查。

## 1. 项目结构

- 后端目录：`app`
- 前端目录：`frontend`
- 数据库文件：`seating_choice.db`
- 数据库初始化脚本：`init_db.py`

## 2. 环境要求

### 后端

- Python 3.10+
- 建议使用项目自带虚拟环境，或自行创建新的 `venv`

### 前端

- Node.js 18+
- npm 9+

## 3. 首次部署

### 3.1 安装后端依赖

在项目根目录执行：

```powershell
cd D:\seating_choice_ol
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

如果 PowerShell 提示脚本执行被限制，可先执行：

```powershell
Set-ExecutionPolicy -Scope Process Bypass
```

### 3.2 安装前端依赖

```powershell
cd D:\seating_choice_ol\frontend
npm install
```

### 3.3 初始化数据库

回到项目根目录执行：

```powershell
cd D:\seating_choice_ol
.\.venv\Scripts\python.exe init_db.py
```

初始化完成后会自动创建默认管理员：

- 用户名：`admin`
- 密码：`admin123456`

可用环境变量覆盖默认管理员信息：

- `ADMIN_USERNAME`
- `ADMIN_PASSWORD`
- `ADMIN_FULL_NAME`

## 4. 环境变量

### 4.1 后端 `.env`

项目根目录可创建 `.env` 文件：

```env
DATABASE_URL=sqlite:///./seating_choice.db
SECRET_KEY=replace-with-a-strong-random-string
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=720
CORS_ORIGINS=["*"]
```

说明：

- `DATABASE_URL` 默认使用 SQLite
- 生产环境必须修改 `SECRET_KEY`
- 如需限制跨域，生产环境不要使用 `["*"]`

### 4.2 前端 `.env`

在 `frontend` 目录创建 `.env`：

```env
VITE_API_BASE_URL=http://localhost:8000
```

如果后端不在本机，改成实际访问地址，例如：

```env
VITE_API_BASE_URL=http://192.168.1.20:8000
```

## 5. 开发环境启动

### 5.1 启动后端

在项目根目录执行：

```powershell
cd D:\seating_choice_ol
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

启动后可访问：

- Swagger 文档：<http://127.0.0.1:8000/docs>
- OpenAPI JSON：<http://127.0.0.1:8000/openapi.json>

### 5.2 启动前端

在前端目录执行：

```powershell
cd D:\seating_choice_ol\frontend
npm run dev
```

当前前端固定端口为：

- <http://127.0.0.1:5173>

登录页地址：

- <http://127.0.0.1:5173/login>

## 6. 生产构建

### 6.1 构建前端

```powershell
cd D:\seating_choice_ol\frontend
npm run build
```

构建产物输出到：

- `frontend/dist`

你可以将 `dist` 部署到 Nginx、IIS、静态文件服务器，或临时使用：

```powershell
npm run preview
```

### 6.2 启动后端服务

生产环境建议使用固定地址启动：

```powershell
cd D:\seating_choice_ol
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

如果需要局域网访问：

- 放行 `8000` 端口
- 前端 `VITE_API_BASE_URL` 改为后端实际 IP
- 浏览器访问前端部署地址

## 7. 推荐部署顺序

每次全新部署或迁移时，建议按下面顺序执行：

1. 拉取代码
2. 安装后端依赖
3. 安装前端依赖
4. 配置根目录 `.env`
5. 配置 `frontend/.env`
6. 执行 `init_db.py`
7. 启动后端并确认 `/docs` 可访问
8. 启动前端并确认 `/login` 可访问
9. 使用默认管理员登录
10. 登录后台后创建学生、学期、轮次、座位布局

## 8. 部署后验证清单

### 8.1 后端验证

确认以下地址可正常打开：

- `GET /docs`
- `GET /openapi.json`

确认登录接口正常：

- `POST /auth/login`
- `GET /auth/me`

### 8.2 前端验证

确认以下流程正常：

1. 打开登录页
2. 使用 `admin / admin123456` 登录
3. 能跳转到管理员后台
4. 输入错误密码时会出现错误提示
5. 进入“座位图管理”可以新建布局

## 9. 管理员首次使用建议

建议首次进入后台后按下面顺序操作：

1. 在“学生管理”中添加学生或导入学分
2. 在“座位图管理”中创建教室布局
3. 创建学期与选座轮次
4. 在“选座控制台”准备队列并开启选座
5. 在“系统设置”中调整系统参数

## 10. 常见问题排查

### 10.1 登录页点了没反应

优先检查：

1. 前端是否打开了正确端口：`5173`
2. 后端是否运行在：`8000`
3. `frontend/.env` 中 `VITE_API_BASE_URL` 是否正确
4. 浏览器是否仍打开旧页面，如 `5174` 或 `5175`

### 10.2 默认账号登录失败

依次检查：

1. 是否执行过 `init_db.py`
2. 根目录是否存在 `seating_choice.db`
3. 数据库里是否已存在 `admin`
4. 是否曾手动改过 `ADMIN_PASSWORD`

如果需要重建默认管理员，可先备份数据库，再重新初始化。

### 10.3 前端提示请求失败或超时

通常是以下原因：

- 后端未启动
- 后端端口不是 `8000`
- 前端请求地址配置错误
- 浏览器仍缓存旧前端页面

处理方式：

1. 重启后端
2. 重启前端
3. 浏览器强制刷新
4. 清理旧标签页，仅保留 `5173`

### 10.4 座位图新建布局没有反应

优先检查：

1. 当前登录角色是否为管理员
2. 浏览器网络面板是否发出了 `POST /admin/layouts`
3. 后端是否返回了 `200`
4. 页面是否连接到了旧前端端口

### 10.5 Swagger 能打开但前端登录失败

这通常说明：

- 后端正常
- 前端访问了错误的 API 地址
- 前端本地缓存了旧 token 或旧页面

建议：

1. 删除浏览器本地存储中的旧登录信息
2. 确认前端运行在 `5173`
3. 确认接口请求发往 `8000`

## 11. 本次联调确认结果

本项目当前已确认：

- `admin / admin123456` 可成功登录
- 登录后可进入管理员后台
- “座位图管理”页面可成功新建布局
- 前端开发服务固定为 `5173`
- 后端接口可正常响应 `8000`

## 12. 建议的长期部署方式

如果后续要给老师和学生长期使用，建议进一步补充：

- 将 SQLite 切换到 PostgreSQL
- 使用反向代理统一前后端域名
- 为后端配置进程守护
- 将 `SECRET_KEY` 改为高强度随机值
- 收紧 CORS 白名单
