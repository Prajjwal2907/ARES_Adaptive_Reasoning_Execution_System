const { contextBridge, ipcRenderer } = require('electron')

contextBridge.exposeInMainWorld('ares', {
    onStateChange: (callback) => ipcRenderer.on('state-change', (event, state) => callback(state)),
    onResponse: (callback) => ipcRenderer.on('response', (event, text) => callback(text)),
    closeMain: () => ipcRenderer.send('close-main')
})