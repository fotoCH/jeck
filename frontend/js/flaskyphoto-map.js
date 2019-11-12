//
// sorry for this #2,
// i aint no fancy frontend dev, mam
//



const base_url = window.location.protocol + "//" + window.location.hostname +
                 ":" + window.location.port + "/";

const api_url = base_url + "api/";

const api_table = "photos";

const API_URL = api_url + api_table;




function in_array(haystack, needle){
  var i, j, current;
  for(i = 0; i < haystack.length; ++i){
    if(needle.length === haystack[i].length){
      current = haystack[i];
      for(j = 0; j < needle.length && needle[j] === current[j]; ++j);
      if(j === needle.length)
      return i;
    }
  }
  return -1;
}


function create_window_content(response){
  return "<b>"+response.dc_title + "</b><br>"
  + "<img src="+response.files[0] + " />"
}

function initMap(){
  fetch(API_URL + '/map')
  .then(response => response.json())
  .then(function(response){
    initMap2(response);
  });
}


function initMap2(locations) {
  var map = new google.maps.Map(document.getElementById('map'), {
    zoom: 6,
    center: { lat: 46.928371, lng: 8.233985 }
  });

  var infowindow = new google.maps.InfoWindow({
    content: "tpl"
  });

  var markers = [];
  var reserved_positons = [];
  for (itm of locations){

    if ( in_array(reserved_positons, [ itm.lat, itm.lng ]) > -1 ) {
      itm.lat = itm.lat + (Math.random() -.5) / 1500;
      itm.lng = itm.lng + (Math.random() -.5) / 1500;
    }

    reserved_positons.push([ itm.lat, itm.lng ]);


    var marker = new google.maps.Marker({
      position: itm,
      //label: ""+itm.id
    });

    // click function
    cfunc = function() {
      var that = this;
      fetch(API_URL + '/' + this.item.id)
      .then(response => response.json())
      .then(function(response){
        infowindow.setContent(create_window_content(response));
        infowindow.open(map, that.marker);
      });

    }
    marker.addListener('click',cfunc.bind({item: itm, marker: marker}))
    markers.push(marker);
  }

  var markerCluster = new MarkerClusterer(map, markers,
    {imagePath: 'https://developers.google.com/maps/documentation/javascript/examples/markerclusterer/m'});

}
