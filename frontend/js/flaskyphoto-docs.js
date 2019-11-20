//
// sorry for this,
// i aint no fancy frontend dev, mam
//



const base_url = window.location.protocol + "//" + window.location.hostname +
                 ":" + window.location.port + "/"

const api_url = base_url + "api/"
// const api_url = base_url

const api_table = "docs"


filter_items = [];
filter_spec = [];
slimselect_arr = [];


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
      var is_date = $(this).attr("data-moment");
      if (is_date == "true"){
        var formated_date = moment(item[datafield]).format('LL');
        $(this).html(formated_date);
      } else {
        $(this).html(item[datafield]);
      }
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



// do query with seted filters
filter_docs = function(filter_spec){
  $.ajax({
    dataType: "json",
    url: api_url + api_table + "/filter",
    type: "POST",
    contentType: 'application/json',
    data: JSON.stringify({ "filter": filter_spec })
  }).done(function(data){
    update_docs(data, true);
  });
}



// builds filter ui according to API specs
build_filter_list = function(){
  $.ajax({
    dataType: "json",
    url: api_url + api_table + "/filter-spec"
  }).done(function(data){
    filter_items = [];
    slimselect_arr = [];
    var tpl = $("#elem-tpl-area > div.filter-item-tpl");
    for (item of data){
      var filterentry = $(tpl).clone();
      filterentry.children(".filter-item-desc").html(item.desc);
      filterentry.children(".filter-item-select").attr("id", "filter-"+item.name);
      var sel_entry = filterentry.children(".filter-item-select").children(".filter-item-entry")
      sel_entry.detach();
      for (entry of item.data){
        var itm = sel_entry.clone().attr("value",entry).html(entry);
        filterentry.children(".filter-item-select").append(itm)
      }
      $("#filterarea").append(filterentry);
      var sel_obj = new SlimSelect({
        select: '#filter-'+item.name
      });
      slimselect_arr.push(sel_obj);
      $('#filter-'+item.name).change(function(itm){
        update_filters();
      });
      filter_items.push({
        'selector': '#filter-'+item.name,
        'obj': item
      });
    }
  });
};


// build filter spec according sqlalchemy_filters
update_filters = function(){
  current_page = 0;
  filters = [];
  for (item of filter_items){
    var res = $(item.selector).val();
    if (res){
      filters.push({ 'field': item.obj.name, 'op': 'in', 'value': res });
    }
  }
  is_filter=true;
  is_search=false;
  filter_spec = filters;

  filter_docs(filter_spec);
};


// reset filters and empty serarch form
reset_filters = function(){
  for (itm of slimselect_arr) {
    if (itm.selected()){
      itm.set([]);
    }
  }
  $("#search-term").val("");
};


// main init function
$(document).ready(function(){


  // set moment.js locale to german
  moment.locale("de");

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


  // build filter list
  build_filter_list();

  load_docs();


});
