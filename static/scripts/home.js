document.addEventListener("DOMContentLoaded", function () {

    let sessionNameInput = document.getElementById("new_session_name");
    let existingSession = document.getElementById("existing_session");
    let newSessionName = document.getElementById("new_session_name");
    let fileInput = document.querySelector('input[type="file"]');
    let conditionalText = document.getElementById("conditional-text");


    // grab first element of every tupple form existing sessions
    let sNames = Array.from(existingSession.options).map(option => {
        const match = option.value.match(/\('([^']+)',/);
        return match ? match[1] : null;
    }).filter(name => name !== null);

    
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
            conditionalText.innerText = "You will continue a conversation with ALP. Hit 'Start Session' to continue.";
        } else if (newSessionName.value) {
            conditionalText.innerText = "You will set a new session. Please select a .pdf file for upload and click 'Session Start'.";
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
            if (sNames.includes(enteredSessionName)) {
                alert("The session name is already taken. Please choose a different one. Note that program turns all special characters into '_'");
                this.value = "";
            }
        });
    }


    existingSession.addEventListener("change", updateConditionalText);
    newSessionName.addEventListener("input", updateConditionalText);
    

});