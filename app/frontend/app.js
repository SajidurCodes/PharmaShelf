"use strict";

(() => {
  const byId = (id) => document.getElementById(id);
  const money = new Intl.NumberFormat("en-BD", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });

  // Theme
  const theme = byId("theme");

  try {
    const saved = localStorage.getItem("pharmashelf-theme");
    if (["dark", "dim", "light"].includes(saved)) theme.value = saved;
  } catch {
    // Storage may be disabled in a private browser session.
  }

  document.documentElement.dataset.theme = theme.value;

  theme.addEventListener("change", () => {
    document.documentElement.dataset.theme = theme.value;
    try {
      localStorage.setItem("pharmashelf-theme", theme.value);
    } catch {
      // The selection still applies for this visit.
    }
  });

  async function responseError(response, fallback) {
    const body = await response.json().catch(() => ({}));

    if (typeof body.detail === "string" && body.detail.trim()) {
      return body.detail;
    }

    if (Array.isArray(body.detail)) {
      const messages = body.detail
        .map((issue) => {
          const field = issue.loc?.at(-1);
          return field ? `${field}: ${issue.msg}` : issue.msg;
        })
        .filter(Boolean);

      if (messages.length) return messages.join(" ");
    }

    return `${fallback} (HTTP ${response.status}).`;
  }

  // Customer availability chat
  const chatForm = byId("chat-form");
  const question = byId("question");
  const chatStatus = byId("chat-status");
  const chatButton = chatForm.querySelector('button[type="submit"]');
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

  chatForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const content = question.value.trim();
    if (!content || chatButton.disabled) return;

    chatButton.disabled = true;
    question.readOnly = true;
    chatStatus.textContent = "Checking availability…";

    try {
      const response = await fetch("/api/v1/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content, history: conversation }),
      });

      if (!response.ok) {
        throw new Error(await responseError(response, "Chat request failed"));
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
      question.value = "";
      chatStatus.textContent = "";
    } catch (error) {
      chatStatus.textContent = error.message;
    } finally {
      chatButton.disabled = false;
      question.readOnly = false;
      if (!byId("availability").hidden) question.focus();
    }
  });

  // Owner report controls
  const reportForm = byId("report-form");
  const reportType = byId("report-type");
  const reportStatus = byId("report-status");
  const reportResult = byId("report-result");
  const reportTitle = byId("report-title");
  const reportRows = byId("report-rows");
  const dateFields = byId("sales-fields");
  const startDate = byId("start-date");
  const endDate = byId("end-date");
  const skuField = byId("trend-sku");
  const rankField = byId("rank");
  const reportButton = reportForm.querySelector('button[type="submit"]');

  if (!reportType.querySelector('option[value="reorder"]')) {
    reportType.add(new Option("Stock & reorder", "reorder"));
  }

  const today = new Intl.DateTimeFormat("sv-SE", {
    timeZone: "Asia/Dhaka",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(new Date());

  startDate.value = `${today.slice(0, 7)}-01`;
  endDate.value = today;

  function clearReport() {
    reportResult.hidden = true;
    reportTitle.textContent = "";
    reportRows.replaceChildren();
    reportStatus.textContent = "";
  }

  function updateReportFields() {
    const trend = reportType.value === "trend";
    const sales = reportType.value === "sales";
    const usesDates = trend || sales;

    dateFields.hidden = !usesDates;
    dateFields.disabled = !usesDates;

    byId("trend-sku-field").hidden = !trend;
    skuField.disabled = !trend;
    skuField.required = trend;

    reportForm.querySelector('label[for="rank"]').hidden = !sales;
    rankField.hidden = !sales;
    rankField.disabled = !sales;
  }

  reportType.addEventListener("change", () => {
    clearReport();
    updateReportFields();
  });
  reportForm.addEventListener("input", clearReport);
  updateReportFields();

  function addReportRow(heading, detail) {
    const row = document.createElement("li");
    const title = document.createElement("strong");
    const caption = document.createElement("small");

    title.textContent = heading;
    caption.textContent = detail;
    row.append(title, caption);
    reportRows.append(row);
    return row;
  }

  function addBar(row, value, maximum) {
    const track = document.createElement("div");
    track.className = "track";
    track.setAttribute("aria-hidden", "true");

    const fill = document.createElement("span");
    fill.className = "fill";
    fill.style.width = `${maximum > 0 ? (value / maximum) * 100 : 0}%`;

    track.append(fill);
    row.append(track);
  }

  function displayExpiry(report) {
    reportTitle.textContent = `৳${money.format(report.total_at_risk_bdt)} at risk`;

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
    const maximum = Math.max(0, ...rows.map((row) => Number(row[metric])));

    reportTitle.textContent = byRevenue
      ? "Best sellers by revenue"
      : "Best sellers by units";
    reportStatus.textContent = `${branch} · ${start} to ${end}`;
    if (!rows.length) reportStatus.textContent += " · No sales recorded.";

    for (const sale of rows) {
      const row = addReportRow(
        sale.name,
        `${sale.sku} · ${sale.units_sold} units · ৳${money.format(sale.revenue_bdt)}`,
      );
      addBar(row, Number(sale[metric]), maximum);
    }
  }

  function displayTrend(report) {
    reportTitle.textContent = `${report.medicine_name} · ${report.units} units`;
    reportStatus.textContent = `${report.branch_code} · ${report.start_date} to ${report.end_date}`;

    let changeTitle = "Sales unchanged";
    if (report.change_units > 0)
      changeTitle = `Up ${report.change_units} units`;
    if (report.change_units < 0)
      changeTitle = `Down ${Math.abs(report.change_units)} units`;

    const comparison =
      report.change_percent === null
        ? "The previous period had zero sales."
        : `Percentage change: ${Number(report.change_percent)}%.`;

    addReportRow(
      changeTitle,
      `Previous period: ${report.previous_units} units from ` +
        `${report.previous_start} to ${report.previous_end}. ${comparison}`,
    );

    addReportRow(
      `৳${money.format(report.revenue_bdt)} sales`,
      `Previous period: ৳${money.format(report.previous_revenue_bdt)}.`,
    );

    const activeDays = report.days.filter((day) => day.units > 0);
    if (!activeDays.length) {
      addReportRow(
        "No sales in this period",
        "Choose another date range to compare demand.",
      );
      return;
    }

    const maximum = Math.max(...activeDays.map((day) => day.units));
    for (const day of activeDays) {
      const row = addReportRow(
        day.day,
        `${day.units} units · ৳${money.format(day.revenue_bdt)}`,
      );
      addBar(row, day.units, maximum);
    }
  }

  function displaySpikes(report) {
    const count = report.alerts.length;
    reportTitle.textContent =
      count === 1
        ? "1 medicine with a demand spike"
        : `${count} medicines with demand spikes`;

    reportStatus.textContent = `${report.branch_code} · ${report.recent_start} to ${report.recent_end}`;

    if (!count) {
      addReportRow(
        "No qualifying spike this week",
        "An alert requires baseline sales history, at least 5 units sold in the last " +
          "7 completed days, and sales at least twice the baseline weekly average.",
      );
      return;
    }

    for (const item of report.alerts) {
      addReportRow(
        `${item.medicine_name} · ${Number(item.multiple)}× its weekly average`,
        `${item.sku} · ${item.recent_units} units in the last 7 completed days. ` +
          `Baseline: ${Number(item.baseline_weekly_average)} units per week ` +
          `from ${report.baseline_start} to ${report.baseline_end}. ` +
          "Check current stock and supplier lead time before reordering.",
      );
    }
  }

  function displayReorder(report) {
    const labels = {
      out_of_stock: "Out of stock",
      running_low: "Running low",
      dead_stock: "Dead stock",
      no_recent_sales: "No recent sales",
      in_stock: "In stock",
    };

    reportTitle.textContent = "Stock & reorder";
    reportStatus.textContent =
      `${report.branch_code} · As of ${report.as_of} · ` +
      `Sales window: ${report.sales_window_start} to ${report.sales_window_end}`;

    if (!report.items.length) {
      addReportRow(
        "No stock history for this branch",
        "Recorded deliveries will appear here.",
      );
      return;
    }

    for (const item of report.items) {
      const coverage =
        item.days_left === null
          ? "Days left unavailable: no sales in the 30-day window."
          : `Estimated days left: ${Number(item.days_left)}.`;

      const row = addReportRow(
        `${item.medicine_name} · ${labels[item.status] ?? item.status}`,
        `${item.sku} · ${item.usable_units} usable units · ` +
          `${item.units_sold_30d} units sold in 30 days. ${coverage}`,
      );
      row.append(document.createTextNode(item.suggested_action));
    }
  }

  // Owner sign-in and report requests
  reportForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (reportButton.disabled) return;
    clearReport();

    const type = reportType.value;
    const branch = byId("branch").value.trim();
    const sku = skuField.value.trim();
    const start = startDate.value;
    const end = endDate.value;
    const rank = rankField.value;
    const usesDates = type === "sales" || type === "trend";

    if (!branch) {
      reportStatus.textContent = "Enter a branch code.";
      byId("branch").focus();
      return;
    }

    if (type === "trend" && !sku) {
      reportStatus.textContent = "Enter a medicine SKU.";
      skuField.focus();
      return;
    }

    if (usesDates && (!start || !end || start > end)) {
      reportStatus.textContent =
        "Choose a date range ending on or after the start date.";
      endDate.focus();
      return;
    }

    const query = new URLSearchParams({ branch_code: branch });
    let path;

    switch (type) {
      case "expiry":
        path = "/api/v1/inventory/expiry-rescue";
        query.set("days", "30");
        break;
      case "sales":
        path = "/api/v1/sales/best-sellers";
        query.set("rank_by", rank);
        query.set("limit", "10");
        break;
      case "trend":
        path = "/api/v1/sales/demand-trend";
        query.set("sku", sku);
        break;
      case "spikes":
        path = "/api/v1/sales/demand-spikes";
        break;
      case "reorder":
        path = "/api/v1/inventory/reorder";
        break;
      default:
        reportStatus.textContent = "Choose a report.";
        return;
    }

    if (usesDates) {
      query.set("start_date", start);
      query.set("end_date", end);
    }

    const password = byId("owner-password");
    const credentials = new URLSearchParams({
      username: byId("owner-email").value.trim(),
      password: password.value,
    });
    password.value = "";

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

      if (login.status === 401)
        throw new Error("Check your owner email and password.");
      if (!login.ok)
        throw new Error(await responseError(login, "Sign-in failed"));

      const { access_token } = await login.json();
      const response = await fetch(`${path}?${query}`, {
        headers: { Authorization: `Bearer ${access_token}` },
        cache: "no-store",
      });

      if (response.status === 403)
        throw new Error("This report requires an owner account.");
      if (!response.ok)
        throw new Error(await responseError(response, "Report request failed"));

      const data = await response.json();

      switch (type) {
        case "expiry":
          displayExpiry(data);
          break;
        case "sales":
          displaySales(data, branch, start, end, rank);
          break;
        case "trend":
          displayTrend(data);
          break;
        case "spikes":
          displaySpikes(data);
          break;
        case "reorder":
          displayReorder(data);
          break;
      }

      reportResult.hidden = false;
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
})();
