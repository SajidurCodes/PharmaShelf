const theme = document.querySelector("#theme");
const form = document.querySelector("#chat-form");
const question = document.querySelector("#question");
const messages = document.querySelector("#messages");
const statusText = document.querySelector("#status");
const send = document.querySelector("#send");

let history = [];

const savedTheme = localStorage.getItem("pharmashelf-theme");
if (["dark", "dim", "light"].includes(savedTheme)) {
  theme.value = savedTheme;
}
document.documentElement.dataset.theme = theme.value;

theme.addEventListener("change", () => {
  document.documentElement.dataset.theme = theme.value;
  localStorage.setItem("pharmashelf-theme", theme.value);
});

function showMessage(author, content) {
  const message = document.createElement("div");
  message.className = "message";

  const label = document.createElement("strong");
  label.textContent = author;

  const text = document.createElement("p");
  text.textContent = content;

  message.append(label, text);
  messages.append(message);
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const content = question.value.trim();
  if (!content || send.disabled) return;

  send.disabled = true;
  question.readOnly = true;
  statusText.textContent = "Checking…";

  try {
    const response = await fetch("/api/v1/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ content, history }),
    });

    if (!response.ok) {
      throw new Error(`Request failed (${response.status}). Please try again.`);
    }

    const data = await response.json();
    if (typeof data.reply !== "string" || !data.reply.trim()) {
      throw new Error("The assistant returned an empty reply. Please try again.");
    }

    showMessage("You", content);
    showMessage("PharmaShelf", data.reply);

    history.push(
      { role: "user", content },
      { role: "assistant", content: data.reply.slice(0, 2000) },
    );
    history = history.slice(-12);

    question.value = "";
    statusText.textContent = "";
  } catch (error) {
    statusText.textContent = error.message;
  } finally {
    send.disabled = false;
    question.readOnly = false;
    question.focus();
  }
});