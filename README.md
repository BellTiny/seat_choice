# seat\_choice

基于德育学分（或其它任何可以用于排名依据的量化数据）排名的智能选座平台 ，用于中小学班级管理场景，解决传统手动排座的效率问题。完整部署说明见 `DEPLOYMENT.md`。

<br />

<br />

基于 `FastAPI + SQLAlchemy + SQLite` 的后端服务，覆盖以下核心能力：

- 管理员/学生账号与 JWT 认证
- 学期、选座轮次、教室布局、座位状态管理
- 德育学分 JSON 文件导入
- 管理员手动推进选座流程
- 学生轮询选座状态与实时座位图
- 组队选座、换座申请、特殊需求申请
- Webhook 事件通知
- 选座结束后导出 Excel 座次表
- 自动生成 Swagger UI 文档与 OpenAPI JSON

## 1. 启动方式

### 安装依赖

```bash
pip install -r requirements.txt
```

### 初始化数据库

```bash
python init_db.py
```

默认会创建一个管理员账号：

- 用户名：`admin`
- 密码：`admin123456`

可通过环境变量覆盖：

- `ADMIN_USERNAME`
- `ADMIN_PASSWORD`
- `ADMIN_FULL_NAME`

### 启动服务

```bash
uvicorn app.main:app --reload
```

默认访问地址：

- Swagger UI: <http://127.0.0.1:8000/docs>
- OpenAPI JSON: <http://127.0.0.1:8000/openapi.json>

## 2. Swagger 使用说明

启动后打开 `/docs`，先调用 `POST /auth/login` 获取 JWT。

管理员建议使用以下顺序：

1. 创建学生账号：`POST /admin/users`
2. 创建学期：`POST /admin/semesters`
3. 创建教室布局：`POST /admin/layouts`
4. 导入德育学分：`POST /admin/score-import`
5. 创建轮次：`POST /admin/rounds`
6. 准备轮次队列：`POST /admin/rounds/{round_id}/prepare`
7. 开放网站：`POST /admin/rounds/{round_id}/open`
8. 推进当前可选学生：`POST /admin/rounds/{round_id}/advance`

学生常用接口：

1. 登录：`POST /auth/login`
2. 轮询状态：`GET /student/rounds/{round_id}/status`
3. 选座：`POST /student/rounds/{round_id}/choose-seats`
4. 组队邀请：`POST /student/rounds/{round_id}/team-invites`
5. 换座申请：`POST /student/rounds/{round_id}/swap-requests`
6. 特殊需求申请：`POST /student/rounds/{round_id}/special-requests`

## 3. 主要设计说明

### 角色与权限

- 管理员接口统一放在 `/admin`
- 学生接口统一放在 `/student`
- 通过 JWT 令牌和角色校验实现权限隔离

### 轮次流程

- 新轮次准备时，会清空非锁定座位
- 锁定座位会保留并自动写入当前轮次结果
- 系统按最新德育学分生成队列
- 管理员通过接口决定何时轮到下一批学生
- 跳过学生会在补选阶段继续按原顺序补选

### 配置项

`/admin/settings` 用于统一管理以下持久化配置：

- 轮次间隔天数
- 最大换座次数
- 是否必须填写换座理由
- 组队开关与相邻规则
- 特殊需求入口开关
- Webhook URL
- JWT 过期时间

### 文件导出

轮次结束后，可通过：

```text
GET /admin/rounds/{round_id}/export
```

导出 Excel 座次表。

## 4. 开发说明

- 开发数据库默认使用 SQLite
- ORM 使用 SQLAlchemy，后续可替换为 PostgreSQL
- 所有请求/响应模型都会自动出现在 `/docs` 和 `/openapi.json`
  \=======

#

