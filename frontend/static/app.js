(function () {
  "use strict";

  const PIE_SCALE = 1000000000n;
  const PIE_CENTER = 100;
  const PIE_RADIUS = 70;
  const VIEW_NAMES = new Set(["overview", "imports", "duplicates"]);
  const state = {
    session: null,
    runs: [],
    months: [],
    monthSummaries: new Map(),
    selectedMonth: null,
    monthData: null,
    identityCatalog: new Map(),
    duplicates: [],
    activeRun: null,
    importItems: [],
    importTail: Promise.resolve(),
    selectedCategory: null,
  };

  const elements = {};

  class ApiError extends Error {
    constructor(status, envelope) {
      const error = envelope && envelope.error ? envelope.error : {};
      super(error.message || `Local request failed with HTTP ${status}`);
      this.name = "ApiError";
      this.status = status;
      this.code = error.code || "unexpected_response";
      this.details = error.details || {};
    }
  }

  function byId(id) {
    return document.getElementById(id);
  }

  function node(tag, className, text) {
    const element = document.createElement(tag);
    if (className) {
      element.className = className;
    }
    if (text !== undefined && text !== null) {
      element.textContent = String(text);
    }
    return element;
  }

  function setText(element, value) {
    element.textContent = value === null || value === undefined ? "" : String(value);
  }

  function exactMinor(value, fieldName) {
    if (typeof value !== "string" || !/^-?(0|[1-9][0-9]*)$/.test(value)) {
      throw new Error(`${fieldName} is not an exact minor-unit string`);
    }
    return BigInt(value);
  }

  function formatMoney(minorText, currency = "CAD") {
    const minor = exactMinor(minorText, "money");
    const negative = minor < 0n;
    const absolute = negative ? -minor : minor;
    const dollars = (absolute / 100n).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    const cents = (absolute % 100n).toString().padStart(2, "0");
    const prefix = currency === "CAD" ? "$" : `${currency} `;
    return `${negative ? "−" : ""}${prefix}${dollars}.${cents}`;
  }

  function formatPercent(partText, totalText) {
    const part = exactMinor(partText, "percentage numerator");
    const total = exactMinor(totalText, "percentage denominator");
    if (total === 0n) {
      return "0.00%";
    }
    const basisPoints = (part * 10000n + total / 2n) / total;
    return `${basisPoints / 100n}.${(basisPoints % 100n).toString().padStart(2, "0")}%`;
  }

  function allocatePieUnits(categoryBreakdown, totalText) {
    const total = exactMinor(totalText, "pie total");
    const nonZero = categoryBreakdown.filter(
      (bucket) => exactMinor(bucket.spending_minor, "category amount") > 0n,
    );
    if (total <= 0n || nonZero.length === 0) {
      return [];
    }
    const allocated = nonZero.map((bucket) => {
      const amount = exactMinor(bucket.spending_minor, "category amount");
      const proportional = (amount * PIE_SCALE) / total;
      return {
        bucket,
        units: proportional > 0n ? proportional : 1n,
      };
    });
    let sum = allocated.reduce((value, item) => value + item.units, 0n);
    let largest = allocated[0];
    for (const item of allocated.slice(1)) {
      if (item.units > largest.units) {
        largest = item;
      }
    }
    if (sum < PIE_SCALE) {
      largest.units += PIE_SCALE - sum;
    } else if (sum > PIE_SCALE) {
      const excess = sum - PIE_SCALE;
      if (largest.units - excess < 1n) {
        throw new Error("pie allocation cannot preserve non-zero slices");
      }
      largest.units -= excess;
    }
    sum = allocated.reduce((value, item) => value + item.units, 0n);
    if (sum !== PIE_SCALE || allocated.some((item) => item.units <= 0n)) {
      throw new Error("pie allocation does not reconcile");
    }
    return allocated;
  }

  function piePointAtUnits(units) {
    const angle = (Number(units) / Number(PIE_SCALE)) * 2 * Math.PI;
    return {
      x: PIE_CENTER + PIE_RADIUS * Math.cos(angle),
      y: PIE_CENTER + PIE_RADIUS * Math.sin(angle),
    };
  }

  function boundedPieCoordinate(value) {
    return value.toFixed(6);
  }

  function pieArcPath(startUnits, sliceUnits) {
    if (
      typeof startUnits !== "bigint"
      || typeof sliceUnits !== "bigint"
      || startUnits < 0n
      || sliceUnits <= 0n
      || startUnits + sliceUnits > PIE_SCALE
    ) {
      throw new Error("pie visual arc requires bounded positive accounting units");
    }
    const start = piePointAtUnits(startUnits);
    const end = piePointAtUnits(startUnits + sliceUnits);
    const move = `M ${boundedPieCoordinate(start.x)} ${boundedPieCoordinate(start.y)}`;
    if (sliceUnits === PIE_SCALE) {
      const midpoint = piePointAtUnits(startUnits + PIE_SCALE / 2n);
      return `${move} A ${PIE_RADIUS} ${PIE_RADIUS} 0 0 1 ${boundedPieCoordinate(midpoint.x)} ${boundedPieCoordinate(midpoint.y)} A ${PIE_RADIUS} ${PIE_RADIUS} 0 0 1 ${boundedPieCoordinate(end.x)} ${boundedPieCoordinate(end.y)}`;
    }
    const largeArc = sliceUnits * 2n > PIE_SCALE ? 1 : 0;
    return `${move} A ${PIE_RADIUS} ${PIE_RADIUS} 0 ${largeArc} 1 ${boundedPieCoordinate(end.x)} ${boundedPieCoordinate(end.y)}`;
  }

  function reconcileMonth(summary) {
    const spendingTotal = exactMinor(summary.spending_total_minor, "spending total");
    const creditTotal = exactMinor(summary.credit_total_minor, "credit total");
    const categorySums = new Map();
    let categoryTotal = 0n;
    for (const bucket of summary.category_breakdown) {
      const amount = exactMinor(bucket.spending_minor, "category amount");
      if (amount <= 0n || categorySums.has(bucket.category)) {
        return { ok: false, reason: "Category buckets must be unique and positive." };
      }
      categorySums.set(bucket.category, amount);
      categoryTotal += amount;
    }

    let transactionSpending = 0n;
    let transactionCredits = 0n;
    let includedCount = 0;
    const transactionCategorySums = new Map();
    for (const transaction of summary.transactions) {
      if (!transaction.included) {
        continue;
      }
      includedCount += 1;
      const amount = exactMinor(transaction.amount_minor, "transaction amount");
      if (transaction.is_spending) {
        const contribution = -amount;
        if (contribution <= 0n) {
          return { ok: false, reason: "A spending transaction has a non-debit amount." };
        }
        transactionSpending += contribution;
        transactionCategorySums.set(
          transaction.effective_category,
          (transactionCategorySums.get(transaction.effective_category) || 0n) + contribution,
        );
      } else if (amount > 0n) {
        transactionCredits += amount;
      }
    }

    if (categoryTotal !== spendingTotal || transactionSpending !== spendingTotal) {
      return { ok: false, reason: "Spending total, categories, and transactions differ." };
    }
    if (transactionCredits !== creditTotal) {
      return { ok: false, reason: "Credit total and included credit rows differ." };
    }
    if (includedCount !== summary.transaction_count) {
      return { ok: false, reason: "Included transaction count differs from the summary." };
    }
    if (transactionCategorySums.size !== categorySums.size) {
      return { ok: false, reason: "Category rows differ from transaction categories." };
    }
    for (const [category, amount] of categorySums) {
      if (transactionCategorySums.get(category) !== amount) {
        return { ok: false, reason: `${category} does not match its included transactions.` };
      }
    }
    return {
      ok: true,
      categoryTotal: categoryTotal.toString(),
      transactionSpending: transactionSpending.toString(),
      transactionCredits: transactionCredits.toString(),
    };
  }

  async function requestJson(path, options = {}) {
    const method = options.method || "GET";
    const headers = new Headers(options.headers || {});
    if (method !== "GET") {
      if (!state.session || !state.session.csrf_token) {
        throw new Error("The local CSRF session is unavailable.");
      }
      headers.set("X-Local-Expense-CSRF", state.session.csrf_token);
    }
    let response;
    try {
      response = await fetch(path, {
        method,
        headers,
        body: options.body,
        cache: "no-store",
        credentials: "same-origin",
      });
    } catch (error) {
      const offline = new Error("The local server is unavailable. Check that the loopback process is running.");
      offline.name = "OfflineError";
      offline.cause = error;
      throw offline;
    }
    let payload;
    try {
      payload = await response.json();
    } catch (error) {
      const invalid = new Error("The local server returned an invalid response.");
      invalid.cause = error;
      throw invalid;
    }
    if (!response.ok) {
      throw new ApiError(response.status, payload);
    }
    return payload.data;
  }

  function errorText(error) {
    if (error instanceof ApiError) {
      return `${error.code}: ${error.message}`;
    }
    return error && error.message ? error.message : "An unexpected local error occurred.";
  }

  function announce(message) {
    setText(elements.statusRegion, message);
  }

  function showGlobalError(error) {
    setText(elements.errorBanner, errorText(error));
    elements.errorBanner.hidden = false;
  }

  function clearGlobalError() {
    elements.errorBanner.hidden = true;
    setText(elements.errorBanner, "");
  }

  function viewFromHash() {
    const value = window.location.hash.replace(/^#/, "");
    return VIEW_NAMES.has(value) ? value : "overview";
  }

  function setView(viewName, options = {}) {
    const view = VIEW_NAMES.has(viewName) ? viewName : "overview";
    for (const panel of document.querySelectorAll("[data-view-panel]")) {
      panel.hidden = panel.dataset.viewPanel !== view;
    }
    for (const button of document.querySelectorAll(".nav-button[data-view]")) {
      const selected = button.dataset.view === view;
      button.classList.toggle("is-active", selected);
      if (selected) {
        button.setAttribute("aria-current", "page");
      } else {
        button.removeAttribute("aria-current");
      }
    }
    if (options.updateHash !== false && window.location.hash !== `#${view}`) {
      window.history.pushState(null, "", `#${view}`);
    }
    if (options.focus) {
      const heading = byId(`${view}-title`);
      if (heading) {
        heading.focus();
      }
    }
  }

  async function loadSession() {
    const session = await requestJson("/api/session");
    if (!session.local_only || typeof session.csrf_token !== "string" || !session.csrf_token) {
      throw new Error("The server did not establish a valid local-only session.");
    }
    state.session = session;
    const megabytes = BigInt(session.max_upload_bytes) / (1024n * 1024n);
    setText(
      elements.uploadLimit,
      `Supported: CSV, text-based PDF · up to ${megabytes.toString()} MB each`,
    );
  }

  async function refreshAll(options = {}) {
    clearGlobalError();
    if (options.loading !== false) {
      elements.overviewLoading.hidden = false;
    }
    elements.duplicatesLoading.hidden = false;
    elements.duplicatesEmpty.hidden = true;
    try {
      const [runs, months, duplicates] = await Promise.all([
        requestJson("/api/import-runs"),
        requestJson("/api/months"),
        requestJson("/api/duplicates"),
      ]);
      state.runs = runs;
      state.months = months;
      state.duplicates = duplicates;

      const summaries = await Promise.all(
        months.map((month) => requestJson(`/api/months/${encodeURIComponent(month)}`)),
      );
      state.monthSummaries = new Map(summaries.map((summary) => [summary.month, summary]));
      state.identityCatalog = new Map();
      for (const summary of summaries) {
        for (const transaction of summary.transactions) {
          state.identityCatalog.set(transaction.identity_id, transaction);
        }
      }

      if (!state.selectedMonth || !state.monthSummaries.has(state.selectedMonth)) {
        state.selectedMonth = months.length ? months[0] : null;
      }
      state.monthData = state.selectedMonth
        ? state.monthSummaries.get(state.selectedMonth)
        : null;
      renderAll();
      if (state.activeRun) {
        const matching = runs.find((run) => run.run_id === state.activeRun.summary.run_id);
        if (matching) {
          await viewRun(matching.run_id, { focus: false, announce: false, throwOnError: true });
        } else {
          state.activeRun = null;
          renderRunDetail();
        }
      }
    } catch (error) {
      showGlobalError(error);
      announce(errorText(error));
      throw error;
    } finally {
      elements.overviewLoading.hidden = true;
      elements.duplicatesLoading.hidden = true;
    }
  }

  function reportCommittedRefreshFailure(committedMessage, error) {
    const message = `${committedMessage} The write is committed, but current views could not refresh. Reload to synchronize. ${errorText(error)}`;
    showGlobalError(new Error(message));
    announce(message);
    return false;
  }

  async function refreshAfterCommit(committedMessage) {
    try {
      await refreshAll({ loading: false });
      return true;
    } catch (error) {
      return reportCommittedRefreshFailure(committedMessage, error);
    }
  }

  function renderAll() {
    renderNavCounts();
    renderMonthSelector();
    renderOverview();
    renderRunHistory();
    renderRunDetail();
    renderDuplicates();
  }

  function renderNavCounts() {
    setText(elements.runCountBadge, state.runs.length);
    elements.runCountBadge.setAttribute(
      "aria-label",
      `${state.runs.length} import ${state.runs.length === 1 ? "run" : "runs"}`,
    );
    const pending = state.duplicates.filter(
      (candidate) => candidate.effective_decision === "pending",
    ).length;
    setText(elements.duplicateCountBadge, pending);
    elements.duplicateCountBadge.setAttribute(
      "aria-label",
      `${pending} pending ${pending === 1 ? "duplicate" : "duplicates"}`,
    );
  }

  function renderMonthSelector() {
    elements.monthSelect.replaceChildren();
    if (!state.months.length) {
      const option = node("option", "", "No imported months");
      elements.monthSelect.append(option);
      elements.monthSelect.disabled = true;
      return;
    }
    for (const month of state.months) {
      const option = node("option", "", month);
      option.value = month;
      option.selected = month === state.selectedMonth;
      elements.monthSelect.append(option);
    }
    elements.monthSelect.disabled = false;
  }

  function renderOverview() {
    const summary = state.monthData;
    elements.overviewEmpty.hidden = Boolean(summary);
    elements.overviewContent.hidden = !summary;
    if (!summary) {
      return;
    }

    const reconciliation = reconcileMonth(summary);
    setText(elements.spendingTotal, formatMoney(summary.spending_total_minor, summary.currency));
    elements.spendingTotal.dataset.minor = summary.spending_total_minor;
    setText(elements.creditTotal, formatMoney(summary.credit_total_minor, summary.currency));
    elements.creditTotal.dataset.minor = summary.credit_total_minor;
    setText(elements.transactionCount, summary.transaction_count);
    setText(
      elements.spendingCount,
      `${summary.spending_transaction_count} spending ${summary.spending_transaction_count === 1 ? "transaction" : "transactions"}`,
    );
    setText(
      elements.creditCount,
      `${summary.credit_transaction_count} credit ${summary.credit_transaction_count === 1 ? "transaction" : "transactions"} · excluded from chart`,
    );
    setText(
      elements.transactionsCaption,
      `Included transactions for ${summary.month}`,
    );

    if (!reconciliation.ok) {
      setText(elements.reconciliationStatus, `Reconciliation blocked: ${reconciliation.reason}`);
      elements.reconciliationStatus.classList.add("is-error");
      elements.chartContent.hidden = true;
      elements.zeroSpending.hidden = true;
      elements.categoryTableBody.replaceChildren();
      elements.transactionTableBody.replaceChildren();
      showGlobalError(new Error("Monthly data did not reconcile, so category and transaction details were not rendered."));
      return;
    }
    elements.reconciliationStatus.classList.remove("is-error");
    setText(elements.reconciliationStatus, "Reconciled exactly");
    const zeroSpending = exactMinor(summary.spending_total_minor, "spending total") === 0n;
    elements.zeroSpending.hidden = !zeroSpending;
    elements.chartContent.hidden = zeroSpending;
    renderChart(summary);
    renderCategoryTable(summary);
    renderTransactions(summary);
  }

  function renderChart(summary) {
    elements.pieChart.replaceChildren();
    elements.chartLegend.replaceChildren();
    if (exactMinor(summary.spending_total_minor, "spending total") === 0n) {
      return;
    }
    const allocations = allocatePieUnits(
      summary.category_breakdown,
      summary.spending_total_minor,
    );
    if (!allocations.some((item) => item.bucket.category === state.selectedCategory)) {
      state.selectedCategory = null;
    }
    const svgNamespace = "http://www.w3.org/2000/svg";
    const svg = document.createElementNS(svgNamespace, "svg");
    svg.setAttribute("viewBox", "0 0 200 200");
    svg.setAttribute("class", "pie-svg");
    svg.setAttribute("role", "img");
    svg.setAttribute("aria-labelledby", "pie-title pie-description");
    const title = document.createElementNS(svgNamespace, "title");
    title.setAttribute("id", "pie-title");
    title.textContent = `Spending categories for ${summary.month}`;
    const description = document.createElementNS(svgNamespace, "desc");
    description.setAttribute("id", "pie-description");
    description.textContent = summary.category_breakdown
      .map(
        (bucket) => `${bucket.category}, ${formatMoney(bucket.spending_minor, summary.currency)}`,
      )
      .join("; ");
    const track = document.createElementNS(svgNamespace, "circle");
    track.setAttribute("class", "pie-track");
    track.setAttribute("cx", "100");
    track.setAttribute("cy", "100");
    track.setAttribute("r", "70");
    svg.append(title, description, track);

    let offset = 0n;
    allocations.forEach((item, index) => {
      const segment = document.createElementNS(svgNamespace, "path");
      segment.setAttribute("class", `pie-segment pie-color-${index % 12}`);
      segment.setAttribute("d", pieArcPath(offset, item.units));
      segment.setAttribute("tabindex", "0");
      segment.setAttribute("role", "button");
      segment.setAttribute(
        "aria-label",
        `${item.bucket.category}: ${formatMoney(item.bucket.spending_minor, summary.currency)}, ${formatPercent(item.bucket.spending_minor, summary.spending_total_minor)}`,
      );
      segment.dataset.category = item.bucket.category;
      segment.dataset.minor = item.bucket.spending_minor;
      segment.dataset.units = item.units.toString();
      segment.classList.toggle("is-selected", state.selectedCategory === item.bucket.category);
      segment.addEventListener("click", () => selectChartCategory(item.bucket.category));
      segment.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          selectChartCategory(item.bucket.category);
        }
      });
      svg.append(segment);
      offset += item.units;

      const legendButton = node("button", "legend-button");
      legendButton.type = "button";
      legendButton.dataset.category = item.bucket.category;
      legendButton.classList.toggle("is-selected", state.selectedCategory === item.bucket.category);
      const swatch = node("span", `legend-swatch swatch-color-${index % 12}`);
      swatch.setAttribute("aria-hidden", "true");
      const label = node("span", "", item.bucket.category);
      const value = node(
        "small",
        "",
        `${formatMoney(item.bucket.spending_minor, summary.currency)} · ${formatPercent(item.bucket.spending_minor, summary.spending_total_minor)}`,
      );
      legendButton.append(swatch, label, value);
      legendButton.addEventListener("click", () => selectChartCategory(item.bucket.category));
      elements.chartLegend.append(legendButton);
    });
    elements.pieChart.append(svg);
  }

  function selectChartCategory(category) {
    state.selectedCategory = state.selectedCategory === category ? null : category;
    for (const element of document.querySelectorAll("[data-category]")) {
      if (element.classList.contains("pie-segment") || element.classList.contains("legend-button")) {
        element.classList.toggle("is-selected", element.dataset.category === state.selectedCategory);
      }
    }
    announce(state.selectedCategory ? `${state.selectedCategory} selected in the chart.` : "Chart selection cleared.");
  }

  function renderCategoryTable(summary) {
    elements.categoryTableBody.replaceChildren();
    for (const bucket of summary.category_breakdown) {
      const row = node("tr");
      row.dataset.category = bucket.category;
      row.dataset.minor = bucket.spending_minor;
      const category = node("th", "", bucket.category);
      category.scope = "row";
      const count = node("td", "numeric", bucket.transaction_count);
      const share = node(
        "td",
        "numeric",
        formatPercent(bucket.spending_minor, summary.spending_total_minor),
      );
      const amount = node(
        "td",
        "numeric",
        formatMoney(bucket.spending_minor, summary.currency),
      );
      amount.dataset.minor = bucket.spending_minor;
      row.append(category, count, share, amount);
      elements.categoryTableBody.append(row);
    }
  }

  function renderTransactions(summary) {
    elements.transactionTableBody.replaceChildren();
    for (const transaction of summary.transactions) {
      if (!transaction.included) {
        continue;
      }
      const row = node("tr");
      row.dataset.identityId = transaction.identity_id;
      row.dataset.minor = transaction.amount_minor;
      row.dataset.spending = String(transaction.is_spending);

      const identityCell = node("td");
      identityCell.append(
        node("span", "merchant", transaction.merchant),
        node("span", "cell-meta", transaction.transaction_date),
        node("span", "cell-meta code-text", `Identity ${transaction.identity_id}`),
      );

      const categoryCell = node("td");
      const editor = node("div", "category-editor");
      const select = node("select");
      select.setAttribute("aria-label", `Category for ${transaction.merchant}`);
      for (const category of state.session.canonical_categories) {
        const option = node("option", "", category);
        option.value = category;
        option.selected = category === transaction.effective_category;
        select.append(option);
      }
      const save = node("button", "action-button", "Save");
      save.type = "button";
      save.dataset.action = "category-correction";
      save.addEventListener("click", () => saveCategory(transaction, select, save));
      editor.append(select, save);
      categoryCell.append(
        editor,
        node(
          "span",
          "cell-meta",
          `${transaction.category_source === "human" ? "Human correction" : "Automatic rule"} · ${transaction.correction_ids.length} history ${transaction.correction_ids.length === 1 ? "entry" : "entries"}`,
        ),
      );

      const supportsCell = node("td");
      const supports = node("ul", "provenance-list");
      for (const support of transaction.active_supports) {
        const item = node(
          "li",
          "",
          `${support.source_name} · ${support.source_locator}`,
        );
        item.title = `Run ${support.run_id}; occurrence ${support.occurrence_id}`;
        supports.append(item);
      }
      supportsCell.append(supports);

      const inclusionCell = node("td");
      inclusionCell.append(
        node("span", "state-pill", transaction.included ? "Included" : "Excluded"),
        node("span", "cell-meta", transaction.inclusion_reason),
      );

      const amountCell = node(
        "td",
        "numeric",
        formatMoney(transaction.amount_minor, transaction.currency),
      );
      amountCell.dataset.minor = transaction.amount_minor;
      amountCell.append(node("span", "cell-meta", transaction.currency));
      row.append(identityCell, categoryCell, supportsCell, inclusionCell, amountCell);
      elements.transactionTableBody.append(row);
    }
  }

  async function saveCategory(transaction, select, button) {
    await withAction(button, async () => {
      let result;
      try {
        result = await requestJson(
          `/api/transactions/${encodeURIComponent(transaction.identity_id)}/category`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ category: select.value }),
          },
        );
      } catch (error) {
        showGlobalError(error);
        announce(errorText(error));
        return;
      }
      const committedMessage = `${transaction.merchant} changed to ${result.effective_category}; ${result.history.length} correction ${result.history.length === 1 ? "entry" : "entries"}.`;
      announce(committedMessage);
      await refreshAfterCommit(committedMessage);
    });
  }

  function allowedFile(file) {
    const lower = file.name.toLocaleLowerCase("en-CA");
    return lower.endsWith(".csv") || lower.endsWith(".pdf");
  }

  function mediaTypeFor(file) {
    return file.name.toLocaleLowerCase("en-CA").endsWith(".pdf")
      ? "application/pdf"
      : "text/csv";
  }

  function safeHeaderFilename(filename) {
    if (
      typeof filename !== "string" ||
      !filename ||
      filename.length > 255 ||
      /[\\/\x00-\x1f\x7f]/.test(filename) ||
      !/^[\x20-\x7e]+$/.test(filename)
    ) {
      throw new Error("The selected filename cannot be represented safely by the local API.");
    }
    return filename;
  }

  function queueFiles(fileList) {
    const files = Array.from(fileList || []);
    if (!files.length) {
      return state.importTail;
    }
    setView("imports", { updateHash: true, focus: false });
    for (const file of files) {
      const item = {
        file,
        name: file.name,
        state: "queued",
        message: "Waiting",
        runId: null,
      };
      state.importItems.push(item);
      state.importTail = state.importTail.then(() => importOneFile(item));
    }
    renderImportQueue();
    return state.importTail;
  }

  async function importOneFile(item) {
    if (!allowedFile(item.file)) {
      item.state = "error";
      item.message = "Unsupported file type; choose a .csv or .pdf file.";
      renderImportQueue();
      announce(`${item.name} was not imported: unsupported file type.`);
      return;
    }
    if (item.file.size === 0) {
      item.state = "error";
      item.message = "The file is empty.";
      renderImportQueue();
      announce(`${item.name} was not imported: empty file.`);
      return;
    }
    if (state.session && item.file.size > state.session.max_upload_bytes) {
      item.state = "error";
      item.message = `File exceeds the ${state.session.max_upload_bytes}-byte local limit.`;
      renderImportQueue();
      announce(`${item.name} was not imported: file is too large.`);
      return;
    }
    item.state = "importing";
    item.message = "Importing…";
    renderImportQueue();
    let result;
    try {
      result = await requestJson("/api/import", {
        method: "POST",
        headers: {
          "Content-Type": mediaTypeFor(item.file),
          "X-Statement-Filename": safeHeaderFilename(item.file.name),
        },
        body: item.file,
      });
    } catch (error) {
      item.state = "error";
      if (error instanceof ApiError && error.status === 422 && error.details.run) {
        item.runId = error.details.run_id;
        item.message = `${error.code}: inspect the retained failed run.`;
        renderImportQueue();
        announce(`${item.name} failed: ${item.message}`);
        try {
          await refreshAll({ loading: false });
          await viewRun(item.runId, { focus: false, announce: false, throwOnError: true });
        } catch (refreshError) {
          showGlobalError(refreshError);
          announce(`${item.name} was retained as a failed run, but current views could not refresh. Reload to synchronize. ${errorText(refreshError)}`);
        }
      } else {
        item.message = errorText(error);
        announce(`${item.name} failed: ${item.message}`);
      }
      renderImportQueue();
      elements.statementFiles.value = "";
      return;
    }

    item.state = "success";
    item.runId = result.summary.run_id;
    item.message = `${result.summary.parsed_count} parsed · ${result.summary.failed_count} failed · ${result.summary.occurrence_count} occurrences`;
    const committedMessage = `${item.name} imported as a separate run.`;
    announce(committedMessage);
    elements.statementFiles.value = "";
    state.selectedMonth = null;
    const refreshed = await refreshAfterCommit(committedMessage);
    renderImportQueue();
    if (refreshed) {
      try {
        await viewRun(item.runId, { focus: false, announce: false, throwOnError: true });
      } catch (error) {
        reportCommittedRefreshFailure(committedMessage, error);
      }
    }
  }

  function renderImportQueue() {
    elements.importQueue.replaceChildren();
    for (const item of state.importItems) {
      const row = node("li", "import-item");
      row.dataset.state = item.state;
      if (item.runId) {
        row.dataset.runId = item.runId;
      }
      const name = node("strong", "", item.name);
      const status = node("span", "import-state", item.message);
      row.append(name, status);
      elements.importQueue.append(row);
    }
  }

  function renderRunHistory() {
    elements.runHistoryBody.replaceChildren();
    elements.runHistoryEmpty.hidden = state.runs.length > 0;
    elements.runHistoryTable.hidden = state.runs.length === 0;
    for (const run of state.runs) {
      const row = node("tr");
      row.dataset.runId = run.run_id;
      row.dataset.state = run.state;
      row.dataset.sourceName = run.source_name;
      const file = node("td");
      file.append(
        node("span", "merchant", run.source_name || "Unnamed source"),
        node("span", "cell-meta code-text", run.run_id),
        node("span", "cell-meta", `${run.source_type.toUpperCase()} · ${run.source_record_count} retained rows`),
      );
      const stateCell = node("td");
      const pill = node("span", "state-pill", run.state);
      pill.dataset.state = run.state;
      stateCell.append(pill);
      if (run.exact_reimport_of_run_id) {
        stateCell.append(node("span", "cell-meta", "Exact re-import"));
      }
      const parsed = node("td", "numeric", run.parsed_count);
      const failed = node("td", "numeric", run.failed_count);
      const actions = node("td");
      const buttons = node("div", "button-row");
      const inspect = node("button", "quiet-button", "Inspect");
      inspect.type = "button";
      inspect.addEventListener("click", () => viewRun(run.run_id));
      buttons.append(inspect);
      if (run.state === "active") {
        const undo = node("button", "danger-button", "Undo run");
        undo.type = "button";
        undo.dataset.action = "undo-run";
        undo.addEventListener("click", () => undoRun(run, undo));
        buttons.append(undo);
      }
      actions.append(buttons);
      row.append(file, stateCell, parsed, failed, actions);
      elements.runHistoryBody.append(row);
    }
  }

  async function viewRun(runId, options = {}) {
    try {
      state.activeRun = await requestJson(`/api/import-runs/${encodeURIComponent(runId)}`);
      renderRunDetail();
      if (options.focus !== false) {
        elements.runDetailTitle.focus();
      }
      if (options.announce !== false) {
        announce(`Run ${runId} loaded for structured review.`);
      }
    } catch (error) {
      if (options.throwOnError) {
        throw error;
      }
      showGlobalError(error);
      announce(errorText(error));
    }
  }

  function renderRunDetail() {
    elements.runDetail.replaceChildren();
    elements.runDetailEmpty.hidden = Boolean(state.activeRun);
    elements.runDetail.hidden = !state.activeRun;
    if (!state.activeRun) {
      return;
    }
    const run = state.activeRun;
    const summary = run.summary;
    const heading = node("div", "panel-heading");
    const titleGroup = node("div");
    titleGroup.append(
      node("h4", "merchant", summary.source_name || "Unnamed source"),
      node("p", "cell-meta code-text", summary.run_id),
    );
    const pill = node("span", "state-pill", summary.state);
    pill.dataset.state = summary.state;
    heading.append(titleGroup, pill);
    const metrics = node("div", "run-summary");
    for (const [label, value] of [
      ["Retained", summary.source_record_count],
      ["Parsed", summary.parsed_count],
      ["Failed", summary.failed_count],
      ["Occurrences", summary.occurrence_count],
    ]) {
      const metric = node("div", "run-metric");
      metric.append(node("strong", "", value), node("span", "cell-meta", label));
      metrics.append(metric);
    }
    const context = node("p", "cell-meta");
    setText(
      context,
      `${summary.source_type.toUpperCase()} · created ${summary.created_at}${summary.exact_reimport_of_run_id ? ` · exact re-import of ${summary.exact_reimport_of_run_id}` : ""}`,
    );

    const tableWrap = node("div", "table-scroll");
    const table = node("table", "run-record-table");
    const caption = node("caption", "", `Structured records for ${summary.source_name}`);
    const head = node("thead");
    const headRow = node("tr");
    for (const label of ["Locator / status", "Normalized transaction", "Effective review", "Provenance"]) {
      const th = node("th", "", label);
      th.scope = "col";
      headRow.append(th);
    }
    head.append(headRow);
    const body = node("tbody");
    for (const record of run.records) {
      const row = node("tr", record.parse_status === "failed" ? "failed-row" : "");
      row.dataset.sourceRecordId = record.source_record_id;
      row.dataset.parseStatus = record.parse_status;
      if (record.error_code) {
        row.dataset.errorCode = record.error_code;
      }
      const locator = node("td");
      locator.append(
        node("span", "code-text", record.source_locator),
        node("span", "cell-meta", record.parse_status),
      );
      if (record.error_code) {
        locator.append(node("span", "cell-meta", `Error: ${record.error_code}`));
      }

      const transactionCell = node("td");
      if (record.normalized_transaction) {
        const transaction = record.normalized_transaction;
        transactionCell.append(
          node("span", "merchant", transaction.merchant),
          node("span", "cell-meta", transaction.transaction_date),
          node("span", "cell-meta", `${formatMoney(transaction.amount_minor, transaction.currency)} ${transaction.currency}`),
        );
      } else {
        transactionCell.append(node("span", "muted", "No normalized transaction"));
      }

      const review = node("td");
      const effective = record.identity_id
        ? state.identityCatalog.get(record.identity_id)
        : null;
      if (effective) {
        review.append(
          node("span", "merchant", effective.effective_category),
          node("span", "cell-meta", effective.category_source === "human" ? "Human correction" : "Automatic category"),
        );
      } else {
        review.append(node("span", "muted", "No active category view"));
      }
      review.append(
        node("span", "cell-meta", `Duplicate: ${record.duplicate_state}`),
        node("span", "cell-meta", `${record.effective_included ? "Included" : "Excluded"} · ${record.effective_inclusion_reason}`),
      );

      const provenance = node("td");
      provenance.append(
        node("span", "cell-meta", `${record.source_name} · ${record.source_type}`),
        node("span", "cell-meta code-text", `Record ${record.source_record_id}`),
      );
      if (record.occurrence_id) {
        provenance.append(node("span", "cell-meta code-text", `Occurrence ${record.occurrence_id}`));
      }
      row.append(locator, transactionCell, review, provenance);
      body.append(row);
    }
    table.append(caption, head, body);
    tableWrap.append(table);
    elements.runDetail.append(heading, metrics, context, tableWrap);
  }

  async function undoRun(run, button) {
    const confirmed = window.confirm(
      `Undo import run for “${run.source_name || run.run_id}”? This removes only this run's active support and keeps retained history.`,
    );
    if (!confirmed) {
      announce("Run undo cancelled.");
      return;
    }
    await withAction(button, async () => {
      let result;
      try {
        result = await requestJson(
          `/api/import-runs/${encodeURIComponent(run.run_id)}/undo`,
          { method: "POST" },
        );
      } catch (error) {
        showGlobalError(error);
        announce(errorText(error));
        return;
      }
      state.activeRun = result;
      renderRunDetail();
      const committedMessage = `${run.source_name || run.run_id} is now undone.`;
      announce(committedMessage);
      await refreshAfterCommit(committedMessage);
    });
  }

  function supportContext(identityId) {
    const transaction = state.identityCatalog.get(identityId);
    if (!transaction || !transaction.active_supports.length) {
      return "No active source support";
    }
    return transaction.active_supports
      .map((support) => `${support.source_name} · ${support.source_locator} · run ${support.run_id}`)
      .join("; ");
  }

  function renderDuplicates() {
    elements.duplicateList.replaceChildren();
    elements.duplicatesEmpty.hidden = state.duplicates.length > 0;
    for (const candidate of state.duplicates) {
      const card = node("article", "duplicate-card");
      card.dataset.duplicateLinkId = candidate.duplicate_link_id;
      card.dataset.effectiveDecision = candidate.effective_decision;
      const header = node("div", "duplicate-card-header");
      const titleGroup = node("div");
      titleGroup.append(
        node("h3", "", "Possible duplicate pair"),
        node("p", "cell-meta code-text", candidate.duplicate_link_id),
      );
      const pill = node("span", "state-pill", candidate.effective_decision.replace("_", " "));
      pill.dataset.state = candidate.effective_decision;
      header.append(titleGroup, pill);

      const sides = node("div", "duplicate-sides");
      const radioName = `kept-${candidate.duplicate_link_id}`;
      sides.append(
        duplicateSide(candidate, candidate.left, "First record", radioName),
        duplicateSide(candidate, candidate.right, "Second record", radioName),
      );

      const actions = node("div", "decision-actions");
      const distinct = node("button", "secondary-button", "They are distinct");
      distinct.type = "button";
      distinct.dataset.action = "duplicate-distinct";
      const same = node("button", "action-button", "Same transaction — keep selected");
      same.type = "button";
      same.dataset.action = "duplicate-same";
      distinct.addEventListener("click", () => decideDuplicate(candidate, "distinct", distinct, card));
      same.addEventListener("click", () => decideDuplicate(candidate, "same_transaction", same, card));
      actions.append(distinct, same);

      const error = node("div", "candidate-error");
      error.setAttribute("role", "alert");
      error.setAttribute("tabindex", "-1");
      error.hidden = true;

      const details = node("details", "history-details");
      const summary = node(
        "summary",
        "",
        `Decision history (${candidate.history.length})`,
      );
      const history = node("ol", "history-list");
      if (!candidate.history.length) {
        history.append(node("li", "", "No human decision yet."));
      } else {
        for (const decision of candidate.history) {
          history.append(
            node(
              "li",
              "",
              `${decision.created_at} · ${decision.decision}${decision.kept_identity_id ? ` · kept ${decision.kept_identity_id}` : ""}`,
            ),
          );
        }
      }
      details.append(summary, history);
      card.append(header, sides, actions, error, details);
      elements.duplicateList.append(card);
    }
  }

  function duplicateSide(candidate, side, labelText, radioName) {
    const wrapper = node("div", "duplicate-side");
    wrapper.dataset.identityId = side.identity_id;
    wrapper.dataset.included = String(side.included);
    wrapper.classList.toggle("is-excluded", !side.included);
    const radio = node("input");
    radio.type = "radio";
    radio.name = radioName;
    radio.value = side.identity_id;
    radio.id = `${radioName}-${side.identity_id}`;
    radio.checked = candidate.kept_identity_id === side.identity_id;
    const label = node("label");
    label.htmlFor = radio.id;
    label.append(
      node("span", "cell-meta", labelText),
      node("span", "merchant", side.merchant),
      node("span", "cell-meta", side.transaction_date),
      node("span", "amount", `${formatMoney(side.amount_minor, side.currency)} ${side.currency}`),
      node("span", "cell-meta", side.included ? "Currently included" : "Currently excluded"),
      node("span", "cell-meta", supportContext(side.identity_id)),
    );
    wrapper.append(radio, label);
    return wrapper;
  }

  async function decideDuplicate(candidate, decision, button, card) {
    const payload = { decision };
    if (decision === "same_transaction") {
      const selected = card.querySelector(`input[name="kept-${CSS.escape(candidate.duplicate_link_id)}"]:checked`);
      if (!selected) {
        const error = card.querySelector(".candidate-error");
        setText(error, "Choose which transaction identity to keep before marking the pair as the same transaction.");
        error.hidden = false;
        error.focus();
        return;
      }
      payload.kept_identity_id = selected.value;
    }
    const error = card.querySelector(".candidate-error");
    error.hidden = true;
    setText(error, "");
    await withAction(button, async () => {
      let result;
      try {
        result = await requestJson(
          `/api/duplicates/${encodeURIComponent(candidate.duplicate_link_id)}/decision`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
          },
        );
      } catch (caught) {
        setText(error, errorText(caught));
        error.hidden = false;
        error.focus();
        announce(`Duplicate decision was not saved: ${errorText(caught)}`);
        return;
      }
      const committedMessage = `Duplicate decision saved as ${result.effective_decision.replace("_", " ")}; history now has ${result.history.length} entries.`;
      announce(committedMessage);
      await refreshAfterCommit(committedMessage);
    });
  }

  async function withAction(button, action) {
    if (button.dataset.busy === "true") {
      return;
    }
    button.dataset.busy = "true";
    button.disabled = true;
    try {
      await action();
    } finally {
      button.dataset.busy = "false";
      if (button.isConnected) {
        button.disabled = false;
      }
    }
  }

  function bindEvents() {
    for (const button of document.querySelectorAll(".nav-button[data-view]")) {
      button.addEventListener("click", () => setView(button.dataset.view, { focus: true }));
    }
    for (const button of document.querySelectorAll("[data-go-view]")) {
      button.addEventListener("click", () => setView(button.dataset.goView, { focus: true }));
    }
    window.addEventListener("hashchange", () => setView(viewFromHash(), { updateHash: false, focus: true }));
    elements.monthSelect.addEventListener("change", () => {
      state.selectedMonth = elements.monthSelect.value;
      state.monthData = state.monthSummaries.get(state.selectedMonth) || null;
      state.selectedCategory = null;
      renderOverview();
      announce(`${state.selectedMonth} loaded.`);
    });
    elements.statementFiles.addEventListener("change", () => queueFiles(elements.statementFiles.files));
    for (const eventName of ["dragenter", "dragover"]) {
      elements.dropZone.addEventListener(eventName, (event) => {
        event.preventDefault();
        elements.dropZone.classList.add("is-dragging");
        if (event.dataTransfer) {
          event.dataTransfer.dropEffect = "copy";
        }
      });
    }
    for (const eventName of ["dragleave", "drop"]) {
      elements.dropZone.addEventListener(eventName, (event) => {
        event.preventDefault();
        elements.dropZone.classList.remove("is-dragging");
      });
    }
    elements.dropZone.addEventListener("drop", (event) => {
      if (event.dataTransfer) {
        queueFiles(event.dataTransfer.files);
      }
    });
    elements.refreshRuns.addEventListener("click", () => refreshAll({ loading: false }).catch(() => {}));
    elements.refreshDuplicates.addEventListener("click", () => refreshAll({ loading: false }).catch(() => {}));
  }

  function captureElements() {
    Object.assign(elements, {
      statusRegion: byId("status-region"),
      errorBanner: byId("error-banner"),
      runCountBadge: byId("run-count-badge"),
      duplicateCountBadge: byId("duplicate-count-badge"),
      monthSelect: byId("month-select"),
      overviewLoading: byId("overview-loading"),
      overviewEmpty: byId("overview-empty"),
      overviewContent: byId("overview-content"),
      spendingTotal: byId("spending-total"),
      creditTotal: byId("credit-total"),
      transactionCount: byId("transaction-count"),
      spendingCount: byId("spending-count"),
      creditCount: byId("credit-count"),
      zeroSpending: byId("zero-spending"),
      chartContent: byId("chart-content"),
      pieChart: byId("pie-chart"),
      chartLegend: byId("chart-legend"),
      categoryTableBody: byId("category-table-body"),
      transactionTableBody: byId("transaction-table-body"),
      transactionsCaption: byId("transactions-caption"),
      reconciliationStatus: byId("reconciliation-status"),
      uploadLimit: byId("upload-limit"),
      dropZone: byId("drop-zone"),
      statementFiles: byId("statement-files"),
      importQueue: byId("import-queue"),
      refreshRuns: byId("refresh-runs"),
      runHistoryEmpty: byId("run-history-empty"),
      runHistoryTable: byId("run-history-table"),
      runHistoryBody: byId("run-history-body"),
      runDetailTitle: byId("run-detail-title"),
      runDetailEmpty: byId("run-detail-empty"),
      runDetail: byId("run-detail"),
      refreshDuplicates: byId("refresh-duplicates"),
      duplicatesLoading: byId("duplicates-loading"),
      duplicatesEmpty: byId("duplicates-empty"),
      duplicateList: byId("duplicate-list"),
    });
  }

  async function boot() {
    captureElements();
    bindEvents();
    setView(viewFromHash(), { updateHash: false, focus: false });
    elements.overviewEmpty.hidden = true;
    elements.overviewLoading.hidden = false;
    try {
      await loadSession();
      await refreshAll({ loading: false });
      announce("Local session ready.");
    } catch (error) {
      elements.overviewLoading.hidden = true;
      elements.overviewEmpty.hidden = false;
      showGlobalError(error);
      announce(errorText(error));
    }
  }

  window.ExpenseAppTesting = Object.freeze({
    PIE_SCALE: PIE_SCALE.toString(),
    allocatePieUnits,
    formatMoney,
    formatPercent,
    pieArcPath,
    queueFiles,
    reconcileMonth,
  });

  boot();
})();
