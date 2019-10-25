const api_url = "http://localhost:5000/"
const table = "photo"


update_photos = function(data){
  elem = $("#photoarea")
  elem.html("")
  content = ""
  for (entry of data) {
    content = content + '<div class="photo-entry"><img src="' +
      entry.files[0] +
      '"></img>Titel: <b>' +
      entry.dc_title+ '</b></div>'
  }
  elem.html(content)
}



$(document).ready(function(){
  $.ajax({
    dataType: "json",
    url: "http://localhost:5000/photos"
  }).done(function(data){
    update_photos(data);
  })

  $("#searchform").submit( function(evt){
    evt.preventDefault();

    query = $("#search-term").val();
    $.ajax({
      dataType: "json",
      url: "http://localhost:5000/photos/search?query="+query
    }).done(function(data){
      update_photos(data);
    })

  });


});
