"use strict";

const byId = (id) => document.getElementById(id);
const theme = byId("theme");
const money = new Intl.NumberFormat("en-BD", {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

try {
  const saved = localStorage.getItem("pharmashelf-theme");
  if (["dark", "dim", "light"].includes(saved)) theme.value = saved;
} catch {
  // Theme selection still works when the browser disables storage.
}

document.documentElement.dataset.theme = theme.value;

theme.addEventListener("change", () => {
  document.documentElement.dataset.theme = theme.value;
  try {
    localStorage.setItem("pharmashelf-theme", theme.value);
  } catch {
    // Keep the selected theme for this page visit.
  }
});

let conversation = [];

function showMessage(author, content) {
  const entry = document.createElement("div");
  entry.className = "message";

  const label = document.createElement("strong");
  label.textContent = author;

  const text = document.createElement("p");
  text.textContent = content;

  entry.append(label, text);
  const log = byId("messages");
  log.append(entry);
  log.scrollTop = log.scrollHeight;
}

byId("chat-form").addEventListener("submit", async (event) => {
  event.preventDefault();

  const input = byId("question");
  const status = byId("chat-status");
  const button = event.currentTarget.querySelector("button");
  const content = input.value.trim();
  if (!content || button.disabled) return;

  button.disabled = true;
  input.readOnly = true;
  status.textContent = "Checking availability…";

  try {
    const response = await fetch("/api/v1/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ content, history: conversation }),
    });

    if (!response.ok) {
      throw new Error(
        `Chat request failed (HTTP ${response.status}). Please try again.`,
      );
    }

    const { reply } = await response.json();
    if (typeof reply !== "string" || !reply.trim()) {
      throw new Error(
        "The assistant returned an empty reply. Please try again.",
      );
    }

    showMessage("You", content);
    showMessage("PharmaShelf", reply);

    conversation.push(
      { role: "user", content },
      { role: "assistant", content: reply.slice(0, 2000) },
    );
    conversation = conversation.slice(-12);

    input.value = "";
    status.textContent = "";
  } catch (error) {
    status.textContent = error.message;
  } finally {
    button.disabled = false;
    input.readOnly = false;
    input.focus();
  }
});

const reportForm = byId("report-form");
const reportType = byId("report-type");
const salesFields = byId("sales-fields");
const reportStatus = byId("report-status");

const today = new Intl.DateTimeFormat("sv-SE", {
  timeZone: "Asia/Dhaka",
  year: "numeric",
  month: "2-digit",
  day: "2-digit",
}).format(new Date());

byId("start-date").value = `${today.slice(0, 7)}-01`;
byId("end-date").value = today;

function clearReport() {
  byId("report-result").hidden = true;
  byId("report-title").textContent = "";
  byId("report-rows").replaceChildren();
  reportStatus.textContent = "";
}

function updateReportFields() {
  const sales = reportType.value === "sales";
  salesFields.hidden = !sales;
  salesFields.disabled = !sales;
}

updateReportFields();
reportType.addEventListener("change", updateReportFields);
reportForm.addEventListener("input", clearReport);

function addReportRow(heading, detail) {
  const row = document.createElement("li");

  const title = document.createElement("strong");
  title.textContent = heading;

  const caption = document.createElement("small");
  caption.textContent = detail;

  row.append(title, caption);
  byId("report-rows").append(row);
  return row;
}

function displayExpiry(report) {
  byId("report-title").textContent =
    `৳${money.format(report.total_at_risk_bdt)} at risk`;

  const count = report.batches.length;
  const summary = count
    ? `${count} ${count === 1 ? "lot" : "lots"} within ${report.window_days} days`
    : "No lots nearing expiry";

  reportStatus.textContent = `${report.branch_code} · As of ${report.as_of} · ${summary}`;

  for (const batch of report.batches) {
    const row = addReportRow(
      `${batch.medicine_name} · ${batch.lot_number}`,
      `${batch.quantity_remaining} units · ৳${money.format(batch.at_risk_bdt)} at risk · ` +
        `Expires ${batch.expires_on} (${batch.days_left} days left)`,
    );
    row.append(document.createTextNode(batch.suggested_action));
  }
}

function displaySales(rows, branch, start, end, rank) {
  const byRevenue = rank === "revenue";
  const metric = byRevenue ? "revenue_bdt" : "units_sold";
  const highest = Math.max(0, ...rows.map((row) => Number(row[metric])));

  byId("report-title").textContent = byRevenue
    ? "Best sellers by revenue"
    : "Best sellers by units";

  reportStatus.textContent = `${branch} · ${start} to ${end}`;
  if (!rows.length) reportStatus.textContent += " · No sales recorded.";

  for (const sale of rows) {
    const row = addReportRow(
      sale.name,
      `${sale.sku} · ${sale.units_sold} units · ৳${money.format(sale.revenue_bdt)}`,
    );

    const track = document.createElement("div");
    track.className = "track";
    track.setAttribute("aria-hidden", "true");

    const fill = document.createElement("span");
    fill.className = "fill";
    const percent = highest ? (Number(sale[metric]) / highest) * 100 : 0;
    fill.style.width = `${percent}%`;

    track.append(fill);
    row.append(track);
  }
}

reportForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const button = reportForm.querySelector("button");
  if (button.disabled) return;

  clearReport();

  const sales = reportType.value === "sales";
  const branch = byId("branch").value.trim();
  const start = byId("start-date").value;
  const end = byId("end-date").value;
  const rank = byId("rank").value;

  if (!branch) {
    reportStatus.textContent = "Enter a branch code.";
    byId("branch").focus();
    return;
  }

  if (sales && start > end) {
    reportStatus.textContent =
      "The end date must be on or after the start date.";
    byId("end-date").focus();
    return;
  }

  const credentials = new URLSearchParams({
    username: byId("owner-email").value.trim(),
    password: byId("owner-password").value,
  });

  byId("owner-password").value = "";
  const controls = reportForm.querySelectorAll("input, select, button");
  controls.forEach((control) => {
    control.disabled = true;
  });
  reportStatus.textContent = "Loading your report…";

  try {
    const login = await fetch("/api/v1/auth/login", {
      method: "POST",
      body: credentials,
    });

    if (login.status === 401) throw new Error("Check your email and password.");
    if (!login.ok) throw new Error(`Sign-in failed (HTTP ${login.status}).`);

    const { access_token } = await login.json();

    const query = new URLSearchParams({ branch_code: branch });
    let path;

    if (sales) {
      path = "/api/v1/sales/best-sellers";
      query.set("start_date", start);
      query.set("end_date", end);
      query.set("rank_by", rank);
      query.set("limit", "10");
    } else {
      path = "/api/v1/inventory/expiry-rescue";
      query.set("days", "30");
    }

    const response = await fetch(`${path}?${query}`, {
      headers: { Authorization: `Bearer ${access_token}` },
      cache: "no-store",
    });

    if (response.status === 403)
      throw new Error("This report requires owner access.");
    if (response.status === 404)
      throw new Error("Check the branch code and try again.");
    if (!response.ok)
      throw new Error(`Report request failed (HTTP ${response.status}).`);

    const data = await response.json();

    if (sales) {
      displaySales(data, branch, start, end, rank);
    } else {
      displayExpiry(data);
    }

    byId("report-result").hidden = false;
  } catch (error) {
    clearReport();
    reportStatus.textContent = error.message;
  } finally {
    controls.forEach((control) => {
      control.disabled = false;
    });
    updateReportFields();
  }
});
