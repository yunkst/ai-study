# AI Study Flutter App

这是一个基于Flutter开发的刷题应用，可以从后端API获取题目进行练习。

## 功能特性

- 用户登录认证
- 按学科浏览题目
- 刷题练习（选择题）
- 实时答案验证
- 答题统计和结果展示
- 题目解析查看

## 技术栈

- Flutter 3.8.1+
- Dart
- HTTP网络请求
- Material Design UI

## 项目结构

```
lib/
├── main.dart                 # 应用入口
├── services/
│   └── api_service.dart      # API服务层
└── screens/
    ├── home_screen.dart      # 主页面（学科列表）
    ├── login_screen.dart     # 登录页面
    └── quiz_screen.dart      # 刷题页面
```

## 安装和运行

### 前置要求

1. 安装Flutter SDK (3.8.1或更高版本)
   - 下载地址：https://flutter.dev/docs/get-started/install
   - 确保Flutter命令在PATH环境变量中

2. 安装Android Studio或VS Code（推荐）

3. 确保后端服务正在运行（默认地址：http://localhost:8000）

### 运行步骤

1. 安装依赖：
```bash
flutter pub get
```

2. 检查Flutter环境：
```bash
flutter doctor
```

3. 连接设备或启动模拟器

4. 运行应用：
```bash
flutter run
```

### 开发模式

```bash
# 热重载开发
flutter run --hot

# 调试模式
flutter run --debug

# 发布模式
flutter run --release
```

## API配置

应用默认连接到 `http://localhost:8000` 的后端服务。如需修改，请编辑 `lib/services/api_service.dart` 文件中的 `baseUrl` 常量。

```dart
static const String baseUrl = 'http://localhost:8000';
```

## 使用说明

1. **登录**：启动应用后，点击登录按钮输入用户名和密码，或点击"跳过登录"进入测试模式

2. **选择学科**：在主页面选择要练习的学科

3. **开始刷题**：
   - 阅读题目内容
   - 选择答案选项
   - 点击"提交答案"查看结果
   - 查看解析（如果有）
   - 继续下一题或完成练习

4. **查看结果**：完成所有题目后查看正确率和统计信息

## 故障排除

### 常见问题

1. **网络连接错误**
   - 确保后端服务正在运行
   - 检查API地址配置是否正确
   - 确保设备/模拟器可以访问localhost

2. **Flutter命令不可用**
   - 确保Flutter SDK已正确安装
   - 检查PATH环境变量配置
   - 重启终端/命令提示符

3. **依赖安装失败**
   - 检查网络连接
   - 尝试使用镜像源：`flutter pub get --verbose`
   - 清理缓存：`flutter clean && flutter pub get`

### 调试技巧

- 使用 `flutter logs` 查看实时日志
- 使用 `flutter inspector` 调试UI
- 在代码中添加 `print()` 语句进行调试

## 开发计划

- [ ] 添加题目收藏功能
- [ ] 实现错题本
- [ ] 添加学习进度跟踪
- [ ] 支持多种题型（填空题、判断题等）
- [ ] 添加离线模式
- [ ] 实现推送通知

## 贡献

欢迎提交Issue和Pull Request来改进这个项目。

## 许可证

本项目采用MIT许可证。
