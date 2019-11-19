//
// sorry for this,
// i aint no fancy frontend dev, mam
//



const base_url = window.location.protocol + "//" + window.location.hostname +
                 ":" + window.location.port + "/"

const api_url = base_url + "api/"
// const api_url = base_url

const api_table = "docs"




reset_filters = function(){
  $("#search-term").val("");
  search_docs();
};



update_docs = function(data, clear=false) {
  if (clear){
    $("#docarea").html("");
  }
  $("#search-result-count").html(data.count);
  var tpl = $("#elem-tpl-area > div.docs-detail-box")
  for (item of data.results){
    var obj = tpl.clone();
    obj.find("span").each(function(){
      var datafield = $(this).attr("data-field");
      $(this).html(item[datafield]);
    });
    obj.find("a").attr("href", item.files[0]);
    $("#docarea").append(obj);
  }
};



load_docs = function(){
  $.ajax({
    dataType: "json",
    url: api_url + api_table
  }).done(function(data){
    update_docs(data);
  });
};


search_docs = function(){
  query = $("#search-term").val();
  $.ajax({
    dataType: "json",
    url: api_url + api_table + "/search?query="+query
  }).done(function(data){
    console.log(data);
    update_docs(data, true);
  });
};


// main init function
$(document).ready(function(){

  // search function handler
  $("#searchform").submit( function(evt){
    search_docs();
    evt.preventDefault();
  });



  // button click reset filters
  $("#reset-filter").click(function(){
    reset_filters();
  });

  // scroll to top button
  var scroll_top_button = $("#scroll-top-btn");
  scroll_top_button.click(function(){
    $(window).scrollTop(0);
  });


  load_docs();


});
