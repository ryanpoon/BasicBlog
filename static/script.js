
function confirm_delete(id){
	if (confirm("Do you really want to delete this entry?")== true){
		document.getElementById("delete"+id).submit();
	}
}
function revealprofpic(){
	var x = document.getElementsByClassName("changeprofpic");
    x[0].style.display = "block";
}