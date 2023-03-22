$(document).ready(function () {
    $("#ask-form").submit(function (event) {
        event.preventDefault();
        var question = $("textarea[name='question']").val();
        var session_name = $("input[name='session_name']").val();

        // Show the processing GIF
        $("#processing").show();

        // Append the user's input to the response div
        $("#response").append('<p><strong>User:</strong> ' + question + '</p>');

        $.ajax({
            type: "POST",
            url: "/ask",
            contentType: "application/json",
            data: JSON.stringify({
                question: question,
                session_name: session_name,
            }),
            success: function (result) {
                // Hide the processing GIF
                $("#processing").hide();

                 // Append the agent's response to the response div
                $("#response").append('<p><strong>Agent:</strong> ' + result.response.choices[0].message.content + '</p>');

            },
            error: function (xhr, status, error) {
                // Hide the processing GIF in case of an error
                $("#processing").hide();

                // Display an error message
                $("#response").text("An error occurred: " + error);
            },
        });
    });
});