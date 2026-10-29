"use strict";

document.addEventListener("DOMContentLoaded", () => {
  const description = document.querySelector("#description");
  const count = document.querySelector("#description-count");

  if (description && count) {
    const updateCount = () => {
      count.textContent = String(description.value.length);
    };
    description.addEventListener("input", updateCount);
    updateCount();
  }

  document.querySelectorAll("[data-confirm-delete]").forEach((form) => {
    form.addEventListener("submit", (event) => {
      if (!window.confirm("Remove this movie from your shelf?")) {
        event.preventDefault();
      }
    });
  });
});
