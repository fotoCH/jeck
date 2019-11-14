const base_url = window.location.protocol + "//" + window.location.hostname +
                 ":" + window.location.port + "/"
const api_url = base_url + "api/"


$(document).ready(function(){


  $( "#contact-form" ).submit(function( evt ) {

    $("#contact-form").css({"display": "none"});
    $("div.form-loading").css({"display": "block"});

    var name = $("#form-field-name").val();
    var from = $("#form-field-email").val();
    var message = $("#form-field-msg").val();

    msg = {
      name: name,
      from: from,
      message: message
    };


    $.ajax({
      dataType: "json",
      url: api_url + "mail",
      type: "POST",
      contentType: 'application/json',
      data: JSON.stringify({ "mail": msg })
    }).done(function(data){

      $("div.form-loading").css({"display": "none"});
      $("div.form-sendt").css({"display": "block"});

    });


    evt.preventDefault();
  });


});
