const proceedForm = document.getElementById("proceed-form");

proceedForm.addEventListener("submit", function (event) {
    event.preventDefault();
    // Show the processing GIF
    document.getElementById("processing").style.display = "flex";
    setTimeout(function () {
        proceedForm.submit();
    }, 5);
});