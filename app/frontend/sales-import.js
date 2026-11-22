"use strict";

(() => {
  const el = (id) => document.getElementById(id);
  const form = el("import-form");
  const fields = el("import-fields");
  const status = el("import-status");
  const confirmButton = el("import-confirm");
  const columnNames = [
    "sale_id",
    "batch_id",
    "sold_at",
    "quantity",
    "unit_sale_price",
  ];
  let pending = null;

  for (const name of columnNames) {
    const label = document.createElement("label");
    label.textContent = name;

    const input = document.createElement("input");
    input.name = name;
    input.placeholder = name;
    label.append(input);
    el("import-mapping").append(label);
  }

  function clearPreview() {
    pending = null;
    confirmButton.hidden = true;
    el("import-result").hidden = true;
    el("import-rows").replaceChildren();
    el("import-errors").replaceChildren();
    status.textContent = "";
  }

  form.addEventListener("input", clearPreview);
  el("import-file").addEventListener("change", clearPreview);

  async function upload(action, request) {
    const body = new FormData();
    body.append("file", request.file);
    body.append("mapping", JSON.stringify(request.mapping));

    const response = await fetch(`/api/v1/imports/sales/${action}`, {
      method: "POST",
      headers: { Authorization: `Bearer ${request.token}` },
      body,
    });

    if (response.status === 401)
      throw new Error("Sign in and preview the workbook again.");
    if (response.status === 403)
      throw new Error("An owner account is required.");

    const data = await response.json();
    if (!response.ok) {
      if (Array.isArray(data.detail)) {
        throw new Error(
          data.detail.map((e) => `Row ${e.row}: ${e.message}`).join("\n"),
        );
      }
      throw new Error(
        data.detail || `Request failed (HTTP ${response.status}).`,
      );
    }
    return data;
  }

  function displayPreview(report) {
    el("import-summary").textContent =
      `${report.valid_rows} valid · ${report.invalid_rows} invalid`;
    el("import-totals").textContent =
      `${report.total_units} units · ৳${report.revenue_bdt} total sales`;

    el("import-table").hidden = report.preview.length === 0;
    for (const sale of report.preview) {
      const row = document.createElement("tr");
      for (const value of [
        sale.row,
        sale.sale_id,
        sale.quantity,
        sale.unit_sale_price,
      ]) {
        const cell = document.createElement("td");
        cell.textContent = value;
        row.append(cell);
      }
      el("import-rows").append(row);
    }

    for (const error of report.errors) {
      const item = document.createElement("li");
      item.textContent = `Excel row ${error.row}: ${error.message}`;
      el("import-errors").append(item);
    }
    el("import-result").hidden = false;
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (fields.disabled) return;
    clearPreview();

    const file = el("import-file").files[0];
    if (!file) return;
    if (file.size > 2_000_000) {
      status.textContent = "Choose a workbook of 2 MB or less.";
      return;
    }

    const mapping = {};
    for (const name of columnNames) {
      const header = form.elements.namedItem(name).value.trim();
      if (header) mapping[name] = header;
    }

    const credentials = new URLSearchParams({
      username: el("import-email").value.trim(),
      password: el("import-password").value,
    });
    el("import-password").value = "";
    fields.disabled = true;
    status.textContent = "Checking the workbook…";

    try {
      const login = await fetch("/api/v1/auth/login", {
        method: "POST",
        body: credentials,
      });
      if (login.status === 401)
        throw new Error("Check your owner email and password.");
      if (!login.ok) throw new Error(`Sign-in failed (HTTP ${login.status}).`);

      const { access_token } = await login.json();
      const request = { file, mapping, token: access_token };
      const report = await upload("preview", request);
      displayPreview(report);

      if (report.invalid_rows > 0) {
        status.textContent = "Review the row errors before importing.";
      } else if (report.valid_rows === 0) {
        status.textContent = "The Sales sheet has no sales to import.";
      } else {
        pending = request;
        confirmButton.hidden = false;
        status.textContent =
          "Preview ready. Confirm to record these sales and deduct stock.";
      }
    } catch (error) {
      status.textContent = error.message;
    } finally {
      fields.disabled = false;
    }
  });

  confirmButton.addEventListener("click", async () => {
    if (!pending || confirmButton.disabled) return;
    const request = pending;
    fields.disabled = true;
    confirmButton.disabled = true;
    status.textContent = "Recording sales…";

    try {
      const result = await upload("confirm", request);
      clearPreview();
      status.textContent =
        `Recorded ${result.inserted_rows}, skipped ${result.skipped_rows}. ` +
        `${result.units_recorded} units · ৳${result.revenue_recorded_bdt}.`;
    } catch (error) {
      clearPreview();
      status.textContent = `${error.message} Preview the workbook again to check its current state.`;
    } finally {
      fields.disabled = false;
      confirmButton.disabled = false;
    }
  });
})();
