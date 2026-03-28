# Test Generator — Claude Code Slash Command

## 使用方法

在 Claude Code 中输入 `/gen-test` 并指定源代码文件路径即可触发。

---

分析指定源代码文件，自动生成对应的单元测试文件。

## 步骤

1. 读取用户指定的源代码文件，识别编程语言和项目使用的测试框架。
2. 分析代码结构：
   - 提取所有公共方法/函数的签名（参数类型、返回值类型）
   - 识别方法内的条件分支（if/else、switch、try/catch）
   - 识别外部依赖（数据库操作、HTTP 调用、文件 I/O）
3. 为每个公共方法生成测试用例，覆盖以下场景：
   - **正常路径**: 合法输入的预期输出
   - **边界条件**: 空值、空字符串、空集合、最大/最小值
   - **异常处理**: 非法输入、依赖服务异常、超时等
   - **业务规则**: 根据 if/else 分支覆盖不同业务路径
4. 为外部依赖生成 Mock：
   - Java: 使用 Mockito `@Mock` + `when().thenReturn()`
   - Python: 使用 `unittest.mock.patch`
   - JavaScript/TypeScript: 使用 Jest `jest.mock()`
   - Go: 使用 interface mock
5. 输出完整的测试文件，可直接运行。

## 测试命名格式

```
should_[预期行为]_when_[前置条件]
```

示例：
- `should_return_user_when_valid_id_provided`
- `should_throw_exception_when_user_not_found`
- `should_encrypt_password_when_creating_new_user`

## 规则

- 每个测试只验证一个行为，不在单个测试中断言多个不相关逻辑
- 测试数据使用工厂方法或 Builder 构造，不依赖共享的全局测试数据
- 禁止使用 Thread.sleep / setTimeout 等硬等待
- 测试必须可独立运行，不依赖外部服务、数据库、网络
- Mock 的返回值要符合真实业务场景，不使用无意义的 placeholder
- 生成的测试文件放在项目约定的测试目录下（如 src/test/、__tests__/、*_test.go）
