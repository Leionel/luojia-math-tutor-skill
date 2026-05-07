#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const readline = require('readline');
const { execFileSync } = require('child_process');

const repoUrl = 'https://github.com/Leionel/luojia-math-tutor-skill.git';
const repoPath = 'luojia-math-tutor';
const activationMarker = '# 珞珈助教激活指令';

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

const cursorRulesContent = `
${activationMarker}

1. 立即读取并内化本项目中 \`${repoPath}/SKILL.md\` 的人设与行为准则。
2. 解题时，优先检索 \`${repoPath}/references/\` 下的 JSON/PDF 知识库；使用当前 AI 客户端可用的文件搜索、读取或命令行工具。
3. 默认执行“思路提示 -> 代码验算 -> 分步提问”的启发式工作流；用户明确要求完整解答时，可以给出完整过程。
4. 开启数学建模或特训模式时，严格遵循指定的输出模板。
5. 遇到文献检索、学术配图或深度建模需求时，若环境已安装对应专业技能则优先调用；否则按本技能的简化流程处理并说明能力边界。
`;

const claudeCodeContent = {
  instructions: `请严格遵循当前目录下 ${repoPath}/SKILL.md 中的助教工作流进行数学问题解答。默认采用启发式分步辅导；用户明确要求完整解答时，可以给出完整过程。若需要文献检索、学术配图或深度建模，只有在当前环境已安装对应专业技能时才调用，否则按本技能简化流程处理。`
};

function ensureKnowledgeBase(cwd) {
  const targetDir = path.join(cwd, repoPath);
  const tmpDir = path.join(cwd, '.tmp-luojia');

  if (fs.existsSync(targetDir)) {
    console.log('\x1b[33m%s\x1b[0m', `⚠️ 目录 ${repoPath} 已存在，跳过克隆。`);
    return;
  }

  if (fs.existsSync(tmpDir)) {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  }

  console.log('\n\x1b[36m%s\x1b[0m', '🔄 正在拉取本地知识库 (luojia-math-tutor/)...');
  try {
    execFileSync('git', ['clone', '--depth', '1', repoUrl, tmpDir], { stdio: 'ignore' });
    fs.renameSync(path.join(tmpDir, repoPath), targetDir);
    fs.rmSync(tmpDir, { recursive: true, force: true });
    console.log('\x1b[32m%s\x1b[0m', '✅ 知识库拉取成功。');
  } catch (error) {
    if (fs.existsSync(tmpDir)) {
      fs.rmSync(tmpDir, { recursive: true, force: true });
    }
    throw new Error(`自动拉取知识库失败，请确认已安装 Git，或手动运行：git clone ${repoUrl}`);
  }
}

function appendOnce(existingContent, addition, marker) {
  if (existingContent.includes(marker)) {
    return existingContent;
  }
  return `${existingContent ? `${existingContent.trimEnd()}\n\n` : ''}${addition.trim()}\n`;
}

function writeRules(cwd, filename, content, isJson = false) {
  const targetPath = path.join(cwd, filename);

  if (isJson) {
    let config = {};
    if (fs.existsSync(targetPath)) {
      try {
        config = JSON.parse(fs.readFileSync(targetPath, 'utf-8'));
      } catch (error) {
        throw new Error(`${filename} 不是合法 JSON，请先修复后再重新运行初始化工具。`);
      }
    }

    if (!String(config.instructions || '').includes(repoPath)) {
      config.instructions = config.instructions
        ? `${config.instructions}\n\n${content.instructions}`
        : content.instructions;
    }
    fs.writeFileSync(targetPath, `${JSON.stringify(config, null, 2)}\n`, 'utf-8');
  } else {
    const existingContent = fs.existsSync(targetPath)
      ? fs.readFileSync(targetPath, 'utf-8')
      : '';
    fs.writeFileSync(
      targetPath,
      appendOnce(existingContent, content, activationMarker),
      'utf-8'
    );
  }

  console.log('\x1b[32m%s\x1b[0m', `✅ 成功生成/更新 ${filename}`);
}

function run(answer) {
  const cwd = process.cwd();
  const selected = {
    cursor: ['1', '4'].includes(answer),
    claude: ['2', '4'].includes(answer),
    cline: ['3', '4'].includes(answer)
  };

  if (!selected.cursor && !selected.claude && !selected.cline) {
    console.log('\x1b[31m%s\x1b[0m', '❌ 无效的选择，操作已取消。');
    return;
  }

  ensureKnowledgeBase(cwd);

  if (selected.cursor) writeRules(cwd, '.cursorrules', cursorRulesContent);
  if (selected.claude) writeRules(cwd, '.claudecode.json', claudeCodeContent, true);
  if (selected.cline) writeRules(cwd, '.clinerules', cursorRulesContent);

  console.log('\n\x1b[36m%s\x1b[0m', '🎉 初始化完成！现在可以开始数学辅导、讲题或特训了。');
}

console.log('\x1b[36m%s\x1b[0m', '🎓 欢迎使用 珞珈数智助教 (Luojia Math Tutor) 初始化工具');
console.log('此工具将帮助您在当前项目中快速接入数学 AI 助教能力。\n');
console.log('请选择您使用的 AI 工具：');
console.log('  1: Cursor / Windsurf (.cursorrules)');
console.log('  2: Claude Code (.claudecode.json)');
console.log('  3: Cline / RooCode (.clinerules)');
console.log('  4: 全部都装');

rl.question('\n请输入选项数字 (1-4): ', (answer) => {
  try {
    run(answer.trim());
  } catch (error) {
    console.log('\x1b[31m%s\x1b[0m', `❌ ${error.message}`);
    process.exitCode = 1;
  } finally {
    rl.close();
  }
});
