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

// sidebar navigation — single unified listener
document.querySelectorAll('.nav-item[data-section]').forEach(item => {
    item.addEventListener('click', () => {
        const target = item.getAttribute('data-section')

        document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'))
        item.classList.add('active')

        document.querySelectorAll('.section').forEach(s => s.classList.remove('active'))
        document.getElementById('section-' + target).classList.add('active')

        if (target === 'history') loadHistory()
        if (target === 'memory') loadMemory()
    })
})

// history
async function loadHistory() {
    const content = document.getElementById('history-content')
    content.innerHTML = '<p class="placeholder-text">Loading...</p>'

    const history = await window.ares.getHistory()

    if (!history || history.length === 0) {
        content.innerHTML = '<p class="history-empty">No conversation history for today.</p>'
        return
    }

    content.innerHTML = ''

    for (let i = 0; i < history.length; i += 2) {
        const userMsg = history[i]
        const aresMsg = history[i + 1]

        if (!userMsg) continue

        const exchange = document.createElement('div')
        exchange.className = 'history-exchange'

        const userDiv = document.createElement('div')
        userDiv.className = 'history-user'
        userDiv.textContent = userMsg.text
        exchange.appendChild(userDiv)

        if (aresMsg) {
            const aresDiv = document.createElement('div')
            aresDiv.className = 'history-ares'
            aresDiv.textContent = aresMsg.text
            exchange.appendChild(aresDiv)
        }

        content.appendChild(exchange)
    }

    content.scrollTop = content.scrollHeight
}

document.getElementById('history-refresh-btn').addEventListener('click', loadHistory)

// memory
window.ares.onMemoryData((data) => {
    renderMemory(data)
})

function loadMemory() {
    document.getElementById('memory-content').style.opacity = '0.5'
    window.ares.getMemory()
}

function renderMemory(data) {
    document.getElementById('memory-content').style.opacity = '1'

    // profile
    const profileDiv = document.getElementById('memory-profile')
    profileDiv.innerHTML = ''
    Object.entries(data.profile).forEach(([field, val]) => {
        const row = document.createElement('div')
        row.className = 'memory-profile-row'
        row.innerHTML = `
            <span class="memory-profile-field">${field}</span>
            <input class="memory-profile-edit" value="${val}" data-field="${field}">
        `
        row.querySelector('input').addEventListener('change', (e) => {
            window.ares.memoryAction('update-profile', { field, val: e.target.value })
        })
        profileDiv.appendChild(row)
    })

    // instructions
    const instDiv = document.getElementById('memory-instructions')
    instDiv.innerHTML = ''
    if (data.instructions.length === 0) {
        instDiv.innerHTML = '<div class="memory-empty">No standing instructions.</div>'
    } else {
        data.instructions.forEach(inst => {
            const item = document.createElement('div')
            item.className = 'memory-item'
            item.innerHTML = `
                <div class="memory-item-text">${inst.text}</div>
                <button class="memory-delete-btn">REVOKE</button>
            `
            item.querySelector('button').addEventListener('click', () => {
                window.ares.memoryAction('revoke-instruction', { id: inst.id })
            })
            instDiv.appendChild(item)
        })
    }

    // semantic
    const semDiv = document.getElementById('memory-semantic')
    semDiv.innerHTML = ''
    if (data.semantic.length === 0) {
        semDiv.innerHTML = '<div class="memory-empty">No semantic memories stored.</div>'
    } else {
        data.semantic.forEach(mem => {
            const item = document.createElement('div')
            item.className = 'memory-item'
            item.innerHTML = `
                <div>
                    <div class="memory-item-text">${mem.text}</div>
                    <div class="memory-item-meta">${mem.metadata.tags || ''} · importance ${mem.metadata.importance || 0}</div>
                </div>
                <button class="memory-delete-btn">DELETE</button>
            `
            item.querySelector('button').addEventListener('click', () => {
                window.ares.memoryAction('delete-semantic', { id: mem.id })
            })
            semDiv.appendChild(item)
        })
    }

    // procedural
    const procDiv = document.getElementById('memory-procedural')
    procDiv.innerHTML = ''
    if (data.procedural.length === 0) {
        procDiv.innerHTML = '<div class="memory-empty">No procedural memories stored.</div>'
    } else {
        data.procedural.forEach(mem => {
            const item = document.createElement('div')
            item.className = 'memory-item'
            item.innerHTML = `
                <div>
                    <div class="memory-item-text">${mem.text}</div>
                    <div class="memory-item-meta">${mem.metadata.tags || ''} · importance ${mem.metadata.importance || 0}</div>
                </div>
                <button class="memory-delete-btn">DELETE</button>
            `
            item.querySelector('button').addEventListener('click', () => {
                window.ares.memoryAction('delete-procedural', { id: mem.id })
            })
            procDiv.appendChild(item)
        })
    }

    // episodes
    const epDiv = document.getElementById('memory-episodes')
    epDiv.innerHTML = ''
    if (data.episodes.length === 0) {
        epDiv.innerHTML = '<div class="memory-empty">No episodic summaries yet.</div>'
    } else {
        data.episodes.forEach(ep => {
            const item = document.createElement('div')
            item.className = 'memory-item'
            item.innerHTML = `
                <div>
                    <div class="memory-item-text">${ep.summary}</div>
                    <div class="memory-item-meta">${ep.date.split('T')[0]}</div>
                </div>
            `
            epDiv.appendChild(item)
        })
    }
}

document.getElementById('memory-refresh-btn').addEventListener('click', loadMemory)

document.getElementById('instruction-submit').addEventListener('click', () => {
    const input = document.getElementById('instruction-input')
    const text = input.value.trim()
    if (!text) return
    input.value = ''
    window.ares.memoryAction('add-instruction', { text })
})

document.getElementById('instruction-input').addEventListener('keydown', (e) => {
    if (e.key === 'Enter') document.getElementById('instruction-submit').click()
})

// visualiser
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
        const waveX = t * canvas.width
        const waveY = getY(waveX)
        const angle = t * Math.PI * 2 + rotationAngle
        const circleX = cx + radius * Math.cos(angle)
        const circleY = cy + radius * Math.sin(angle)
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

    const targetMorph = currentState === 'processing' ? 1 : 0
    morphProgress = lerp(morphProgress, targetMorph, 0.035)
    rotationAngle += current.speed * morphProgress

    drawMorphedPath(getWaveY, CIRCLE_RADIUS, CRIMSON, 1, 1)
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
    const historySection = document.getElementById('section-history')
    if (historySection.classList.contains('active')) {
        loadHistory()
    }
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