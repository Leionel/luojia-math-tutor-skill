#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const readline = require('readline');

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

console.log('\x1b[36m%s\x1b[0m', '🎓 欢迎使用 珞珈数智助教 (Luojia Math Tutor) 初始化工具');
console.log('此工具将帮助您在当前项目中快速接入硬核数学 AI 助教能力。\n');

const repoUrl = 'https://github.com/Leionel/luojia-math-tutor-skill.git'; // Actual repository URL
const repoPath = 'luojia-math-tutor';

const cursorRulesContent = `
# 珞珈助教激活指令

1. 立即读取并内化本项目中 \`${repoPath}/SKILL.md\` 的人设与行为准则。
2. 解题时，必须优先检索 \`${repoPath}/references/\` 下的 JSON/PDF 知识库。
3. 严格执行“思路提示 -> 代码验算 -> 分步提问”的工作流。
4. 若本地不存在 \`${repoPath}\` 目录，请提示用户从 ${repoUrl} 克隆。
`;

const claudeCodeContent = {
  "instructions": `请严格遵循当前目录下 ${repoPath}/SKILL.md 中的助教工作流进行所有数学问题的解答。若该目录不存在，请提示用户从 ${repoUrl} 克隆。`
};

rl.question('请选择您使用的 AI 工具 (1: Cursor/Windsurf, 2: Claude Code, 3: 两者都要): ', (answer) => {
  const cwd = process.cwd();
  let success = false;

  if (answer === '1' || answer === '3') {
    const cursorPath = path.join(cwd, '.cursorrules');
    let existingContent = '';
    if (fs.existsSync(cursorPath)) {
      existingContent = fs.readFileSync(cursorPath, 'utf-8') + '\n\n';
    }
    fs.writeFileSync(cursorPath, existingContent + cursorRulesContent.trim());
    console.log('\x1b[32m%s\x1b[0m', '✅ 成功生成/更新 .cursorrules');
    success = true;
  }

  if (answer === '2' || answer === '3') {
    const claudePath = path.join(cwd, '.claudecode.json');
    let claudeConfig = {};
    if (fs.existsSync(claudePath)) {
      try {
        claudeConfig = JSON.parse(fs.readFileSync(claudePath, 'utf-8'));
      } catch (e) {
        console.warn('⚠️ 现有的 .claudecode.json 格式不正确，将被覆盖。');
      }
    }
    
    if (claudeConfig.instructions) {
      claudeConfig.instructions += '\n\n' + claudeCodeContent.instructions;
    } else {
      claudeConfig.instructions = claudeCodeContent.instructions;
    }

    fs.writeFileSync(claudePath, JSON.stringify(claudeConfig, null, 2));
    console.log('\x1b[32m%s\x1b[0m', '✅ 成功生成/更新 .claudecode.json');
    success = true;
  }

  if (success) {
    console.log('\n\x1b[36m%s\x1b[0m', '🎉 初始化完成！');
    console.log(`接下来，请确保将知识库克隆到您的项目中：`);
    console.log(`git clone ${repoUrl} ${repoPath}`);
    console.log('\n开始与您的 AI 助教探讨数学问题吧！');
  } else {
    console.log('\x1b[31m%s\x1b[0m', '❌ 无效的选择，操作已取消。');
  }

  rl.close();
});
