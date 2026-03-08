const API_BASE = "http://127.0.0.1:8000/api/v1";
const WS_BASE = "ws://127.0.0.1:8000";

// Device info for authentication
const DEVICE_ID = localStorage.getItem("device_id") || `web_${Math.random().toString(36).substring(2, 15)}`;
localStorage.setItem("device_id", DEVICE_ID);
const DEVICE_NAME = "Web Browser";
const PLATFORM = "web";

// Firebase configuration
const firebaseConfig = {
  apiKey: "AIzaSyDCfsnoCwWy3lut2aCrewoW3McCMqTpZ5k",
  authDomain: "nexchat-3a27a.firebaseapp.com",
  databaseURL: "https://nexchat-3a27a-default-rtdb.asia-southeast1.firebasedatabase.app",
  projectId: "nexchat-3a27a",
  storageBucket: "nexchat-3a27a.firebasestorage.app",
  messagingSenderId: "378052560187",
  appId: "1:378052560187:web:48d56e0095399d8f18231e",
  measurementId: "G-D533SNCCRW"
};

// Initialize Firebase
firebase.initializeApp(firebaseConfig);
const auth = firebase.auth();
const googleProvider = new firebase.auth.GoogleAuthProvider();

let token = localStorage.getItem("token");
let ws = null;
let currentChatId = null;
let currentChatUserId = null;
let myId = null;
let myProfile = null;
let typingTimeout = null;
let searchTimeout = null;

// Helper for Fetch Headers
function getAuthHeaders() {
    return {
        "Authorization": `Session ${token}`,
        "Device-Id": DEVICE_ID,
        "Content-Type": "application/json"
    };
}

// Auto-login if token exists
if (token) { checkProfileStatus(); }

async function checkProfileStatus() {
    try {
        const res = await fetch(`${API_BASE}/users/me`, {
            headers: getAuthHeaders()
        });
        if (!res.ok) throw new Error();
        myProfile = await res.json();

        if (!myProfile.is_profile_complete) {
            showSetupScreen();
        } else {
            showMainApp();
        }
    } catch (err) { logout(); }
}

function showSetupScreen() {
    document.getElementById("auth-section").classList.add("hidden");
    document.getElementById("setup-section").classList.remove("hidden");
    document.getElementById("main-app").classList.add("hidden");
    document.getElementById("user-info").classList.add("hidden");

    document.getElementById("setup-name").value = myProfile.full_name || "";
    if (myProfile.profile_photo_url) {
        document.getElementById("setup-avatar-preview").innerHTML = `<img src="${myProfile.profile_photo_url}" class="w-full h-full object-cover">`;
    }
}

// --- PROFILE SETUP LOGIC ---
function previewSetupPhoto(input) {
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = (e) => {
            document.getElementById("setup-avatar-preview").innerHTML = `<img src="${e.target.result}" class="w-full h-full object-cover">`;
        };
        reader.readAsDataURL(input.files[0]);
    }
}

async function saveSetup() {
    const name = document.getElementById("setup-name").value.trim();
    const photoInput = document.getElementById("setup-photo-input");

    try {
        const profileRes = await fetch(`${API_BASE}/users/me`, {
            method: "PUT",
            headers: getAuthHeaders(),
            body: JSON.stringify({ full_name: name })
        });

        if (!profileRes.ok) throw new Error("Failed to update profile");

        if (photoInput.files[0]) {
            const formData = new FormData();
            formData.append("file", photoInput.files[0]);
            const headers = getAuthHeaders();
            delete headers["Content-Type"];

            await fetch(`${API_BASE}/uploads/profile-photo`, {
                method: "POST",
                headers: headers,
                body: formData
            });
        }

        showMainApp();
    } catch (err) {
        alert(err.message);
    }
}

async function skipSetup() {
    try {
        await fetch(`${API_BASE}/users/me`, {
            method: "PUT",
            headers: getAuthHeaders(),
            body: JSON.stringify({})
        });
        showMainApp();
    } catch (err) {
        showMainApp();
    }
}

// --- AUTH FLOW ---
function resetAuthUI() {
    document.getElementById("otp-container").classList.add("hidden");
    document.getElementById("verify-otp-btn").classList.add("hidden");
    document.getElementById("request-actions").classList.remove("hidden");
    document.getElementById("otp").value = "";
}

function showOTPInput() {
    const email = document.getElementById("email").value.trim();
    if(!email) return alert("Please enter your email first so we know which account to verify");

    document.getElementById("otp-container").classList.remove("hidden");
    document.getElementById("verify-otp-btn").classList.remove("hidden");
    document.getElementById("request-actions").classList.add("hidden");
    document.getElementById("otp").focus();
}

async function requestOTP() {
    const email = document.getElementById("email").value.trim();
    if(!email) return alert("Please enter your email");

    const btn = document.getElementById("request-otp-btn");
    btn.disabled = true;
    btn.innerText = "Sending...";

    try {
        const res = await fetch(`${API_BASE}/auth/otp/request`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email })
        });
        const data = await res.json();
        if (res.ok) {
            showOTPInput();
        } else alert(data.detail || "Failed to send OTP");
    } catch (err) { alert("Connection error"); }
    finally {
        btn.disabled = false;
        btn.innerText = "Get Verification Code";
    }
}

async function verifyOTP() {
    const email = document.getElementById("email").value.trim();
    const otp = document.getElementById("otp").value.trim();
    if(!otp || otp.length < 6) return alert("Enter 6-digit code");

    try {
        const res = await fetch(`${API_BASE}/auth/otp/verify`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                email,
                otp,
                device_id: DEVICE_ID,
                device_name: DEVICE_NAME,
                platform: PLATFORM
            })
        });
        const data = await res.json();
        if (res.ok) {
            token = data.session_id;
            localStorage.setItem("token", token);
            handleAuthResult(data);
        } else alert(data.detail || "Invalid code");
    } catch (err) { alert("Verification failed"); }
}

async function googleLogin() {
    try {
        const result = await auth.signInWithPopup(googleProvider);
        const idToken = await result.user.getIdToken();

        const res = await fetch(`${API_BASE}/auth/google`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                id_token: idToken,
                device_id: DEVICE_ID,
                device_name: DEVICE_NAME,
                platform: PLATFORM
            })
        });
        const data = await res.json();
        if (res.ok) {
            token = data.session_id;
            localStorage.setItem("token", token);
            handleAuthResult(data);
        } else alert("Google Login failed on server");
    } catch (err) { alert("Google Login cancelled"); }
}

function handleAuthResult(data) {
    if (!data.is_profile_complete) {
        checkProfileStatus();
    } else {
        showMainApp();
    }
}

async function showMainApp() {
    document.getElementById("auth-section").classList.add("hidden");
    document.getElementById("setup-section").classList.add("hidden");
    document.getElementById("main-app").classList.remove("hidden");
    document.getElementById("user-info").classList.remove("hidden");

    try {
        const res = await fetch(`${API_BASE}/users/me`, {
            headers: getAuthHeaders()
        });
        myProfile = await res.json();
        myId = myProfile.id;

        document.getElementById("me-name").innerText = myProfile.full_name || "User";
        if (myProfile.profile_photo_url) {
            document.getElementById("nav-my-avatar").innerHTML = `<img src="${myProfile.profile_photo_url}" class="w-full h-full object-cover">`;
        }

        loadChatList();
        connectWebSocket();
    } catch (err) { logout(); }
}

// --- WEB SOCKET & MESSAGING ---
function connectWebSocket() {
    if (ws) ws.close();
    ws = new WebSocket(`${WS_BASE}/ws?session_id=${token}&device_id=${DEVICE_ID}`);

    ws.onmessage = (event) => {
        const { type, payload } = JSON.parse(event.data);
        if (type === "message") {
            if (payload.chat_id === currentChatId) appendMessage(payload);
            const lastMsgEl = document.getElementById(`last-msg-${payload.chat_id}`);
            if (lastMsgEl) lastMsgEl.innerText = payload.content || "Image 📷";
        } else if (type === "presence") {
            updatePresenceInUI(payload);
        } else if (type === "typing") {
            if (payload.chat_id === currentChatId && payload.user_id !== myId) {
                showTypingIndicator(payload.is_typing);
            }
        } else if (type === "message_status_update") {
            updateReadReceipt(payload);
        }
    };
}

function updateReadReceipt(payload) {
    const tickEl = document.querySelector(`#msg-${payload.message_id} .ticks`);
    if (!tickEl) return;

    if (payload.status === "read") {
        tickEl.innerHTML = `<span style="color: #34B7F1">✔✔</span>`;
    } else if (payload.status === "delivered") {
        tickEl.innerHTML = `<span style="color: #AAAAAA">✔✔</span>`;
    }
}

function showTypingIndicator(isTyping) {
    const container = document.getElementById("messages");
    let bubble = document.getElementById("typing-bubble");

    const statusEl = document.getElementById("chat-with-status");
    const originalStatus = document.getElementById("chat-status-dot").classList.contains("bg-green-500") ? "ONLINE" : "OFFLINE";

    if (isTyping) {
        statusEl.innerText = "typing...";
        statusEl.classList.add("text-indigo-600");

        if (!bubble) {
            bubble = document.createElement("div");
            bubble.id = "typing-bubble";
            bubble.className = "self-start bg-white p-3 px-4 rounded-2xl rounded-tl-none shadow-sm mb-3 flex items-center space-x-1 border border-gray-100 animate-in fade-in slide-in-from-bottom-1 duration-200";
            bubble.innerHTML = `
                <div class="w-1.5 h-1.5 bg-gray-300 rounded-full animate-bounce" style="animation-duration: 0.8s"></div>
                <div class="w-1.5 h-1.5 bg-gray-300 rounded-full animate-bounce" style="animation-duration: 0.8s; animation-delay: 0.1s"></div>
                <div class="w-1.5 h-1.5 bg-gray-300 rounded-full animate-bounce" style="animation-duration: 0.8s; animation-delay: 0.2s"></div>
            `;
            container.appendChild(bubble);
            container.scrollTop = container.scrollHeight;
        }
    } else {
        statusEl.innerText = originalStatus;
        statusEl.classList.remove("text-indigo-600");
        if (bubble) bubble.remove();
    }
}

function appendMessage(msg) {
    const container = document.getElementById("messages");
    if (document.getElementById(`msg-${msg.id}`)) return;

    const bubble = document.getElementById("typing-bubble");
    if (bubble) bubble.remove();

    const isMe = msg.sender_id === myId;
    const div = document.createElement("div");
    div.id = `msg-${msg.id}`;
    div.className = `max-w-[80%] p-2 px-3 rounded-2xl text-[13px] shadow-sm flex flex-col relative ${isMe ? 'bg-indigo-600 text-white self-end rounded-tr-none' : 'bg-white text-gray-800 self-start rounded-tl-none border border-gray-100'}`;

    let content = `<span>${msg.content || ''}</span>`;
    if (msg.media_url) content = `<img src="${msg.media_url}" class="rounded-xl mb-1 max-w-full h-auto shadow-sm">` + content;

    const time = msg.created_at ? new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : "";

    // TICK LOGIC: Only for Sender
    let ticks = "";
    if (isMe) {
        const status = msg.status || [];
        const isRead = status.some(s => s.read_at);
        const isDelivered = status.some(s => s.delivered_at);

        if (isRead) {
            ticks = `<span class="ticks" style="color: #34B7F1">✔✔</span>`;
        } else if (isDelivered) {
            ticks = `<span class="ticks" style="color: #AAAAAA">✔✔</span>`;
        } else {
            ticks = `<span class="ticks" style="color: #AAAAAA">✔</span>`;
        }
    }

    div.innerHTML = `
        ${content}
        <div class="flex items-center self-end space-x-1 mt-0.5" style="font-size: 9px; line-height: 1">
            <span class="${isMe ? 'text-indigo-200' : 'text-gray-400'}">${time}</span>
            ${ticks}
        </div>
    `;

    container.appendChild(div);
    if (bubble && !isMe) container.appendChild(bubble);
    container.scrollTop = container.scrollHeight;

    if (!isMe) {
        sendStatusUpdate(msg.id, msg.chat_id, "delivered");
        setTimeout(() => sendStatusUpdate(msg.id, msg.chat_id, "read"), 500);
    }
}

function sendStatusUpdate(messageId, chatId, status) {
    if (!ws || ws.readyState !== WebSocket.OPEN) return;
    ws.send(JSON.stringify({
        type: "read_receipt",
        payload: {
            message_id: messageId,
            chat_id: chatId,
            status: status
        }
    }));
}

function sendTypingStatus() {
    if (!ws || ws.readyState !== WebSocket.OPEN || !currentChatId) return;

    ws.send(JSON.stringify({
        type: "typing",
        payload: {
            chat_id: currentChatId,
            is_typing: true
        }
    }));

    if (typingTimeout) clearTimeout(typingTimeout);
    typingTimeout = setTimeout(() => {
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({
                type: "typing",
                payload: {
                    chat_id: currentChatId,
                    is_typing: false
                }
            }));
        }
    }, 2000);
}

function sendMessage() {
    const input = document.getElementById("msg-input");
    if (!input.value.trim() || !ws || ws.readyState !== WebSocket.OPEN || !currentChatId) return;
    ws.send(JSON.stringify({ type: "message", payload: { chat_id: currentChatId, content: input.value.trim(), type: "text" } }));
    input.value = "";

    if (typingTimeout) clearTimeout(typingTimeout);
    ws.send(JSON.stringify({
        type: "typing",
        payload: {
            chat_id: currentChatId,
            is_typing: false
        }
    }));
}

async function loadChatList() {
    const res = await fetch(`${API_BASE}/chats/`, { headers: getAuthHeaders() });
    const chats = await res.json();
    const container = document.getElementById("chat-list");
    container.innerHTML = "";
    chats.forEach(chat => {
        const other = chat.other_user || { full_name: "NexChat User", id: 'ghost' };
        const div = document.createElement("div");
        div.className = `p-4 border-b border-gray-50 flex items-center space-x-3 cursor-pointer hover:bg-gray-50 transition-all ${currentChatId === chat.id ? 'bg-indigo-50/50 border-l-4 border-l-indigo-600' : ''}`;
        div.onclick = () => selectChat(chat.id, other.full_name, other.id, other.is_online);
        div.innerHTML = `
            <div class="w-11 h-11 rounded-full bg-indigo-100 flex items-center justify-center font-black text-indigo-600 uppercase border shadow-sm">
                ${other.profile_photo_url ? `<img src="${other.profile_photo_url}" class="w-full h-full object-cover rounded-full">` : other.full_name[0]}
            </div>
            <div class="flex-1 min-w-0">
                <div class="flex justify-between items-baseline">
                    <h4 class="text-sm font-bold truncate text-gray-800">${other.full_name}</h4>
                    <span id="status-${other.id}" class="text-[8px] font-black uppercase tracking-tighter ${other.is_online ? 'text-green-500' : 'text-gray-300'}">${other.is_online ? 'online' : 'offline'}</span>
                </div>
                <p id="last-msg-${chat.id}" class="text-xs text-gray-400 truncate mt-0.5">${chat.last_message ? chat.last_message.content : 'New conversation'}</p>
            </div>`;
        container.appendChild(div);
    });
}

async function selectChat(chatId, name, otherId, isOnline) {
    currentChatId = chatId;
    currentChatUserId = otherId;
    document.getElementById("no-chat-selected").classList.add("hidden");
    document.getElementById("chat-with-name").innerText = name;
    document.getElementById("chat-avatar").innerText = name[0];
    document.getElementById("chat-actions").classList.remove("hidden");

    const res = await fetch(`${API_BASE}/messages/?chat_id=${chatId}`, { headers: getAuthHeaders() });
    const messages = await res.json();
    const msgContainer = document.getElementById("messages");
    msgContainer.innerHTML = "";

    const orderedMessages = messages.reverse();
    orderedMessages.forEach(appendMessage);

    orderedMessages.forEach(msg => {
        if (msg.sender_id !== myId) {
            const hasMyRead = (msg.status || []).some(s => s.user_id === myId && s.read_at);
            if (!hasMyRead) {
                sendStatusUpdate(msg.id, chatId, "read");
            }
        }
    });

    updatePresenceInUI({ user_id: otherId, status: isOnline ? 'online' : 'offline' });
}

function updatePresenceInUI(payload) {
    const sidebarStatus = document.getElementById(`status-${payload.user_id}`);
    if (sidebarStatus) {
        sidebarStatus.innerText = payload.status.toUpperCase();
        sidebarStatus.className = `text-[8px] font-black uppercase tracking-tighter ${payload.status === 'online' ? 'text-green-500' : 'text-gray-300'}`;
    }
    if (payload.user_id === currentChatUserId) {
        document.getElementById("chat-with-status").innerText = payload.status.toUpperCase();
        document.getElementById("chat-status-dot").className = `w-2 h-2 rounded-full ${payload.status === 'online' ? 'bg-green-500' : 'bg-gray-300'}`;
    }
}

// --- SEARCH & UTILS ---
function debouncedSearch() {
    const q = document.getElementById("search-email").value.trim();
    if (!q.includes('@')) { if (!q) clearSearch(); return; }
    if (searchTimeout) clearTimeout(searchTimeout);
    searchTimeout = setTimeout(async () => {
        const res = await fetch(`${API_BASE}/users/find-contact?email=${q}`, { headers: getAuthHeaders() });
        if (res.ok) {
            const users = await res.json();
            const container = document.getElementById("search-results-list");
            document.getElementById("search-results-container").classList.remove("hidden");
            container.innerHTML = users.length ? "" : '<p class="text-xs text-gray-400">User not found</p>';
            users.forEach(u => {
                const div = document.createElement("div");
                div.className = "flex justify-between items-center p-2 bg-white rounded-xl mb-2 shadow-sm border border-indigo-50";
                div.innerHTML = `<div class="text-xs font-bold">${u.email}</div>
                    <button onclick="startChat('${u.id}','${u.full_name || u.email}',${u.is_online})" class="bg-indigo-600 text-white text-[10px] px-3 py-1 rounded-lg font-bold">CHAT</button>`;
                container.appendChild(div);
            });
        }
    }, 500);
}

async function startChat(userId, name, isOnline) {
    const res = await fetch(`${API_BASE}/chats/`, {
        method: "POST",
        headers: getAuthHeaders(),
        body: JSON.stringify({ members: [userId], type: "direct" })
    });
    if (res.ok) {
        const chat = await res.json();
        clearSearch();
        document.getElementById("search-email").value = "";
        loadChatList();
        selectChat(chat.id, name, userId, isOnline);
    }
}

function clearSearch() { document.getElementById("search-results-container").classList.add("hidden"); }
function logout() { localStorage.clear(); location.reload(); }
function closeModal() { document.getElementById("profile-modal").classList.add("hidden"); }
function showProfileModal(type) {
    document.getElementById("profile-modal").classList.remove("hidden");
    if (type === 'me') {
        document.getElementById("p-name").innerText = myProfile.full_name || "User";
        document.getElementById("p-email").innerText = myProfile.email;
        document.getElementById("p-bio").innerText = myProfile.bio || "Hey there! I am using NexChat.";
        document.getElementById("my-profile-actions").classList.remove("hidden");
        if (myProfile.profile_photo_url) document.getElementById("p-avatar").innerHTML = `<img src="${myProfile.profile_photo_url}" class="w-full h-full object-cover">`;
    }
}
