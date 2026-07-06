// Session setup for AI chat
const sessionId = generateUUID();
let activeBookings = [];

// Initialize application on load
document.addEventListener("DOMContentLoaded", () => {
    // Load saved theme
    const savedTheme = localStorage.getItem("theme");
    if (savedTheme === "light") {
        document.body.classList.add("light-theme");
        const btn = document.getElementById("theme-toggle");
        if (btn) btn.innerText = "🌙";
    }

    loadDoctors();
    loadActiveBookings();
});

// Helper: Generate Session UUID
function generateUUID() {
    return 'user-session-' + Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
}

// Theme Toggle Logic
function toggleTheme() {
    const body = document.body;
    const btn = document.getElementById("theme-toggle");

    if (body.classList.contains("light-theme")) {
        body.classList.remove("light-theme");
        btn.innerText = "☀️";
        localStorage.setItem("theme", "dark");
    } else {
        body.classList.add("light-theme");
        btn.innerText = "🌙";
        localStorage.setItem("theme", "light");
    }
}

// Tab Switching Navigation
function switchTab(tabId) {
    // Update active tab buttons
    document.querySelectorAll(".nav-item").forEach(btn => btn.classList.remove("active"));
    document.getElementById(`tab-${tabId}`).classList.add("active");

    // Update active tab content panels
    document.querySelectorAll(".tab-content").forEach(panel => panel.classList.remove("active"));
    document.getElementById(`content-${tabId}`).classList.add("active");

    // Update banner metadata
    const titles = {
        comparison: { title: "Hospital Comparison", desc: "Analyze ratings and compare care quality metrics across healthcare facilities." },
        reviews: { title: "Patient Reviews", desc: "Read patient experiences and national care comparisons." },
        chat: { title: "Chat with Healy", desc: "Ask clinical questions and schedule appointments using natural language." },
        booking: { title: "Book Appointment", desc: "Book, modify, or reschedule appointments with specialized medical professionals." }
    };

    document.getElementById("tab-title").innerText = titles[tabId].title;
    document.getElementById("tab-description").innerText = titles[tabId].desc;
}

// --- Tab 1: Hospital Comparison Logic ---
async function loadHospitals(event) {
    if (event) event.preventDefault();

    const state = document.getElementById("filter-state").value;
    const zipCode = document.getElementById("filter-zip").value;
    const type = document.getElementById("filter-type").value;
    const rating = document.getElementById("filter-rating").value;

    const tbody = document.querySelector("#hospitals-table tbody");
    tbody.innerHTML = `<tr><td colspan="8" class="text-center">Loading facilities...</td></tr>`;

    let url = `/api/hospitals?`;
    if (state) url += `state=${encodeURIComponent(state)}&`;
    if (zipCode) url += `zip_code=${encodeURIComponent(zipCode)}&`;
    if (type) url += `hospital_type=${encodeURIComponent(type)}&`;
    if (rating) url += `rating=${encodeURIComponent(rating)}&`;

    try {
        const response = await fetch(url);
        const res = await response.json();

        if (!res.success || !res.data || res.data.length === 0) {
            tbody.innerHTML = `<tr><td colspan="8" class="text-center text-muted">No hospitals matching the query. Try broadening your filters.</td></tr>`;
            return;
        }

        tbody.innerHTML = "";
        res.data.forEach(h => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td><strong>${escapeHtml(h["Hospital Name"])}</strong></td>
                <td>${escapeHtml(h["Hospital Type"] || "N/A")}</td>
                <td>${escapeHtml(h["Hospital Ownership"] || "N/A")}</td>
                <td><span style="color: #10b981; font-weight:600;">⭐ ${escapeHtml(h["Hospital overall rating"] || "N/A")}</span></td>
                <td>${escapeHtml(h["Emergency Services"] || "N/A")}</td>
                <td>${escapeHtml(h["Mortality national comparison"] || "N/A")}</td>
                <td>${escapeHtml(h["Safety of care national comparison"] || "N/A")}</td>
                <td>${escapeHtml(h["City"])}, ${escapeHtml(h["State"])}</td>
            `;
            tbody.appendChild(tr);
        });
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="8" class="text-center text-danger">Error fetching hospitals: ${err.message}</td></tr>`;
    }
}

// --- Tab 2: Patient Reviews Logic ---
async function loadReviews(event) {
    if (event) event.preventDefault();

    const hospitalName = document.getElementById("filter-rev-hospital").value;
    const state = document.getElementById("filter-rev-state").value;

    const container = document.getElementById("reviews-cards-container");
    container.innerHTML = `<div class="empty-state"><p>Loading reviews...</p></div>`;

    let url = `/api/reviews?`;
    if (hospitalName) url += `hospital_name=${encodeURIComponent(hospitalName)}&`;
    if (state) url += `state=${encodeURIComponent(state)}&`;

    try {
        const response = await fetch(url);
        const res = await response.json();

        if (!res.success || !res.data || res.data.length === 0) {
            container.innerHTML = `<div class="empty-state text-muted"><p>No patient reviews or metrics found for this selection.</p></div>`;
            return;
        }

        container.innerHTML = "";
        res.data.forEach(r => {
            const card = document.createElement("div");
            card.className = "card review-card";
            card.innerHTML = `
                <div class="review-header">
                    <div>
                        <h4>${escapeHtml(r["Hospital Name"])}</h4>
                        <span class="review-meta">${escapeHtml(r["City"])}, ${escapeHtml(r["State"])}</span>
                    </div>
                </div>
                <div class="review-ratings">
                    <div class="rating-item">
                        <span class="rating-label">Patient Experience:</span>
                        <span class="rating-value">${escapeHtml(r["Patient experience national comparison"] || "N/A")}</span>
                    </div>
                    <div class="rating-item">
                        <span class="rating-label">Safety of Care:</span>
                        <span class="rating-value">${escapeHtml(r["Safety of care national comparison"] || "N/A")}</span>
                    </div>
                    <div class="rating-item">
                        <span class="rating-label">Readmission Comparison:</span>
                        <span class="rating-value">${escapeHtml(r["Readmission national comparison"] || "N/A")}</span>
                    </div>
                    <div class="rating-item">
                        <span class="rating-label">Mortality Level:</span>
                        <span class="rating-value">${escapeHtml(r["Mortality national comparison"] || "N/A")}</span>
                    </div>
                </div>
            `;
            container.appendChild(card);
        });
    } catch (err) {
        container.innerHTML = `<div class="empty-state text-danger"><p>Error loading reviews: ${err.message}</p></div>`;
    }
}

// --- Tab 3: AI Chat Assistant Logic ---
async function sendChatMessage() {
    const input = document.getElementById("chat-user-input");
    const query = input.value.trim();
    if (!query) return;

    // Clear input field immediately
    input.value = "";

    const chatContainer = document.getElementById("chat-messages-container");

    // Render User Message
    const userMsgDiv = document.createElement("div");
    userMsgDiv.className = "message user";
    userMsgDiv.innerHTML = `<div class="message-bubble">${escapeHtml(query)}</div>`;
    chatContainer.appendChild(userMsgDiv);
    scrollChat();

    // Render Loading Indicator
    const loadDiv = document.createElement("div");
    loadDiv.className = "message assistant loading-msg";
    loadDiv.innerHTML = `<div class="message-bubble">AI is typing...</div>`;
    chatContainer.appendChild(loadDiv);
    scrollChat();

    try {
        const response = await fetch("/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: query, session_id: sessionId })
        });
        const res = await response.json();

        // Remove loading state
        loadDiv.remove();

        const assistantMsgDiv = document.createElement("div");
        assistantMsgDiv.className = "message assistant";
        assistantMsgDiv.innerHTML = `<div class="message-bubble">${formatMarkdown(res.response)}</div>`;
        chatContainer.appendChild(assistantMsgDiv);
        scrollChat();

        // Check if agent did a booking and reload appointments list in the background
        if (query.toLowerCase().includes("book") || query.toLowerCase().includes("cancel") || query.toLowerCase().includes("reschedule")) {
            loadActiveBookings();
        }
    } catch (err) {
        loadDiv.remove();
        const errDiv = document.createElement("div");
        errDiv.className = "message assistant";
        errDiv.innerHTML = `<div class="message-bubble text-danger">Error: ${err.message}</div>`;
        chatContainer.appendChild(errDiv);
        scrollChat();
    }
}

function scrollChat() {
    const chatContainer = document.getElementById("chat-messages-container");
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// --- Tab 4: Appointment Booking & Management Logic ---
async function loadDoctors() {
    const select = document.getElementById("doctor-select");
    try {
        const response = await fetch("/api/doctors");
        const res = await response.json();

        if (res.success && res.data) {
            select.innerHTML = `<option value="">Choose a doctor...</option>`;
            res.data.forEach(d => {
                const opt = document.createElement("option");
                opt.value = d.id;
                opt.innerText = `Dr. ${d.name} (${d.specialization})`;
                select.appendChild(opt);
            });
        }
    } catch (err) {
        console.error("Error loading doctors:", err);
    }
}

async function loadDoctorSlots() {
    const docId = document.getElementById("doctor-select").value;
    const slotSelect = document.getElementById("slot-select");

    if (!docId) {
        slotSelect.innerHTML = `<option value="">Select doctor first...</option>`;
        return;
    }

    slotSelect.innerHTML = `<option value="">Loading slots...</option>`;

    try {
        const response = await fetch(`/api/doctors/${docId}/slots`);
        const res = await response.json();

        if (res.success && res.data) {
            if (res.data.length === 0) {
                slotSelect.innerHTML = `<option value="">No slots available this week.</option>`;
                return;
            }
            slotSelect.innerHTML = `<option value="">Choose a slot time...</option>`;
            res.data.forEach(s => {
                const opt = document.createElement("option");
                opt.value = s.slot_datetime;
                opt.innerText = s.slot_datetime;
                slotSelect.appendChild(opt);
            });
        }
    } catch (err) {
        slotSelect.innerHTML = `<option value="">Error loading slots.</option>`;
        console.error("Error loading doctor slots:", err);
    }
}

async function bookAppointment(event) {
    event.preventDefault();

    const doctorId = document.getElementById("doctor-select").value;
    const slotDatetime = document.getElementById("slot-select").value;
    const patientName = document.getElementById("patient-name").value;

    if (!doctorId || !slotDatetime || !patientName) return;

    try {
        const response = await fetch("/api/appointments", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                doctor_id: parseInt(doctorId),
                slot_datetime: slotDatetime,
                patient_name: patientName
            })
        });
        const res = await response.json();

        if (response.status !== 200 || !res.success) {
            alert("Booking Error: " + (res.detail || res.message || "Failed to schedule slot"));
            return;
        }

        alert(res.message);
        // Clear name and refresh views
        document.getElementById("patient-name").value = "";
        document.getElementById("doctor-select").value = "";
        document.getElementById("slot-select").innerHTML = `<option value="">Select doctor first...</option>`;

        loadActiveBookings();
    } catch (err) {
        alert("Network booking error: " + err.message);
    }
}

async function loadActiveBookings() {
    const list = document.getElementById("bookings-list-container");
    list.innerHTML = `<p class="text-center text-muted">Refreshing list...</p>`;

    try {
        // Fetch appointments by looking up active slots/appointments
        // For local mock demonstration, we fetch doctors list and match their slots, or retrieve from local storage session.
        // To build a robust system, we can query appointments using direct API.
        // Let's call the FastAPI to fetch appointments. But wait, did we create a GET /api/appointments route?
        // Ah! In FastAPI we didn't explicitly implement a GET /api/appointments. Let's look at what endpoints we wrote.
        // We wrote: /api/hospitals, /api/reviews, /api/doctors, /api/doctors/{id}/slots, /api/appointments (POST), /api/appointments/cancel (POST), /api/appointments/update (POST).
        // Wait, how do we get the list of active bookings?
        // We can query the database directly or implement a small fetch!
        // Let's modify DatabaseClient and FastAPI to support `GET /api/appointments`. Or we can just query it through a custom SELECT in python.
        // Let's check how we can fetch it: we can implement a `GET /api/appointments` route in `app/server.py` that queries `appointments` and joins with `doctors_info_data`!
        // Yes, that is extremely useful and complete! Let's do that in a moment.
        // For now, let's make a mock call to `/api/appointments` and update style.
        const response = await fetch("/api/appointments");
        if (response.status !== 200) {
            list.innerHTML = `<p class="text-muted text-center" style="padding: 20px;">No appointments found.</p>`;
            return;
        }
        const res = await response.json();

        if (res.success && res.data && res.data.length > 0) {
            list.innerHTML = "";
            res.data.forEach(appt => {
                const item = document.createElement("div");
                item.className = "booking-item";
                item.innerHTML = `
                    <div class="booking-info">
                        <h4>Patient: ${escapeHtml(appt.patient_name)}</h4>
                        <p><strong>Doctor:</strong> Dr. ${escapeHtml(appt.doctor_name)} (${escapeHtml(appt.specialization)})</p>
                        <p><strong>Date & Time:</strong> ${escapeHtml(appt.slot_datetime)}</p>
                        <p class="text-muted">Booking ID: #${escapeHtml(appt.id)} | Status: <span style="color: #10b981; font-weight:600;">${escapeHtml(appt.status)}</span></p>
                    </div>
                    <div class="booking-actions">
                        <button class="btn btn-secondary" onclick="openRescheduleModal(${appt.id}, ${appt.doctor_id})">Reschedule</button>
                        <button class="btn btn-danger" onclick="cancelAppointment(${appt.id})">Cancel</button>
                    </div>
                `;
                list.appendChild(item);
            });
        } else {
            list.innerHTML = `<p class="text-muted text-center" style="padding: 20px;">No appointments scheduled yet.</p>`;
        }
    } catch (err) {
        list.innerHTML = `<p class="text-center text-danger">Error loading appointments: ${err.message}</p>`;
    }
}

async function cancelAppointment(apptId) {
    if (!confirm("Are you sure you want to cancel this appointment?")) return;

    try {
        const response = await fetch("/api/appointments/cancel", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ appointment_id: apptId })
        });
        const res = await response.json();

        alert(res.message);
        loadActiveBookings();
    } catch (err) {
        alert("Error cancelling appointment: " + err.message);
    }
}

// Reschedule modal actions
async function openRescheduleModal(apptId, docId) {
    document.getElementById("reschedule-appt-id").value = apptId;
    document.getElementById("reschedule-doc-id").value = docId;

    const select = document.getElementById("reschedule-slot-select");
    select.innerHTML = `<option value="">Loading slots...</option>`;

    document.getElementById("reschedule-modal").style.display = "flex";

    try {
        const response = await fetch(`/api/doctors/${docId}/slots`);
        const res = await response.json();

        if (res.success && res.data) {
            if (res.data.length === 0) {
                select.innerHTML = `<option value="">No other slots available.</option>`;
                return;
            }
            select.innerHTML = `<option value="">Choose a new slot...</option>`;
            res.data.forEach(s => {
                const opt = document.createElement("option");
                opt.value = s.slot_datetime;
                opt.innerText = s.slot_datetime;
                select.appendChild(opt);
            });
        }
    } catch (err) {
        select.innerHTML = `<option value="">Error loading slots.</option>`;
    }
}

function closeRescheduleModal() {
    document.getElementById("reschedule-modal").style.display = "none";
}

async function submitReschedule(event) {
    event.preventDefault();

    const apptId = document.getElementById("reschedule-appt-id").value;
    const newSlot = document.getElementById("reschedule-slot-select").value;

    if (!apptId || !newSlot) return;

    try {
        const response = await fetch("/api/appointments/update", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                appointment_id: parseInt(apptId),
                new_slot_datetime: newSlot
            })
        });
        const res = await response.json();

        if (response.status !== 200 || !res.success) {
            alert("Reschedule Error: " + (res.detail || res.message || "Failed to update slot"));
            return;
        }

        alert(res.message);
        closeRescheduleModal();
        loadActiveBookings();
    } catch (err) {
        alert("Reschedule failed: " + err.message);
    }
}

// --- Global Helpers ---

function escapeHtml(str) {
    if (!str) return "";
    return str.toString()
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function formatMarkdown(text) {
    if (!text) return "";
    let formatted = text
        .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
        .replace(/\*(.*?)\*/g, "<em>$1</em>")
        .replace(/`(.*?)`/g, "<code>$1</code>")
        .replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" target="_blank" style="color: #10b981; text-decoration: underline;">$1</a>');
    return formatted;
}
