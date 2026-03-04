document.addEventListener("DOMContentLoaded", () => {
  const startBtn = document.getElementById("startPipelineBtn");
  const clearBtn = document.getElementById("clearLogBtn");
  const terminal = document.getElementById("terminalOutput");
  let eventSource = null;

  function appendLine(text, type = "normal") {
    const line = document.createElement("div");
    line.className = `log-line ${type}`;

    // Color coding logic based on standard Scrapy logs
    if (text.includes("Successfully inserted")) {
      line.classList.add("success");
      line.innerHTML = `<i class="ri-check-line"></i> ${escapeHTML(text)}`;
    } else if (
      text.includes("ERROR") ||
      text.includes("Duplicated") ||
      text.includes("Dropped") ||
      text.includes("WARNING")
    ) {
      line.classList.add("warning");
      line.innerHTML = `<i class="ri-error-warning-line"></i> ${escapeHTML(text)}`;
    } else if (text.includes("[SYSTEM]")) {
      line.classList.add("system");
      line.innerHTML = `<i class="ri-cpu-line"></i> ${escapeHTML(text)}`;
    } else if (text.includes("DEBUG")) {
      line.classList.add("debug");
      line.textContent = text;
    } else {
      line.textContent = text;
    }

    terminal.appendChild(line);
    terminal.scrollTop = terminal.scrollHeight; // Auto-scroll to bottom
  }

  startBtn.addEventListener("click", () => {
    // Prevent multiple simultaneous runs in this demo
    if (eventSource) {
      appendLine("[SYSTEM] Pipeline is already running.", "system");
      return;
    }

    startBtn.disabled = true;
    startBtn.innerHTML = `<i class="ri-loader-4-line ri-spin"></i> Crawling...`;

    appendLine("\n--- NEW CRAWL SESSION INITIATED ---", "system");

    eventSource = new EventSource("/api/scrape/stream");

    eventSource.onmessage = function (event) {
      try {
        const data = JSON.parse(event.data);
        appendLine(data.msg, data.type);
      } catch (e) {
        appendLine(event.data, "normal");
      }
    };

    eventSource.onerror = function (err) {
      console.error("EventSource failed:", err);
      // It could be due to process finishing
    };

    // Custom event triggered by Flask when Python process ends
    eventSource.addEventListener("end", function (event) {
      appendLine("[SYSTEM] Pipeline stream closed by server.", "system");
      eventSource.close();
      eventSource = null;

      startBtn.disabled = false;
      startBtn.innerHTML = `<i class="ri-play-fill"></i> Trigger Crawl Event`;
    });
  });

  clearBtn.addEventListener("click", () => {
    terminal.innerHTML =
      '<div class="log-line info"><span class="prompt">$</span> Pipeline Agent standing by. Awaiting trigger sequence...</div>';
  });

  function escapeHTML(str) {
    if (!str) return "";
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
