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
      throw new Error(
        "The assistant returned an empty reply. Please try again.",
      );
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

function setupExpiryReport() {
  const form = document.getElementById("expiry-form");
  if (!form) return;

  const status = document.getElementById("expiry-status");
  const result = document.getElementById("expiry-result");
  const total = document.getElementById("expiry-total");
  const lots = document.getElementById("expiry-lots");
  const button = form.querySelector('button[type="submit"]');
  const money = new Intl.NumberFormat("en-BD", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const fields = new FormData(form);
    const branch = fields.get("branch").trim();

    result.hidden = true;
    total.textContent = "";
    lots.replaceChildren();
    if (!branch) {
      status.textContent = "Enter a branch code.";
      return;
    }

    button.disabled = true;
    status.textContent = "Loading your expiry report…";

    try {
      const login = await fetch("/api/v1/auth/login", {
        method: "POST",
        body: new URLSearchParams({
          username: fields.get("email").trim(),
          password: fields.get("password"),
        }),
      });
      form.elements.namedItem("password").value = "";

      if (login.status === 401)
        throw new Error("Check your email and password.");
      if (!login.ok) throw new Error(`Sign-in failed (HTTP ${login.status}).`);

      const { access_token } = await login.json();
      const query = new URLSearchParams({ branch_code: branch, days: "30" });
      const response = await fetch(`/api/v1/inventory/expiry-rescue?${query}`, {
        headers: { Authorization: `Bearer ${access_token}` },
        cache: "no-store",
      });

      if (response.status === 403)
        throw new Error("This report requires an owner account.");
      if (response.status === 404)
        throw new Error("Check the branch code and try again.");
      if (!response.ok)
        throw new Error(`Report request failed (HTTP ${response.status}).`);

      const report = await response.json();
      total.textContent = `৳${money.format(report.total_at_risk_bdt)} at risk in ${report.window_days} days`;

      for (const batch of report.batches) {
        const item = document.createElement("li");
        item.textContent =
          `${batch.medicine_name} · ${batch.lot_number} · ${batch.quantity_remaining} units. ` +
          `Expires ${batch.expires_on} (${batch.days_left} days left). ${batch.suggested_action}`;
        lots.append(item);
      }

      status.textContent =
        `${report.branch_code} · As of ${report.as_of} · ` +
        (report.batches.length
          ? `${report.batches.length} lot(s) nearing expiry.`
          : "No lots nearing expiry.");
      result.hidden = false;
    } catch (error) {
      status.textContent = error.message;
    } finally {
      button.disabled = false;
    }
  });
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", setupExpiryReport);
} else {
  setupExpiryReport();
}
