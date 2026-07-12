const { contextBridge, ipcRenderer } = require('electron')

contextBridge.exposeInMainWorld('ares', {
    onStateChange: (callback) => ipcRenderer.on('state-change', (event, state) => callback(state)),
    onResponse: (callback) => ipcRenderer.on('response', (event, text) => callback(text)),
    onMemoryData: (callback) => ipcRenderer.on('memory-data', (event, data) => callback(data)),
    closeMain: () => ipcRenderer.send('close-main'),
    quit: () => ipcRenderer.send('quit-app'),
    sendCommand: (text) => ipcRenderer.send('command', text),
    getHistory: () => ipcRenderer.invoke('get-history'),
    getMemory: () => ipcRenderer.send('get-memory'),
    memoryAction: (action, payload) => ipcRenderer.send('memory-action', action, payload)
})