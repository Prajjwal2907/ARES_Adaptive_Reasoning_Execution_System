// splash screen sequence
window.addEventListener('DOMContentLoaded', () => {
    const splash = document.getElementById('splash')
    const splashLogo = document.getElementById('splash-logo')
    const appDiv = document.getElementById('app')

    setTimeout(() => splashLogo.classList.add('visible'), 300)
    setTimeout(() => splashLogo.classList.remove('visible'), 2500)
    setTimeout(() => splash.classList.add('hidden'), 3500)
    setTimeout(() => {
        appDiv.classList.add('visible')
        splash.style.display = 'none'
    }, 4700)
})
// sidebar navigation
document.querySelectorAll('.nav-item[data-section]').forEach(item => {
    item.addEventListener('click', () => {
        const target = item.getAttribute('data-section')

        document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'))
        item.classList.add('active')

        document.querySelectorAll('.section').forEach(s => s.classList.remove('active'))
        document.getElementById('section-' + target).classList.add('active')
    })
})

const canvas = document.getElementById('visualiser')
const ctx = canvas.getContext('2d')
const stateLabel = document.getElementById('state-label')
const responseText = document.getElementById('response-text')
const timeDisplay = document.getElementById('time-display')

canvas.width = 500
canvas.height = 200

const cx = canvas.width / 2
const cy = canvas.height / 2

let currentState = 'standby'
let animFrame = 0
let morphProgress = 0
let rotationAngle = 0

const CRIMSON = '#dc143c'
const CRIMSON_DIM = 'rgba(220, 20, 60, 0.5)'

const states = {
    standby: {
        amplitude: 3,
        frequency: 0.015,
        speed: 0.008,
        glowSize: 8,
        lineWidth: 1.5
    },
    listening: {
        amplitude: 30,
        frequency: 0.022,
        speed: 0.035,
        glowSize: 20,
        lineWidth: 2
    },
    processing: {
        amplitude: 0,
        frequency: 0.015,
        speed: 0.05,
        glowSize: 22,
        lineWidth: 2
    },
    speaking: {
        amplitude: 52,
        frequency: 0.028,
        speed: 0.06,
        glowSize: 28,
        lineWidth: 2.5
    }
}

const current = {
    amplitude: 3,
    frequency: 0.015,
    speed: 0.008,
    glowSize: 8,
    lineWidth: 1.5
}

const NUM_POINTS = 200
const CIRCLE_RADIUS = 60

function lerp(a, b, t) {
    return a + (b - a) * t
}

function interpolateToTarget() {
    const target = states[currentState]
    const t = 0.04
    current.amplitude = lerp(current.amplitude, target.amplitude, t)
    current.frequency = lerp(current.frequency, target.frequency, t)
    current.speed = lerp(current.speed, target.speed, t)
    current.glowSize = lerp(current.glowSize, target.glowSize, t)
    current.lineWidth = lerp(current.lineWidth, target.lineWidth, t)
}

function getWaveY(x) {
    return cy
        + Math.sin(x * current.frequency + animFrame * current.speed) * current.amplitude
        + Math.sin(x * current.frequency * 2.3 + animFrame * current.speed * 1.7) * (current.amplitude * 0.35)
        + Math.sin(x * current.frequency * 0.7 + animFrame * current.speed * 0.5) * (current.amplitude * 0.2)
}

function getWaveYEcho(x) {
    return cy
        + Math.sin(x * current.frequency * 1.4 + animFrame * current.speed * 0.8 + 1.2) * (current.amplitude * 0.45)
        + Math.sin(x * current.frequency * 0.5 + animFrame * current.speed * 1.3) * (current.amplitude * 0.25)
}

function drawMorphedPath(getY, radius, color, glowMultiplier, widthMultiplier) {
    ctx.beginPath()
    ctx.shadowBlur = current.glowSize * glowMultiplier
    ctx.shadowColor = color
    ctx.strokeStyle = color
    ctx.lineWidth = current.lineWidth * widthMultiplier

    for (let i = 0; i <= NUM_POINTS; i++) {
        const t = i / NUM_POINTS

        // wave position
        const waveX = t * canvas.width
        const waveY = getY(waveX)

        // circle position — points evenly distributed around the circumference
        const angle = t * Math.PI * 2 + rotationAngle
        const circleX = cx + radius * Math.cos(angle)
        const circleY = cy + radius * Math.sin(angle)

        // morph between the two
        const x = lerp(waveX, circleX, morphProgress)
        const y = lerp(waveY, circleY, morphProgress)

        if (i === 0) {
            ctx.moveTo(x, y)
        } else {
            ctx.lineTo(x, y)
        }
    }

    ctx.stroke()
}

function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height)
    ctx.shadowBlur = 0

    interpolateToTarget()

    // morph progress toward 1 when processing, toward 0 otherwise
    const targetMorph = currentState === 'processing' ? 1 : 0
    morphProgress = lerp(morphProgress, targetMorph, 0.035)

    // rotation only matters when morphed toward circle
    rotationAngle += current.speed * morphProgress

    // primary path
    drawMorphedPath(getWaveY, CIRCLE_RADIUS, CRIMSON, 1, 1)

    // echo path
    drawMorphedPath(getWaveYEcho, CIRCLE_RADIUS - 15, CRIMSON_DIM, 0.5, 0.6)

    animFrame++
    requestAnimationFrame(draw)
}

function setState(state) {
    currentState = state
    stateLabel.textContent = state.toUpperCase()
}

function updateTime() {
    const now = new Date()
    const hours = String(now.getHours()).padStart(2, '0')
    const minutes = String(now.getMinutes()).padStart(2, '0')
    const seconds = String(now.getSeconds()).padStart(2, '0')
    const timeStr = `${hours}:${minutes}:${seconds}`
    document.getElementById('time-display').textContent = timeStr
    document.getElementById('clock-display').textContent = timeStr
}

function submitCommand() {
    const input = document.getElementById('command-input')
    const text = input.value.trim()
    if (!text) return
    input.value = ''
    window.ares.sendCommand(text)
}

document.getElementById('command-submit').addEventListener('click', submitCommand)

document.getElementById('command-input').addEventListener('keydown', (e) => {
    if (e.key === 'Enter') submitCommand()
})

window.ares.onStateChange((state) => {
    setState(state)
})

window.ares.onResponse((text) => {
    responseText.textContent = text
})

document.addEventListener('keydown', (e) => {
    if (e.key === '1') setState('standby')
    if (e.key === '2') setState('listening')
    if (e.key === '3') setState('processing')
    if (e.key === '4') setState('speaking')
})

document.getElementById('close-btn').addEventListener('click', () => {
    window.ares.closeMain()
})

document.getElementById('quit-btn').addEventListener('click', () => {
    window.ares.quit()
})

draw()
setInterval(updateTime, 1000)
updateTime()