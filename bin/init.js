#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const readline = require('readline');
const { execSync } = require('child_process');

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

console.log('\x1b[36m%s\x1b[0m', '🎓 欢迎使用 珞珈数智助教 (Luojia Math Tutor) 初始化工具');
console.log('此工具将帮助您在当前项目中快速接入硬核数学 AI 助教能力。\n');

const repoUrl = 'https://github.com/Leionel/luojia-math-tutor-skill.git';
const repoPath = 'luojia-math-tutor';

const cursorRulesContent = `
# 珞珈助教激活指令

1. 立即读取并内化本项目中 \`${repoPath}/SKILL.md\` 的人设与行为准则。
2. 解题时，必须优先检索 \`${repoPath}/references/\` 下的 JSON/PDF 知识库。
3. 严格执行“思路提示 -> 代码验算 -> 分步提问”的工作流。
4. 开启数学建模或特训模式时，严格遵循指定的输出模板。
5. 若本地不存在 \`${repoPath}\` 目录，请提示用户从 ${repoUrl} 克隆。
`;

const claudeCodeContent = {
  "instructions": `请严格遵循当前目录下 ${repoPath}/SKILL.md 中的助教工作流进行所有数学问题的解答。支持考研特训与数学建模模式。若该目录不存在，请提示用户从 ${repoUrl} 克隆。`
};

console.log('请选择您使用的 AI 工具：');
console.log('  1: Cursor / Windsurf (.cursorrules)');
console.log('  2: Claude Code (.claudecode.json)');
console.log('  3: Cline / RooCode (.clinerules)');
console.log('  4: 全部都装');

rl.question('\n请输入选项数字 (1-4): ', (answer) => {
  const cwd = process.cwd();
  let success = false;

  const writeRules = (filename, content, isJson = false) => {
    const targetPath = path.join(cwd, filename);
    if (isJson) {
        let config = {};
        if (fs.existsSync(targetPath)) {
            try { config = JSON.parse(fs.readFileSync(targetPath, 'utf-8')); } catch (e) { /* ignore */ }
        }
        config.instructions = config.instructions ? config.instructions + '\n\n' + content.instructions : content.instructions;
        fs.writeFileSync(targetPath, JSON.stringify(config, null, 2));
    } else {
        let existingContent = fs.existsSync(targetPath) ? fs.readFileSync(targetPath, 'utf-8') + '\n\n' : '';
        fs.writeFileSync(targetPath, existingContent + content.trim());
    }
    console.log('\x1b[32m%s\x1b[0m', `✅ 成功生成/更新 ${filename}`);
    success = true;
  };

  if (['1', '4'].includes(answer)) writeRules('.cursorrules', cursorRulesContent);
  if (['2', '4'].includes(answer)) writeRules('.claudecode.json', claudeCodeContent, true);
  if (['3', '4'].includes(answer)) writeRules('.clinerules', cursorRulesContent);

  if (success) {
    console.log('\n\x1b[36m%s\x1b[0m', '🔄 正在为您自动拉取本地知识库 (luojia-math-tutor/)...');
    try {
        const targetDir = path.join(cwd, repoPath);
        if (fs.existsSync(targetDir)) {
            console.log('\x1b[33m%s\x1b[0m', `⚠️ 目录 ${repoPath} 已存在，跳过克隆。`);
        } else {
            console.log('\x1b[90m%s\x1b[0m', `执行: git clone ${repoUrl} ./.tmp-luojia`);
            execSync(`git clone ${repoUrl} ./.tmp-luojia`, { stdio: 'ignore' });
            fs.renameSync(path.join(cwd, '.tmp-luojia', repoPath), targetDir);
            fs.rmSync(path.join(cwd, '.tmp-luojia'), { recursive: true, force: true });
            console.log('\x1b[32m%s\x1b[0m', '✅ 知识库拉取成功！');
        }
    } catch (e) {
        console.log('\x1b[31m%s\x1b[0m', '❌ 自动拉取知识库失败，请确保您已安装 Git，或者手动运行：');
        console.log(`git clone ${repoUrl}`);
    }
    
    console.log('\n\x1b[36m%s\x1b[0m', '🎉 初始化彻底完成！开始与您的 AI 助教探讨数学问题吧！');
  } else {
    console.log('\x1b[31m%s\x1b[0m', '❌ 无效的选择，操作已取消。');
  }

  rl.close();
});
