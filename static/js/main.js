document.addEventListener("DOMContentLoaded", () => {
  const jobsContainer = document.getElementById("jobsContainer");
  const searchInput = document.getElementById("searchInput");
  const jobCount = document.getElementById("jobCount");

  let allJobs = [];

  // Fetch jobs from the Flask API
  fetch("/api/jobs")
    .then((response) => response.json())
    .then((data) => {
      if (data.status === "success") {
        allJobs = data.data;
        renderJobs(allJobs);
      } else {
        jobsContainer.innerHTML = `<div class="error-msg">Error loading jobs: ${data.message}</div>`;
      }
    })
    .catch((err) => {
      jobsContainer.innerHTML = `<div class="error-msg">Connection error. Could not reach the API.</div>`;
    });

  // Render logic
  function renderJobs(jobs) {
    if (jobs.length === 0) {
      jobsContainer.innerHTML = `<div class="loader"><p>No relevant jobs found matching your criteria.</p></div>`;
      jobCount.textContent = `0 Roles Found`;
      return;
    }

    jobCount.textContent = `${jobs.length} Active Roles Found`;
    jobsContainer.innerHTML = jobs.map((job) => createJobCard(job)).join("");
  }

  // Beautiful Job Card Component
  function createJobCard(job) {
    // Generate a pseudo-logo
    const initial = job.company ? job.company.charAt(0).toUpperCase() : "C";

    return `
            <div class="job-card">
                <div class="job-header">
                    <div class="company-logo">${initial}</div>
                    <span class="job-date"><i class="ri-history-line"></i> ${job.scraped_at}</span>
                </div>
                
                <div class="job-company">${job.company}</div>
                <h3 class="job-title">${job.title}</h3>
                
                <div class="job-tags">
                    <span class="tag"><i class="ri-map-pin-line"></i> ${escapeHTML(job.location)}</span>
                    <span class="tag"><i class="ri-macbook-line"></i> Remote</span>
                    <span class="tag"><i class="ri-global-line"></i> ${escapeHTML(job.source_board)}</span>
                </div>
                
                <div class="job-footer">
                    <div class="salary">
                        <i class="ri-money-dollar-circle-line"></i> ${escapeHTML(job.salary)}
                    </div>
                    <a href="${job.job_url}" target="_blank" class="apply-btn">Apply Now <i class="ri-arrow-right-up-line"></i></a>
                </div>
            </div>
        `;
  }

  // Search Filtering
  searchInput.addEventListener("input", (e) => {
    const term = e.target.value.toLowerCase();
    const filtered = allJobs.filter(
      (job) =>
        (job.title && job.title.toLowerCase().includes(term)) ||
        (job.company && job.company.toLowerCase().includes(term)) ||
        (job.location && job.location.toLowerCase().includes(term)),
    );
    renderJobs(filtered);
  });

  // Utility to prevent XSS from scraped data
  function escapeHTML(str) {
    if (!str) return "Not Specified";
    return str.replace(
      /[&<>'"]/g,
      (tag) =>
        ({
          "&": "&amp;",
          "<": "&lt;",
          ">": "&gt;",
          "'": "&#39;",
          '"': "&quot;",
        })[tag],
    );
  }
});
