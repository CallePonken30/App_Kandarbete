const { app, BrowserWindow } = require('electron');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

const logFile = path.join(app.getPath('userData'), 'log.txt');

function log(msg) {
  const text = `[${new Date().toISOString()}] ${msg}\n`;
  fs.appendFileSync(logFile, text);
  console.log(text.trim());
}

let backendProcess = null;

function startBackend() {
  let scriptPath;
  if (process.platform === 'win32') {
    scriptPath = path.join(process.resourcesPath, 'backend', 'backend_win.exe');
  } else {
    scriptPath = path.join(process.resourcesPath, 'backend', 'backend');
  }

  log(`Starting backend at ${scriptPath}`);
  backendProcess = spawn(scriptPath, [], {
    windowsHide: true,   // ← hides the black console window on Windows
    stdio: 'ignore',     // ← don’t pipe stdout/stderr into your app window
    detached: false
  });

  backendProcess.on('error', err => {
    log(`Backend error: ${err.message}`);
  });

  backendProcess.on('exit', (code, signal) => {
    log(`Backend exited with code ${code}, signal ${signal}`);
  });
}


function createWindow() {
  const win = new BrowserWindow({
    width: 1024,
    height: 768,
    backgroundColor: '#cce5ff',
    icon: path.join(__dirname, 'frontend', 'src', 'designs', 'logo.png'),
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false
    }
  });

  if (!app.isPackaged) {
    log('Running in dev mode');
    win.loadURL('http://localhost:3000');
  } else {
    log('Running in production mode');
    startBackend();
    win.loadFile(path.join(__dirname, 'frontend', 'build', 'index.html'));
    log('Frontend loaded');
  }
}

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
  if (backendProcess) backendProcess.kill();
  if (process.platform !== 'darwin') app.quit();
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) createWindow();
});
