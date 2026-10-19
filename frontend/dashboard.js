// =========================================================
// HELPERS
// =========================================================

function el(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
}

function emptyState(container, message) {
    container.replaceChildren(el("p", "empty", message));
}

function formatBytes(bytes) {
    if (bytes === null || bytes === undefined) return "—";
    if (bytes < 1024) return bytes + " B";
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
    return (bytes / (1024 * 1024)).toFixed(1) + " MB";
}

function formatDate(iso) {
    if (!iso) return "—";
    return new Date(iso).toLocaleString();
}

function dayKey(date) {
    // Local calendar day as YYYY-MM-DD
    const y = date.getFullYear();
    const m = String(date.getMonth() + 1).padStart(2, "0");
    const d = String(date.getDate()).padStart(2, "0");
    return `${y}-${m}-${d}`;
}

// Horizontal bar chart: rows = [{ label, value }]
function barChart(container, rows, emptyMessage) {
    if (!rows.length || rows.every(row => row.value === 0)) {
        emptyState(container, emptyMessage);
        return;
    }

    const max = Math.max(...rows.map(row => row.value));
    const list = el("div", "bars");

    rows.forEach(row => {
        const line = el("div", "bar-row");
        const label = el("span", "bar-label", row.label);
        label.title = row.label;

        const track = el("div", "bar-track");
        const fill = el("div", "bar-fill");
        fill.style.width = max ? (row.value / max) * 100 + "%" : "0";
        track.appendChild(fill);

        line.append(label, track, el("span", "bar-value", String(row.value)));
        list.appendChild(line);
    });

    container.replaceChildren(list);
}

// Vertical column chart for the last N days
function columnChart(container, rows, emptyMessage) {
    if (!rows.length || rows.every(row => row.value === 0)) {
        emptyState(container, emptyMessage);
        return;
    }

    const max = Math.max(...rows.map(row => row.value));
    const chart = el("div", "columns");

    rows.forEach(row => {
        const column = el("div", "column");
        column.title = `${row.label}: ${row.value}`;

        const area = el("div", "column-area");
        const fill = el("div", "column-fill");
        fill.style.height = max ? (row.value / max) * 100 + "%" : "0";
        area.appendChild(fill);

        column.append(
            el("span", "column-value", row.value ? String(row.value) : ""),
            area,
            el("span", "column-label", row.shortLabel)
        );
        chart.appendChild(column);
    });

    container.replaceChildren(chart);
}


// =========================================================
// RENDERING
// =========================================================

function renderStats(data) {
    document.getElementById("statDocuments").textContent = data.total_documents;
    document.getElementById("statUnique").textContent = data.unique_documents;
    document.getElementById("statChunks").textContent = data.total_chunks;
    document.getElementById("statVectors").textContent = data.total_vectors;
}

function renderUploadsChart(documents) {
    const container = document.getElementById("uploadsChart");
    const dated = documents.filter(doc => doc.uploaded_at);

    if (!dated.length) {
        emptyState(
            container,
            documents.length
                ? "No upload dates yet. Dates are recorded for new uploads."
                : "No uploads yet."
        );
        return;
    }

    const counts = {};
    dated.forEach(doc => {
        const key = dayKey(new Date(doc.uploaded_at));
        counts[key] = (counts[key] || 0) + 1;
    });

    // Last 14 days, oldest first
    const rows = [];
    const today = new Date();
    for (let i = 13; i >= 0; i--) {
        const day = new Date(today);
        day.setDate(today.getDate() - i);
        const key = dayKey(day);
        rows.push({
            label: key,
            shortLabel: day.toLocaleDateString(undefined, { day: "numeric", month: "short" }),
            value: counts[key] || 0
        });
    }

    columnChart(container, rows, "No uploads in the last 14 days.");
}

function renderTypesChart(documents) {
    const counts = {};
    documents.forEach(doc => {
        const parts = doc.filename.split(".");
        const type = parts.length > 1 ? parts.pop().toUpperCase() : "Unknown";
        counts[type] = (counts[type] || 0) + 1;
    });

    const rows = Object.entries(counts)
        .map(([label, value]) => ({ label, value }))
        .sort((a, b) => b.value - a.value);

    barChart(document.getElementById("typesChart"), rows, "No documents yet.");
}

function renderChunksChart(documents) {
    const rows = documents
        .map(doc => ({ label: doc.filename, value: doc.chunks }))
        .sort((a, b) => b.value - a.value)
        .slice(0, 10);

    barChart(document.getElementById("chunksChart"), rows, "No documents yet.");
}

function renderDocumentsTable(documents) {
    const container = document.getElementById("documentsTable");

    if (!documents.length) {
        emptyState(container, "No documents uploaded yet. Upload a PDF to get started.");
        return;
    }

    const table = el("table");
    const head = el("tr");
    ["File", "Chunks", "Size", "Uploaded", "Note"].forEach(title => {
        head.appendChild(el("th", null, title));
    });
    table.appendChild(head);

    documents.slice(0, 10).forEach(doc => {
        const row = el("tr");
        row.append(
            el("td", null, doc.filename),
            el("td", null, String(doc.chunks)),
            el("td", null, formatBytes(doc.size_bytes)),
            el("td", null, formatDate(doc.uploaded_at)),
            noteCell(doc)
        );
        table.appendChild(row);
    });

    const wrap = el("div", "table-wrap");
    wrap.appendChild(table);
    container.replaceChildren(wrap);
}

function noteCell(doc) {
    const cell = el("td");
    if (doc.duplicate_of) {
        const badge = el("span", "badge", "Duplicate");
        badge.title = `Same file as ${doc.duplicate_of}`;
        cell.append(badge, el("span", "muted", ` of ${doc.duplicate_of}`));
    }
    return cell;
}

function renderQuestions() {
    const history = getQuestionHistory();
    const container = document.getElementById("questionsList");

    document.getElementById("statQuestions").textContent = history.length;

    if (!history.length) {
        emptyState(container, "No questions asked from this browser yet.");
        return;
    }

    const list = el("ul", "question-list");
    history.slice(0, 10).forEach(item => {
        const entry = el("li");
        entry.append(
            el("span", null, item.question),
            el("span", "muted", formatDate(item.asked_at) + (item.answered ? "" : " · no answer"))
        );
        list.appendChild(entry);
    });

    container.replaceChildren(list);
}


// =========================================================
// LOAD DATA
// =========================================================

async function loadDashboard() {
    const status = document.getElementById("status");
    status.textContent = "Loading…";
    status.className = "status";

    renderQuestions();

    try {
        const response = await fetch(`${API_BASE}/dashboard`);
        if (!response.ok) throw new Error(`Server returned ${response.status}`);

        const data = await response.json();
        const documents = data.documents || [];

        renderStats(data);
        renderUploadsChart(documents);
        renderTypesChart(documents);
        renderChunksChart(documents);
        renderDocumentsTable(documents);

        status.textContent = "";
    } catch (error) {
        status.textContent = `Could not reach the backend at ${API_BASE}. Is it running? (${error.message})`;
        status.className = "status error";

        ["uploadsChart", "typesChart", "chunksChart", "documentsTable"].forEach(id => {
            emptyState(document.getElementById(id), "No data available.");
        });
    }
}


// =========================================================
// QUICK UPLOAD
// =========================================================

document.getElementById("uploadButton").addEventListener("click", async function () {
    const file = document.getElementById("document").files[0];
    const status = document.getElementById("status");

    if (!file) {
        alert("Please choose a PDF first.");
        return;
    }

    const formData = new FormData();
    formData.append("file", file);

    this.disabled = true;
    status.textContent = `Uploading ${file.name}…`;
    status.className = "status";

    try {
        const response = await fetch(`${API_BASE}/upload`, { method: "POST", body: formData });
        const data = await response.json();

        if (data.error) {
            status.textContent = data.error;
            status.className = "status error";
        } else {
            await loadDashboard();
            status.textContent = `${data.message} (${data.filename})`;
        }
    } catch (error) {
        status.textContent = `Upload failed: ${error.message}`;
        status.className = "status error";
    } finally {
        this.disabled = false;
    }
});

document.getElementById("refreshButton").addEventListener("click", loadDashboard);

loadDashboard();
