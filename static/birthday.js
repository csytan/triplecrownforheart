(function($){

var today = new Date();
var years = [];
var months = ['January','February','March','April','May','June','July','August','September','October','November','December'];

for (var y=1900; y <= today.getFullYear(); y++){
    years.push(y);
}

var html = '<select name="month">';
for (var i=0, month; month=months[i]; i++){
    html += '<option value="' + i + '">' + month + '</option>';
}
html += '</select>';
$()


function setDays(){
    var html = '';
    var days = new Date(year, month, 0).getDate();

}


})(jQuery);