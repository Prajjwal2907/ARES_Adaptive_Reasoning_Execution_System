const { app, BrowserWindow, Tray, Menu, ipcMain } = require('electron')
const path = require('path')
const WebSocket = require('ws')

let mainWindow = null
let overlayWindow = null
let tray = null
let isQuitting = false
let wss = null

function createMainWindow() {
    mainWindow = new BrowserWindow({
        width: 1280,
        height: 800,
        frame: false,
        transparent: false,
        backgroundColor: '#0a0000',
        show: false,
        icon: path.join(__dirname, 'assets', 'ares_icon.png'),
        webPreferences: {
            preload: path.join(__dirname, 'preload.js')
        }
    })

    mainWindow.loadFile('renderer/index.html')

    mainWindow.once('ready-to-show', () => {
        mainWindow.show()
        mainWindow.maximize()
    })

    mainWindow.on('close', (e) => {
        if (!isQuitting) {
            e.preventDefault()
            mainWindow.hide()
            overlayWindow.show()
        }
    })
}

function createOverlayWindow() {
    overlayWindow = new BrowserWindow({
        width: 500,
        height: 120,
        x: Math.floor((require('electron').screen.getPrimaryDisplay().workAreaSize.width - 500) / 2),
        y: 0,
        frame: false,
        transparent: true,
        alwaysOnTop: true,
        skipTaskbar: true,
        show: false,
        icon: path.join(__dirname, 'assets', 'ares_icon.png'),
        webPreferences: {
            preload: path.join(__dirname, 'preload.js')
        }
    })

    overlayWindow.loadFile('overlay/overlay.html')
    overlayWindow.setIgnoreMouseEvents(true)
}

function createTray() {
    tray = new Tray(path.join(__dirname, 'assets', 'ares_icon.png'))

    const contextMenu = Menu.buildFromTemplate([
        {
            label: 'Open ARES',
            click: () => {
                overlayWindow.hide()
                mainWindow.show()
            }
        },
        { type: 'separator' },
        {
            label: 'Quit',
            click: () => {
                isQuitting = true
                app.quit()
            }
        }
    ])

    tray.setToolTip('ARES')
    tray.setContextMenu(contextMenu)

    tray.on('double-click', () => {
        overlayWindow.hide()
        mainWindow.show()
    })
}

function startWebSocketServer() {
    wss = new WebSocket.Server({ port: 8765 })

    wss.on('connection', (ws) => {
        console.log('Python backend connected')

        ws.on('message', (message) => {
            try {
                const data = JSON.parse(message)

                // decide which window to send to
                const targetWindow = mainWindow.isVisible() ? mainWindow : overlayWindow

                if (data.type === 'state') {
                    targetWindow.webContents.send('state-change', data.value)

                    // if overlay is hidden and state is not standby, show it
                    if (!mainWindow.isVisible() && data.value !== 'standby') {
                        overlayWindow.show()
                    }

                    // when conversation ends, hide overlay again
                    if (!mainWindow.isVisible() && data.value === 'standby') {
                        setTimeout(() => {
                            overlayWindow.hide()
                        }, 3000)
                    }
                }

                if (data.type === 'response') {
                    targetWindow.webContents.send('response', data.value)
                }

            } catch (e) {
                console.error('WebSocket message error:', e)
            }
        })

        ws.on('close', () => {
            console.log('Python backend disconnected')
        })
    })

    console.log('WebSocket server running on port 8765')
}
ipcMain.on('close-main', () => {
    mainWindow.hide()
    overlayWindow.show()
})

app.whenReady().then(() => {
    createOverlayWindow()
    createMainWindow()
    createTray()
    startWebSocketServer()
})

app.on('before-quit', () => {
    isQuitting = true
})

app.on('window-all-closed', (e) => {
    e.preventDefault()
})