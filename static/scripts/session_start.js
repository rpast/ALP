document.addEventListener("DOMContentLoaded", function () {

    let sessionNameInput = document.getElementById("new_session_name");
    let existingSession = document.getElementById("existing_session");
    let newSessionName = document.getElementById("new_session_name");
    let fileInput = document.querySelector('input[type="file"]');
    let conditionalText = document.getElementById("conditional-text");


    // Process the session name to make it compatible with SQLite
    function processSessionName(name) {
        name = name.trim();
        // Exclude all signs that conflict with SQLite
        name = name.replace(/[^\w]/g, '_');
        name = name.toLowerCase();
    
        return name;
    }

    //Update text according to the condition set
    function updateConditionalText() {
        if (existingSession.value) {
            conditionalText.innerText = "You are about to continue a conversation with ALP. Hit 'Start Session' to continue.";
        } else if (newSessionName.value) {
            conditionalText.innerText = "You are about to set a new session with ALP. Please select a .pdf file for upload and click 'Start Session'.";
        } else {
            conditionalText.innerText = "(ﾉ☉ヮ⚆)ﾉ ⌒*:･ﾟ✧";
        }
    }

    // disable/enable the session name and file upload input fields
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
            const enteredSessionName = processSessionName(this.value);;
            if (sessionNames.includes(enteredSessionName)) {
            alert("The session name is already taken. Please choose a different one. Note that program turns all special characters into '_'");
            this.value = "";
            }
        });
    }


    existingSession.addEventListener("change", updateConditionalText);
    newSessionName.addEventListener("input", updateConditionalText);
    

});


