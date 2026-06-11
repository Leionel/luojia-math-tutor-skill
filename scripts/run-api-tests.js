const fs = require("fs");
const path = require("path");
const { spawnSync } = require("child_process");

const root = path.resolve(__dirname, "..");
const apiDir = path.join(root, "apps", "api");
const venvPython = process.platform === "win32"
  ? path.join(apiDir, ".venv", "Scripts", "python.exe")
  : path.join(apiDir, ".venv", "bin", "python");
const python = fs.existsSync(venvPython)
  ? venvPython
  : process.platform === "win32"
    ? "python"
    : "python3";

const result = spawnSync(
  python,
  ["-m", "pytest", ...process.argv.slice(2)],
  {
    cwd: apiDir,
    stdio: "inherit",
  },
);

if (result.error) {
  console.error(result.error.message);
  process.exit(1);
}

process.exit(result.status ?? 1);
