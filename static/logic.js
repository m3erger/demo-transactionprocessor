// A $( document ).ready() block.
$( document ).ready(function() {
    var users = null;
    var user_id = $('#user_id').val();
    console.log(user_id);
    if (user_id === undefined) {
        //$.ajaxSend()
    }
    $("#users").prepend($("<text/>", {text: "selected user: " + user_id}) );
    $("#add_user").on( "submit", function( event ) {
        // Prevent the form's default submission.
        event.preventDefault();
        // Prevent event from bubbling up DOM tree, prohibiting delegation
        event.stopPropagation();

        // Make an AJAX request to submit the form data
        var users_data = $.post()
    });


    // Using the core $.ajax() method
    $.ajax({

        // The URL for the request
        url: "user",

        // The data to send (will be converted to a query string)
        data: {
            id: user_id
        },

        // Whether this is a POST or GET request
        type: "GET",

        // The type of data we expect back
        dataType : "json"
    })
      // Code to run if the request succeeds (is done);
      // The response is passed to the function
      .done(function( json ) {
          users = json;
          $("#users").append($("<textarea/>", {text: JSON.stringify(json)}));
      })
      // Code to run if the request fails; the raw request and
      // status codes are passed to the function
      .fail(function( xhr, status, errorThrown ) {
        alert( "Sorry, there was a problem!" );
        console.log( "Error: " + errorThrown );
        console.log( "Status: " + status );
        console.dir( xhr );
      })
      // Code to run regardless of success or failure;
      .always(function( xhr, status ) {
        //alert( "The request is complete!" );
      });
});