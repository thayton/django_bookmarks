$(document).ready(function() {
  $("a.follow-user-link").click(follow_user);
});

function follow_user_post(result) {
  // Wrap result in a fake div so we can get the top level form
  // http://stackoverflow.com/questions/7723320/why-cant-you-select-top-level-elements-in-an-html-string-with-jquery-and-how-d
  // http://stackoverflow.com/questions/11047670/creating-a-jquery-object-from-a-big-html-string
  var wrapped_result = $("<div/>").html(result)
  var form = $("#follow-user-form", wrapped_result);
  var data = {
    csrfmiddlewaretoken: form.find("input[name=csrfmiddlewaretoken]").val()
  };

  $.post(form.attr('action'), data, function () { window.location.href = window.location.href; });
  return false;
}

function follow_user() {
  var url = $(this).attr("href");
  $.get(url, follow_user_post);
  return false;
}