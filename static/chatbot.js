document.addEventListener("DOMContentLoaded", () => {
    const chatBox = document.createElement("div");
    chatBox.id = "chat-assistant";
    chatBox.innerHTML = `
        <div id="chat-toggle">💬 Help</div>
        <div id="chat-body" style="display: none;">
            <div id="chat-log"></div>
            <input id="chat-input" placeholder="Ask a question..." />
        </div>
    `;
    document.body.appendChild(chatBox);

    // Toggle visibility
    document.getElementById("chat-toggle").onclick = () => {
        const body = document.getElementById("chat-body");
        body.style.display = body.style.display === "none" ? "block" : "none";
    };

    // Handle user input
    document.getElementById("chat-input").addEventListener("keypress", function (e) {
        if (e.key === "Enter") {
            const msg = this.value.trim();
            if (!msg) return;
            appendMessage("You", msg);
            this.value = "";

            fetch("/chat-assistant", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    message: msg,
                    form: document.body.getAttribute("data-form") || "default"
                })
            })
                .then(res => res.json())
                .then(data => appendMessage("Assistant", data.response))
                .catch(() => appendMessage("Assistant", "Sorry, something went wrong."));
        }
    });

    function appendMessage(sender, msg) {
        const chatLog = document.getElementById("chat-log");
        const bubble = document.createElement("div");
        bubble.className = "chat-msg";
        bubble.innerHTML = `<strong>${sender}:</strong> ${msg}`;
        chatLog.appendChild(bubble);
        chatLog.scrollTop = chatLog.scrollHeight;
    }
});

