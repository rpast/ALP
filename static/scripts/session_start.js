// document.addEventListener("DOMContentLoaded", function() {
//     const sessionNameInput = document.getElementById("session_name");

//     if (sessionNameInput) {
//         sessionNameInput.addEventListener("change", function() {
//             const enteredSessionName = this.value;
//             if (sessionNames.includes(enteredSessionName)) {
//                 alert("The session name is already taken. Please choose a different one.");
//                 this.value = "";
//             }
//         });
//     }
// });

var existingSession = document.getElementById("existing_session");
var newSessionName = document.getElementById("new_session_name");
var fileInput = document.querySelector('input[type="file"]');
var sessionNames = JSON.parse(newSessionName.dataset.sessionNames);

existingSession.addEventListener("change", function() {
    if (this.value !== "") {
        newSessionName.disabled = true;
        fileInput.disabled = true;
    } else {
        newSessionName.disabled = false;
        fileInput.disabled = false;
    }
});


document.addEventListener("DOMContentLoaded", function() {
    const sessionNameInput = document.getElementById("session_name");

    if (sessionNameInput) {
        sessionNameInput.addEventListener("change", function() {
            const enteredSessionName = this.value;
            if (sessionNames.includes(enteredSessionName)) {
                alert("The session name is already taken. Please choose a different one.");
                this.value = "";
            }
        });
    }
});

