const form = document.getElementById("routine-form");
const list = document.getElementById("routines");
const empty = document.getElementById("empty");
const msg = document.getElementById("msg");
let filter = "";

function el(tag, cls, text) {
  const n = document.createElement(tag);
  if (cls) n.className = cls;
  if (text !== undefined) n.textContent = text; // textContent => no XSS
  return n;
}

async function load() {
  const url = "/api/routines" + (filter ? `?period=${filter}` : "");
  const res = await fetch(url);
  const data = await res.json();
  list.replaceChildren();
  empty.hidden = data.length > 0;
  for (const r of data) {
    const li = el("li", `routine ${r.period}`);
    const head = el("div", "routine-head");
    head.append(el("strong", "", r.title), el("span", "badge", r.period === "morning" ? "☀️ Morning" : "🌙 Night"));
    li.append(head);
    if (r.products) li.append(el("p", "products", r.products));
    if (r.notes) li.append(el("p", "notes", r.notes));
    list.append(li);
  }
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const payload = Object.fromEntries(new FormData(form));
  const res = await fetch("/api/routines", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (res.status === 201) {
    msg.textContent = "Saved ✓";
    msg.className = "ok";
    form.reset();
    load();
  } else {
    const err = await res.json();
    msg.textContent = "Could not save: " + Object.values(err.details || { e: err.error }).join(", ");
    msg.className = "bad";
  }
});

document.querySelectorAll(".tab").forEach((b) =>
  b.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach((t) => t.classList.remove("active"));
    b.classList.add("active");
    filter = b.dataset.filter;
    load();
  })
);

load();
