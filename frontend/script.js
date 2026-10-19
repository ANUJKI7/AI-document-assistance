const askButton = document.getElementById("askButton");

askButton.addEventListener("click", async function () {

    const question = document.getElementById("question").value;

    const response = await fetch(
        `${API_BASE}/ask?question=${encodeURIComponent(question)}`
    );

    const data = await response.json();

    document.getElementById("answer").textContent = data.answer || data.error;

    // Saved in this browser so the dashboard can show recent questions
    addQuestionToHistory(question, Boolean(data.answer));
});
const uploadButton = document.getElementById("uploadButton");

uploadButton.addEventListener("click", async function () {

    const fileInput = document.getElementById("document");
    const file = fileInput.files[0];

    if (!file) {
        alert("Please choose a file first.");
        return;
    }

    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch(
        `${API_BASE}/upload`,
        {
            method: "POST",
            body: formData
        }
    );

    const data = await response.json();

    alert(data.message + ": " + data.filename);
});