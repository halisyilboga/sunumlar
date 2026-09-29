#!/usr/bin/env node
'use strict';
const path=require('path');const {STATE_DIR,ensureDirs}=require('../lib/paths');
const lock=require('../lib/queue-lock');const boot=require('../lib/boot');const {loadModel,restore}=require('../lib/restore');
const {save}=require('../lib/snapshot');
ensureDirs();const lease=path.join(STATE_DIR,'.restore-queue.lock');
const args=process.argv.slice(2);const arg=(name)=>{const i=args.indexOf(name);return i<0?null:args[i+1];};
const token=arg('--boot-token') || boot.token();
if(!lock.acquire(lease)){console.log(`${new Date().toISOString()} restore already running; duplicate request skipped`);process.exit(0);}
const log=(line)=>console.log(`${new Date().toISOString()} ${line}`);
try {
 const model=loadModel(arg('--file'));
 log(`paced restore started: snapshot ${model.saved_at}`);
 restore(model,{mode:args.includes('--recreate')?'recreate':args.includes('--rehydrate')?'rehydrate':'auto',log});
 if(token)boot.markDone(token);
 save();log('paced restore completed; snapshot saved');
} catch(e) {
 log(`paced restore failed: ${e.message}; original restore-input retained`);
 // Keep the pre-boot snapshot until an explicit retry succeeds.
 if(token){const fs=require('fs');fs.writeFileSync(boot.lockPath(token),JSON.stringify({token,status:'failed',ts:Date.now()}));}
 process.exitCode=1;
} finally {lock.release(lease);}
