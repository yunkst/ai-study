# 测试框架配置指南

本项目为前端和后端分别配置了完整的单元测试框架，支持自动化测试、代码覆盖率分析和持续集成。

## 后端测试框架 (pytest)

### 技术栈
- **测试框架**: pytest + pytest-asyncio
- **HTTP测试**: httpx
- **模拟工具**: pytest-mock
- **覆盖率**: pytest-cov
- **数据工厂**: factory-boy

### 项目结构
```
app/backend/
├── tests/
│   ├── __init__.py
│   ├── test_main.py          # 主要API测试
│   ├── test_auth.py          # 认证系统测试
│   └── unit/
│       ├── __init__.py
│       └── test_services.py  # 服务层单元测试
├── conftest.py               # 测试配置和fixture
├── pytest.ini               # pytest配置
└── test_runner.py           # 测试运行脚本
```

### 运行测试
```bash
cd app/backend

# 安装依赖
pip install -r requirements.txt

# 运行全部测试
python test_runner.py

# 运行特定类型测试
python test_runner.py unit      # 单元测试
python test_runner.py api       # API测试
python test_runner.py auth      # 认证测试
python test_runner.py integration # 集成测试

# 代码覆盖率
python test_runner.py coverage

# 直接使用pytest
pytest -v                       # 详细输出
pytest --cov=.                  # 代码覆盖率
pytest -m unit                  # 只运行单元测试
pytest tests/test_auth.py       # 运行特定文件
```

### 测试标记
使用pytest标记来分类测试：
- `@pytest.mark.unit` - 单元测试
- `@pytest.mark.integration` - 集成测试
- `@pytest.mark.api` - API测试
- `@pytest.mark.auth` - 认证相关测试
- `@pytest.mark.db` - 数据库相关测试
- `@pytest.mark.slow` - 慢速测试

### 测试配置
- **测试数据库**: SQLite内存数据库
- **模拟API**: 使用pytest-mock模拟外部API
- **认证测试**: 提供认证fixture和模拟数据
- **覆盖率要求**: 80%

## 前端测试框架 (Vitest)

### 技术栈
- **测试框架**: Vitest + Vue Test Utils
- **环境**: jsdom / happy-dom
- **覆盖率**: @vitest/coverage-v8
- **UI界面**: @vitest/ui

### 项目结构
```
app/frontend/
├── tests/
│   ├── setup.ts              # 测试环境设置
│   ├── utils/
│   │   └── test-utils.ts     # 测试工具函数
│   ├── components/
│   │   └── Home.test.ts      # 组件测试
│   ├── stores/
│   │   └── auth.test.ts      # Store测试
│   └── api/
│       └── index.test.ts     # API测试
├── vitest.config.ts          # Vitest配置
└── test-runner.js           # 测试运行脚本
```

### 运行测试
```bash
cd app/frontend

# 安装依赖
npm install

# 运行测试
npm run test                 # 单次运行全部测试
npm run test:watch           # 监视模式
npm run test:ui              # 启动测试UI界面
npm run test:coverage        # 代码覆盖率

# 使用测试运行器
node test-runner.js          # 全部测试
node test-runner.js watch    # 监视模式
node test-runner.js ui       # UI界面
node test-runner.js coverage # 覆盖率
node test-runner.js component # 组件测试
node test-runner.js store    # Store测试
node test-runner.js api      # API测试

# 直接使用Vitest
npx vitest                   # 监视模式
npx vitest run               # 单次运行
npx vitest --ui              # UI界面
npx vitest --coverage        # 覆盖率
```

### 测试工具
提供了丰富的测试工具函数：
- `mountComponent()` - 组件挂载工具
- `createTestRouter()` - 测试路由器
- `createTestPinia()` - 测试状态管理
- `mockApiResponse()` - 模拟API响应
- `waitFor()` - 异步等待
- `userInput()` - 模拟用户输入

### 测试覆盖率
- **组件测试**: 渲染、交互、事件处理
- **Store测试**: 状态管理、持久化、错误处理
- **API测试**: 请求拦截、响应处理、错误处理
- **覆盖率要求**: 70%

## 持续集成

### GitHub Actions (推荐配置)
```yaml
name: Tests
on: [push, pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          cd app/backend
          pip install -r requirements.txt
      - name: Run tests
        run: |
          cd app/backend
          python test_runner.py coverage

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - name: Install dependencies
        run: |
          cd app/frontend
          npm ci
      - name: Run tests
        run: |
          cd app/frontend
          npm run test:coverage
```

### 本地预提交检查
```bash
# 运行全部测试
cd app/backend && python test_runner.py
cd app/frontend && npm run test:run

# 检查代码覆盖率
cd app/backend && python test_runner.py coverage
cd app/frontend && npm run test:coverage
```

## 最佳实践

### 测试文件命名
- 后端: `test_*.py` 或 `*_test.py`
- 前端: `*.test.ts` 或 `*.spec.ts`

### 测试组织
- 使用描述性的测试类和方法名
- 按功能模块组织测试文件
- 使用setup/teardown管理测试数据

### 模拟和存根
- 模拟外部API调用
- 模拟数据库操作
- 模拟浏览器API

### 断言策略
- 使用明确的断言
- 测试正常流程和异常情况
- 验证副作用和状态变化

## 故障排除

### 常见问题

1. **测试数据库连接问题**
   ```bash
   # 确保测试环境变量正确设置
   export TESTING=true
   ```

2. **前端组件挂载失败**
   ```typescript
   // 确保正确导入测试工具
   import { mountComponent } from '../utils/test-utils'
   ```

3. **API模拟不生效**
   ```typescript
   // 确保在beforeEach中清除模拟
   beforeEach(() => {
     vi.clearAllMocks()
   })
   ```

4. **覆盖率报告问题**
   ```bash
   # 清除旧的覆盖率文件
   rm -rf coverage/ htmlcov/
   ```

### 调试技巧
- 使用 `console.log` 调试测试
- 利用测试UI界面查看详细信息
- 检查测试报告和覆盖率数据
- 单独运行失败的测试进行调试

通过这个完整的测试框架，可以确保代码质量和系统稳定性，支持持续集成和自动化部署。 