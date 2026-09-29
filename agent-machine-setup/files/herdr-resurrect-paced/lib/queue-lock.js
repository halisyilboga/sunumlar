'use strict';
const fs=require('fs');
const boot=require('./boot');
function active(file) {
  try { const owner=JSON.parse(fs.readFileSync(file,'utf8'));
    const token=boot.token();if(token && owner.bootToken && token!==owner.bootToken)return false;
    process.kill(owner.pid,0); return true; }
  catch (e) {
    if(e.code==='EPERM')return true;
    if(e.code==='ESRCH'||e.code==='ENOENT')return false;
    try{return Date.now()-fs.statSync(file).mtimeMs<30000;}catch{return false;}
  }
}
function acquire(file) {
  for(let i=0;i<2;i++) {
    try { const fd=fs.openSync(file,'wx',0o600);fs.writeFileSync(fd,JSON.stringify({pid:process.pid,started:Date.now(),bootToken:boot.token()}));fs.closeSync(fd);return true; }
    catch(e) { if(e.code!=='EEXIST')throw e;if(active(file))return false;try{fs.unlinkSync(file);}catch{} }
  }
  return false;
}
function release(file) {
  try { if(JSON.parse(fs.readFileSync(file,'utf8')).pid===process.pid)fs.unlinkSync(file); } catch{}
}
module.exports={active,acquire,release};
