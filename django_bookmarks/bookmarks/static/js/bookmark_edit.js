$(document).ready(function () {
  $("ul.bookmarks .edit").click(bookmark_edit);
});

function bookmark_edit() {
  var item = $(this).parent(); // Parent <li> element of edit link
  var url = item.find(".title").attr("href");
  item.load("/save/?ajax&url=" + encodeURIComponent(url), null,
            function () {
              $("#save-form").submit(bookmark_save);
            });
  return false; 
}

function bookmark_save() {
  var item = $(this).parent(); // Parent <li> element of form
  var data = {
    csrfmiddlewaretoken: item.find("input[name=csrfmiddlewaretoken]").val(),
    url: item.find("#id_url").val(),
    title: item.find("#id_title").val(),
    tags: item.find("#id_tags").val(),
    share: item.find("#id_share").prop('checked')
  };
  $.post("/save/?ajax", data, function (result) {
    if (result != "failure") {
      item.before($("li", result).get(0));
      item.remove();
      $("ul.bookmarks .edit").click(bookmark_edit);
    } else {
      alert("Failed to validate bookmark before saving.");
    }
  });
  return false;
}
