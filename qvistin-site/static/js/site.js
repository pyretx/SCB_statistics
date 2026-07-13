/* Qvistin homepage — interactivity (vanilla, no framework).
   Reproduces the original React behaviour: branch-diagram hover, topic chips,
   and a contact form that composes a mailto: (no backend needed). */
(function () {
  "use strict";

  // ── Branch diagram: sync hover between the SVG group and its HTML label ──────
  var labels = {};
  document.querySelectorAll(".branch-label").forEach(function (el) {
    labels[el.dataset.i] = el;
  });
  document.querySelectorAll(".branch").forEach(function (g) {
    var i = g.dataset.i, lbl = labels[i];
    g.addEventListener("mouseenter", function () {
      g.classList.add("is-hover"); if (lbl) lbl.classList.add("is-hover");
    });
    g.addEventListener("mouseleave", function () {
      g.classList.remove("is-hover"); if (lbl) lbl.classList.remove("is-hover");
    });
    if (g.dataset.href) {
      g.addEventListener("click", function () { window.location.href = g.dataset.href; });
    }
  });

  // ── Contact form ────────────────────────────────────────────────────────────
  var form = document.getElementById("contact-form");
  if (!form) return;
  var name = document.getElementById("f-name"),
      email = document.getElementById("f-email"),
      msg = document.getElementById("f-msg"),
      send = document.getElementById("f-send"),
      sent = document.getElementById("form-sent"),
      fields = form.querySelector(".form-fields"),
      again = document.getElementById("f-again"),
      topicWrap = document.getElementById("topics");
  var topic = topicWrap ? topicWrap.querySelector(".topic.is-active") : null;
  topic = topic ? topic.dataset.topic : "General";

  // topic chips
  if (topicWrap) {
    topicWrap.querySelectorAll(".topic").forEach(function (b) {
      b.addEventListener("click", function () {
        topicWrap.querySelectorAll(".topic").forEach(function (o) { o.classList.remove("is-active"); });
        b.classList.add("is-active");
        topic = b.dataset.topic;
      });
    });
  }

  function canSend() {
    return name.value.trim() && email.value.indexOf("@") > -1 && msg.value.trim();
  }
  function sync() { send.disabled = !canSend(); }
  [name, email, msg].forEach(function (el) { el.addEventListener("input", sync); });
  sync();

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    if (!canSend()) return;
    var to = send.dataset.email || "hello@qvistin.com";
    var subject = "[" + topic + "] Message from " + name.value.trim();
    var body = "Name: " + name.value.trim() + "\nEmail: " + email.value.trim() +
               "\nTopic: " + topic + "\n\n" + msg.value.trim();
    window.location.href = "mailto:" + to + "?subject=" + encodeURIComponent(subject) +
                           "&body=" + encodeURIComponent(body);
    fields.hidden = true;
    sent.hidden = false;
  });

  if (again) {
    again.addEventListener("click", function () {
      name.value = email.value = msg.value = "";
      sent.hidden = true; fields.hidden = false; sync();
    });
  }
})();
