# Flutter API格式检查插件使用指南

## 概述

本插件为Flutter应用提供了完整的API格式检查解决方案，确保所有API调用都符合OpenAPI规范。插件包含以下组件：

- **运行时验证器** (`ApiValidator`) - 在应用运行时验证API请求和响应
- **HTTP拦截器** (`ApiInterceptor`) - 自动拦截和验证所有HTTP请求
- **静态代码分析器** (`FlutterApiAnalyzer`) - 分析Dart代码中的API调用
- **命令行工具** (`api_analyzer_cli.dart`) - 独立的分析工具
- **CI/CD集成** - GitHub Actions工作流和Git钩子

## 功能特性

### ✅ 运行时验证
- 自动验证所有HTTP请求和响应
- 支持参数化路径匹配
- 详细的错误日志和调试信息
- 可配置的验证模式（开发/生产）

### ✅ 静态代码分析
- 检查API路径是否在OpenAPI文档中定义
- 验证数据模型是否符合schema定义
- 识别无效的HTTP方法调用
- 生成详细的分析报告

### ✅ 开发工具集成
- VS Code任务集成
- Git pre-commit钩子
- GitHub Actions CI/CD
- 命令行工具

## 安装配置

### 1. 文件结构

确保项目包含以下文件：

```
lib/
├── utils/
│   ├── api_validator.dart      # 运行时验证器
│   ├── api_interceptor.dart    # HTTP拦截器
│   └── flutter_api_analyzer.dart # 静态分析器
├── tools/
│   └── api_analyzer_cli.dart   # 命令行工具
└── services/
    └── api_service.dart        # API服务（已集成验证）

assets/
└── openapi.json               # OpenAPI规范文档

.vscode/
└── tasks.json                 # VS Code任务配置

.github/workflows/
└── api-validation.yml         # GitHub Actions工作流

.githooks/
└── pre-commit                 # Git pre-commit钩子
```

### 2. 依赖配置

在 `pubspec.yaml` 中添加：

```yaml
dependencies:
  http: ^1.1.0

assets:
  - assets/openapi.json
```

### 3. 应用初始化

在 `main.dart` 中初始化验证器：

```dart
import 'package:flutter/foundation.dart';
import 'utils/flutter_api_analyzer.dart';
import 'services/api_service.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  // 初始化API服务（包含验证器）
  await ApiService.initialize();
  
  // 在调试模式下启用静态分析器
  if (kDebugMode) {
    await FlutterApiAnalyzer.initialize('assets/openapi.json');
  }
  
  runApp(MyApp());
}
```

## 使用方法

### 1. 运行时验证

验证器会自动拦截所有通过 `ApiService` 发出的HTTP请求：

```dart
// 这个请求会被自动验证
final response = await ApiService.get('/api/v1/subjects');

// 如果请求不符合OpenAPI规范，会在控制台输出警告
```

### 2. 静态代码分析

#### 命令行使用

```bash
# 分析整个lib目录
dart run lib/tools/api_analyzer_cli.dart

# 分析指定文件
dart run lib/tools/api_analyzer_cli.dart lib/services/api_service.dart

# 生成报告文件
dart run lib/tools/api_analyzer_cli.dart --output report.txt

# 详细模式
dart run lib/tools/api_analyzer_cli.dart -v

# 自定义OpenAPI文档路径
dart run lib/tools/api_analyzer_cli.dart -o custom_openapi.json
```

#### VS Code集成

1. 打开命令面板 (`Ctrl+Shift+P`)
2. 选择 "Tasks: Run Task"
3. 选择以下任务之一：
   - "Flutter: API规范检查" - 检查整个项目
   - "Flutter: API规范检查 (当前文件)" - 检查当前文件
   - "Flutter: 生成API规范报告" - 生成详细报告

### 3. Git集成

#### 启用pre-commit钩子

```bash
# 复制钩子到Git目录
cp .githooks/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit

# 或者配置Git使用自定义钩子目录
git config core.hooksPath .githooks
```

#### 跳过验证（紧急情况）

```bash
# 跳过pre-commit检查
git commit --no-verify -m "紧急修复"
```

### 4. CI/CD集成

GitHub Actions会在以下情况自动运行：
- 推送到main或develop分支
- 创建Pull Request
- 修改Dart文件或OpenAPI文档

## 配置选项

### 1. 验证模式

在 `ApiService.initialize()` 中配置：

```dart
// 严格模式 - 验证失败时抛出异常
await ApiService.initialize(validationMode: ValidationMode.strict);

// 警告模式 - 验证失败时仅输出警告（默认）
await ApiService.initialize(validationMode: ValidationMode.warning);

// 禁用模式 - 完全禁用验证
await ApiService.initialize(validationMode: ValidationMode.disabled);
```

### 2. 日志配置

```dart
// 启用详细日志
ApiInterceptor.enableVerboseLogging = true;

// 禁用验证日志
ApiInterceptor.enableValidationLogging = false;
```

### 3. 自定义OpenAPI路径

```dart
// 使用自定义OpenAPI文档
await ApiValidator.initialize('assets/custom_openapi.json');
```

## 错误处理

### 常见错误类型

1. **无效API路径**
   ```
   ❌ 无效的API路径: GET /api/v1/invalid-endpoint
   💡 请检查OpenAPI文档中是否定义了此路径
   ```

2. **未定义数据模型**
   ```
   ❌ 未定义的数据模型: CustomModel
   💡 请在OpenAPI文档的components/schemas中定义此模型
   ```

3. **请求体验证失败**
   ```
   ❌ 请求体验证失败: 缺少必需字段 'username'
   💡 请检查请求体是否符合schema定义
   ```

### 调试技巧

1. **启用详细日志**
   ```dart
   ApiInterceptor.enableVerboseLogging = true;
   ```

2. **检查OpenAPI文档**
   ```bash
   # 验证OpenAPI文档格式
   npx @apidevtools/swagger-parser validate assets/openapi.json
   ```

3. **使用命令行工具调试**
   ```bash
   dart run lib/tools/api_analyzer_cli.dart -v
   ```

## 最佳实践

### 1. 开发流程

1. **API设计阶段**
   - 先定义OpenAPI规范
   - 使用工具验证规范的正确性

2. **开发阶段**
   - 启用运行时验证
   - 定期运行静态分析

3. **提交代码前**
   - 运行完整的API规范检查
   - 确保所有验证都通过

4. **CI/CD阶段**
   - 自动运行验证
   - 生成分析报告

### 2. 团队协作

1. **统一OpenAPI规范**
   - 保持前后端OpenAPI文档同步
   - 使用版本控制管理API变更

2. **代码审查**
   - 检查API调用是否符合规范
   - 确保新增的API都有对应的文档

3. **持续改进**
   - 定期更新OpenAPI文档
   - 优化验证规则和错误提示

## 故障排除

### 1. 验证器初始化失败

**问题**: `API分析器初始化失败`

**解决方案**:
- 检查 `assets/openapi.json` 文件是否存在
- 验证OpenAPI文档格式是否正确
- 确保 `pubspec.yaml` 中已配置assets

### 2. 静态分析无结果

**问题**: 命令行工具没有输出任何结果

**解决方案**:
- 检查目标路径是否正确
- 确保Dart文件中包含API调用
- 使用 `-v` 参数查看详细输出

### 3. CI/CD失败

**问题**: GitHub Actions中API验证失败

**解决方案**:
- 检查Flutter版本是否兼容
- 确保所有依赖都已正确安装
- 查看详细的错误日志

## 扩展开发

### 1. 自定义验证规则

```dart
class CustomApiValidator extends ApiValidator {
  @override
  bool validateCustomRule(String path, String method) {
    // 实现自定义验证逻辑
    return true;
  }
}
```

### 2. 添加新的分析器

```dart
class CustomAnalyzer {
  static void analyzeCustomPattern(String line, int lineNumber) {
    // 实现自定义分析逻辑
  }
}
```

### 3. 集成其他工具

- **Swagger Codegen**: 自动生成API客户端代码
- **OpenAPI Generator**: 生成文档和测试用例
- **Postman**: 导入OpenAPI规范进行API测试

## 总结

这个Flutter API格式检查插件提供了完整的解决方案，确保API调用的一致性和正确性。通过运行时验证、静态分析和CI/CD集成，可以在开发的各个阶段捕获API规范违规问题，提高代码质量和开发效率。

建议在项目开始时就集成这个插件，并建立相应的开发流程和团队规范，以最大化其效益。