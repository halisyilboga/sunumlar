'use strict';
const herdr = require('./herdr');
const sleep = (ms) => Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, ms);

// Serialises agent/command launches so a restore never floods the machine.
//
// Launches travel in batches: `startupBatchSize` panes are started (staggered by
// `startupDelayMs` so the box is not hammered at the exact same millisecond), then the
// queue waits for every agent in that batch to reach a settled state before the next
// batch begins. `startupBatchDelayMs` is the cool-off between two batches.
//
// A pane that never becomes ready is recorded in `failures` and, unless
// `startupAbortOnFailure` is on, the run keeps going: one stubborn agent must not
// leave the other seventy tabs empty.
class StartupQueue {
  constructor(o = {}) {
    // Minimum gap between two consecutive launches inside one batch.
    this.delay = Number.isFinite(o.startupDelayMs) ? Math.max(0, o.startupDelayMs) : 10000;
    // How many launches may be in flight at once.
    this.batchSize = Number.isFinite(o.startupBatchSize) ? Math.max(1, Math.floor(o.startupBatchSize)) : 1;
    // Cool-off after a batch is fully ready, before the next one starts.
    this.batchDelay = Number.isFinite(o.startupBatchDelayMs) ? Math.max(0, o.startupBatchDelayMs) : 0;
    this.timeout = Number.isFinite(o.startupReadyTimeoutMs) ? Math.max(1000, o.startupReadyTimeoutMs) : 60000;
    this.abortOnFailure = o.startupAbortOnFailure !== false;
    this.now = o.clock || Date.now;
    this.sleep = o.sleep || sleep;
    this.log = o.log || (() => {});
    this.lastStart = null;
    this.failures = [];
  }
  beforeStart() {
    if (this.lastStart !== null) {
      const remaining = this.delay - (this.now() - this.lastStart);
      if (remaining > 0) this.sleep(remaining);
    }
  }
  started() { this.lastStart = this.now(); }
  // Poll `isReady` every 500ms until it holds or the deadline passes. The predicate is
  // evaluated once more at the deadline, so an agent that settles exactly on the last
  // tick counts as ready instead of being reported as a timeout.
  pollUntil(isReady, end) {
    for (;;) {
      if (isReady()) return true;
      const remaining = end - this.now();
      if (remaining <= 0) return isReady();
      this.sleep(Math.min(500, remaining));
    }
  }
  readyProbe(paneId, expected) {
    return () => {
      const live = herdr.agentList().find(a => a.pane_id === paneId);
      const expectedId = expected.session?.value;
      const actualId = live?.agent_session?.value;
      return !!(live?.agent === expected.name && ['idle', 'done', 'blocked'].includes(live.agent_status)
        && (!expectedId || !actualId || actualId === expectedId));
    };
  }
  waitReady(paneId, expected) {
    const end = this.now() + this.timeout;
    if (this.pollUntil(this.readyProbe(paneId, expected), end)) {
      const live = herdr.agentList().find(a => a.pane_id === paneId);
      this.log(`ready  ${paneId} (${expected.name}; ${live && live.agent_status})`);
      return;
    }
    throw new Error(`${paneId}: ${expected.name} not ready after ${this.timeout}ms`);
  }
  // Settle a whole batch against one shared deadline. Polling the agents one after
  // another instead would hand each one less than `timeout` of wall clock and fail the
  // tail of every batch; here they all get the same window and are read in one pass.
  waitReadyAll(jobs) {
    const pending = jobs.filter(j => j.pane.agent);
    if (!pending.length) return;
    const end = this.now() + this.timeout;
    const waiting = new Map(pending.map(j => [j.paneId, j.pane.agent]));
    const probe = () => {
      const live = herdr.agentList();
      for (const [paneId, agent] of waiting) {
        const found = live.find(a => a.pane_id === paneId);
        const expectedId = agent.session?.value;
        const actualId = found?.agent_session?.value;
        if (found?.agent === agent.name && ['idle', 'done', 'blocked'].includes(found.agent_status)
            && (!expectedId || !actualId || actualId === expectedId)) {
          this.log(`ready  ${paneId} (${agent.name}; ${found.agent_status})`);
          waiting.delete(paneId);
        }
      }
      return waiting.size === 0;
    };
    if (this.pollUntil(probe, end)) return;
    for (const [paneId, agent] of waiting) {
      this.failures.push(`${paneId}: ${agent.name} not ready after ${this.timeout}ms`);
    }
  }
  fail(message) {
    this.failures.push(message);
    return message;
  }
  // Launch `jobs` ({ paneId, pane, kind, cmd }) in batches, waiting for each batch's
  // agents to settle before starting the next one. `isIdle(paneId)` is a re-check right
  // before a launch, so a pane the user started working in during a wait is left alone.
  run(jobs, act, isIdle) {
    if (!jobs.length) return { batches: 0, launched: 0, failures: this.failures };
    let launched = 0;
    let batches = 0;
    for (let i = 0; i < jobs.length; i += this.batchSize) {
      const batch = jobs.slice(i, i + this.batchSize);
      const inFlight = [];
      for (const job of batch) {
        this.beforeStart();
        if (isIdle && !isIdle(job.paneId)) {
          act('skip', `${job.paneId} became busy before launch`);
          continue;
        }
        act('run', `${job.paneId} <- ${job.kind}: ${job.cmd}`);
        const result = herdr.runInPane(job.paneId, job.cmd);
        if (result.code !== 0) {
          const message = this.fail(`launch failed in ${job.paneId}: ${(result.stderr || result.stdout || '').trim()}`);
          act('error', message);
          if (this.abortOnFailure) throw new Error(message);
          continue;
        }
        this.started();
        launched++;
        inFlight.push(job);
      }
      const settled = this.failures.length;
      this.waitReadyAll(inFlight);
      for (const message of this.failures.slice(settled)) {
        act('error', `${message}; continuing with the remaining panes`);
        if (this.abortOnFailure) throw new Error(message);
      }
      batches++;
      if (i + this.batchSize < jobs.length && this.batchDelay) this.sleep(this.batchDelay);
    }
    return { batches, launched, failures: this.failures };
  }
}
module.exports = { StartupQueue };
