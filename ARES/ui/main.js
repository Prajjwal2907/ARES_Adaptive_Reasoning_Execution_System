const { app, BrowserWindow, Tray, Menu, ipcMain } = require('electron')
const path = require('path')
const WebSocket = require('ws')

let mainWindow = null
let overlayWindow = null
let tray = null
let isQuitting = false
let wss = null
let currentState = 'standby'

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
            if (currentState !== 'standby') {
                overlayWindow.show()
            }
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
                mainWindow.focus()
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
        mainWindow.focus()
    })
}

function startWebSocketServer() {
    wss = new WebSocket.Server({ port: 8765 })

    wss.on('connection', (ws) => {
        console.log('Python backend connected')

        ws.on('message', (message) => {
            try {
                const data = JSON.parse(message)
                if (data.type === 'memory-data') {
                    mainWindow.webContents.send('memory-data', data.value)
                }
                if (data.type === 'state') {
                    currentState = data.value

                    // always send to main window for its visualiser
                    mainWindow.webContents.send('state-change', data.value)

                    // send to overlay too
                    overlayWindow.webContents.send('state-change', data.value)

                    // show overlay if not focused on main window and not standby
                    if (!mainWindow.isFocused() && data.value !== 'standby') {
                        overlayWindow.show()
                    }

                    // hide overlay after 3 seconds of standby
                    if (data.value === 'standby') {
                        setTimeout(() => {
                            if (currentState === 'standby') {
                                overlayWindow.hide()
                            }
                        }, 3000)
                    }
                }

                if (data.type === 'response') {
                    mainWindow.webContents.send('response', data.value)
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

function startFocusPoller() {
    setInterval(() => {
        if (!mainWindow || !overlayWindow) return

        const mainFocused = mainWindow.isFocused() && mainWindow.isVisible()

        if (mainFocused) {
            overlayWindow.hide()
        } else if (currentState !== 'standby') {
            overlayWindow.show()
        }
    }, 500)
}

ipcMain.on('command', (event, text) => {
    wss.clients.forEach(client => {
        if (client.readyState === WebSocket.OPEN) {
            client.send(JSON.stringify({ type: 'command', value: text }))
        }
    })
})

ipcMain.on('close-main', () => {
    mainWindow.hide()
    if (currentState !== 'standby') {
        overlayWindow.show()
    }
})

ipcMain.on('quit-app', () => {
    isQuitting = true
    app.quit()
})

const fs = require('fs')

ipcMain.handle('get-history', () => {
    try {
        const historyPath = path.join(__dirname, '..', 'data', 'memory', 'history.json')
        console.log('Looking for history at:', historyPath)
        if (!fs.existsSync(historyPath)) {
            console.log('File not found at that path')
            return []
        }
        const data = JSON.parse(fs.readFileSync(historyPath, 'utf8'))
        return data.history || []
    } catch (e) {
        console.error('Failed to read history:', e)
        return []
    }
})
ipcMain.on('get-memory', () => {
    wss.clients.forEach(client => {
        if (client.readyState === WebSocket.OPEN) {
            client.send(JSON.stringify({ type: 'get-memory' }))
        }
    })
})

ipcMain.on('memory-action', (event, action, payload) => {
    wss.clients.forEach(client => {
        if (client.readyState === WebSocket.OPEN) {
            client.send(JSON.stringify({ type: 'memory-action', action, payload }))
        }
    })
})
app.whenReady().then(() => {
    createOverlayWindow()
    createMainWindow()
    createTray()
    startWebSocketServer()
    startFocusPoller()
})

app.on('before-quit', () => {
    isQuitting = true
})

app.on('window-all-closed', (e) => {
    e.preventDefault()
})