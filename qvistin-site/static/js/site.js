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

  var errEl = document.getElementById("form-err");
  var SB_URL = (form.dataset.supabaseUrl || "").replace(/\/+$/, "");
  var SB_KEY = form.dataset.supabaseKey || "";

  function showSent() { fields.hidden = true; sent.hidden = false; }
  function showErr() { if (errEl) errEl.hidden = false; send.disabled = false; }

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    if (!canSend()) return;
    if (errEl) errEl.hidden = true;

    var payload = {
      name: name.value.trim().slice(0, 200),
      email: email.value.trim().slice(0, 320),
      topic: (topic || "General").slice(0, 60),
      message: msg.value.trim().slice(0, 5000)
    };

    // No Supabase backend configured → fall back to a mailto: link.
    if (!SB_URL || !SB_KEY) {
      var to = send.dataset.email || "hello@qvist.in";
      var subject = "[" + payload.topic + "] Message from " + payload.name;
      var body = "Name: " + payload.name + "\nEmail: " + payload.email +
                 "\nTopic: " + payload.topic + "\n\n" + payload.message;
      window.location.href = "mailto:" + to + "?subject=" + encodeURIComponent(subject) +
                             "&body=" + encodeURIComponent(body);
      showSent();
      return;
    }

    send.disabled = true;
    fetch(SB_URL + "/rest/v1/qvistin_messages", {
      method: "POST",
      headers: {
        "apikey": SB_KEY,
        "Authorization": "Bearer " + SB_KEY,
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
      },
      body: JSON.stringify(payload)
    }).then(function (r) { if (r.ok) { showSent(); } else { showErr(); } })
      .catch(function () { showErr(); });
  });

  if (again) {
    again.addEventListener("click", function () {
      name.value = email.value = msg.value = "";
      if (errEl) errEl.hidden = true;
      sent.hidden = true; fields.hidden = false; sync();
    });
  }
})();
