$(document).ready(function() {
  $("a.follow-user-link").click(follow_user);
});

function follow_user_post(result) {
  // Wrap result in a fake div so we can get the top level form
  // http://stackoverflow.com/questions/7723320/why-cant-you-select-top-level-elements-in-an-html-string-with-jquery-and-how-d
  // http://stackoverflow.com/questions/11047670/creating-a-jquery-object-from-a-big-html-string
  var wrapped_result = $("<div/>").html(result);
  var form = $("#follow-user-form", wrapped_result);
  var data = {
    csrfmiddlewaretoken: form.find("input[name=csrfmiddlewaretoken]").val()
  };

  $.post(form.attr('action'), data, function () { 
    // 'Refresh' the current page /user/<username>/ manually so that we 
    // can get our status messages displayed. Without ajax, this is taken 
    // care of by Django's HttpRedirect being sent to the browser to take
    // us from /follow/<username>/ to /user/<username>/
    window.location.href = window.location.href; 
  });
  return false;
}

//
// When the user clicks the follow-user-link we retrieve the follow-user-form
// Then we POST the form in follow_user_post
// Then we refresh the page so we can status messages
// 
// This two step process (GET followed by POST) is used so that we can display
// follow-user as a link, and because just sending a POST request to /follow/<username>/
// won't work since we'll be missing the CSRF token required by Django.
//
function follow_user() {
  var url = $(this).attr("href");
  $.get(url, follow_user_post);
  return false;
}
