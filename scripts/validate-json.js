#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

const outputDir = path.join(__dirname, '..', 'luojia-math-tutor', 'references', 'output');
const files = fs
  .readdirSync(outputDir)
  .filter((file) => file.endsWith('.json'))
  .sort();

let failed = false;

for (const file of files) {
  const fullPath = path.join(outputDir, file);
  try {
    const parsed = JSON.parse(fs.readFileSync(fullPath, 'utf8'));
    const count = Array.isArray(parsed) ? parsed.length : Object.keys(parsed).length;
    console.log(`OK ${file} (${count} records)`);
  } catch (error) {
    failed = true;
    console.error(`FAIL ${file}: ${error.message}`);
  }
}

if (failed) {
  process.exitCode = 1;
}
