const canvas = document.getElementById('overlay-canvas')
const ctx = canvas.getContext('2d')

canvas.width = 500
canvas.height = 120

const cx = canvas.width / 2
const cy = canvas.height / 2

let currentState = 'standby'
let animFrame = 0
let morphProgress = 0
let rotationAngle = 0

const CRIMSON = '#dc143c'
const CRIMSON_DIM = 'rgba(220, 20, 60, 0.5)'

const states = {
    standby: { amplitude: 3, frequency: 0.015, speed: 0.008, glowSize: 8, lineWidth: 1.5 },
    listening: { amplitude: 25, frequency: 0.022, speed: 0.035, glowSize: 20, lineWidth: 2 },
    processing: { amplitude: 0, frequency: 0.015, speed: 0.05, glowSize: 22, lineWidth: 2 },
    speaking: { amplitude: 40, frequency: 0.028, speed: 0.06, glowSize: 28, lineWidth: 2.5 }
}

const current = {
    amplitude: 3, frequency: 0.015, speed: 0.008, glowSize: 8, lineWidth: 1.5
}

function lerp(a, b, t) { return a + (b - a) * t }

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

function drawMorphedPath(getY, radius, color, glowMult, widthMult) {
    ctx.beginPath()
    ctx.shadowBlur = current.glowSize * glowMult
    ctx.shadowColor = color
    ctx.strokeStyle = color
    ctx.lineWidth = current.lineWidth * widthMult

    const NUM_POINTS = 200
    for (let i = 0; i <= NUM_POINTS; i++) {
        const t = i / NUM_POINTS
        const waveX = t * canvas.width
        const waveY = getY(waveX)
        const angle = t * Math.PI * 2 + rotationAngle
        const circleX = cx + 40 * Math.cos(angle)
        const circleY = cy + 40 * Math.sin(angle)
        const x = lerp(waveX, circleX, morphProgress)
        const y = lerp(waveY, circleY, morphProgress)
        if (i === 0) ctx.moveTo(x, y)
        else ctx.lineTo(x, y)
    }
    ctx.stroke()
}

function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height)
    ctx.shadowBlur = 0
    interpolateToTarget()

    const targetMorph = currentState === 'processing' ? 1 : 0
    morphProgress = lerp(morphProgress, targetMorph, 0.035)
    rotationAngle += current.speed * morphProgress

    drawMorphedPath(getWaveY, 40, CRIMSON, 1, 1)
    drawMorphedPath(getWaveYEcho, 28, CRIMSON_DIM, 0.5, 0.6)

    animFrame++
    requestAnimationFrame(draw)
}

window.ares.onStateChange((state) => {
    currentState = state
})

draw()