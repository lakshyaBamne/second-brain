document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll("[data-txn-form]").forEach(function (formBlock) {
    const aspectId = formBlock.getAttribute("data-aspect-id");
    const form = formBlock.closest("form");
    const container = formBlock.parentElement;
    const stagedList = container.querySelector("[data-txn-staged]");
    const countInput = container.querySelector("[data-txn-count]");

    const nameEl = formBlock.querySelector('[data-txn-field="name"]');
    const descEl = formBlock.querySelector('[data-txn-field="description"]');
    const amountEl = formBlock.querySelector('[data-txn-field="amount"]');
    const categoryEl = formBlock.querySelector('[data-txn-field="category"]');
    const addBtn = formBlock.querySelector("[data-txn-add]");

    let count = 0;

    function addHidden(index, field, value) {
      const hidden = document.createElement("input");
      hidden.type = "hidden";
      hidden.name = "txn_" + aspectId + "_" + index + "_" + field;
      hidden.value = value;
      hidden.setAttribute("data-txn-row", index);
      form.appendChild(hidden);
      return hidden;
    }

    function addRow() {
      const name = nameEl.value.trim();
      const amount = amountEl.value;
      if (!name || !amount) {
        nameEl.focus();
        return;
      }
      const description = descEl.value.trim();
      const category = categoryEl.value;
      const categoryLabel = categoryEl.options[categoryEl.selectedIndex].text;
      const index = count;

      addHidden(index, "name", name);
      addHidden(index, "description", description);
      addHidden(index, "amount", amount);
      addHidden(index, "category", category);

      const row = document.createElement("div");
      row.className = "flex items-center justify-between gap-2 text-sm rounded-lg px-3 py-2";
      row.style.background = "var(--page)";

      const label = document.createElement("div");
      label.className = "flex-1 min-w-0 truncate";
      label.textContent = description ? name + " — " + description : name;

      const badge = document.createElement("span");
      badge.className = "text-xs px-2 py-0.5 rounded-full shrink-0";
      badge.style.color = "var(--ink-secondary)";
      badge.style.border = "1px solid var(--border)";
      badge.textContent = categoryLabel;

      const amountLabel = document.createElement("span");
      amountLabel.className = "font-medium shrink-0";
      amountLabel.textContent = parseFloat(amount).toFixed(2);

      const removeBtn = document.createElement("button");
      removeBtn.type = "button";
      removeBtn.className = "text-sm leading-none shrink-0";
      removeBtn.style.color = "var(--ink-muted)";
      removeBtn.setAttribute("aria-label", "Remove");
      removeBtn.textContent = "×";
      removeBtn.addEventListener("click", function () {
        row.remove();
        form.querySelectorAll('[data-txn-row="' + index + '"]').forEach(function (el) {
          el.disabled = true;
        });
      });

      row.appendChild(label);
      row.appendChild(badge);
      row.appendChild(amountLabel);
      row.appendChild(removeBtn);
      stagedList.appendChild(row);

      count += 1;
      countInput.value = count;

      nameEl.value = "";
      descEl.value = "";
      amountEl.value = "";
      categoryEl.selectedIndex = 0;
      nameEl.focus();
    }

    addBtn.addEventListener("click", addRow);
    [nameEl, descEl, amountEl].forEach(function (el) {
      el.addEventListener("keydown", function (e) {
        if (e.key === "Enter") {
          e.preventDefault();
          addRow();
        }
      });
    });
  });
});
