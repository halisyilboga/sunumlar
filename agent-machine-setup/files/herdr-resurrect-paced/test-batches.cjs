'use strict';
// Restoring 70+ agents one at a time is safe but glacial; starting them all at once is
// fast but floods the box. This pins the middle ground: batches of N, staggered inside
// the batch, with the next batch held back until every agent in the current one settled.
const assert = require('node:assert/strict');
const herdr = require('./lib/herdr');
require('./lib/pstree').query = () => null;

let now = 0;
let launched = [];
let readyAt = {};
let stuck = new Set();
const ids = Array.from({ length: 12 }, (_, i) => `w1:p${i + 1}`);

herdr.snapshot = () => ({ workspaces: [{ number: 1, label: 'x', workspace_id: 'w1' }] });
herdr.tabList = () => [{ number: 1, tab_id: 'w1:t1' }];
herdr.paneList = () => ids.map((pane_id) => ({ pane_id, tab_id: 'w1:t1' }));
herdr.processInfo = () => ({ shell_pid: 1, foreground_processes: [{ pid: 1 }], foreground_process_group_id: 1 });
herdr.runInPane = (pane_id, cmd) => { launched.push({ pane_id, cmd, at: now }); readyAt[pane_id] = now + 2000; return { code: 0 }; };
herdr.agentList = () => launched
  .filter((l) => !stuck.has(l.pane_id) && now >= readyAt[l.pane_id])
  .map((l) => ({ pane_id: l.pane_id, agent: 'opencode', agent_status: 'idle' }));

const { restore: restoreSession } = require('./lib/restore');
const pane = (id) => ({ pane_id: id, agent: { name: 'opencode', session: { value: 'ses_' + id } } });
const model = { tool: 'herdr-resurrect', workspaces: [{ number: 1, label: 'x', tabs: [{ number: 1, panes: ids.map(pane) }] }] };
const clock = () => now;
const nap = (ms) => { now += ms; };

const res = restoreSession(model, {
  mode: 'rehydrate', startupBatchSize: 5, startupDelayMs: 1000, startupBatchDelayMs: 5000,
  startupReadyTimeoutMs: 60000, startupAbortOnFailure: false, clock, sleep: nap,
});

assert.equal(launched.length, 12, JSON.stringify(launched));
// Inside a batch the launches are staggered, never simultaneous.
for (let i = 1; i < 5; i++) {
  assert.ok(launched[i].at - launched[i - 1].at >= 1000, `intra-batch stagger at ${i}: ${JSON.stringify(launched)}`);
}
// The 6th launch waits for the whole first batch to be ready, then the cool-off.
const batch1Ready = Math.max(...launched.slice(0, 5).map((l) => readyAt[l.pane_id]));
assert.ok(launched[5].at >= batch1Ready + 5000, `batch gap: ${launched[5].at} < ${batch1Ready + 5000}`);
// Never more than the batch size in flight at once.
const inFlight = (t) => launched.filter((l) => l.at <= t && readyAt[l.pane_id] > t).length;
assert.ok(Math.max(...launched.map((l) => inFlight(l.at))) <= 5, 'more than startupBatchSize in flight');
assert.equal(res.failures.length, 0);

// One pane that never settles is recorded as a failure and does not strand the rest.
launched = []; readyAt = {}; stuck = new Set(['w1:p1']);
const res2 = restoreSession(model, {
  mode: 'rehydrate', startupBatchSize: 2, startupDelayMs: 0, startupBatchDelayMs: 0,
  startupReadyTimeoutMs: 3000, startupAbortOnFailure: false, clock, sleep: nap,
});
assert.equal(launched.length, 12, `remaining panes must still launch: ${JSON.stringify(launched)}`);
assert.equal(res2.failures.length, 1, JSON.stringify(res2.failures));
assert.match(res2.failures[0], /w1:p1: opencode not ready after 3000ms/);

// With abort on, the very first stuck pane stops the run before the next batch.
launched = []; readyAt = {}; stuck = new Set(['w1:p1']);
assert.throws(() => restoreSession(model, {
  mode: 'rehydrate', startupBatchSize: 2, startupDelayMs: 0, startupBatchDelayMs: 0,
  startupReadyTimeoutMs: 3000, startupAbortOnFailure: true, clock, sleep: nap,
}), /not ready after 3000ms/);
assert.equal(launched.length, 2, JSON.stringify(launched));

console.log('PASS: batches of 5 with intra-batch stagger, inter-batch cool-off, bounded in-flight count, non-aborting failure path');
