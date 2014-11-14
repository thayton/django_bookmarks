$(document).ready(function () {
  $("#id_tags").autocomplete({source: '/ajax/tag/autocomplete',  minLength:2});
});
