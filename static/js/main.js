/**
 * ResolveDesk - Client-side interactions
 */

document.addEventListener("DOMContentLoaded", function () {
    // Mobile navigation toggle
    const navToggle = document.getElementById("navToggle");
    const navMenu = document.getElementById("navMenu");

    if (navToggle && navMenu) {
        navToggle.addEventListener("click", function () {
            navMenu.classList.toggle("show");
        });
    }

    // Auto-dismiss flash alerts after 5 seconds
    const alerts = document.querySelectorAll(".alert");
    alerts.forEach((alert) => {
        setTimeout(() => {
            alert.style.transition = "opacity 0.4s ease, transform 0.4s ease";
            alert.style.opacity = "0";
            alert.style.transform = "translateY(-5px)";
            setTimeout(() => alert.remove(), 400);
        }, 5000);
    });

    // Client-side quick filter on tables if search input has data-table-filter
    const quickSearchInput = document.querySelector("[data-table-filter]");
    if (quickSearchInput) {
        quickSearchInput.addEventListener("input", function (e) {
            const query = e.target.value.toLowerCase().trim();
            const tableRows = document.querySelectorAll("tbody tr");

            tableRows.forEach((row) => {
                const text = row.textContent.toLowerCase();
                if (text.includes(query)) {
                    row.style.display = "";
                } else {
                    row.style.display = "none";
                }
            });
        });
    }
});
