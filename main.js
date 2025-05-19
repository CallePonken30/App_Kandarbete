const { app, BrowserWindow } = require('electron');
const { spawn } = require('child_process');
const path = require('path');

let backendProcess = null;

function startBackend() {
  let scriptPath;

  if (process.platform === 'win32') {
    scriptPath = path.join(process.resourcesPath, 'backend', 'backend_win.exe');
  } else {
    scriptPath = path.join(process.resourcesPath, 'backend', 'backend'); // macOS universal binary
  }

  backendProcess = spawn(scriptPath, [], { stdio: 'inherit' });
  backendProcess.on('error', console.error);
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
    // Load from local React dev server
    win.loadURL('http://localhost:3000');
  } else {
    // Load from packaged frontend + start backend
    startBackend();
    win.loadFile(path.join(__dirname, 'frontend', 'build', 'index.html'));
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
