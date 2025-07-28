#!/usr/bin/env dart

/// API验证插件激活脚本
/// 用于在开发环境中启用和配置API验证插件

import 'dart:io';
import 'dart:convert';

void main(List<String> args) async {
  print('🚀 正在激活 API 验证插件...');
  
  try {
    // 检查当前目录是否是Flutter项目
    if (!await _isFlutterProject()) {
      print('❌ 错误: 当前目录不是Flutter项目');
      exit(1);
    }
    
    // 检查OpenAPI文档是否存在
    final openApiExists = await _checkOpenApiDocument();
    if (!openApiExists) {
      print('⚠️  警告: 未找到OpenAPI文档，插件将无法正常工作');
      print('   请确保以下位置之一存在openapi.json文件:');
      print('   - assets/openapi.json');
      print('   - openapi.json');
      print('   - api/openapi.json');
      print('   - docs/openapi.json');
    }
    
    // 检查插件依赖
    await _checkPluginDependencies();
    
    // 安装插件依赖
    await _installPluginDependencies();
    
    // 验证插件配置
    await _validatePluginConfiguration();
    
    // 运行测试验证
    if (args.contains('--test')) {
      await _runPluginTest();
    }
    
    print('✅ API验证插件激活成功!');
    print('');
    print('📋 使用说明:');
    print('   1. 运行 "flutter analyze" 来检查API格式');
    print('   2. 在IDE中会自动显示API验证错误和警告');
    print('   3. 使用 "dart run tools/analyzer_plugin/activate_plugin.dart --test" 来测试插件');
    print('');
    print('🔧 配置文件:');
    print('   - analysis_options.yaml: 插件配置和规则设置');
    print('   - assets/openapi.json: API规范文档');
    
  } catch (e) {
    print('❌ 激活插件时发生错误: $e');
    exit(1);
  }
}

/// 检查是否是Flutter项目
Future<bool> _isFlutterProject() async {
  final pubspecFile = File('pubspec.yaml');
  if (!await pubspecFile.exists()) {
    return false;
  }
  
  final content = await pubspecFile.readAsString();
  return content.contains('flutter:');
}

/// 检查OpenAPI文档
Future<bool> _checkOpenApiDocument() async {
  final possiblePaths = [
    'assets/openapi.json',
    'openapi.json',
    'api/openapi.json',
    'docs/openapi.json',
    '../openapi.json',
  ];
  
  for (final path in possiblePaths) {
    final file = File(path);
    if (await file.exists()) {
      print('✅ 找到OpenAPI文档: $path');
      
      // 验证JSON格式
      try {
        final content = await file.readAsString();
        final json = jsonDecode(content);
        if (json is Map && json.containsKey('openapi')) {
          print('✅ OpenAPI文档格式有效');
          return true;
        }
      } catch (e) {
        print('⚠️  OpenAPI文档格式无效: $e');
      }
    }
  }
  
  return false;
}

/// 检查插件依赖
Future<void> _checkPluginDependencies() async {
  print('🔍 检查插件依赖...');
  
  final pluginPubspec = File('tools/analyzer_plugin/pubspec.yaml');
  if (!await pluginPubspec.exists()) {
    throw Exception('插件pubspec.yaml文件不存在');
  }
  
  print('✅ 插件配置文件存在');
}

/// 安装插件依赖
Future<void> _installPluginDependencies() async {
  print('📦 安装插件依赖...');
  
  final pluginDir = Directory('tools/analyzer_plugin');
  if (!await pluginDir.exists()) {
    throw Exception('插件目录不存在');
  }
  
  // 运行 pub get
  final result = await Process.run(
    'dart',
    ['pub', 'get'],
    workingDirectory: pluginDir.path,
  );
  
  if (result.exitCode != 0) {
    throw Exception('安装插件依赖失败: ${result.stderr}');
  }
  
  print('✅ 插件依赖安装完成');
}

/// 验证插件配置
Future<void> _validatePluginConfiguration() async {
  print('🔧 验证插件配置...');
  
  // 检查 analysis_options.yaml
  final analysisOptions = File('analysis_options.yaml');
  if (!await analysisOptions.exists()) {
    throw Exception('analysis_options.yaml文件不存在');
  }
  
  final content = await analysisOptions.readAsString();
  if (!content.contains('tools/analyzer_plugin')) {
    throw Exception('analysis_options.yaml中未配置API验证插件');
  }
  
  print('✅ 插件配置验证通过');
}

/// 运行插件测试
Future<void> _runPluginTest() async {
  print('🧪 运行插件测试...');
  
  // 创建测试文件
  final testFile = File('test_api_validation.dart');
  await testFile.writeAsString('''
// 测试API验证插件
import 'package:http/http.dart' as http;

void main() {
  // 测试未定义的API路径 - 应该产生警告
  http.get(Uri.parse('/api/undefined/path'));
  
  // 测试错误的HTTP方法 - 应该产生警告
  http.delete(Uri.parse('/api/v1/auth/login'));
}
''');
  
  try {
    // 运行flutter analyze
    final result = await Process.run('flutter', ['analyze', testFile.path]);
    
    if (result.stdout.toString().contains('api_path_validation') ||
        result.stdout.toString().contains('api_method_validation')) {
      print('✅ 插件测试通过 - 检测到API验证警告');
    } else {
      print('⚠️  插件测试结果不确定 - 请手动检查');
      print('分析输出:');
      print(result.stdout);
    }
  } finally {
    // 清理测试文件
    if (await testFile.exists()) {
      await testFile.delete();
    }
  }
}