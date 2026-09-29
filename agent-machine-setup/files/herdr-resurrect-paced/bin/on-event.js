#!/usr/bin/env node
'use strict';
// Single handler for herdr lifecycle events. Two jobs:
//   1. Debounced autosave (<= 1 write / HERDR_RESURRECT_DEBOUNCE ms).
//   2. Optional one-shot auto-restore on the first event after a server (re)start.
//
// Ordering matters on boot: the good pre-crash snapshot must be READ before any
// autosave overwrites last.json with the post-crash bare-shell state. The boot
// "claimer" reads it first, stands other handlers down until restore is `done`.
const fs = require('fs');
const settings = require('../lib/settings').load();
const boot = require('../lib/boot');
const { save } = require('../lib/snapshot');
const { loadModel, restore } = require('../lib/restore');
const { LAST, STATE_DIR } = require('../lib/paths');
const path = require('path');
const queueLock = require('../lib/queue-lock');
const { launch } = require('../lib/launch-restore');

const DEBOUNCE_MS = Number(process.env.HERDR_RESURRECT_DEBOUNCE || 20000);

function autosaveDebounced() {
  const lease = path.join(STATE_DIR, '.autosave.lock');
  try { if (Date.now() - fs.statSync(LAST).mtimeMs < DEBOUNCE_MS) return; } catch {}
  require('../lib/paths').ensureDirs();
  if (!queueLock.acquire(lease)) return;
  try {
    try { if (Date.now() - fs.statSync(LAST).mtimeMs < DEBOUNCE_MS) return; } catch {}
    save();
  } catch(e) { console.error('herdr-resurrect autosave failed:', e.message); }
  finally { queueLock.release(lease); }
}

async function main() {
  if (queueLock.active(path.join(STATE_DIR, '.restore-queue.lock'))) return;
  if (!settings.autoRestore) return autosaveDebounced();

  const token = boot.token();
  if (!token) return autosaveDebounced();          // can't detect boots -> just autosave

  const st = boot.status(token);
  if (st === 'done') return autosaveDebounced();     // normal mid-session event
  if (st === 'failed') return;
  if (st === 'restoring') return;                    // boot restore underway: skip autosave (would clobber snapshot)

  if (boot.claim(token) !== 'claimed') return;       // another handler just claimed the boot

  // We own this boot's restore. Capture the pre-crash snapshot before autosave can touch it.
  let model = null;
  try { model = loadModel(); } catch { /* nothing saved yet */ }

  if (model) {
    await new Promise((r) => setTimeout(r, settings.autoRestoreSettleMs)); // let herdr finish recreating panes
    const job = launch(['--rehydrate'], model, token);
    console.log(`herdr-resurrect: sequential boot restore queued (pid ${job.pid}); ${job.log}`);
    return;
  }
  boot.markDone(token);
  try { save(); } catch { /* refresh snapshot now that it's safe */ }
}

main();
