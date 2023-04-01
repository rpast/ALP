document.addEventListener("DOMContentLoaded", function () {

    const sessionNameInput = document.getElementById("new_session_name");
    var existingSession = document.getElementById("existing_session");
    var newSessionName = document.getElementById("new_session_name");
    var fileInput = document.querySelector('input[type="file"]');

    console.log("sessionNames:", sessionNames);

    existingSession.addEventListener("change", function () {
        console.log("existingSession change");
        if (this.value !== "") {
            newSessionName.disabled = true;
            fileInput.disabled = true;
        } else {
            newSessionName.disabled = false;
            fileInput.disabled = false;
        }
    });

    if (sessionNameInput) {
        sessionNameInput.addEventListener("change", function () {
            console.log("sessionNameInput change");
            const enteredSessionName = this.value;
            if (sessionNames.includes(enteredSessionName)) {
            alert("The session name is already taken. Please choose a different one.");
            this.value = "";
            }
        });
    }
});
