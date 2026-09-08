const askButton = document.getElementById("askButton");

askButton.addEventListener("click", async function () {

    const question = document.getElementById("question").value;

    const response = await fetch(
        `http://127.0.0.1:8000/ask?question=${encodeURIComponent(question)}`
    );

    const data = await response.json();

    document.getElementById("answer").textContent = data.answer;
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
        "http://127.0.0.1:8000/upload",
        {
            method: "POST",
            body: formData
        }
    );

    const data = await response.json();

    alert(data.message + ": " + data.filename);
});