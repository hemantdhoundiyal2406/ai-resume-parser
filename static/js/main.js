const form = document.querySelector("#resumeForm");
const fileInput = document.querySelector("#resume");
const submitBtn = document.querySelector("#submitBtn");
const jdTextarea = document.querySelector("#job_description");
const jdCount = document.querySelector("#jdCount");

if (jdTextarea && jdCount) {
    jdTextarea.addEventListener("input", () => {
        jdCount.textContent = `${jdTextarea.value.length} characters`;
    });
}

if (form && fileInput && submitBtn) {
    form.addEventListener("submit", (event) => {
        const file = fileInput.files[0];
        if (!file) {
            return;
        }

        const allowedExtensions = [".pdf", ".docx"];
        const fileName = file.name.toLowerCase();
        const isAllowed = allowedExtensions.some((extension) => fileName.endsWith(extension));

        if (!isAllowed) {
            event.preventDefault();
            alert("Please upload a PDF or DOCX resume.");
            return;
        }

        submitBtn.disabled = true;
        submitBtn.querySelector(".btn-label").classList.add("d-none");
        submitBtn.querySelector(".btn-loading").classList.remove("d-none");
    });
}
