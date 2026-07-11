const ambientCanvas = document.createElement('canvas')
ambientCanvas.id = 'ambient-canvas'
ambientCanvas.style.cssText = `
    position: fixed;
    top: 0;
    left: 200px;
    width: calc(100vw - 200px);
    height: 100vh;
    pointer-events: none;
    z-index: 0;
`
document.getElementById('content').appendChild(ambientCanvas)

const actx = ambientCanvas.getContext('2d')

function resizeAmbient() {
    ambientCanvas.width = ambientCanvas.offsetWidth
    ambientCanvas.height = ambientCanvas.offsetHeight
}
resizeAmbient()
window.addEventListener('resize', resizeAmbient)

let scanY = 0
let uptime = 0
let memCount = 0

function drawGrid() {
    const spacing = 40
    actx.strokeStyle = 'rgba(20, 60, 120, 0.08)'
    actx.lineWidth = 0.5

    for (let x = 0; x < ambientCanvas.width; x += spacing) {
        actx.beginPath()
        actx.moveTo(x, 0)
        actx.lineTo(x, ambientCanvas.height)
        actx.stroke()
    }

    for (let y = 0; y < ambientCanvas.height; y += spacing) {
        actx.beginPath()
        actx.moveTo(0, y)
        actx.lineTo(ambientCanvas.width, y)
        actx.stroke()
    }
}

function drawCornerBrackets() {
    const size = 24
    const margin = 20
    const w = ambientCanvas.width
    const h = ambientCanvas.height

    actx.strokeStyle = 'rgba(220, 20, 60, 0.35)'
    actx.lineWidth = 1.5

    const corners = [
        [margin, margin, 1, 1],
        [w - margin, margin, -1, 1],
        [margin, h - margin, 1, -1],
        [w - margin, h - margin, -1, -1]
    ]

    corners.forEach(([x, y, dx, dy]) => {
        actx.beginPath()
        actx.moveTo(x + dx * size, y)
        actx.lineTo(x, y)
        actx.lineTo(x, y + dy * size)
        actx.stroke()
    })
}

function drawScanLine() {
    const gradient = actx.createLinearGradient(0, scanY - 40, 0, scanY + 40)
    gradient.addColorStop(0, 'rgba(20, 60, 120, 0)')
    gradient.addColorStop(0.5, 'rgba(20, 60, 120, 0.08)')
    gradient.addColorStop(1, 'rgba(20, 60, 120, 0)')

    actx.fillStyle = gradient
    actx.fillRect(0, scanY - 40, ambientCanvas.width, 80)

    actx.beginPath()
    actx.moveTo(0, scanY)
    actx.lineTo(ambientCanvas.width, scanY)
    actx.strokeStyle = 'rgba(20, 60, 120, 0.12)'
    actx.lineWidth = 0.5
    actx.stroke()

    scanY += 0.4
    if (scanY > ambientCanvas.height) scanY = 0
}

function drawDataReadout() {
    const x = ambientCanvas.width - 180
    const y = ambientCanvas.height - 120

    actx.font = '10px Courier New'
    actx.fillStyle = 'rgba(220, 20, 60, 0.25)'

    const now = new Date()
    const timeStr = now.toTimeString().split(' ')[0]
    const dateStr = now.toLocaleDateString('en-GB').replace(/\//g, '.')

    const lines = [
        `SYS.TIME  ${timeStr}`,
        `SYS.DATE  ${dateStr}`,
        `UPTIME    ${formatUptime(uptime)}`,
        `MEM.IDX   ${String(memCount).padStart(4, '0')}`,
        `STATUS    NOMINAL`
    ]

    lines.forEach((line, i) => {
        actx.fillText(line, x, y + i * 16)
    })
}

function formatUptime(seconds) {
    const h = Math.floor(seconds / 3600)
    const m = Math.floor((seconds % 3600) / 60)
    const s = seconds % 60
    return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}

setInterval(() => {
    uptime++
    memCount = Math.floor(Math.random() * 20) + 80
}, 1000)

function drawAmbient() {
    actx.clearRect(0, 0, ambientCanvas.width, ambientCanvas.height)
    drawGrid()
    drawCornerBrackets()
    drawScanLine()
    drawDataReadout()
    requestAnimationFrame(drawAmbient)
}

drawAmbient()