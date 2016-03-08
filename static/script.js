
function confirm_delete(id){
	if (confirm("Do you really want to delete this entry?")== true){
		document.getElementById("delete"+id).submit();
	}
}