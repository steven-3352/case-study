import { mkdir, writeFile } from "node:fs/promises";
import { spawn } from "node:child_process";
import { pathToFileURL } from "node:url";

const args = new Map();
for (let i = 2; i < process.argv.length; i += 2) args.set(process.argv[i], process.argv[i + 1]);

const chromePath = args.get("--chrome");
const htmlPath = args.get("--html");
const outDir = args.get("--out");
const duration = Number(args.get("--duration"));
const fps = Number(args.get("--fps"));
const width = Number(args.get("--width"));
const height = Number(args.get("--height"));
const port = 9333 + Math.floor(Math.random() * 400);
const userDataDir = `/tmp/chrome-w28d01-render-${Date.now()}`;

if (!chromePath || !htmlPath || !outDir || !duration || !fps || !width || !height) {
  throw new Error("missing required arguments");
}

await mkdir(outDir, { recursive: true });

const chrome = spawn(chromePath, [
  "--headless=new",
  "--disable-gpu",
  "--disable-dev-shm-usage",
  "--no-first-run",
  "--hide-scrollbars",
  `--remote-debugging-port=${port}`,
  `--user-data-dir=${userDataDir}`,
  `--window-size=${width},${height}`,
  "about:blank",
], { stdio: ["ignore", "ignore", "pipe"] });

let stderr = "";
chrome.stderr.on("data", (d) => { stderr += d.toString(); });

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function getJson(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`${res.status} ${url}`);
  return res.json();
}

async function waitForWs() {
  const deadline = Date.now() + 12000;
  while (Date.now() < deadline) {
    try {
      const tabs = await getJson(`http://127.0.0.1:${port}/json/list`);
      const page = tabs.find((tab) => tab.type === "page" && tab.webSocketDebuggerUrl);
      if (page) return page.webSocketDebuggerUrl;
    } catch {}
    await sleep(150);
  }
  throw new Error(`Chrome DevTools did not start: ${stderr.slice(0, 2000)}`);
}

const wsUrl = await waitForWs();
const ws = new WebSocket(wsUrl);
let nextId = 1;
const pending = new Map();

ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  if (msg.id && pending.has(msg.id)) {
    const { resolve, reject } = pending.get(msg.id);
    pending.delete(msg.id);
    if (msg.error) reject(new Error(JSON.stringify(msg.error)));
    else resolve(msg.result);
  }
};

await new Promise((resolve, reject) => {
  ws.onopen = resolve;
  ws.onerror = reject;
});

function send(method, params = {}) {
  const id = nextId++;
  ws.send(JSON.stringify({ id, method, params }));
  return new Promise((resolve, reject) => pending.set(id, { resolve, reject }));
}

async function capture() {
  return send("Page.captureScreenshot", {
    format: "png",
    fromSurface: true,
    clip: { x: 0, y: 0, width, height, scale: 1 },
  });
}

try {
  await send("Page.enable");
  await send("Runtime.enable");
  await send("Emulation.setDeviceMetricsOverride", {
    width,
    height,
    deviceScaleFactor: 1,
    mobile: true,
    screenOrientation: { type: "portraitPrimary", angle: 0 },
  });
  await send("Page.navigate", { url: pathToFileURL(htmlPath).toString() });
  await sleep(500);

  const frames = Math.ceil(duration * fps);
  for (let i = 0; i < frames; i++) {
    const t = Math.min(i / fps, duration - 0.001);
    await send("Runtime.evaluate", {
      expression: `window.__renderAt(${t.toFixed(4)}, ${duration.toFixed(4)})`,
      awaitPromise: true,
    });
    const shot = await capture();
    const file = `${outDir}/frame_${String(i).padStart(5, "0")}.png`;
    await writeFile(file, Buffer.from(shot.data, "base64"));
    if (i % 75 === 0) console.log(`captured ${i}/${frames}`);
  }
  console.log(`captured ${frames}/${frames}`);
} finally {
  ws.close();
  chrome.kill("SIGTERM");
}
