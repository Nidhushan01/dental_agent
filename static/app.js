// ===========================================================================
// Dental Web Agent - Frontend JS
// ===========================================================================

// State
let currentMode = 'appointments';  // 'appointments' or 'faq'
let conversationHistory = [];
let mediaRecorder = null;
let recordedChunks = [];
let isRecording = false;

// ===========================================================================
// DOM Elements
// ===========================================================================

const textInput    = document.getElementById('text-input');
const sendBtn      = document.getElementById('send-btn');
const micBtn       = document.getElementById('mic-btn');
const messagesDiv  = document.getElementById('messages');
const micStatus    = document.getElementById('mic-status');
const audioPlayer  = document.getElementById('audio-player');
const responseAudio = document.getElementById('response-audio');
const flowBtns     = document.querySelectorAll('.flow-btn');

// Appointment form elements
const apptName    = document.getElementById('appt-name');
const apptDate    = document.getElementById('appt-date');
const apptTime    = document.getElementById('appt-time');
const apptService = document.getElementById('appt-service');
const apptId      = document.getElementById('appt-id');
const apptNewDate = document.getElementById('appt-new-date');
const apptNewTime = document.getElementById('appt-new-time');

// Per-section result panels
const bookResult   = document.getElementById('book-result');
const viewResult   = document.getElementById('view-result');
const modifyResult = document.getElementById('modify-result');
const scheduledAppointmentsList = document.getElementById('scheduled-appointments-list');

// ===========================================================================
// Initialize
// ===========================================================================

document.addEventListener('DOMContentLoaded', () => {
    // Text / send
    sendBtn.addEventListener('click', sendTextMessage);
    textInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendTextMessage();
    });

    // Mic
    micBtn.addEventListener('click', toggleMicRecording);

    // Tab switching
    const appointmentsSection = document.getElementById('appointments-section');
    const chatSection = document.getElementById('chat-section');

    flowBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            flowBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentMode = btn.dataset.flow;

            if (currentMode === 'appointments') {
                appointmentsSection.style.display = 'flex';
                chatSection.style.display = 'none';
            } else {
                appointmentsSection.style.display = 'none';
                chatSection.style.display = 'flex';
            }
        });
    });

    // Accordion setup
    setupAccordions();

    // Request microphone support (only needed for FAQ tab, but check early)
    checkMicrophoneSupport();

    // Appointment button listeners
    document.getElementById('check-availability').addEventListener('click', handleCheckAvailability);
    document.getElementById('book-appointment').addEventListener('click', handleBookAppointment);
    document.getElementById('show-scheduled-appointments').addEventListener('click', handleShowScheduled);
    document.getElementById('reschedule-appointment').addEventListener('click', handleReschedule);
    document.getElementById('cancel-appointment').addEventListener('click', handleCancel);
});

// ===========================================================================
// Accordion Logic
// ===========================================================================

function setupAccordions() {
    const headers = document.querySelectorAll('.accordion-header');
    headers.forEach(header => {
        header.addEventListener('click', () => {
            const targetId = header.getAttribute('data-target');
            const accordion = header.closest('.accordion');
            const isOpen = accordion.classList.contains('open');

            // Close all
            document.querySelectorAll('.accordion').forEach(acc => {
                acc.classList.remove('open');
                acc.querySelector('.accordion-header').setAttribute('aria-expanded', 'false');
            });

            // Open clicked one (toggle)
            if (!isOpen) {
                accordion.classList.add('open');
                header.setAttribute('aria-expanded', 'true');
            }
        });
    });
}

// ===========================================================================
// Result Panel Helpers
// ===========================================================================

function showResult(panel, message, type = 'info') {
    panel.style.display = 'block';
    panel.className = 'result-panel ' + type;
    panel.textContent = message;
}

function showResultHtml(panel, html, type = 'info') {
    panel.style.display = 'block';
    panel.className = 'result-panel ' + type;
    panel.innerHTML = html;
}

// ===========================================================================
// Appointment Handlers
// ===========================================================================

async function handleCheckAvailability() {
    const date = apptDate.value;
    const time = apptTime.value || null;
    if (!date) {
        showResult(bookResult, '⚠️ Please select a date to check availability.', 'error');
        return;
    }
    showResult(bookResult, '⏳ Checking availability...', 'loading');
    try {
        const res = await fetch('/api/appointments/check', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ date, time })
        });
        const data = await res.json();
        if (data.error) {
            showResult(bookResult, `❌ Error: ${data.error}`, 'error');
        } else {
            const result = data.result;
            const available = result.available;
            const icon = available ? '✅' : '❌';
            let msg = `${icon} ${result.message || (available ? 'Available!' : 'Not available.')}`;
            if (result.available_slots && result.available_slots.length) {
                msg += `\n\nAvailable slots: ${result.available_slots.join(', ')}`;
            }
            showResult(bookResult, msg, available ? 'success' : 'error');
        }
    } catch (e) {
        showResult(bookResult, `❌ Request failed: ${e}`, 'error');
    }
}

async function handleBookAppointment() {
    const name    = apptName.value.trim();
    const date    = apptDate.value;
    const time    = apptTime.value;
    const service = apptService.value.trim();
    if (!name || !date || !time || !service) {
        showResult(bookResult, '⚠️ Please fill in Name, Date, Time and Service.', 'error');
        return;
    }
    showResult(bookResult, '⏳ Booking your appointment...', 'loading');
    try {
        const res = await fetch('/api/appointments/book', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, date, time, service })
        });
        const data = await res.json();
        if (data.error) {
            showResult(bookResult, `❌ Error: ${data.error}`, 'error');
        } else {
            const msg = data.result?.message || 'Appointment booked successfully!';
            const id  = data.result?.appointment_id ? ` (ID: ${data.result.appointment_id})` : '';
            showResult(bookResult, `✅ ${msg}${id}`, 'success');
            // Clear form
            apptName.value = '';
            apptDate.value = '';
            apptTime.value = '';
            apptService.value = '';
        }
    } catch (e) {
        showResult(bookResult, `❌ Request failed: ${e}`, 'error');
    }
}

async function handleShowScheduled() {
    showResult(viewResult, '⏳ Loading your appointments...', 'loading');
    scheduledAppointmentsList.innerHTML = '';

    try {
        const res = await fetch('/api/appointments/scheduled');
        const data = await res.json();

        if (data.error) {
            showResult(viewResult, `❌ Error: ${data.error}`, 'error');
            return;
        }

        const appointments = data.appointments || [];
        if (!appointments.length) {
            showResult(viewResult, '📭 No scheduled appointments found.', 'info');
            scheduledAppointmentsList.innerHTML = '<div class="scheduled-empty">No scheduled appointments right now.</div>';
            return;
        }

        showResult(viewResult, `📋 Found ${appointments.length} scheduled appointment(s).`, 'success');

        scheduledAppointmentsList.innerHTML = appointments.map(appt => `
            <div class="scheduled-card">
                <div class="scheduled-card-header">
                    <strong>#${escapeHtml(String(appt.id))}</strong>
                    <span class="scheduled-status">${escapeHtml(appt.status || 'confirmed')}</span>
                </div>
                <div class="scheduled-card-body">
                    <div><strong>Name:</strong> ${escapeHtml(appt.name || '')}</div>
                    <div><strong>Date:</strong> ${escapeHtml(appt.date || '')}</div>
                    <div><strong>Time:</strong> ${escapeHtml(appt.time || '')}</div>
                    <div><strong>Service:</strong> ${escapeHtml(appt.service || '')}</div>
                </div>
            </div>
        `).join('');
    } catch (e) {
        showResult(viewResult, `❌ Request failed: ${e}`, 'error');
    }
}

async function handleReschedule() {
    const id       = apptId.value;
    const new_date = apptNewDate.value;
    const new_time = apptNewTime.value;
    if (!id || !new_date || !new_time) {
        showResult(modifyResult, '⚠️ Please provide Appointment ID and a new date/time.', 'error');
        return;
    }
    showResult(modifyResult, '⏳ Rescheduling...', 'loading');
    try {
        const res = await fetch('/api/appointments/reschedule', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ appointment_id: parseInt(id, 10), new_date, new_time })
        });
        const data = await res.json();
        if (data.error) {
            showResult(modifyResult, `❌ Error: ${data.error}`, 'error');
        } else {
            const msg = data.result?.message || 'Appointment rescheduled successfully!';
            showResult(modifyResult, `✅ ${msg}`, 'success');
            apptId.value = '';
            apptNewDate.value = '';
            apptNewTime.value = '';
        }
    } catch (e) {
        showResult(modifyResult, `❌ Request failed: ${e}`, 'error');
    }
}

async function handleCancel() {
    const id = apptId.value;
    if (!id) {
        showResult(modifyResult, '⚠️ Please provide an Appointment ID to cancel.', 'error');
        return;
    }
    showResult(modifyResult, '⏳ Cancelling...', 'loading');
    try {
        const res = await fetch('/api/appointments/cancel', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ appointment_id: parseInt(id, 10) })
        });
        const data = await res.json();
        if (data.error) {
            showResult(modifyResult, `❌ Error: ${data.error}`, 'error');
        } else {
            const msg = data.result?.message || 'Appointment cancelled.';
            showResult(modifyResult, `✅ ${msg}`, 'success');
            apptId.value = '';
        }
    } catch (e) {
        showResult(modifyResult, `❌ Request failed: ${e}`, 'error');
    }
}

// ===========================================================================
// Microphone & Voice Recording (FAQ tab only)
// ===========================================================================

async function checkMicrophoneSupport() {
    const hasMediaDevices = !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia);
    if (!hasMediaDevices) {
        micBtn.disabled = true;
        micBtn.title = 'Microphone not supported in your browser';
        return;
    }
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        stream.getTracks().forEach(track => track.stop());
        setupMediaRecorder();
    } catch (error) {
        console.warn('Microphone permission denied:', error);
        micBtn.disabled = true;
        micBtn.title = 'Microphone permission denied';
    }
}

function setupMediaRecorder() {
    navigator.mediaDevices.getUserMedia({ audio: true })
        .then(stream => {
            mediaRecorder = new MediaRecorder(stream);
            mediaRecorder.ondataavailable = (event) => {
                recordedChunks.push(event.data);
            };
            mediaRecorder.onstop = async () => {
                const audioBlob = new Blob(recordedChunks, { type: 'audio/webm' });
                recordedChunks = [];
                await sendVoiceMessage(audioBlob);
            };
        })
        .catch(err => console.error('Failed to setup media recorder:', err));
}

function toggleMicRecording() {
    if (!mediaRecorder) {
        alert('Microphone not available');
        return;
    }
    if (!isRecording) {
        isRecording = true;
        recordedChunks = [];
        mediaRecorder.start();
        micBtn.classList.add('recording');
        micStatus.textContent = '🔴 Recording...';
        micBtn.textContent = '⏹️ Stop';
    } else {
        isRecording = false;
        mediaRecorder.stop();
        micBtn.classList.remove('recording');
        micStatus.textContent = '⏳ Processing...';
        micBtn.textContent = '🎤 Record';
    }
}

async function sendVoiceMessage(audioBlob) {
    try {
        const formData = new FormData();
        formData.append('file', audioBlob, 'audio.webm');
        formData.append('mode', currentMode);

        const response = await fetch('/api/chat/voice', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.error) {
            micStatus.textContent = '✗ Voice failed';
            addBotMessage(`Error: ${data.error}`);
        } else {
            micStatus.textContent = '✓ Processed';
            if (data.transcribed_text) {
                addUserMessage(data.transcribed_text);
            }
            addBotMessage(data.reply_text || 'No response received.');
            if (data.voice_url) {
                playAudio(data.voice_url);
            }
        }
        setTimeout(() => { micStatus.textContent = ''; }, 1500);
    } catch (error) {
        micStatus.textContent = '✗ Voice error';
        console.error('Voice chat error:', error);
    }
}

// ===========================================================================
// Chat / Text Functions (FAQ tab)
// ===========================================================================

async function sendTextMessage() {
    if (currentMode !== 'faq') {
        return;
    }
    const text = textInput.value.trim();
    if (!text) return;

    addUserMessage(text);
    textInput.value = '';
    await sendChatMessage(text);
}

async function sendChatMessage(userText) {
    try {
        sendBtn.disabled = true;
        micBtn.disabled  = true;

        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                text: userText,
                mode: currentMode,
                context: conversationHistory
            })
        });

        const data = await response.json();

        if (data.error) {
            addBotMessage(`Error: ${data.error}`);
        } else {
            addBotMessage(data.reply_text || 'No response received.');
            conversationHistory.push({ role: 'user',      content: userText });
            conversationHistory.push({ role: 'assistant', content: data.reply_text || '' });

            if (data.voice_url) {
                playAudio(data.voice_url);
            }
        }
    } catch (error) {
        console.error('Chat error:', error);
        addBotMessage('Sorry, I encountered an error. Please try again.');
    } finally {
        sendBtn.disabled = false;
        micBtn.disabled  = false;
    }
}

function playAudio(audioUrl) {
    audioPlayer.style.display = 'block';
    responseAudio.src = audioUrl;
    responseAudio.play().catch(err => console.error('Audio playback error:', err));
}

// ===========================================================================
// Message Helpers
// ===========================================================================

function addUserMessage(text) {
    const msgEl = document.createElement('div');
    msgEl.className = 'message user';
    msgEl.innerHTML = `<p>${formatBubbleText(text)}</p>`;
    messagesDiv.appendChild(msgEl);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function addBotMessage(text) {
    const msgEl = document.createElement('div');
    msgEl.className = 'message bot';
    msgEl.innerHTML = `<div class="bubble-content">${formatReplyText(text)}</div>`;
    messagesDiv.appendChild(msgEl);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function formatBubbleText(text) {
    return escapeHtml(String(text || '')).replace(/\n/g, '<br>');
}

function formatReplyText(text) {
    const raw = String(text || '').trim();
    if (!raw) return '<p>No response received.</p>';

    const normalized = raw
        .replace(/\r\n/g, '\n')
        .replace(/\s+(\d+\.\s+)/g, '\n$1')
        .replace(/\n{2,}/g, '\n');
    const lines = normalized.split('\n').map(line => line.trim()).filter(Boolean);

    const numberedItems = lines.filter(line => /^\d+\.\s+/.test(line));
    const bulletItems   = lines.filter(line => /^[-*•]\s+/.test(line));

    if (numberedItems.length >= 2) {
        const intro = lines.find(line => !/^\d+\.\s+/.test(line) && !/^[-*•]\s+/.test(line));
        const items = numberedItems.map(line => `<li>${formatInlineMarkdown(line.replace(/^\d+\.\s+/, ''))}</li>`).join('');
        const introHtml = intro ? `<p>${formatInlineMarkdown(intro)}</p>` : '';
        return `${introHtml}<ol class="reply-list">${items}</ol>`;
    }

    if (bulletItems.length >= 2) {
        const intro = lines.find(line => !/^\d+\.\s+/.test(line) && !/^[-*•]\s+/.test(line));
        const items = bulletItems.map(line => `<li>${formatInlineMarkdown(line.replace(/^[-*•]\s+/, ''))}</li>`).join('');
        const introHtml = intro ? `<p>${formatInlineMarkdown(intro)}</p>` : '';
        return `${introHtml}<ul class="reply-list">${items}</ul>`;
    }

    return lines.map(line => `<p>${formatInlineMarkdown(line)}</p>`).join('');
}

function formatInlineMarkdown(text) {
    const escaped = escapeHtml(String(text || ''));
    return escaped.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ===========================================================================
// Persist conversation history
// ===========================================================================

window.addEventListener('beforeunload', () => {
    localStorage.setItem('conversationHistory', JSON.stringify(conversationHistory));
});

window.addEventListener('load', () => {
    const saved = localStorage.getItem('conversationHistory');
    if (saved) {
        try {
            conversationHistory = JSON.parse(saved);
        } catch (e) {
            conversationHistory = [];
        }
    }
});
