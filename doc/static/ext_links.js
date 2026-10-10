// Update external links to open them in a new tab
document.addEventListener("DOMContentLoaded", function () {
  const links = document.querySelectorAll("a.external");
  links.forEach(function (link) {
    link.setAttribute("target", "_blank");
    link.setAttribute("rel", "noopener noreferrer");
  });
});
