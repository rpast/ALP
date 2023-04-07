const proceedForm = document.getElementById("proceed-form");
console.log(proceedForm)


proceedForm.addEventListener("submit", function (event) {
    console.log("submit1")
    event.preventDefault();
    console.log("submit2")
    // event.preventDefault();
    // Show the processing GIF
    document.getElementById("processing").style.display = "flex";
    setTimeout(function () {
        proceedForm.submit();
    }, 5);
});



    