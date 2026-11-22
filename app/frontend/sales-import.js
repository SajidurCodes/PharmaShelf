"use strict";

(() => {
  const el = (id) => document.getElementById(id);

  const form = el("import-form");
  const fields = el("import-fields");
  const kind = el("import-kind");
  const fileInput = el("import-file");
  const mappingFields = el("import-mapping");
  const status = el("import-status");
  const confirmButton = el("import-confirm");

  const columns = {
    sales: ["sale_id", "batch_id", "sold_at", "quantity", "unit_sale_price"],
    stock: [
      "id",
      "branch_code",
      "sku",
      "lot_number",
      "received_on",
      "expires_on",
      "quantity_received",
      "unit_cost",
    ],
  };

  const headings = {
    sales: ["Excel row", "Sale ID", "Units", "Unit price (৳)"],
    stock: ["Excel row", "SKU", "Lot", "Units received", "Unit cost (৳)"],
  };

  let pending = null;

  function clearPreview() {
    pending = null;
    confirmButton.hidden = true;
    el("import-result").hidden = true;
    el("import-rows").replaceChildren();
    el("import-errors").replaceChildren();
    status.textContent = "";
  }

  function switchWorkbook() {
    clearPreview();
    fileInput.value = "";
    mappingFields.replaceChildren();

    for (const name of columns[kind.value]) {
      const label = document.createElement("label");
      label.textContent = name;

      const input = document.createElement("input");
      input.name = name;
      input.placeholder = name;

      label.append(input);
      mappingFields.append(label);
    }

    const headerRow = el("import-headings");
    headerRow.replaceChildren();

    for (const title of headings[kind.value]) {
      const cell = document.createElement("th");
      cell.scope = "col";
      cell.textContent = title;
      headerRow.append(cell);
    }
  }

  function readMapping() {
    const mapping = {};

    for (const input of mappingFields.querySelectorAll("input")) {
      const header = input.value.trim();
      if (header) mapping[input.name] = header;
    }

    return mapping;
  }

  async function upload(action, request) {
    const body = new FormData();
    body.append("file", request.file);
    body.append("mapping", JSON.stringify(request.mapping));

    const response = await fetch(`/api/v1/imports/${request.kind}/${action}`, {
      method: "POST",
      headers: { Authorization: `Bearer ${request.token}` },
      body,
    });

    if (response.status === 401) {
      throw new Error(
        "Your session expired. Sign in and preview the workbook again.",
      );
    }
    if (response.status === 403) {
      throw new Error("An owner account is required.");
    }

    if (!response.ok) {
      const data = await response.json().catch(() => ({}));

      if (Array.isArray(data.detail)) {
        const messages = data.detail.map((issue) => {
          if (issue.row != null)
            return `Excel row ${issue.row}: ${issue.message}`;
          return issue.msg || "Invalid request.";
        });
        throw new Error(messages.join(" "));
      }

      throw new Error(
        typeof data.detail === "string"
          ? data.detail
          : `Import request failed (HTTP ${response.status}).`,
      );
    }

    return response.json();
  }

  function displayPreview(report, workbookKind) {
    const stock = workbookKind === "stock";

    let summary = `${report.valid_rows} valid · ${report.invalid_rows} invalid`;
    if (stock) summary += ` · ${report.skipped_rows} already recorded`;
    el("import-summary").textContent = summary;

    el("import-totals").textContent = stock
      ? `${report.total_units} incoming units · ৳${report.cost_bdt} total cost`
      : `${report.total_units} units sold · ৳${report.revenue_bdt} total sales`;

    el("import-table").hidden = report.preview.length === 0;

    for (const entry of report.preview) {
      const values = stock
        ? [
            entry.row,
            entry.sku,
            entry.lot_number,
            entry.quantity_received,
            entry.unit_cost,
          ]
        : [entry.row, entry.sale_id, entry.quantity, entry.unit_sale_price];

      const row = document.createElement("tr");
      for (const value of values) {
        const cell = document.createElement("td");
        cell.textContent = value;
        row.append(cell);
      }
      el("import-rows").append(row);
    }

    for (const issue of report.errors) {
      const item = document.createElement("li");
      item.textContent = `Excel row ${issue.row}: ${issue.message}`;
      el("import-errors").append(item);
    }

    el("import-result").hidden = false;
  }

  kind.addEventListener("change", switchWorkbook);
  form.addEventListener("input", clearPreview);
  fileInput.addEventListener("change", clearPreview);
  switchWorkbook();

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (fields.disabled) return;

    clearPreview();

    const file = fileInput.files[0];
    if (!file) {
      status.textContent = "Choose an Excel workbook.";
      return;
    }
    if (file.size > 2_000_000) {
      status.textContent = "Choose a workbook of 2 MB or less.";
      return;
    }

    const workbookKind = kind.value;
    const mapping = readMapping();
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

      if (login.status === 401) {
        throw new Error("Check your owner email and password.");
      }
      if (!login.ok) {
        throw new Error(`Sign-in failed (HTTP ${login.status}).`);
      }

      const { access_token } = await login.json();
      const request = {
        kind: workbookKind,
        file,
        mapping,
        token: access_token,
      };

      const report = await upload("preview", request);
      displayPreview(report, workbookKind);

      if (report.invalid_rows > 0) {
        status.textContent = "Review the row errors before importing.";
      } else if (report.valid_rows === 0) {
        status.textContent = "No new rows to import.";
      } else {
        pending = request;
        confirmButton.hidden = false;
        status.textContent =
          workbookKind === "stock"
            ? "Preview ready. Confirm to receive these units into stock."
            : "Preview ready. Confirm to record these sales and deduct stock.";
      }
    } catch (error) {
      clearPreview();
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
    status.textContent =
      request.kind === "stock" ? "Recording deliveries…" : "Recording sales…";

    try {
      const result = await upload("confirm", request);

      const totals =
        request.kind === "stock"
          ? `${result.units_received} units received · ৳${result.cost_bdt} cost`
          : `${result.units_recorded} units sold · ৳${result.revenue_recorded_bdt} sales`;

      clearPreview();
      status.textContent = `Recorded ${result.inserted_rows}, skipped ${result.skipped_rows}. ${totals}.`;
    } catch (error) {
      clearPreview();
      status.textContent = `${error.message} Preview the workbook again to check its current state.`;
    } finally {
      fields.disabled = false;
      confirmButton.disabled = false;
    }
  });
})();
