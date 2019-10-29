//
// sorry for this,
// i aint no fancy frontend dev, mam
//


const api_url = "http://localhost:5000/"
const table = "photo"

current_page = 1;
is_search = false;
is_filter = false;
filter_items = [];
filter_spec = [];
gallery_is_open = false;
gallery_curr_id = 0;


update_photos = function(data, append=false){
  elem = $("#photoarea")
  if (!append){
    elem.html("")
  }
  content = ""
  for (entry of data) {
    content = content + '<div class="photo-entry" data-id="'+entry.id+
      '"><img src="' +
      entry.files[0] +
      '"></img>Titel: <b>' +
      entry.dc_title+ '</b></div>'
  }
  if (append){
    elem.append(content);
  }
  else {
    $("#photo-detail").detach().insertAfter($("body"));
    elem.html(content);
  }
  // gallery event
  $("#photoarea > div.photo-entry").unbind("click");
  $("#photoarea > div.photo-entry").click(function(){
    open_gallery_photo($(this));
  });

}





//
// Gallery detail view
//

// this function gets called when clicking on a photo image
// or do next-prev on image
open_gallery_photo = function(elem){
    // calculate position of pdiv
    gallery_is_open = true;
    gallery_curr_id = elem.attr("data-id");
    var offset = elem.offset().top;
    var found_last = false;
    var last_elem = false;
    var prev = elem;
    var next = elem;
    var this_offs = false;
    while (!found_last) {
      prev = next;
      next = prev.next();
      var this_offs = next.offset();
      if (!this_offs){
        found_last=true;
      } else {
        if (this_offs.top > offset){
          found_last=true;
        }
      }
    }
    $("#photo-detail").detach().insertAfter(prev).css({"display":"inline-block"});
    $.ajax({
      dataType: "json",
      url: "http://localhost:5000/photos/"+gallery_curr_id
    }).done(function(data){
      $("#photo-detail").children("div.img").children("img").attr("src", data.files[0])
      $("html, body").scrollTop( $('#photo-detail').offset().top-10 );

    });
};


// this function gets called when key arrow right
gallery_next_photo = function(){
  var sel = "div.photo-entry[data-id="+gallery_curr_id+"]";
  var list = $("#photoarea div.photo-entry");
  var idx = list.index($(sel));
  idx = (idx + 1) % list.length;
  var elem = list.eq(idx);
  if (elem.length>0){
    open_gallery_photo(elem)
  }
}


// // this function gets called when key arrow left
gallery_prev_photo = function(){
  var sel = "div.photo-entry[data-id="+gallery_curr_id+"]";
  var list = $("#photoarea div.photo-entry");
  var idx = list.index($(sel));
  idx = (idx - 1) % list.length;
  var elem = list.eq(idx);
  if (elem.length>0){
    open_gallery_photo(elem)
  }
}



// this function gets called on infinite scroll
load_next_page = function(){
  current_page++;

  // search entry added
  if (is_search){
    console.log("load next search page")
    if (current_page==1){
      $("#photo-detail").detach().insertAfter($("body"));
      $("#photoarea").html("");
    }
    query = $("#search-term").val();
    $.ajax({
      dataType: "json",
      url: "http://localhost:5000/photos/search?query="+query+"&page="+current_page+"&page_size=32"
    }).done(function(data){
      update_photos(data, true);
    });
  }

  // filter updated
  else if (is_filter){
    if (current_page==1){
      $("#photo-detail").detach().insertAfter($("body"));
      $("#photoarea").html("");
    }
    $.ajax({
      dataType: "json",
      url: "http://localhost:5000/photos/filter?page="+current_page+"&page_size=32",
      type: "POST",
      contentType: 'application/json',
      data: JSON.stringify({ "filter": filter_spec })
    }).done(function(data){
      update_photos(data, true);
    });
  }

  // normal scroll
  else {
    $.ajax({
      dataType: "json",
      url: "http://localhost:5000/photos?page="+current_page+"&page_size=32"
    }).done(function(data){
      update_photos(data, true);
    });
  }

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
  load_next_page();
};





$(document).ready(function(){

  // search function handler
  $("#searchform").submit( function(evt){
    current_page=0;
    is_search=true;
    load_next_page();
    evt.preventDefault();
  });

  load_next_page();

  // infinite scroll loader
  $(window).scroll(function() {
     if($(window).scrollTop() + $(window).height() == $(document).height()) {
       //console.log("scrolload");
       load_next_page();
     }
  });


  // event binding for left-right keys if gallery is open
  $(document).keydown(function(e) {
    if (!gallery_is_open){
      return;
    }
    console.log("keyevent", e, gallery_is_open);
    switch(e.which) {
      case 37: // left
        gallery_prev_photo();
        break;
      case 39: // right
        gallery_next_photo();
        break;
      default: return;
    }
    e.preventDefault();
  });


  // build filters list
  $.ajax({
    dataType: "json",
    url: "http://localhost:5000/photos/filter-spec"
  }).done(function(data){
    filter_items = []
    for (item of data){
      sel ="<b>"+item.desc+"</b>";
      sel+= "<select id='filter-"+item.name+"' multiple>";
      for (entry of item.data){
        sel+="<option value='"+entry+"'>"+entry+"</option>";
      }
      sel+="</select>";
      $("#filterarea").append(sel);
      new SlimSelect({
        select: '#filter-'+item.name
      });
      $('#filter-'+item.name).change(function(itm){
        update_filters();
      });
      filter_items.push({
        'selector': '#filter-'+item.name,
        'obj': item
      });
    }
  });

});
