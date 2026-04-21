const { spawnSync } = require("child_process");
const fs = require("fs");
const path = require("path");

const repoRoot = path.resolve(__dirname, "..", "..");
const dashboardDir = path.join(repoRoot, "dashboard");
const sourceDir = path.join(dashboardDir, "dist");
const targetDir = path.join(repoRoot, "desktop-app", "dashboard-dist");

function copyDirectory(source, destination) {
  fs.mkdirSync(destination, { recursive: true });
  for (const entry of fs.readdirSync(source, { withFileTypes: true })) {
    const sourcePath = path.join(source, entry.name);
    const destinationPath = path.join(destination, entry.name);
    if (entry.isDirectory()) {
      copyDirectory(sourcePath, destinationPath);
    } else {
      fs.copyFileSync(sourcePath, destinationPath);
    }
  }
}

const buildCommand = process.platform === "win32" ? "cmd.exe" : "npm";
const buildArgs = process.platform === "win32" ? ["/c", "npm", "run", "build"] : ["run", "build"];
const result = spawnSync(buildCommand, buildArgs, {
  cwd: dashboardDir,
  stdio: "inherit",
});

if (result.error) {
  console.error(result.error.message);
  process.exit(1);
}

if (result.status !== 0) {
  process.exit(result.status || 1);
}

if (!fs.existsSync(sourceDir)) {
  console.error(`Dashboard build output was not found at ${sourceDir}`);
  process.exit(1);
}

fs.rmSync(targetDir, { recursive: true, force: true });
copyDirectory(sourceDir, targetDir);

console.log(`Orbit renderer prepared at ${targetDir}`);
