#!/usr/bin/env dart

/// 简化的插件测试脚本
/// 用于验证插件文件结构和基本功能

import 'dart:io';
import 'dart:convert';

void main() async {
  print('🧪 测试 API 验证插件结构...');
  
  var allTestsPassed = true;
  
  // 测试1: 检查插件文件结构
  print('\n📁 检查插件文件结构...');
  final requiredFiles = [
    'bin/plugin.dart',
    'lib/api_validator_plugin.dart',
    'lib/utils/openapi_loader.dart',
    'lib/rules/api_path_rule.dart',
    'lib/rules/api_schema_rule.dart',
    'lib/rules/api_method_rule.dart',
    'pubspec.yaml',
    'README.md',
  ];
  
  for (final filePath in requiredFiles) {
    final file = File(filePath);
    if (await file.exists()) {
      print('✅ $filePath');
    } else {
      print('❌ $filePath (缺失)');
      allTestsPassed = false;
    }
  }
  
  // 测试2: 检查主项目配置
  print('\n🔧 检查主项目配置...');
  
  // 检查 analysis_options.yaml
  final analysisOptions = File('../../analysis_options.yaml');
  if (await analysisOptions.exists()) {
    final content = await analysisOptions.readAsString();
    if (content.contains('tools/analyzer_plugin')) {
      print('✅ analysis_options.yaml 已配置插件');
    } else {
      print('❌ analysis_options.yaml 未配置插件');
      allTestsPassed = false;
    }
  } else {
    print('❌ analysis_options.yaml 不存在');
    allTestsPassed = false;
  }
  
  // 检查 OpenAPI 文档
  final openApiPaths = [
    '../../assets/openapi.json',
    '../../openapi.json',
    '../../../openapi.json',
  ];
  
  var openApiFound = false;
  for (final path in openApiPaths) {
    final file = File(path);
    if (await file.exists()) {
      print('✅ 找到 OpenAPI 文档: $path');
      
      // 验证JSON格式
      try {
        final content = await file.readAsString();
        final json = jsonDecode(content);
        if (json is Map && json.containsKey('openapi')) {
          print('✅ OpenAPI 文档格式有效');
          openApiFound = true;
          break;
        } else {
          print('⚠️  OpenAPI 文档格式可能无效');
        }
      } catch (e) {
        print('⚠️  OpenAPI 文档解析错误: $e');
      }
    }
  }
  
  if (!openApiFound) {
    print('⚠️  未找到有效的 OpenAPI 文档');
  }
  
  // 测试3: 检查插件代码语法
  print('\n🔍 检查插件代码语法...');
  
  final dartFiles = [
    'lib/api_validator_plugin.dart',
    'lib/utils/openapi_loader.dart',
    'lib/rules/api_path_rule.dart',
    'lib/rules/api_schema_rule.dart',
    'lib/rules/api_method_rule.dart',
  ];
  
  for (final filePath in dartFiles) {
    final file = File(filePath);
    if (await file.exists()) {
      final content = await file.readAsString();
      
      // 基本语法检查
      if (content.contains('import ') && 
          content.contains('class ') && 
          content.contains('{') && 
          content.contains('}')) {
        print('✅ $filePath 语法结构正常');
      } else {
        print('❌ $filePath 语法结构异常');
        allTestsPassed = false;
      }
    }
  }
  
  // 测试4: 检查依赖配置
  print('\n📦 检查依赖配置...');
  
  final pubspecFile = File('pubspec.yaml');
  if (await pubspecFile.exists()) {
    final content = await pubspecFile.readAsString();
    
    final requiredDeps = ['analyzer', 'analyzer_plugin'];
    for (final dep in requiredDeps) {
      if (content.contains(dep)) {
        print('✅ 依赖 $dep 已配置');
      } else {
        print('❌ 依赖 $dep 未配置');
        allTestsPassed = false;
      }
    }
  } else {
    print('❌ pubspec.yaml 不存在');
    allTestsPassed = false;
  }
  
  // 输出测试结果
  print('\n' + '='*50);
  if (allTestsPassed) {
    print('🎉 所有测试通过！插件结构完整。');
    print('');
    print('📋 下一步操作:');
    print('1. 确保 Flutter/Dart 环境已正确安装');
    print('2. 在插件目录运行: dart pub get');
    print('3. 在主项目运行: flutter analyze');
    print('4. 检查 IDE 中是否显示 API 验证警告');
  } else {
    print('❌ 部分测试失败，请检查上述错误。');
    exit(1);
  }
  
  print('');
  print('🔧 手动验证步骤:');
  print('1. 创建包含错误API调用的测试文件');
  print('2. 运行 flutter analyze 检查是否产生警告');
  print('3. 在 IDE 中查看是否显示实时错误提示');
}