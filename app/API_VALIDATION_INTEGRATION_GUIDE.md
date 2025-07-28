# Flutter API 验证插件集成指南

## 概述

本指南介绍了如何将 API 格式检查功能完全集成到 Flutter 的 `flutter analyze` 体系中，实现无缝的 API 验证和错误检测。

## 🎯 实现目标

- ✅ 集成到 `flutter analyze` 命令
- ✅ IDE 实时错误提示
- ✅ CI/CD 自动化检查
- ✅ OpenAPI 规范验证
- ✅ 自定义 lint 规则

## 📁 项目结构

```
app/
├── tools/analyzer_plugin/          # 分析器插件
│   ├── bin/plugin.dart            # 插件入口
│   ├── lib/
│   │   ├── api_validator_plugin.dart    # 主插件类
│   │   ├── utils/openapi_loader.dart    # OpenAPI 加载器
│   │   └── rules/                       # 验证规则
│   │       ├── api_path_rule.dart       # 路径验证
│   │       ├── api_schema_rule.dart     # Schema 验证
│   │       └── api_method_rule.dart     # HTTP 方法验证
│   ├── pubspec.yaml               # 插件依赖
│   ├── README.md                  # 插件文档
│   ├── activate_plugin.dart       # 激活脚本
│   └── test_plugin.ps1           # 测试脚本
├── analysis_options.yaml          # 分析器配置
├── openapi.json                   # API 规范文档
└── lib/example/api_test.dart      # 测试示例
```

## 🔧 核心组件

### 1. 分析器插件 (`ApiValidatorPlugin`)

主要功能：
- 加载 OpenAPI 规范
- 注册验证规则
- 处理文件分析事件
- 生成错误报告

### 2. 验证规则

#### API 路径规则 (`ApiPathRule`)
- 检查 API 路径是否在 OpenAPI 文档中定义
- 支持参数化路径匹配
- 验证 `http`、`dio` 和自定义 `ApiService` 调用

#### Schema 验证规则 (`ApiSchemaRule`)
- 验证数据模型是否符合 OpenAPI Schema
- 检查必需字段
- 验证字段类型兼容性

#### HTTP 方法规则 (`ApiMethodRule`)
- 验证 HTTP 方法是否被端点支持
- 检查 RESTful 约定
- 支持多种 HTTP 客户端库

### 3. OpenAPI 加载器 (`OpenApiSpec`)
- 解析 OpenAPI 3.x 文档
- 提供路径匹配功能
- 支持 Schema 引用解析

## ⚙️ 配置说明

### analysis_options.yaml

```yaml
include: package:flutter_lints/flutter.yaml

analyzer:
  plugins:
    - tools/analyzer_plugin
  exclude:
    - tools/analyzer_plugin/**

linter:
  rules:
    # API 验证相关错误级别
    api_path_not_found: warning
    api_method_not_supported: warning
    api_schema_mismatch: warning
    
    # 其他常见错误
    avoid_print: error
    prefer_const_constructors: warning
    unused_import: error
```

### 插件依赖 (pubspec.yaml)

```yaml
name: api_validator_plugin
description: Flutter API 格式检查插件
version: 1.0.0

environment:
  sdk: '>=3.0.0 <4.0.0'

dependencies:
  analyzer: ^6.0.0
  analyzer_plugin: ^0.11.0
  path: ^1.8.0

dev_dependencies:
  test: ^1.21.0
  lints: ^3.0.0

analyzer_plugin:
  entry_point: bin/plugin.dart
```

## 🚀 使用方法

### 1. 命令行使用

```bash
# 运行完整分析
flutter analyze

# 只检查特定文件
flutter analyze lib/services/api_service.dart

# 详细输出
flutter analyze --verbose
```

### 2. IDE 集成

插件会自动集成到支持 Dart Analysis Server 的 IDE 中：
- VS Code (Dart 扩展)
- IntelliJ IDEA / Android Studio
- Vim/Neovim (coc-flutter)

### 3. CI/CD 集成

```yaml
# GitHub Actions 示例
name: API Validation
on: [push, pull_request]

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: subosito/flutter-action@v2
      - run: flutter pub get
      - run: flutter analyze --fatal-warnings
```

## 📝 验证示例

### 错误示例（会被检测）

```dart
// ❌ 未定义的 API 路径
await http.get(Uri.parse('https://api.example.com/undefined/path'));

// ❌ 不支持的 HTTP 方法
await http.delete(Uri.parse('https://api.example.com/users'));

// ❌ Schema 不匹配
final user = {'name': 'John'}; // 缺少必需的 'email' 字段
await dio.post('/users', data: user);
```

### 正确示例

```dart
// ✅ 正确的 API 调用
await http.get(Uri.parse('https://api.example.com/users'));

// ✅ 符合 Schema 的数据
final user = {
  'name': 'John',
  'email': 'john@example.com',
  'age': 30,
};
await dio.post('/users', data: user);
```

## 🔍 测试验证

### 运行插件测试

```powershell
# Windows PowerShell
cd tools/analyzer_plugin
powershell -ExecutionPolicy Bypass -File test_plugin.ps1
```

### 手动验证步骤

1. 创建包含错误 API 调用的测试文件
2. 运行 `flutter analyze` 检查警告
3. 在 IDE 中查看实时错误提示
4. 修复错误后验证警告消失

## 📋 配置要求

### OpenAPI 文档要求

- 支持 OpenAPI 3.0+ 规范
- 必须包含完整的路径定义
- Schema 定义应包含必需字段标记
- 建议包含详细的操作描述

### 环境要求

- Flutter SDK 3.0+
- Dart SDK 3.0+
- 支持 Dart Analysis Server 的 IDE

## 🛠️ 故障排除

### 常见问题

1. **插件未加载**
   - 检查 `analysis_options.yaml` 配置
   - 确认插件路径正确
   - 重启 IDE 或 Analysis Server

2. **OpenAPI 文档未找到**
   - 确认 `openapi.json` 文件存在
   - 检查文件格式是否正确
   - 验证 JSON 语法

3. **验证规则不生效**
   - 检查错误级别配置
   - 确认文件未被排除
   - 查看 Analysis Server 日志

### 调试方法

```bash
# 启用详细日志
flutter analyze --verbose

# 检查 Analysis Server 状态
dart language-server --help
```

## 🔄 扩展开发

### 添加新的验证规则

1. 在 `lib/rules/` 目录创建新规则文件
2. 实现 `LintRule` 接口
3. 在 `ApiValidatorPlugin` 中注册规则
4. 更新 `analysis_options.yaml` 配置

### 自定义错误消息

```dart
AnalysisError.tmp(
  source: source,
  errorCode: AnalysisErrorType.LINT,
  location: location,
  message: '自定义错误消息：API 路径未定义',
  correction: '请检查 OpenAPI 文档中的路径定义',
);
```

## 📊 性能优化

- OpenAPI 文档缓存
- 增量分析支持
- 异步处理大文件
- 内存使用优化

## 🎉 总结

通过本插件，您可以：

1. **无缝集成**：完全融入 Flutter 开发工作流
2. **实时反馈**：IDE 中即时显示 API 错误
3. **自动化检查**：CI/CD 流程中自动验证
4. **标准化开发**：确保 API 调用符合规范
5. **提高质量**：减少运行时 API 错误

插件已成功改造并兼容到 Flutter analyzer 格式检查体系中，为您的项目提供强大的 API 验证能力！