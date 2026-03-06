const API_BASE = "http://127.0.0.1:8000/api/v1";
const WS_BASE = "ws://127.0.0.1:8000/ws";

// Real Firebase configuration provided by you
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

// Initialize Firebase (Compat mode for script tags)
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

if (token) { checkProfileStatus(); }

async function checkProfileStatus() {
    try {
        const res = await fetch(`${API_BASE}/users/me`, {
            headers: { "Authorization": `Bearer ${token}` }
        });
        if (!res.ok) throw new Error();
        myProfile = await res.json();

        // Agar profile incomplete hai toh setup screen dikhao, warna seedha app
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

    // Default values (could be from Google)
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
        // 1. Update Name (Always marks as complete due to backend logic on PUT)
        await fetch(`${API_BASE}/users/me`, {
            method: "PUT",
            headers: {
                "Authorization": `Bearer ${token}`,
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ full_name: name })
        });

        // 2. Update Photo if selected
        if (photoInput.files[0]) {
            const formData = new FormData();
            formData.append("file", photoInput.files[0]);
            await fetch(`${API_BASE}/uploads/profile-photo`, {
                method: "POST",
                headers: { "Authorization": `Bearer ${token}` },
                body: formData
            });
        }

        showMainApp();
    } catch (err) { alert("Failed to save profile"); }
}

async function skipSetup() {
    try {
        // Mark complete with empty PUT request
        await fetch(`${API_BASE}/users/me`, {
            method: "PUT",
            headers: {
                "Authorization": `Bearer ${token}`,
                "Content-Type": "application/json"
            },
            body: JSON.stringify({})
        });
        showMainApp();
    } catch (err) { showMainApp(); }
}

// --- AUTH ---
async function requestOTP() {
    const email = document.getElementById("email").value.trim();
    if(!email) return alert("Email required");

    try {
        const res = await fetch(`${API_BASE}/auth/otp/request`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email })
        });
        const data = await res.json();
        if (res.ok) {
            alert(data.message);
            document.getElementById("otp-container").classList.remove("hidden");
            document.getElementById("verify-otp-btn").classList.remove("hidden");
            document.getElementById("request-otp-btn").classList.add("hidden");
        } else alert(data.detail || "Failed to send OTP");
    } catch (err) { alert("Server error."); }
}

async function verifyOTP() {
    const email = document.getElementById("email").value.trim();
    const otp = document.getElementById("otp").value.trim();
    if(!email || !otp) return alert("Email and OTP required");

    try {
        const res = await fetch(`${API_BASE}/auth/otp/verify`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, otp })
        });
        const data = await res.json();
        if (res.ok) {
            token = data.access_token;
            localStorage.setItem("token", token);
            handleAuthResult(data);
        } else alert(data.detail || "OTP verification failed");
    } catch (err) { alert("Server error."); }
}

async function googleLogin() {
    try {
        const result = await auth.signInWithPopup(googleProvider);
        const idToken = await result.user.getIdToken();

        const res = await fetch(`${API_BASE}/auth/google`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ id_token: idToken })
        });
        const data = await res.json();
        if (res.ok) {
            token = data.access_token;
            localStorage.setItem("token", token);
            handleAuthResult(data);
        } else alert(data.detail || "Google Login failed at backend");
    } catch (err) {
        console.error(err);
        alert("Google Login failed: " + err.message);
    }
}

async function handleAuthResult(data) {
    if (!data.is_profile_complete) {
        // Fetch full profile first to get default name/photo from Google if any
        const res = await fetch(`${API_BASE}/users/me`, { headers: { "Authorization": `Bearer ${token}` } });
        myProfile = await res.json();
        showSetupScreen();
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
            headers: { "Authorization": `Bearer ${token}` }
        });
        if (!res.ok) throw new Error();
        myProfile = await res.json();
        myId = myProfile.id;
        localStorage.setItem("my_id", myId);

        document.getElementById("me-name").innerText = myProfile.full_name || "User";
        if (myProfile.profile_photo_url) {
            document.getElementById("nav-my-avatar").innerHTML = `<img src="${myProfile.profile_photo_url}" class="w-full h-full object-cover">`;
        }

        registerDeviceToken();
        loadChatList();
        connectWebSocket();
    } catch (err) { logout(); }
}

// --- PRIVACY ---
async function blockUser() {
    if (!currentChatUserId) return;
    const res = await fetch(`${API_BASE}/users/block/${currentChatUserId}`, { method: "POST", headers: { "Authorization": `Bearer ${token}` } });
    if (res.ok) { const data = await res.json(); alert(data.message); toggleBlockButtons(true); }
}

async function unblockUser() {
    if (!currentChatUserId) return;
    const res = await fetch(`${API_BASE}/users/unblock/${currentChatUserId}`, { method: "POST", headers: { "Authorization": `Bearer ${token}` } });
    if (res.ok) { const data = await res.json(); alert(data.message); toggleBlockButtons(false); }
}

function toggleBlockButtons(isBlocked) {
    document.getElementById("block-btn").classList.toggle("hidden", isBlocked);
    document.getElementById("unblock-btn").classList.toggle("hidden", !isBlocked);
}

// --- MESSAGING ---
function toggleTypingBubble(isTyping) {
    const container = document.getElementById("messages");
    let bubble = document.getElementById("typing-bubble");

    if (isTyping) {
        if (!bubble) {
            bubble = document.createElement("div");
            bubble.id = "typing-bubble";
            bubble.className = "self-start bg-white text-gray-400 p-2 px-4 rounded-xl text-[10px] italic shadow-sm mb-2 border border-gray-100 flex items-center space-x-1";
            bubble.innerHTML = `<span>typing</span><span class="animate-bounce">.</span><span class="animate-bounce" style="animation-delay: 0.2s">.</span><span class="animate-bounce" style="animation-delay: 0.4s">.</span>`;
            container.appendChild(bubble);
        }
        container.scrollTop = container.scrollHeight;
    } else {
        if (bubble) bubble.remove();
    }
}

async function deleteMessage(msgId) {
    if (!confirm("Delete this message?")) return;
    const res = await fetch(`${API_BASE}/messages/${msgId}`, { method: "DELETE", headers: { "Authorization": `Bearer ${token}` } });
    if (res.ok) handleMessageDeleted(msgId, true);
}

function handleMessageDeleted(msgId, isMe) {
    const el = document.getElementById(`msg-${msgId}`);
    if (el) {
        el.classList.remove('bg-indigo-600', 'bg-white', 'text-white', 'text-gray-800');
        el.classList.add('bg-gray-100', 'text-gray-400', 'italic', 'opacity-60', 'border-gray-200', 'border');
        el.innerHTML = `<span class="text-[11px]">🚫 ${isMe ? "You deleted this message" : "This message was deleted"}</span>`;
    }
}

// --- CORE REALTIME ---
function connectWebSocket() {
    if (ws) ws.close();
    ws = new WebSocket(`${WS_BASE}?token=${token}`);

    ws.onopen = () => console.log("WS Connected ✅");

    ws.onmessage = (event) => {
        const { type, payload } = JSON.parse(event.data);
        if (type === "message") {
            toggleTypingBubble(false);
            if (payload.chat_id === currentChatId) appendMessage(payload);
            const lastMsgEl = document.getElementById(`last-msg-${payload.chat_id}`);
            if (lastMsgEl) lastMsgEl.innerText = payload.content || "Image 📷";
        } else if (type === "message_delete") {
            handleMessageDeleted(payload.id, false);
        } else if (type === "presence") {
            updatePresenceInUI(payload);
        } else if (type === "typing" && payload.chat_id === currentChatId && payload.user_id !== myId) {
            toggleTypingBubble(payload.is_typing);
        }
    };

    ws.onclose = () => {
        console.log("WS Disconnected ❌. Reconnecting...");
        setTimeout(connectWebSocket, 3000);
    };
}

function updatePresenceInUI(payload) {
    const sidebarStatus = document.getElementById(`status-${payload.user_id}`);
    if (sidebarStatus) {
        sidebarStatus.innerText = payload.status.toUpperCase();
        sidebarStatus.className = `text-[9px] ${payload.status === "online" ? 'text-green-500' : 'text-gray-400'} font-bold uppercase`;
    }
    if (payload.user_id === currentChatUserId) {
        document.getElementById("chat-with-status").innerText = payload.status.toUpperCase();
        document.getElementById("chat-status-dot").className = `w-2 h-2 rounded-full ${payload.status === "online" ? 'bg-green-500' : 'bg-gray-300'}`;
    }
}

function sendTypingStatus() {
    if (!ws || ws.readyState !== WebSocket.OPEN || !currentChatId) return;
    ws.send(JSON.stringify({ type: "typing", payload: { chat_id: currentChatId, is_typing: true } }));
    if (typingTimeout) clearTimeout(typingTimeout);
    typingTimeout = setTimeout(() => {
        if (ws && ws.readyState === WebSocket.OPEN) ws.send(JSON.stringify({ type: "typing", payload: { chat_id: currentChatId, is_typing: false } }));
    }, 2000);
}

function sendMessage() {
    const input = document.getElementById("msg-input");
    if (!input.value.trim() || !ws || ws.readyState !== WebSocket.OPEN || !currentChatId) return;
    ws.send(JSON.stringify({ type: "message", payload: { chat_id: currentChatId, content: input.value.trim(), type: "text" } }));
    input.value = "";
}

function appendMessage(msg) {
    const container = document.getElementById("messages");
    if (document.getElementById(`msg-${msg.id}`)) return;

    const bubble = document.getElementById("typing-bubble");
    if (bubble) bubble.remove();

    const isMe = msg.sender_id === myId;
    const div = document.createElement("div");
    div.id = `msg-${msg.id}`;
    div.className = `group relative max-w-[70%] p-2 px-3 rounded-xl text-sm shadow-sm mb-1 flex flex-col ${isMe ? 'bg-indigo-600 text-white self-end rounded-tr-none' : 'bg-white text-gray-800 self-start rounded-tl-none'}`;

    let content = `<span>${msg.content || ''}</span>`;
    if (msg.media_url) content = `<img src="${msg.media_url}" class="rounded-lg mb-1 max-w-full h-auto cursor-pointer shadow-sm">` + content;
    div.innerHTML = content + (isMe ? `<button onclick="deleteMessage('${msg.id}')" class="absolute -left-6 top-1 text-gray-400 opacity-0 group-hover:opacity-100 hover:text-red-500 transition-all">🗑️</button>` : '');

    container.appendChild(div);
    if (bubble) container.appendChild(bubble);
    container.scrollTop = container.scrollHeight;
}

// --- UTILS ---
function logout() { localStorage.clear(); location.reload(); }

async function loadChatList() {
    const res = await fetch(`${API_BASE}/chats/`, { headers: { "Authorization": `Bearer ${token}` } });
    const chats = await res.json();
    const container = document.getElementById("chat-list");
    container.innerHTML = "";
    chats.forEach(chat => {
        const otherUser = chat.other_user || { full_name: "Chat", id: null, is_online: false };
        const div = document.createElement("div");
        div.className = `p-3 border-b flex items-center space-x-3 cursor-pointer hover:bg-gray-50 transition-all ${currentChatId === chat.id ? 'active-chat' : ''}`;
        div.onclick = () => selectChat(chat.id, otherUser.full_name, otherUser.id, otherUser.is_online);
        div.innerHTML = `<div class="w-10 h-10 rounded-full bg-indigo-100 flex items-center justify-center font-bold text-indigo-600 uppercase overflow-hidden border">
            ${otherUser.profile_photo_url ? `<img src="${otherUser.profile_photo_url}" class="w-full h-full object-cover">` : (otherUser.full_name ? otherUser.full_name[0] : "?")}</div>
            <div class="flex-1 min-w-0"><div class="flex justify-between"><h4 class="text-sm font-bold truncate">${otherUser.full_name || "Unknown"}</h4><span id="status-${otherUser.id}" class="text-[9px] ${otherUser.is_online ? 'text-green-500' : 'text-gray-400'} font-bold uppercase">${otherUser.is_online ? 'online' : 'offline'}</span></div>
            <p id="last-msg-${chat.id}" class="text-xs text-gray-500 truncate">${chat.last_message ? chat.last_message.content : "No messages"}</p></div>`;
        container.appendChild(div);
    });
}

async function selectChat(chatId, name, otherUserId, isOnline) {
    currentChatId = chatId; currentChatUserId = otherUserId;
    document.getElementById("no-chat-selected").classList.add("hidden");
    document.getElementById("chat-with-name").innerText = name || "User";
    document.getElementById("chat-avatar").innerText = name ? name[0] : "?";
    document.getElementById("chat-actions").classList.remove("hidden");

    const resBlocked = await fetch(`${API_BASE}/users/blocked`, { headers: { "Authorization": `Bearer ${token}` } });
    const blockedList = await resBlocked.json();
    toggleBlockButtons(blockedList.some(u => u.id === otherUserId));

    document.getElementById("chat-status-dot").className = `w-2 h-2 rounded-full ${isOnline ? 'bg-green-500' : 'bg-gray-300'}`;
    document.getElementById("chat-with-status").innerText = isOnline ? "ONLINE" : "OFFLINE";

    const res = await fetch(`${API_BASE}/messages/?chat_id=${chatId}`, { headers: { "Authorization": `Bearer ${token}` } });
    const messages = await res.json();
    const msgContainer = document.getElementById("messages");
    msgContainer.innerHTML = "";
    messages.reverse().forEach(appendMessage);
}

function debouncedSearch() {
    const q = document.getElementById("search-email").value.trim();
    if (!q.includes('@')) { if (!q) clearSearch(); return; }
    if (searchTimeout) clearTimeout(searchTimeout);
    searchTimeout = setTimeout(findContact, 500);
}

async function findContact() {
    const q = document.getElementById("search-email").value.trim();
    const res = await fetch(`${API_BASE}/users/find-contact?email=${q}`, { headers: { "Authorization": `Bearer ${token}` } });
    if (res.ok) { const users = await res.json(); renderSearchResults(users); }
}

function renderSearchResults(users) {
    const container = document.getElementById("search-results-list");
    const parent = document.getElementById("search-results-container");
    container.innerHTML = users.length ? "" : '<p class="text-[10px] text-gray-400 p-2">No users found.</p>';
    users.forEach(user => {
        const div = document.createElement("div");
        div.className = "flex justify-between items-center bg-white p-2 rounded-lg shadow-sm border border-indigo-100 mb-2";
        div.innerHTML = `<div class="flex flex-col"><span class="text-xs font-bold text-gray-800">${user.full_name || "User"}</span><span class="text-[9px] text-gray-400">${user.email}</span></div>
            <button onclick="startChat('${user.id}','${user.full_name}',${user.is_online})" class="bg-indigo-600 text-white text-[10px] px-2 py-1 rounded font-bold shadow-sm">CHAT</button>`;
        container.appendChild(div);
    });
    parent.classList.remove("hidden");
}

function clearSearch() { document.getElementById("search-results-container").classList.add("hidden"); }

async function startChat(userId, name, isOnline) {
    const res = await fetch(`${API_BASE}/chats/`, {
        method: "POST",
        headers: { "Authorization": `Bearer ${token}`, "Content-Type": "application/json" },
        body: JSON.stringify({ members: [userId], type: "direct" })
    });
    if (res.ok) {
        const chat = await res.json();
        clearSearch(); document.getElementById("search-email").value = "";
        selectChat(chat.id, name, userId, isOnline);
        loadChatList();
    }
}

async function registerDeviceToken() {
    try { await fetch(`${API_BASE}/notifications/tokens`, { method: "POST", headers: { "Authorization": `Bearer ${token}`, "Content-Type": "application/json" }, body: JSON.stringify({ token: `web_${myId.substring(0,5)}`, platform: "web" }) }); } catch(e){}
}

function closeModal() { document.getElementById("profile-modal").classList.add("hidden"); }
function showProfileModal(type) {
    document.getElementById("profile-modal").classList.remove("hidden");
    if (type === 'me') {
        document.getElementById("p-name").innerText = myProfile.full_name || "User";
        document.getElementById("p-email").innerText = myProfile.email;
        document.getElementById("p-bio").innerText = myProfile.bio || "Hey there!";
        document.getElementById("my-profile-actions").classList.remove("hidden");
    }
}
