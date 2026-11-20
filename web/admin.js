const el = id => document.getElementById(id);
const fields = id => el(id).elements;
const days = ['Senin','Selasa','Rabu','Kamis','Jumat','Sabtu','Minggu'];
const statusText = {draft:'Draf',revision:'Perlu revisi',submitted:'Menunggu persetujuan',approved:'Disetujui'};
let key = '', data, current, generation = 0;

async function api(path, method='GET', body, headers={}) {
  const response = await fetch(path, {method, headers:{'X-Admin-Key':key,'Content-Type':'application/json',...headers},body:JSON.stringify(body)});
  const result = await response.json();
  if (!response.ok) {
    const details = result.detail;
    const message = Array.isArray(details) ? details.map(d => d.types ? 'Bentrok dengan '+d.jadwal[1]+' ('+d.types.filter(t=>t!=='time_overlap').map(t=>t==='room_conflict'?'ruangan':'dosen').join(' dan ')+')' : d.pesan).join('. ') : details;
    throw Object.assign(new Error(message || 'Permintaan gagal.'), {status:response.status});
  }
  return result;
}
function run(action) {
  return async event => {
    event?.preventDefault();
    el('notice').textContent='';
    try {await action();} catch(error) {el('notice').textContent=error.message;}
  };
}
function options(select, rows, value, label) {
  const previous=select.value;
  select.replaceChildren(...rows.map(row=>new Option(label(row),row[value])));
  if([...select.options].some(o=>o.value===previous)) select.value=previous;
}
function item(list, title, caption, action) {
  const li=document.createElement('li');
  li.textContent=title;
  if(action){const b=document.createElement('button'); b.textContent=caption;b.onclick=run(action);li.append(b);}
  list.append(li);
}
const courseName = code => data.kuliah.find(c=>c.kode===code)?.nama || code;
async function loadPeople() {
  data=await api('/admin/data');
  options(fields('register').program_studi_id,data.prodi,'id',r=>r.nama);
  options(fields('register').jalur_masuk_id,data.jalur,'id',r=>r.nama);
  options(el('student'),data.pendaftar.filter(p=>p.nim),'nim',p=>p.nama_lengkap+' · '+p.nim);
  for(const select of [fields('schedule').kode,fields('add').course]) options(select,data.kuliah,'kode',c=>c.nama);
  options(fields('schedule').ruangan,data.ruang,'kode',r=>r.kode+' · '+r.kapasitas+' kursi');
  const list=el('people');list.replaceChildren();
  if(!data.pendaftar.length)item(list,'Belum ada pendaftar.');
  for(const p of data.pendaftar){
    item(list,p.nama_lengkap+' · '+(p.nim || 'Menunggu persetujuan'),'Setujui',p.status==='pending'?async()=>{
      const approved=await api('/api/pmb/approve/'+p.id,'PUT');await loadPeople();
      el('student').value=approved.nim;el('notice').textContent='Pendaftaran disetujui. NIM '+approved.nim;
    }:null);
  }
}
const krsPath = () => '/api/krs/'+encodeURIComponent(el('student').value)+'/'+el('semester').value;
async function loadKrs(){
  const request=++generation;
  current=null;
  el('courses').replaceChildren();
  for(const id of ['add','submitKrs','review'])el(id).hidden=true;
  if(!el('student').value){el('summary').textContent='Setujui pendaftar di menu Pendaftaran untuk membuat KRS.';return;}
  if(!el('semester').validity.valid || !el('semester').value){el('summary').textContent='Pilih semester mulai dari 1.';return;}
  let record;
  try{record=await api(krsPath()+'/validasi');}catch(e){if(e.status!==404)throw e;}
  if(request!==generation)return;
  current=record;
  el('summary').textContent=record?[statusText[record.status],record.total_sks+' SKS',record.catatan].filter(Boolean).join(' · '):'Belum ada mata kuliah yang dipilih.';
  const editable=!record || ['draft','revision'].includes(record.status);
  for(const code of record?.mata_kuliah || [])item(el('courses'),courseName(code),'Hapus',editable?async()=>{await api(krsPath()+'/mata-kuliah/'+code,'DELETE');await loadKrs();}:null);
  el('add').hidden=!editable;el('submitKrs').hidden=!editable || !record?.mata_kuliah.length;
  el('review').hidden=record?.status!=='submitted';
}
async function transition(action){
  const body={version:current.version};
  if(action==='revise')body.catatan=fields('revise').note.value;
  const headers=action==='submit'?{'X-Nim':el('student').value}:{'X-Dosen-Pa':current.dosen_pa_id};
  try{await api(krsPath()+'/'+action,'POST',body,headers);}finally{await loadKrs();}
}
const clock=n=>[Math.floor(n/60),n%60].map(i=>String(i).padStart(2,'0')).join(':');
const minutes=t=>Number(t.slice(0,2))*60+Number(t.slice(3));
async function loadSlots(){
  const rows=await api('/jadwal'), list=el('slots');list.replaceChildren();
  if(!rows.length)item(list,'Belum ada jadwal.');
  for(const r of rows)item(list,[courseName(r.kode),days[r.hari-1],clock(r.mulai)+'–'+clock(r.selesai),r.ruangan,r.dosen].join(' · '),'Hapus',async()=>{
    if(confirm('Hapus jadwal '+courseName(r.kode)+'?')){await api('/jadwal/'+r.kode,'DELETE');await loadSlots();}
  });
}
async function show(tab){
  for(const btn of document.querySelectorAll('[data-tab]')){
    const active=btn.dataset.tab===tab;btn.setAttribute('aria-current',String(active));el(btn.dataset.tab).hidden=!active;
  }
  if(tab==='krs')await loadKrs();
  if(tab==='jadwal')await loadSlots();
}
el('signin').onsubmit=run(async()=>{
  key=fields('signin').key.value.trim();await loadPeople();el('signin').reset();
  el('login').hidden=true;el('logout').hidden=false;el('portal').hidden=false;await show('pmb');
});
el('logout').onclick=()=>location.reload();
for(const b of document.querySelectorAll('[data-tab]'))b.onclick=run(()=>show(b.dataset.tab));
el('register').onsubmit=run(async()=>{
  const body=Object.fromEntries(new FormData(el('register')));
  for(const k of ['jalur_masuk_id','program_studi_id'])body[k]=Number(body[k]);
  await api('/api/pmb/register','POST',body);el('register').reset();await loadPeople();el('notice').textContent='Pendaftar berhasil ditambahkan.';
});
for(const id of ['student','semester'])el(id).onchange=run(loadKrs);
el('add').onsubmit=run(async()=>{await api(krsPath()+'/mata-kuliah/'+fields('add').course.value,'POST');await loadKrs();});
el('submitKrs').onclick=run(()=>transition('submit'));
el('approve').onclick=run(()=>transition('approve'));
el('revise').onsubmit=run(()=>transition('revise'));
days.forEach((d,i)=>fields('schedule').hari.add(new Option(d,i+1)));
el('schedule').onsubmit=run(async()=>{
  const f=fields('schedule');
  await api('/jadwal/'+f.kode.value,'PUT',{hari:Number(f.hari.value),mulai:minutes(f.mulai.value),selesai:minutes(f.selesai.value),ruangan:f.ruangan.value,dosen:f.dosen.value});
  await loadSlots();el('notice').textContent='Jadwal tersimpan.';
});
