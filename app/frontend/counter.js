"use strict";

(() => {
  const form = document.getElementById("counter-form");
  const fields = document.getElementById("counter-fields");
  const mode = document.getElementById("counter-mode");
  const deliveryFields = document.getElementById("delivery-fields");
  const saleFields = document.getElementById("counter-sale-fields");
  const button = document.getElementById("counter-submit");
  const status = document.getElementById("counter-status");

  // Keep the same ID when retrying the same entry after a connection error.
  let pendingKey = "";
  let pendingId = "";

  function updateMode() {
    const delivery = mode.value === "receipt";
    deliveryFields.hidden = !delivery;
    deliveryFields.disabled = !delivery;
    saleFields.hidden = delivery;
    saleFields.disabled = delivery;
    button.textContent = delivery ? "Record delivery" : "Record sale";
  }

  mode.addEventListener("change", updateMode);
  updateMode();

  async function errorMessage(response) {
    const body = await response.json().catch(() => ({}));
    if (typeof body.detail === "string") return body.detail;
    if (Array.isArray(body.detail)) {
      return body.detail
        .map((item) => {
          const field = item.loc?.at(-1) || "Entry";
          return `${field}: ${item.msg}`;
        })
        .join(". ");
    }
    return `Request failed (HTTP ${response.status}).`;
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (fields.disabled) return;

    const entry = new FormData(form);
    const value = (name) => String(entry.get(name) ?? "").trim();
    const delivery = mode.value === "receipt";
    const quantity = Number(value("quantity"));

    if (delivery && value("expires_on") <= value("received_on")) {
      status.textContent = "Expiry date must be after the received date.";
      return;
    }

    const payload = delivery
      ? {
          branch_code: value("branch_code"),
          sku: value("sku"),
          lot_number: value("lot_number"),
          received_on: value("received_on"),
          expires_on: value("expires_on"),
          quantity_received: quantity,
          unit_cost: value("unit_cost"),
        }
      : {
          batch_id: value("batch_id"),
          quantity,
          unit_sale_price: value("unit_sale_price"),
        };

    const key = JSON.stringify([mode.value, value("email"), payload]);
    if (key !== pendingKey) {
      pendingId = crypto.randomUUID();
      pendingKey = key;
    }
    payload.id = pendingId;

    fields.disabled = true;
    status.textContent = "Saving entry…";

    try {
      const login = await fetch("/api/v1/auth/login", {
        method: "POST",
        body: new URLSearchParams({
          username: value("email"),
          password: entry.get("password"),
        }),
      });
      if (!login.ok) throw new Error(await errorMessage(login));

      const { access_token } = await login.json();
      const path = delivery ? "/api/v1/inventory/receipts" : "/api/v1/sales";
      const response = await fetch(path, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${access_token}`,
        },
        body: JSON.stringify(payload),
      });
      if (!response.ok) throw new Error(await errorMessage(response));

      const saved = await response.json();
      const action = response.status === 201 ? "Recorded" : "Already recorded";
      status.textContent = delivery
        ? `${action}. Batch ID: ${saved.id}. Lot ${saved.lot_number} has ${saved.quantity_remaining} units remaining.`
        : `${action}. Sale ID: ${saved.id}. Quantity sold: ${saved.quantity}.`;

      pendingKey = "";
      pendingId = "";
      form.elements.namedItem("quantity").value = "";
    } catch (error) {
      status.textContent = error.message;
    } finally {
      form.elements.namedItem("password").value = "";
      fields.disabled = false;
      updateMode();
    }
  });
})();
