#!/usr/bin/env node
/**
 * 前端测试运行脚本
 */

const { spawn } = require('child_process')
const path = require('path')
const fs = require('fs')

// 获取命令行参数
const args = process.argv.slice(2)
const command = args[0] || 'test'

// 项目根目录
const projectRoot = __dirname

console.log('🧪 前端测试运行器')
console.log(`📁 工作目录: ${projectRoot}`)
console.log()

// 检查依赖是否安装
if (!fs.existsSync(path.join(projectRoot, 'node_modules'))) {
  console.log('❌ 依赖未安装，请先运行: npm install')
  process.exit(1)
}

// 构建测试命令
let testCommand = 'npm'
let testArgs = []

switch (command) {
  case 'test':
  case 'run':
    testArgs = ['run', 'test:run']
    console.log('🚀 运行全部测试...')
    break
    
  case 'watch':
    testArgs = ['run', 'test:watch']
    console.log('👀 监视模式运行测试...')
    break
    
  case 'ui':
    testArgs = ['run', 'test:ui']
    console.log('🖥️  启动测试UI界面...')
    break
    
  case 'coverage':
    testArgs = ['run', 'test:coverage']
    console.log('📊 运行代码覆盖率测试...')
    break
    
  case 'component':
  case 'components':
    testArgs = ['run', 'test', '--', 'tests/components']
    console.log('🧩 运行组件测试...')
    break
    
  case 'store':
  case 'stores':
    testArgs = ['run', 'test', '--', 'tests/stores']
    console.log('🗃️  运行Store测试...')
    break
    
  case 'api':
    testArgs = ['run', 'test', '--', 'tests/api']
    console.log('🌐 运行API测试...')
    break
    
  case 'unit':
    testArgs = ['run', 'test', '--', '--reporter=verbose']
    console.log('🔧 运行单元测试...')
    break
    
  case 'help':
  case '-h':
  case '--help':
    showHelp()
    process.exit(0)
    break
    
  default:
    // 自定义测试文件或模式
    testArgs = ['run', 'test', '--', args.join(' ')]
    console.log(`🎯 运行自定义测试: ${args.join(' ')}`)
    break
}

console.log()

// 执行测试命令
const testProcess = spawn(testCommand, testArgs, {
  stdio: 'inherit',
  shell: true,
  cwd: projectRoot
})

testProcess.on('close', (code) => {
  console.log()
  
  if (code === 0) {
    console.log('✅ 测试完成！')
    
    if (command === 'coverage') {
      console.log()
      console.log('📊 查看详细报告:')
      console.log(`   HTML覆盖率报告: file://${path.join(projectRoot, 'coverage/index.html')}`)
    }
    
    if (command === 'ui') {
      console.log()
      console.log('🖥️  测试UI已启动，请在浏览器中查看')
    }
  } else {
    console.log('❌ 测试失败！')
    console.log(`   退出码: ${code}`)
  }
  
  process.exit(code)
})

testProcess.on('error', (err) => {
  console.log()
  console.log('❌ 测试执行错误:')
  console.error(err)
  process.exit(1)
})

// 处理中断信号
process.on('SIGINT', () => {
  console.log()
  console.log('🛑 测试被用户中断')
  testProcess.kill('SIGINT')
})

function showHelp() {
  console.log('🧪 前端测试运行器')
  console.log()
  console.log('用法:')
  console.log('  node test-runner.js [命令]')
  console.log('  npm run test:[命令]')
  console.log()
  console.log('命令:')
  console.log('  test, run      运行全部测试（默认）')
  console.log('  watch          监视模式运行测试')
  console.log('  ui             启动测试UI界面')
  console.log('  coverage       运行代码覆盖率测试')
  console.log('  component      运行组件测试')
  console.log('  store          运行Store测试')
  console.log('  api            运行API测试')
  console.log('  unit           运行单元测试')
  console.log('  help           显示帮助信息')
  console.log()
  console.log('示例:')
  console.log('  node test-runner.js                    # 运行全部测试')
  console.log('  node test-runner.js watch              # 监视模式')
  console.log('  node test-runner.js coverage           # 覆盖率测试')
  console.log('  node test-runner.js component          # 组件测试')
  console.log('  npm run test                           # 通过npm运行')
  console.log('  npm run test:ui                        # 启动测试UI')
} 