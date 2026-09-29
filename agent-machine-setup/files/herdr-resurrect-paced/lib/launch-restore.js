'use strict';
const fs=require('fs');const path=require('path');const cp=require('child_process');
const {STATE_DIR,PLUGIN_ROOT,ensureDirs}=require('./paths');
function launch(args=[],model=null,token=null) {
  ensureDirs();
  const workerArgs=[path.join(PLUGIN_ROOT,'bin','restore-worker.js'),...args];
  if(model) {
    const file=path.join(STATE_DIR,`restore-input-${Date.now()}-${process.pid}.json`);
    fs.writeFileSync(file,JSON.stringify(model),{mode:0o600});workerArgs.push('--file',file);
  }
  if(token)workerArgs.push('--boot-token',token);
  const log=path.join(STATE_DIR,'paced-restore.log');const fd=fs.openSync(log,'a',0o600);
  try { const child=cp.spawn(process.execPath,workerArgs,{cwd:PLUGIN_ROOT,env:process.env,detached:true,stdio:['ignore',fd,fd]}); child.unref();return {pid:child.pid,log}; }
  finally{fs.closeSync(fd);}
}
module.exports={launch};
