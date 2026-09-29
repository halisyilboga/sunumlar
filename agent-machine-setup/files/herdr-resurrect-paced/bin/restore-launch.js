#!/usr/bin/env node
'use strict';
if(process.argv.includes('--dry-run')||process.argv.includes('-n')){require('./restore');}
else {const r=require('../lib/launch-restore').launch(process.argv.slice(2));console.log(`Sequential restore queued (pid ${r.pid}). Progress: ${r.log}`);}
