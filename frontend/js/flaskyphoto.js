//
// sorry for this,
// i aint no fancy frontend dev, mam
//



const base_url = window.location.protocol + "//" + window.location.hostname +
                 ":" + window.location.port + "/"



// const base_url = "http://localhost:5000/"



const api_url = base_url + "api/"
// const api_url = base_url

const api_table = "photos"
const thumb_url = base_url + "image-proxy/crop?width=170&height=170&gravity=smart&file="


current_page = 0;
is_search = false;
is_filter = false;
filter_items = [];
filter_spec = [];
gallery_is_open = false;
gallery_curr_id = 0;


get_thumb_url = function(data_url){
  if (data_url){
    var path = data_url.replace(/^[a-z]{4,5}\:\/{2}[a-z]{1,}\:[0-9]{1,4}.(.*)/, '$1');
    return thumb_url + path;
  }
  return null;
};


// rebuild list of photos from a given data array
update_photos = function(data, append=false){
  var elem = $("#photoarea");
  var tpl = $("#elem-tpl-area > div.photo-entry");
  if (!append){
    elem.html("")
  }
  $("#search-result-count").html(data.count);
  for (entry of data.results) {
    var imgentry = tpl.clone();
    imgentry.attr("data-id", entry.id);

    var thumburl = get_thumb_url(entry.files[0]);

    imgentry.children(".photo-entry-img").attr("src", thumburl);
    imgentry.children(".photo-entry-txt").html(entry.dc_title);
    if (append){
      elem.append(imgentry);
    }
    else {
      gallery_move_detail();
      elem.html(imgentry);
    }
  }
  // gallery bind events to open details
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
    $("#photo-detail").detach().insertAfter(prev);
    $("html, body").scrollTop( $('#photo-detail').offset().top-200 );

    $.ajax({
      dataType: "json",
      url: api_url + api_table + "/" + gallery_curr_id
    }).done(function(data){
      $("#photo-detail").children("div.img").children("img").attr("src", data.files[0])

      // TODO: fill out all elems
      $("#photo-detail-title").html(data.dc_title);
      $("#photo-detail-photographer").html(data.dc_creator_text);
      $("#photo-detail-year").html(data.zeitraum);
      $("#photo-detail-spatial").html(data.dcterms_spatial);
      $("#photo-detail-right").html(data.dc_right);
      $("#photo-detail-id").html(data.id);

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


// move photo detail out of body
gallery_move_detail = function(){
  $("#photo-detail").detach().appendTo($("#elem-tpl-area"));
};


// this function gets called on infinite scroll
load_next_page = function(){
  current_page++;

  // search entry added
  if (is_search){
    console.log("load next search page")
    if (current_page==1){
      gallery_move_detail();
      $("#photoarea").html("");
    }
    query = $("#search-term").val();
    $.ajax({
      dataType: "json",
      url: api_url + api_table + "/search?query="+query+"&page="+current_page+"&page_size=32"
    }).done(function(data){
      update_photos(data, true);
    });
  }

  // filter updated
  else if (is_filter){
    if (current_page==1){
      gallery_move_detail();
      $("#photoarea").html("");
    }
    $.ajax({
      dataType: "json",
      url: api_url + api_table + "/filter?page="+current_page+"&page_size=32",
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
      url: api_url + api_table + "?page="+current_page+"&page_size=32"
    }).done(function(data){
      update_photos(data, true);
    });
  }

};


// builds filter ui according to API specs
build_filter_list = function(){
  $.ajax({
    dataType: "json",
    url: api_url + api_table + "/filter-spec"
  }).done(function(data){
    filter_items = [];
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





// main init function
$(document).ready(function(){

  // search function handler
  $("#searchform").submit( function(evt){
    current_page=0;
    is_search=true;
    load_next_page();
    evt.preventDefault();
  });

  // load photos
  load_next_page();

  // build filter list
  build_filter_list();

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

  // left/right arrows on image detail
  $(".img-nav-left").click(function(){
    gallery_prev_photo();
  });
  $(".img-nav-right").click(function(){
    gallery_next_photo();
  });


});
