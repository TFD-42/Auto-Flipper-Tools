// Auto-Flipper-Tools GUI — logique 3 colonnes (source -> classé -> prêt à flasher)

async function refreshTree(stage) {
  const res = await fetch(`/api/tree/${stage}`);
  const data = await res.json();
  renderTree(document.getElementById(`${stage}-tree`), data);
  return data;
}

function renderTree(container, data) {
  container.innerHTML = "";
  if (!data.exists || data.children.length === 0) {
    container.innerHTML = '<p class="empty">(vide)</p>';
    return;
  }
  container.appendChild(renderNodes(data.children));
}

function renderNodes(nodes) {
  const ul = document.createElement("ul");
  for (const node of nodes) {
    const li = document.createElement("li");
    if (node.type === "dir") {
      li.className = "node-dir";
      li.textContent = "📁 " + node.name;
      li.appendChild(renderNodes(node.children));
    } else {
      li.className = "node-file";
      li.textContent = "📄 " + node.name;
    }
    ul.appendChild(li);
  }
  return ul;
}

function setStatus(id, message, isError) {
  const el = document.getElementById(id);
  el.textContent = message;
  el.className = "status " + (isError ? "error" : "ok");
}

// ─── Colonne 1 — Source: dossier déposé / choisi / cloné ────────────────────

async function uploadFiles(fileEntries) {
  // fileEntries: [{file, relpath}]
  if (fileEntries.length === 0) return;
  setStatus("source-status", `Envoi de ${fileEntries.length} fichier(s)...`, false);

  const CHUNK = 200;
  let written = 0;
  for (let i = 0; i < fileEntries.length; i += CHUNK) {
    const chunk = fileEntries.slice(i, i + CHUNK);
    const form = new FormData();
    for (const { file, relpath } of chunk) {
      form.append("files", file);
      form.append("relpaths", relpath);
    }
    const res = await fetch("/api/upload", { method: "POST", body: form });
    const data = await res.json();
    if (data.error) {
      setStatus("source-status", "Erreur: " + data.error, true);
      return;
    }
    written += data.written;
    setStatus("source-status", `${written}/${fileEntries.length} fichier(s) envoyés...`, false);
  }
  setStatus("source-status", `${written} fichier(s) importés.`, false);
  refreshTree("source");
}

function readDirectoryEntry(entry, basePath) {
  return new Promise((resolve) => {
    if (entry.isFile) {
      entry.file((file) => resolve([{ file, relpath: basePath + entry.name }]));
    } else if (entry.isDirectory) {
      const reader = entry.createReader();
      const all = [];
      const readBatch = () => {
        reader.readEntries(async (entries) => {
          if (entries.length === 0) {
            const results = await Promise.all(all);
            resolve(results.flat());
            return;
          }
          for (const child of entries) {
            all.push(readDirectoryEntry(child, basePath + entry.name + "/"));
          }
          readBatch();
        });
      };
      readBatch();
    } else {
      resolve([]);
    }
  });
}

function setupDropzone() {
  const zone = document.getElementById("dropzone");
  ["dragenter", "dragover"].forEach((evt) =>
    zone.addEventListener(evt, (e) => {
      e.preventDefault();
      zone.classList.add("dragover");
    })
  );
  ["dragleave", "drop"].forEach((evt) =>
    zone.addEventListener(evt, (e) => {
      e.preventDefault();
      zone.classList.remove("dragover");
    })
  );
  zone.addEventListener("drop", async (e) => {
    const items = e.dataTransfer.items;
    if (!items || items.length === 0) return;
    const promises = [];
    for (const item of items) {
      const entry = item.webkitGetAsEntry && item.webkitGetAsEntry();
      if (entry) promises.push(readDirectoryEntry(entry, ""));
    }
    const results = await Promise.all(promises);
    await uploadFiles(results.flat());
  });
}

function setupFolderInput() {
  const input = document.getElementById("folder-input");
  input.addEventListener("change", async () => {
    const entries = Array.from(input.files).map((file) => ({
      file,
      relpath: file.webkitRelativePath || file.name,
    }));
    await uploadFiles(entries);
    input.value = "";
  });
}

function setupClone() {
  document.getElementById("clone-btn").addEventListener("click", async () => {
    const url = document.getElementById("clone-url").value.trim();
    if (!url) return;
    setStatus("source-status", "Clonage...", false);
    const res = await fetch("/api/clone", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
    });
    const data = await res.json();
    if (data.error) {
      setStatus("source-status", "Erreur: " + data.error, true);
      return;
    }
    setStatus("source-status", "Cloné.", false);
    document.getElementById("clone-url").value = "";
    refreshTree("source");
  });
}

// ─── Colonne 1 — Cloner depuis un fichier .txt d'URLs (url.txt par défaut) ──

let selectedUrlFile = null;

async function loadDefaultUrlFileInfo() {
  const hint = document.getElementById("url-file-hint");
  try {
    const res = await fetch("/api/urlfile/default");
    const data = await res.json();
    if (data.error) {
      hint.textContent = "Pas de fichier par défaut (" + data.error + ")";
      return;
    }
    hint.dataset.count = data.count;
    hint.dataset.filename = data.filename;
    hint.textContent = `Par défaut : ${data.filename} (${data.count} sources)`;
  } catch (e) {
    hint.textContent = "Impossible de charger le fichier par défaut.";
  }
}

function setupUrlFileInput() {
  const input = document.getElementById("url-file-input");
  const label = document.getElementById("url-file-label");
  input.addEventListener("change", () => {
    selectedUrlFile = input.files[0] || null;
    label.textContent = selectedUrlFile ? selectedUrlFile.name : "Fichier d'URLs (.txt)…";
  });

  document.getElementById("clone-list-btn").addEventListener("click", async () => {
    const hint = document.getElementById("url-file-hint");
    const usingDefault = !selectedUrlFile;
    setStatus(
      "source-status",
      usingDefault
        ? `Clonage depuis ${hint.dataset.filename || "url.txt"} (défaut)...`
        : `Clonage depuis ${selectedUrlFile.name}...`,
      false
    );

    const form = new FormData();
    if (selectedUrlFile) form.append("file", selectedUrlFile);

    const res = await fetch("/api/clone-list", { method: "POST", body: form });
    const data = await res.json();
    if (data.error) {
      setStatus("source-status", "Erreur: " + data.error, true);
      return;
    }
    setStatus(
      "source-status",
      `${data.source_label}: ${data.new_repos.length} nouveau(x) dépôt(s) clonés sur ${data.total} source(s).`,
      false
    );
    refreshTree("source");
  });
}

// ─── Colonne 2 — Classification ──────────────────────────────────────────────

function setupClassify() {
  document.getElementById("classify-btn").addEventListener("click", async () => {
    setStatus("organized-status", "Classification en cours...", false);
    const useOllama = document.getElementById("classify-ollama").checked;
    const res = await fetch("/api/classify", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ use_ollama: useOllama }),
    });
    const data = await res.json();
    if (data.error) {
      setStatus("organized-status", "Erreur: " + data.error, true);
      return;
    }
    setStatus("organized-status", "Classification terminée.", false);
    refreshTree("organized");
    refreshTree("ready");
  });
}

// ─── Colonne 3 — Enrichissement ──────────────────────────────────────────────

function renderEnrichForm(data) {
  const container = document.getElementById("enrich-form");
  container.innerHTML = "";

  const summary = document.createElement("p");
  summary.className = "hint";
  summary.textContent = `${data.ready_count} prêt(s) sans config, ${data.to_configure_count} à configurer, ${data.skipped_count} ignoré(s).`;
  container.appendChild(summary);

  if (data.fields.length === 0) {
    return;
  }

  for (const field of data.fields) {
    const box = document.createElement("div");
    box.className = "field-box";

    const label = document.createElement("label");
    label.textContent = `${field.label} (${field.files.length} fichier(s))`;
    box.appendChild(label);

    if (field.key === "discord_webhook") {
      const guideBtn = document.createElement("button");
      guideBtn.type = "button";
      guideBtn.className = "guide-btn";
      guideBtn.textContent = "Pas encore de webhook ? Guide";
      const guide = document.createElement("pre");
      guide.className = "guide-text hidden";
      guide.textContent = data.discord_webhook_guide;
      guideBtn.addEventListener("click", () => guide.classList.toggle("hidden"));
      box.appendChild(guideBtn);
      box.appendChild(guide);
    }

    const input = document.createElement("input");
    input.type = "text";
    input.placeholder = field.example || "";
    input.dataset.fieldKey = field.key;
    input.className = "field-value";
    box.appendChild(input);

    const filesToggle = document.createElement("button");
    filesToggle.type = "button";
    filesToggle.className = "files-toggle";
    filesToggle.textContent = "voir les fichiers concernés";
    const filesList = document.createElement("ul");
    filesList.className = "affected-files hidden";
    for (const f of field.files) {
      const li = document.createElement("li");
      li.textContent = `${f.file} (ligne ${f.line_no})`;
      filesList.appendChild(li);
    }
    filesToggle.addEventListener("click", () => filesList.classList.toggle("hidden"));
    box.appendChild(filesToggle);
    box.appendChild(filesList);

    container.appendChild(box);
  }

  const applyBtn = document.createElement("button");
  applyBtn.id = "enrich-apply-btn";
  applyBtn.textContent = "Appliquer et finaliser →";
  applyBtn.addEventListener("click", applyEnrichment);
  container.appendChild(applyBtn);
}

async function applyEnrichment() {
  const inputs = document.querySelectorAll(".field-value");
  const values = {};
  for (const input of inputs) {
    if (input.value.trim()) {
      values[input.dataset.fieldKey] = input.value.trim();
    }
  }
  setStatus("ready-status", "Application...", false);
  const res = await fetch("/api/enrich/apply", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ values }),
  });
  const data = await res.json();
  if (data.error) {
    setStatus("ready-status", "Erreur: " + data.error, true);
    return;
  }
  setStatus("ready-status", "Terminé — prêt à copier sur la carte SD.", false);
  refreshTree("ready");
}

function setupEnrich() {
  document.getElementById("enrich-scan-btn").addEventListener("click", async () => {
    setStatus("ready-status", "Analyse en cours...", false);
    const useOllama = document.getElementById("enrich-ollama").checked;
    const res = await fetch("/api/enrich/scan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ use_ollama: useOllama }),
    });
    const data = await res.json();
    if (data.error) {
      setStatus("ready-status", "Erreur: " + data.error, true);
      return;
    }
    setStatus("ready-status", "", false);
    renderEnrichForm(data);
  });
}

// ─── Reset ────────────────────────────────────────────────────────────────

function setupResets() {
  document.querySelectorAll(".reset-btn").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const stage = btn.dataset.stage;
      await fetch("/api/reset", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ stage }),
      });
      refreshTree(stage);
      if (stage === "ready") document.getElementById("enrich-form").innerHTML = "";
    });
  });
}

// ─── Init ─────────────────────────────────────────────────────────────────

window.addEventListener("DOMContentLoaded", () => {
  setupDropzone();
  setupFolderInput();
  setupClone();
  setupUrlFileInput();
  setupClassify();
  setupEnrich();
  setupResets();
  loadDefaultUrlFileInfo();
  refreshTree("source");
  refreshTree("organized");
  refreshTree("ready");
});
