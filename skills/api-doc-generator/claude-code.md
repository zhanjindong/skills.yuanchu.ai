# API Doc Generator — Claude Code Slash Command

## 使用方法

在 Claude Code 中输入 `/api-doc` 并指定 Controller 文件路径或 API 目录即可触发。

---

分析指定的后端接口代码，自动生成完整的 API 文档。

## 步骤

1. 读取用户指定的文件或目录。如果是目录，扫描其中所有 Controller/Router 文件。
2. 识别后端框架（Spring Boot / Express / FastAPI / Gin 等）。
3. 对每个接口提取以下信息：
   - HTTP 方法（GET/POST/PUT/DELETE/PATCH）
   - 请求路径（包含路径参数）
   - 请求参数（Query、Path、Header、Body），包含类型、是否必填、默认值、校验规则
   - 响应体结构和字段说明
   - 认证要求（是否需要登录、权限级别）
4. 生成文档，格式如下：

```markdown
# API Documentation

## [模块名称]

### [接口名称]

[功能描述]

**请求**

`POST /api/v1/users`

| 参数 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| name | body | string | 是 | 用户名，2-50 字符 |
| email | body | string | 是 | 邮箱地址 |

**请求示例**

​```json
{
  "name": "张三",
  "email": "zhang@example.com"
}
​```

**成功响应** `200 OK`

​```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "name": "张三",
    "email": "zhang@example.com"
  }
}
​```

**错误响应**

| 状态码 | code | 说明 |
|--------|------|------|
| 400 | 40001 | 参数校验失败 |
| 409 | 40901 | 用户名已存在 |
```

## 规则

- 参数说明要包含校验规则（长度限制、格式要求等），从 @Valid 注解或 Joi schema 等提取
- 响应示例使用合理的模拟数据，而非空值或 placeholder
- 如果接口需要认证，在文档顶部标注 "需要认证: Bearer Token"
- 按模块/资源分组组织文档，而非按文件顺序
- 如果代码中有 OpenAPI/Swagger 注解，优先从注解提取信息
