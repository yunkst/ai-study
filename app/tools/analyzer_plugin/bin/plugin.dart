import 'dart:isolate';

import 'package:analyzer_plugin/starter.dart';

import '../lib/api_validator_plugin.dart';

/// Entry point for the API validator analyzer plugin
void main(List<String> args, SendPort sendPort) {
  ServerPluginStarter(ApiValidatorPlugin()).start(sendPort);
}