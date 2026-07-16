async function uploadResume() {

    let fileInput = document.getElementById("resume");
    let output = document.getElementById("output");

    // ✅ Check if file selected
    if (!fileInput.files.length) {
        output.innerHTML = "<p style='color:red;'>Please upload a resume first.</p>";
        return;
    }

    let file = fileInput.files[0];

    let formData = new FormData();
    formData.append("file", file);

    // ✅ Show loading
    output.innerHTML = "<p>Analyzing resume... ⏳</p>";

    try {
        let res = await fetch("http://127.0.0.1:8000/analyze", {
            method: "POST",
            body: formData
        });

        // ✅ Handle API error
        if (!res.ok) {
            throw new Error("Server error. Try again.");
        }

        let data = await res.json();

        // ✅ Build UI output
        let html = `
            <h2>📊 Resume Score: ${data.score}/100</h2>
        `;

        // Suggestions
        if (data.suggestions && data.suggestions.length > 0) {
            html += "<h3>💡 Suggestions:</h3><ul>";

            data.suggestions.forEach(s => {
                html += `<li>${s}</li>`;
            });

            html += "</ul>";
        } else {
            html += "<p style='color:lightgreen;'>✅ Excellent resume! No major issues found.</p>";
        }

        output.innerHTML = html;

    } catch (error) {
        output.innerHTML = `<p style="color:red;">❌ ${error.message}</p>`;
    }
}