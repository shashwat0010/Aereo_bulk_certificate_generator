// App State
let activeJobId = null;
let pollInterval = null;

// Sample Data Sets
const SAMPLE_VALID_RECIPIENTS = [
  { name: "Eleanor Vance", email: "eleanor.vance@example.com" },
  { name: "Marcus Thorne", email: "marcus.thorne@example.com" },
  { name: "Sophia Sterling", email: "sophia.sterling@example.com" },
  { name: "Devon Reynolds", email: "devon.reynolds@example.com" },
  { name: "Aria Montgomery", email: "aria.montgomery@example.com" }
];

const SAMPLE_MIXED_RECIPIENTS = [
  { name: "Alice Wonderland", email: "alice.wonderland@example.com" },
  { name: "Bob Martin", email: "invalid-email-address-missing-domain" }, // Demonstrates error isolation
  { name: "Carlos Santana", email: "carlos.santana@example.com" },
  { name: "Diana Prince", email: "diana.prince@example.com" }
];

// Initialize on DOM load
document.addEventListener("DOMContentLoaded", () => {
  loadSampleData(false);
});

function switchTab(tabId) {
  document.querySelectorAll(".tab-content").forEach(el => el.classList.remove("active"));
  document.querySelectorAll(".tab-btn").forEach(el => el.classList.remove("active"));
  
  const target = document.getElementById(tabId);
  if (target) target.classList.add("active");

  const btnMap = {
    "tab-generate": "tab-btn-generate",
    "tab-history": "tab-btn-history",
    "tab-verify": "tab-btn-verify"
  };
  const btn = document.getElementById(btnMap[tabId]);
  if (btn) btn.classList.add("active");

  if (tabId === "tab-history") {
    loadJobHistory();
  }
}

function startNewJob() {
  // 1. Switch to the generate tab
  switchTab("tab-generate");

  // 2. Clear any polling interval and active state
  if (pollInterval) {
    clearInterval(pollInterval);
    pollInterval = null;
  }
  activeJobId = null;

  // 3. Reset the monitor panel back to clean placeholder state
  const placeholder = document.getElementById("monitor-placeholder");
  const activeBox = document.getElementById("monitor-active");
  const badge = document.getElementById("active-job-badge");
  const tbody = document.getElementById("cert-table-body");
  const zipContainer = document.getElementById("zip-action-container");

  if (placeholder) placeholder.style.display = "block";
  if (activeBox) activeBox.style.display = "none";
  if (badge) {
    badge.className = "badge badge-idle";
    badge.innerText = "Ready to Run";
  }
  if (tbody) tbody.innerHTML = "";
  if (zipContainer) zipContainer.style.display = "none";

  // 4. Reset progress indicators
  const fill = document.getElementById("progress-fill");
  if (fill) fill.style.width = "0%";
  const pLabel = document.getElementById("progress-percent-label");
  if (pLabel) pLabel.innerText = "0% Complete";
  const cLabel = document.getElementById("progress-counts-label");
  if (cLabel) cLabel.innerText = "0 / 0 processed";

  // 5. Reset metrics counters
  const statTotal = document.getElementById("stat-total");
  const statSuccess = document.getElementById("stat-success");
  const statFailed = document.getElementById("stat-failed");
  if (statTotal) statTotal.innerText = "0";
  if (statSuccess) statSuccess.innerText = "0";
  if (statFailed) statFailed.innerText = "0";

  // 6. Ensure sample recipients are populated if empty
  const recipientsField = document.getElementById("recipients-json");
  if (recipientsField && !recipientsField.value.trim()) {
    loadSampleData(false);
  }

  // 7. Focus on the job title input for fast entry
  const titleInput = document.getElementById("job-title");
  if (titleInput) {
    titleInput.focus();
    titleInput.select();
  }
}

function loadSampleData(withError = false) {
  const data = withError ? SAMPLE_MIXED_RECIPIENTS : SAMPLE_VALID_RECIPIENTS;
  document.getElementById("recipients-json").value = JSON.stringify(data, null, 2);
}

async function handleJobSubmit(e) {
  e.preventDefault();
  const submitBtn = document.getElementById("btn-submit-job");
  
  try {
    const rawRecipients = document.getElementById("recipients-json").value.trim();
    let recipientsList;
    try {
      recipientsList = JSON.parse(rawRecipients);
      if (!Array.isArray(recipientsList) || recipientsList.length === 0) {
        throw new Error("Recipients must be a non-empty array of objects.");
      }
    } catch (err) {
      alert("Invalid JSON format for recipients: " + err.message);
      return;
    }

    const payload = {
      title: document.getElementById("job-title").value.trim(),
      issuer_name: document.getElementById("issuer-name").value.trim(),
      issue_date: document.getElementById("issue-date").value.trim(),
      description: document.getElementById("job-desc").value.trim(),
      recipients: recipientsList
    };

    submitBtn.disabled = true;
    submitBtn.innerHTML = "<span>Submitting...</span>";

    const res = await fetch("/api/v1/certificates/jobs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      const errData = await res.json();
      throw new Error(errData.detail || "Job creation failed.");
    }

    const jobData = await res.json();
    activeJobId = jobData.job_id;

    // Show monitor panel
    document.getElementById("monitor-placeholder").style.display = "none";
    document.getElementById("monitor-active").style.display = "block";
    document.getElementById("active-job-id").innerText = activeJobId;
    document.getElementById("active-job-title").innerText = jobData.title;

    // Start polling
    startPolling(activeJobId);

  } catch (err) {
    alert("Error: " + err.message);
  } finally {
    submitBtn.disabled = false;
    submitBtn.innerHTML = "<span>Generate Certificates</span><span class='btn-icon'>⚡</span>";
  }
}

function startPolling(jobId) {
  if (pollInterval) clearInterval(pollInterval);
  fetchJobDetails(jobId);
  pollInterval = setInterval(() => {
    fetchJobDetails(jobId);
  }, 1000);
}

async function fetchJobDetails(jobId) {
  try {
    const res = await fetch(`/api/v1/certificates/jobs/${jobId}`);
    if (!res.ok) return;

    const data = await res.json();
    renderJobProgress(data);

    // Stop polling if completed or failed or partial
    if (["COMPLETED", "PARTIAL_SUCCESS", "FAILED"].includes(data.status)) {
      if (pollInterval) {
        clearInterval(pollInterval);
        pollInterval = null;
      }
    }
  } catch (err) {
    console.error("Polling error:", err);
  }
}

function renderJobProgress(data) {
  // Status Badge
  const badge = document.getElementById("active-job-badge");
  badge.className = "badge";
  badge.innerText = data.status;

  if (data.status === "PENDING") badge.classList.add("badge-pending");
  else if (data.status === "PROCESSING") badge.classList.add("badge-processing");
  else if (data.status === "COMPLETED") badge.classList.add("badge-completed");
  else if (data.status === "PARTIAL_SUCCESS") badge.classList.add("badge-partial");
  else badge.classList.add("badge-failed");

  // Metrics
  document.getElementById("stat-total").innerText = data.total_count;
  document.getElementById("stat-success").innerText = data.success_count;
  document.getElementById("stat-failed").innerText = data.failed_count;

  // Progress Bar
  const percent = data.total_count > 0 ? Math.round((data.processed_count / data.total_count) * 100) : 0;
  document.getElementById("progress-fill").style.width = `${percent}%`;
  document.getElementById("progress-percent-label").innerText = `${percent}% Complete`;
  document.getElementById("progress-counts-label").innerText = `${data.processed_count} / ${data.total_count} processed`;

  // Zip Action
  const zipContainer = document.getElementById("zip-action-container");
  const zipBtn = document.getElementById("btn-download-zip");
  if (data.zip_download_url) {
    zipContainer.style.display = "block";
    zipBtn.href = data.zip_download_url;
  } else {
    zipContainer.style.display = "none";
  }

  // Certificate Rows
  const tbody = document.getElementById("cert-table-body");
  if (data.certificates && data.certificates.length > 0) {
    tbody.innerHTML = data.certificates.map(cert => {
      let statusClass = "badge-pending";
      if (cert.status === "COMPLETED") statusClass = "badge-completed";
      if (cert.status === "FAILED") statusClass = "badge-failed";

      let actions = "-";
      if (cert.status === "COMPLETED") {
        actions = `
          <button class="table-btn" onclick="openPdfModal('${cert.id}', '${escapeQuotes(cert.recipient_name)}')">👁️ Preview</button>
          <a class="table-btn" href="${cert.download_url}" target="_blank">⬇️ Download</a>
        `;
      } else if (cert.status === "FAILED") {
        actions = `<span style="color: var(--error-red); font-size: 0.75rem;" title="${escapeQuotes(cert.error_message || '')}">❌ ${cert.error_message ? escapeQuotes(cert.error_message.slice(0, 30)) + '...' : 'Failed'}</span>`;
      }

      return `
        <tr>
          <td>
            <strong>${escapeQuotes(cert.recipient_name)}</strong><br>
            <span style="color: var(--text-dim); font-size: 0.75rem;">${escapeQuotes(cert.recipient_email)}</span>
          </td>
          <td><span class="badge ${statusClass}">${cert.status}</span></td>
          <td class="code-font" style="font-size: 0.8rem;">${cert.certificate_code}</td>
          <td>${actions}</td>
        </tr>
      `;
    }).join("");
  }
}

async function loadJobHistory() {
  const tbody = document.getElementById("history-table-body");
  try {
    const res = await fetch("/api/v1/certificates/jobs");
    if (!res.ok) throw new Error("Failed to load jobs");
    const jobs = await res.json();

    if (jobs.length === 0) {
      tbody.innerHTML = `<tr><td colspan="8" class="text-center" style="padding: 2rem; color: var(--text-dim);">No jobs found. Run your first job from the Generate tab.</td></tr>`;
      return;
    }

    tbody.innerHTML = jobs.map(j => {
      let statusClass = "badge-pending";
      if (j.status === "COMPLETED") statusClass = "badge-completed";
      if (j.status === "PARTIAL_SUCCESS") statusClass = "badge-partial";
      if (j.status === "FAILED") statusClass = "badge-failed";

      const createdDate = j.created_at ? new Date(j.created_at).toLocaleString() : "-";
      return `
        <tr>
          <td style="font-size: 0.75rem; color: var(--text-muted);">${createdDate}</td>
          <td class="code-font" style="font-size: 0.75rem;">${j.job_id.slice(0, 8)}...</td>
          <td><strong>${escapeQuotes(j.title)}</strong></td>
          <td><span class="badge ${statusClass}">${j.status}</span></td>
          <td>${j.total_count}</td>
          <td style="color: var(--success-green); font-weight: 600;">${j.success_count}</td>
          <td style="color: var(--error-red); font-weight: 600;">${j.failed_count}</td>
          <td>
            <button class="table-btn" onclick="inspectJob('${j.job_id}')">Track / View</button>
          </td>
        </tr>
      `;
    }).join("");
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="8" style="color: var(--error-red);">Error loading history: ${err.message}</td></tr>`;
  }
}

function inspectJob(jobId) {
  activeJobId = jobId;
  switchTab("tab-generate");
  document.getElementById("monitor-placeholder").style.display = "none";
  document.getElementById("monitor-active").style.display = "block";
  document.getElementById("active-job-id").innerText = jobId;
  startPolling(jobId);
}

async function handleVerifySubmit(e) {
  e.preventDefault();
  const code = document.getElementById("verify-code").value.trim();
  const resultBox = document.getElementById("verify-result");

  try {
    const res = await fetch(`/api/v1/certificates/verify/${encodeURIComponent(code)}`);
    const data = await res.json();
    resultBox.style.display = "block";

    if (data.valid) {
      resultBox.innerHTML = `
        <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid var(--success-green); border-radius: var(--radius-md); padding: 1.25rem;">
          <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.75rem;">
            <span style="font-size: 1.5rem;">✅</span>
            <strong style="color: var(--success-green); font-size: 1.1rem;">Authentic Certificate Verified</strong>
          </div>
          <p style="font-size: 0.9rem; margin-bottom: 0.5rem;"><strong>Recipient:</strong> ${escapeQuotes(data.recipient_name)} (${escapeQuotes(data.recipient_email)})</p>
          <p style="font-size: 0.9rem; margin-bottom: 0.5rem;"><strong>Course / Program:</strong> ${escapeQuotes(data.title)}</p>
          <p style="font-size: 0.9rem; margin-bottom: 0.5rem;"><strong>Issuer:</strong> ${escapeQuotes(data.issuer_name)}</p>
          <p style="font-size: 0.9rem; margin-bottom: 0.5rem;"><strong>Date of Issue:</strong> ${escapeQuotes(data.issue_date)}</p>
          <p style="font-size: 0.8rem; color: var(--text-dim); margin-top: 0.75rem;">Verification Code: <code>${data.certificate_code}</code></p>
        </div>
      `;
    } else {
      resultBox.innerHTML = `
        <div style="background: rgba(239, 68, 68, 0.1); border: 1px solid var(--error-red); border-radius: var(--radius-md); padding: 1.25rem;">
          <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">
            <span style="font-size: 1.5rem;">❌</span>
            <strong style="color: var(--error-red); font-size: 1.1rem;">Certificate Verification Failed</strong>
          </div>
          <p style="font-size: 0.85rem; color: var(--text-muted);">${escapeQuotes(data.message || 'Certificate record not found.')}</p>
        </div>
      `;
    }
  } catch (err) {
    alert("Verification error: " + err.message);
  }
}

function openPdfModal(certId, recipientName) {
  const modal = document.getElementById("pdf-modal");
  const frame = document.getElementById("pdf-frame");
  const title = document.getElementById("modal-title");

  title.innerText = `Certificate Preview - ${recipientName}`;
  frame.src = `/api/v1/certificates/${certId}/preview`;
  modal.classList.add("open");
}

function closeModal() {
  const modal = document.getElementById("pdf-modal");
  const frame = document.getElementById("pdf-frame");
  frame.src = "";
  modal.classList.remove("open");
}

function escapeQuotes(str) {
  if (!str) return "";
  return str.replace(/"/g, "&quot;").replace(/'/g, "&#39;");
}
