$(document).ready(function () {
    $("#search-form").submit(function () {
        location.href = "/masterpiece/search/"+$("#search-key").val()+'/';
        return false;
    });
})
