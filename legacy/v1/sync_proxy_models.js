#!/usr/bin/env node
"use strict";

const fs = require("fs");
const path = require("path");
const os = require("os");
const crypto = require("crypto");

const CONFIG_PATH = path.join(os.homedir(), ".config", "opencode", "opencode.json");
const STATE_PATH = path.join(os.homedir(), ".config", "opencode", "proxy-models-state.json");
const PRUNE = process.argv.includes("--prune");

const PROVIDERS = [
  {
    key: "opencodefree",
    name: "OpenCode Free Proxy",
    urls: ["http://localhost:6446/v1", "http://10.1.37.223:6446/v1"],
  },
  {
    key: "clineproxy",
    name: "Cline Free Proxy",
    urls: ["http://localhost:6447/v1", "http://10.1.37.223:6447/v1"],
  },
  {
    key: "kiloproxy",
    name: "Kilo Free Proxy",
    urls: ["http://localhost:5380/v1", "http://10.1.37.223:5380/v1"],
  },
];

function hashIds(ids) {
  return crypto
    .createHash("sha256")
    .update([...ids].sort().join("\n"))
    .digest("hex");
}

async function fetchModels(urls) {
  for (const url of urls) {
    try {
      const ctl = new AbortController();
      const t = setTimeout(() => ctl.abort(), 8000);
      const res = await fetch(`${url}/models`, { signal: ctl.signal });
      clearTimeout(t);
      if (!res.ok) continue;
      const data = await res.json();
      if (Array.isArray(data.data) && data.data.length) return data.data;
    } catch {
      /* try next url */
    }
  }
  return null;
}

function deriveName(id) {
  return id
    .split("/")
    .pop()
    .split(/[:_]/)
    .map((w) =>
      w
        .split("-")
        .map((p) => (p.length <= 2 && /[0-9]/.test(p) ? p : p.charAt(0).toUpperCase() + p.slice(1)))
        .join(" "),
    )
    .join(" ");
}

function desiredEntry(id, api, existing) {
  const entry = { ...(existing || {}) };
  delete entry.context; // legacy invalid field -> move into limit

  if (!entry.name) entry.name = api.name || deriveName(id);

  const ctx =
    api.context_length ||
    (api.top_provider && api.top_provider.context_length) ||
    (existing && existing.limit && existing.limit.context) ||
    (existing && existing.context);
  const out =
    (api.top_provider && api.top_provider.max_completion_tokens) ||
    api.max_completion_tokens ||
    (existing && existing.limit && existing.limit.output);

  if (ctx) {
    entry.limit = { ...(entry.limit || {}), context: ctx, output: out || 32768 };
  }

  const modalities =
    (api.architecture && api.architecture.input_modalities) ||
    (api.architecture && api.architecture.modality) ||
    "";
  const inMods = Array.isArray(modalities) ? modalities : String(modalities).split("+");
  if (inMods.includes("image") && entry.attachment === undefined) entry.attachment = true;

  return entry;
}

function stable(value) {
  if (Array.isArray(value)) return value.map(stable);
  if (value && typeof value === "object") {
    return Object.fromEntries(
      Object.keys(value)
        .sort()
        .map((k) => [k, stable(value[k])]),
    );
  }
  return value;
}

async function main() {
  if (!fs.existsSync(CONFIG_PATH)) {
    console.error(`❌ Config bulunamadı: ${CONFIG_PATH}`);
    process.exit(1);
  }

  const config = JSON.parse(fs.readFileSync(CONFIG_PATH, "utf8"));
  config.provider = config.provider || {};
  const state = fs.existsSync(STATE_PATH)
    ? JSON.parse(fs.readFileSync(STATE_PATH, "utf8"))
    : {};
  let changed = false;
  const summary = [];

  for (const p of PROVIDERS) {
    const apiModels = await fetchModels(p.urls);
    if (!apiModels) {
      summary.push(`⚠️  ${p.key}: API'ye ulaşılamadı (tunnel kapalı olabilir), atlandı.`);
      continue;
    }

    const existing = config.provider[p.key];
    if (!existing) {
      config.provider[p.key] = {
        npm: "@ai-sdk/openai-compatible",
        name: p.name,
        options: { baseURL: p.urls[0] },
        models: {},
      };
      changed = true;
    }
    const prov = config.provider[p.key];
    prov.models = prov.models || {};

    const apiIds = apiModels.map((m) => m.id);
    const newHash = hashIds(apiIds);
    const prevHash = state[p.key] && state[p.key].hash;

    const apiById = Object.fromEntries(apiModels.map((m) => [m.id, m]));
    const desired = {};
    for (const id of apiIds) {
      desired[id] = desiredEntry(id, apiById[id], prov.models[id]);
    }

    if (PRUNE) {
      for (const id of Object.keys(prov.models)) {
        if (!(id in desired)) delete prov.models[id];
      }
    }

    const added = Object.keys(desired).filter((id) => !(id in prov.models));
    const removed = PRUNE
      ? Object.keys(prov.models).filter((id) => !(id in desired))
      : [];
    const drifted = Object.keys(desired).filter(
      (id) =>
        id in prov.models &&
        JSON.stringify(stable(prov.models[id])) !== JSON.stringify(stable(desired[id])),
    );

    const configChanged =
      added.length > 0 ||
      removed.length > 0 ||
      drifted.length > 0 ||
      JSON.stringify(stable(prov.models)) !== JSON.stringify(stable(desired));

    if (configChanged) {
      prov.models = desired;
      changed = true;
    }

    const hashChanged = prevHash !== newHash;
    state[p.key] = { hash: newHash, count: apiIds.length, syncedAt: new Date().toISOString() };

    const notes = [];
    if (added.length) notes.push(`+${added.length} yeni: ${added.join(", ")}`);
    if (removed.length) notes.push(`-${removed.length} silindi: ${removed.join(", ")}`);
    if (drifted.length && !added.length && !removed.length)
      notes.push(`${drifted.length} model metadata güncellendi`);
    if (!notes.length)
      notes.push(hashChanged ? "içerik değişti ama yeni model yok" : "değişiklik yok");
    summary.push(`🔹 ${p.key} (${apiIds.length} model${hashChanged ? ", HASH DEĞİŞTİ" : ""}): ${notes.join("; ")}`);
  }

  if (changed) {
    const bak = CONFIG_PATH + ".bak";
    fs.copyFileSync(CONFIG_PATH, bak);
    fs.writeFileSync(CONFIG_PATH, JSON.stringify(config, null, 2) + "\n");
    console.log(`💾 Yedek alındı: ${bak}`);
  }

  fs.writeFileSync(STATE_PATH, JSON.stringify(state, null, 2) + "\n");

  console.log("=========================================");
  console.log("🔄 OpenCode proxy model sync");
  console.log("=========================================");
  for (const line of summary) console.log(line);
  console.log("-----------------------------------------");
  console.log(changed ? "✅ opencode.json GÜNCELLENDİ — opencode'u yeniden başlat." : "ℹ️  Değişiklik yok.");
  console.log(`state: ${STATE_PATH}`);
}

main().catch((err) => {
  console.error("❌ Hata:", err.message);
  process.exit(1);
});
