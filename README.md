# ai_learn

一个最小可用的 AI 问答 Demo：Vue 3 + TypeScript + Element Plus 前端，FastAPI + SQLAlchemy 后端，会话与消息落 SQLite。

## 目录结构

```text
ai_learn/
├── frontend/                 Vue 3 + TypeScript + Element Plus
│   ├── src/
│   │   ├── api/              统一 HTTP 出口（只请求 /api）
│   │   ├── components/       问题输入、回答区域、会话列表
│   │   ├── views/            问答页编排
│   │   ├── types/            前端类型定义
│   │   └── utils/            时间与空输入文案
│   ├── vite.config.ts        /api 代理到 FastAPI
│   └── package.json
├── backend/                  FastAPI + SQLAlchemy
│   ├── app/
│   │   ├── main.py           应用入口、CORS、建表
│   │   ├── config.py         环境变量配置
│   │   ├── database.py       引擎与会话
│   │   ├── models.py         ChatSession / Message
│   │   ├── schemas.py        Pydantic 出入参
│   │   ├── llm.py            模型调用（仅后端持有密钥）
│   │   └── routers/          会话接口、问答接口
│   ├── requirements.txt
│   └── .env.example
└── .gitignore
```

## 启动后端

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate    macOS / Linux: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env      # Windows；macOS / Linux 用 cp
uvicorn app.main:app --reload --port 8000
```

首次启动自动创建 `backend/ai_learn.db`。接口文档在 <http://127.0.0.1:8000/docs>。

`.env` 三种可选配置：

- 真实模型（按量付费）：`MIMO_BASE_URL=https://api.xiaomimimo.com/v1`、`MIMO_MODEL=mimo-v2.6-flash`（或 `mimo-v2.6-pro`）、`MIMO_API_KEY` 填 `sk-` 开头的 key。
- Token Plan 订阅：`MIMO_BASE_URL` 用以订阅页为准的 `https://token-plan-cn.xiaomimimo.com/v1`，key 是 `tp-` 开头；它和按量付费的 key 不能混用。
- 演示模式：`MOCK_LLM=true`，不调用外部模型，直接返回固定回答。

`MIMO_BASE_URL` 写到 `/v1` 这一级即可，代码会自动拼 `/chat/completions`。

## 启动前端

```bash
cd frontend
npm install
npm run dev
```

打开 <http://localhost:5173>。开发服务器把 `/api` 代理到 `http://127.0.0.1:8000`，所以浏览器不跨域、也不直连模型。

构建与类型检查：

```bash
npm run type-check
npm run build
```

## 问答页的三块结构

1. **问题输入**（`ChatInput.vue`）：textarea、发送按钮、空输入提示；Enter 发送，Shift + Enter 换行，输入法选词时不会误发。
2. **回答区域**（`ChatAnswer.vue`）：加载中、成功回答、模型不可用三种状态；回答按 Markdown 渲染，支持标题、列表、表格、引用、代码高亮与一键复制；失败时可用同一个问题重试。
3. **会话列表**（`SessionList.vue`）：按最近更新时间倒序，展示时间与消息数，支持切换和删除。

## 页面边界

前端只调用后端 `/api`：模型密钥、SQLAlchemy、SQLite 全部留在后端，浏览器里没有任何模型地址或数据库连接。

## 接口

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/sessions` | 会话列表（按更新时间倒序，含消息条数） |
| POST | `/api/sessions` | 新建空会话 |
| GET | `/api/sessions/{id}` | 会话详情与全部消息 |
| DELETE | `/api/sessions/{id}` | 删除会话及其消息 |
| POST | `/api/chat` | 提交问题，返回会话 id、标题与回答 |
| POST | `/api/chat/stream` | 同上，但按 SSE 逐字返回（前端默认用这个） |
| GET | `/api/prompt` | 读取当前系统提示词与默认值 |
| PUT | `/api/prompt` | 保存系统提示词（1~2000 字） |
| POST | `/api/prompt/reset` | 恢复默认提示词 |
| GET | `/api/health` | 健康检查 |

`POST /api/chat` 请求体：

```json
{ "question": "什么是过拟合？", "session_id": null }
```

`session_id` 为空会新建会话，标题取问题前 20 个字。模型不可用时返回 `503`，且不会写入半条消息。

`/api/chat/stream` 同样接收这份请求体，返回 `text/event-stream`，四种事件：

| 事件 | data | 说明 |
| --- | --- | --- |
| `meta` | `{ session_id, title }` | 会话确定后的首帧 |
| `delta` | `{ text }` | 增量文本，逐字追加到气泡 |
| `done` | `{ session_id, title, answer, message }` | 回答完整落库，`message` 与消息详情结构一致 |
| `error` | `{ detail }` | 模型不可用，`detail` 可直接展示 |

前端点「停止生成」会中断连接：后端把已生成的部分回答落库，不留下空消息；若一个字都没产出，新建的空会话会被清理。

## 系统提示词

左侧栏顶部有「会话 / 提示词」两个切换按钮，主区页头也有一个「提示词」入口。提示词页可以编辑、保存、恢复默认，保存后对下一次提问立即生效。

提示词存在 `app_settings` 表（键 `system_prompt`），每次调用模型时作为 `system` 消息放在最前面，历史消息与用户问题排在其后。未保存过自定义内容时使用内置默认提示词，默认值把这个应用限定成考研助手：

- 只回答择校、各科复习、真题资料、报名复试调剂、备考心态等考研相关问题
- 遇到天气、新闻、娱乐、编程等范围外话题，先用一句话说明只能提供考研帮助，再给出 1~2 个考研问题把用户引回来
- 不编造分数线、报录比等具体数据，不给作弊类建议

想换领域（比如只答编程、只答法律），把提示词整体替换成自己的规则即可，不需要改代码。
