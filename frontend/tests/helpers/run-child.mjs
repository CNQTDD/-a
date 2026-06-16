import { spawn } from "node:child_process";

const [script, ...args] = process.argv.slice(2);

if (!script) {
  console.error("Expected a script path.");
  process.exit(1);
}

const child = spawn(process.execPath, [script, ...args], {
  stdio: "inherit",
  windowsHide: true,
});

let shuttingDown = false;

function shutdown(signal) {
  if (shuttingDown) {
    return;
  }
  shuttingDown = true;
  child.kill(signal);
  setTimeout(() => process.exit(0), 1000).unref();
}

process.on("SIGTERM", () => shutdown("SIGTERM"));
process.on("SIGINT", () => shutdown("SIGINT"));

child.on("exit", (code, signal) => {
  if (signal) {
    process.exit(1);
    return;
  }
  process.exit(code ?? 0);
});
