
function confirm_delete(id){
	if (confirm("Do you really want to delete this entry?")== true){
		document.getElementById("delete"+id).submit();
	}
}
function revealprofpic(){
	var x = document.getElementsByClassName("changeprofpic");
    x[0].style.display = "block";
}
function changeprofdesc(){
	var y = document.getElementById('profiledesc');
	var x = document.getElementsByClassName("changeprofdesc");
    x[0].style.display = "block";
    console.log(y.clientHeight);
    var xrows = (y.clientHeight-5)/20;
    document.getElementsByClassName("changeprofdesc")[0].rows = xrows.toString();
// 
//     x[0].style.width = y.clientWidth+'px';
//     x[0].style.height = y.clientHeight+'px';
//     
        console.log(x[0].rows);
    y.style.display = "none";
     
}