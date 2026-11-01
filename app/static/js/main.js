document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll('input[type="file"]').forEach(input => {
    input.addEventListener("change", () => {
      const label = input.closest(".file-drop");
      if (label && input.files.length) {
        const name = input.files.length === 1 ? input.files[0].name : `${input.files.length} files selected`;
        const small = label.querySelector("small");
        if (small) small.textContent = name;
      }
    });
  });
});
