function scrollToBottom(element) {
    const lastElement = element.lastElementChild;
    if (lastElement) {
        lastElement.scrollIntoView({ behavior: 'smooth', block: 'end', inline: 'nearest' });
    }
}


// Render chat history
function renderChatHistory(chatHistory) {
    const responseDiv = document.getElementById("response");

    chatHistory.forEach((interaction) => {
        const role = interaction.interaction_type === "user" ? "User" : "Agent";
        const messageElement = document.createElement("p");
        messageElement.innerHTML = `<strong>${role}:</strong> ${interaction.text}`;
        responseDiv.appendChild(messageElement);
    });

    // If chat history is empty, display the agent's message
    if (chatHistory.length === 0) {
        const messageElement = document.createElement("p");
        messageElement.innerHTML = "<strong>Agent:</strong> Hi! Let's talk about your sources.";
        responseDiv.appendChild(messageElement);
    }

    // Scroll to the bottom
    scrollToBottom(responseDiv);
}
renderChatHistory(chatHistory);


document.addEventListener("DOMContentLoaded", function () {
    const askForm = document.getElementById("ask-form");
    const responseDiv = document.getElementById("response");

    askForm.addEventListener("submit", function (event) {

        event.preventDefault();

        const question = askForm.querySelector("textarea[name='question']").value;

        // Show the processing GIF
        document.getElementById("processing").style.display = "block";

        // Append the user's input to the response div
        const userMessageElement = document.createElement("p");
        userMessageElement.innerHTML = "<strong>User:</strong> " + question;
        responseDiv.appendChild(userMessageElement);

        // Scroll to the bottom
        scrollToBottom(responseDiv);

        fetch("/ask", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                question: question,
            }),
        })
        .then((response) => response.json())
        .then((result) => {
            // Hide the processing GIF
            document.getElementById("processing").style.display = "none";

            // Append the agent's response to the response div
            const agentMessageElement = document.createElement("p");
            agentMessageElement.innerHTML = "<strong>Agent:</strong> " + result.response.choices[0].message.content;
            responseDiv.appendChild(agentMessageElement);

            // Scroll to the bottom
            scrollToBottom(responseDiv);
        })
        .catch((error) => {
            // Hide the processing GIF in case of an error
            document.getElementById("processing").style.display = "none";

            // Display an error message
            responseDiv.textContent = "An error occurred: " + error;
        });
    });
});


