"use strict";
const $ = id => document.getElementById(id);
let token, submission, lastResult;
$("key").value = crypto.randomUUID();
const ready = fetch("/api/session").then(r => r.json()).then(r => token = r.token);
async function api(path, method = "GET", body, extra = {}, raw = false) {
  await ready;
  const r = await fetch(path, {method, headers: {"Authorization": "Bearer " + token, "Content-Type": "application/json", ...extra}, body: body === undefined ? undefined : raw ? body : JSON.stringify(body)});
  const data = await r.json();
  if (!r.ok) throw Error(data.error || "Request failed");
  return data;
}
function show(value) { lastResult = value; $("result").textContent = JSON.stringify(value, null, 2); }
async function action(work) {
  document.querySelectorAll("button").forEach(b => b.disabled = true);
  try { await work(); } catch(e) { $("status").textContent = e.message; }
  finally { document.querySelectorAll("button").forEach(b => b.disabled = false); }
}
function download(name, text, type) {
  const url = URL.createObjectURL(new Blob([text], {type}));
  const a = document.createElement("a"); a.href = url; a.download = name; a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
$("submit").onclick = () => action(async () => {
  $("status").textContent = "Running local OCR and classifier…";
  const file = $("image").files[0];
  let body;
  if (file && $("ocr").value.trim()) throw Error("Choose an image or pasted OCR, then clear the other input.");
  if (file) {
    if (file.size > 20 * 1024 * 1024) throw Error("Choose an image under 20 MB.");
    const data = await new Promise((resolve, reject) => { const r = new FileReader(); r.onload = () => resolve(r.result.split(",")[1]); r.onerror = reject; r.readAsDataURL(file); });
    body = {filename:file.name, image_base64:data};
  } else body = {text:$("ocr").value};
  const response = await api("/api/submissions", "POST", body, {"Idempotency-Key":$("key").value});
  submission = response.result; $("prompt").value = submission.prompt || ""; show(response);
  $("status").textContent = submission.state + (response.replayed ? " · Existing submission" : "");
});
$("copy").onclick = () => action(async () => { await navigator.clipboard.writeText($("prompt").value); $("status").textContent = "Prompt copied."; });
$("download").onclick = () => download("extraction-prompt.txt", $("prompt").value, "text/plain");
$("verify").onclick = () => action(async () => {
  if (!submission) throw Error("Read a document first.");
  submission = await api("/api/submissions/" + submission.submission_id + "/extraction", "POST", $("extraction").value, {}, true);
  show(submission); $("status").textContent = submission.verification.review_required ? "Completed · Review required" : "Completed · Checks passed; field correctness unproven";
});
$("consumer").onclick = () => action(async () => {
  if (!submission) throw Error("Read a document first.");
  show(await api("/api/consumer/" + submission.submission_id)); $("status").textContent = "Demonstration consumer response";
});
$("export").onclick = () => { if (lastResult) download("pipeline-result.json", JSON.stringify(lastResult,null,2), "application/json"); };

