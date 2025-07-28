# Flutter API 验证插件

一个集成到 `flutter analyze` 体系中的 API 格式检查插件，提供实时的 API 路径、Schema 和 HTTP 方法验证。

## 功能特性

### 🛣️ API 路径验证
- 检查代码中使用的 API 路径是否在 OpenAPI 文档中定义
- 支持参数化路径匹配（如 `/api/users/{id}`）
- 自动识别 `http.get`、`ApiService.post` 等调用

### 📋 Schema 验证
- 验证数据模型是否符合 OpenAPI Schema 定义
- 检查必需字段和字段类型
- 支持 JSON 序列化/反序列化验证

### 🔧 HTTP 方法验证
- 检查 HTTP 方法是否被 API 端点支持
- RESTful 约定检查
- 方法语义验证（如 GET 不应用于修改操作）

## 安装配置

### 1. 文件结构
```
project/
├── tools/
│   └── analyzer_plugin/
│       ├── bin/
│       │   └── plugin.dart
│       ├── lib/
│       │   ├── api_validator_plugin.dart
│       │   ├── utils/
│       │   │   └── openapi_loader.dart
│       │   └── rules/
│       │       ├── api_path_rule.dart
│       │       ├── api_schema_rule.dart
│       │       └── api_method_rule.dart
│       ├── pubspec.yaml
│       └── README.md
├── assets/
│   └── openapi.json
├── analysis_options.yaml
└── pubspec.yaml
```

### 2. 激活插件
```bash
# 激活插件
dart run tools/analyzer_plugin/activate_plugin.dart

# 激活插件并运行测试
dart run tools/analyzer_plugin/activate_plugin.dart --test
```

### 3. 配置 analysis_options.yaml
```yaml
analyzer:
  plugins:
    - tools/analyzer_plugin
  
  errors:
    api_path_validation: warning
    api_schema_validation: warning
    api_method_validation: warning
```

## 使用方法

### 命令行使用
```bash
# 运行 API 格式检查
flutter analyze

# 检查特定文件
flutter analyze lib/services/api_service.dart

# 详细输出
flutter analyze --verbose
```

### IDE 集成
插件会自动集成到支持 Dart 分析器的 IDE 中：
- **VS Code**: 错误和警告会在问题面板中显示
- **Android Studio**: 错误会在代码编辑器中高亮显示
- **IntelliJ IDEA**: 支持实时错误检测

### 代码示例

#### ✅ 正确的 API 调用
```dart
// 使用已定义的 API 路径和正确的 HTTP 方法
final response = await http.post(
  Uri.parse('/api/v1/auth/login'),
  body: jsonEncode({
    'username': 'user@example.com',
    'password': 'password123',
  }),
);
```

#### ❌ 会产生警告的代码
```dart
// 警告: API路径未定义
final response = await http.get(
  Uri.parse('/api/undefined/endpoint'),
);

// 警告: 不支持的HTTP方法
final response = await http.delete(
  Uri.parse('/api/v1/auth/login'),  // login端点不支持DELETE
);

// 警告: RESTful约定违规
final response = await http.get(
  Uri.parse('/api/v1/users/create'),  // GET不应用于创建操作
);
```

## 验证规则

### API 路径规则 (`api_path_validation`)
- 检查路径是否在 OpenAPI 文档中定义
- 支持路径参数匹配
- 识别常见的 API 调用模式

### Schema 规则 (`api_schema_validation`)
- 验证数据模型字段完整性
- 检查字段类型兼容性
- 验证必需字段

### HTTP 方法规则 (`api_method_validation`)
- 检查方法是否被端点支持
- RESTful 约定检查
- 语义验证

## 配置选项

### 错误级别配置
```yaml
analyzer:
  errors:
    # 设置为 error 会阻止构建
    api_path_validation: error
    
    # 设置为 warning 会显示警告但不阻止构建
    api_schema_validation: warning
    
    # 设置为 info 会显示信息但不影响构建
    api_method_validation: info
```

### 排除特定文件
```yaml
analyzer:
  exclude:
    - lib/generated/**
    - test/**
    - tools/analyzer_plugin/**
```

## OpenAPI 文档要求

插件会自动查找以下位置的 OpenAPI 文档：
1. `assets/openapi.json`
2. `openapi.json`
3. `api/openapi.json`
4. `docs/openapi.json`
5. `../openapi.json`

### OpenAPI 文档示例
```json
{
  "openapi": "3.0.0",
  "info": {
    "title": "API Documentation",
    "version": "1.0.0"
  },
  "paths": {
    "/api/v1/auth/login": {
      "post": {
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
                "$ref": "#/components/schemas/LoginRequest"
              }
            }
          }
        }
      }
    }
  },
  "components": {
    "schemas": {
      "LoginRequest": {
        "type": "object",
        "required": ["username", "password"],
        "properties": {
          "username": {"type": "string"},
          "password": {"type": "string"}
        }
      }
    }
  }
}
```

## 故障排除

### 插件未生效
1. 检查 `analysis_options.yaml` 配置
2. 确保插件依赖已安装：`dart pub get` (在插件目录)
3. 重启 IDE 或分析服务器

### OpenAPI 文档未找到
1. 确认文档路径正确
2. 验证 JSON 格式有效性
3. 检查文档是否包含 `openapi` 字段

### 验证规则过于严格
1. 调整 `analysis_options.yaml` 中的错误级别
2. 使用 `// ignore: rule_name` 忽略特定行
3. 使用 `// ignore_for_file: rule_name` 忽略整个文件

## 开发和扩展

### 添加自定义规则
1. 在 `lib/rules/` 目录创建新规则文件
2. 继承 `ApiValidationRule` 类
3. 在 `api_validator_plugin.dart` 中注册规则

### 规则开发示例
```dart
class CustomApiRule extends ApiValidationRule {
  @override
  Future<List<plugin.AnalysisError>> analyze(
    AnalysisResult analysisResult,
    OpenApiSpec openApiSpec,
  ) async {
    // 实现自定义验证逻辑
    return [];
  }
}
```

## 版本历史

- **1.0.0**: 初始版本，支持基础 API 验证功能

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request 来改进这个插件。