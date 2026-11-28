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
    if(details?.alternatif){showConflicts(details.konflik);showAlternatives(details.alternatif);}
    const message = Array.isArray(details) ? details.map(d => d.types ? 'Bentrok dengan '+d.jadwal[1]+' ('+d.types.filter(t=>t!=='time_overlap').map(t=>t==='room_conflict'?'ruangan':'dosen').join(' dan ')+')' : d.pesan).join('. ') : details?.pesan || details;
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
  options(el('student'),data.pendaftar.filter(p=>p.nim),'nim',p=>p.nama_lengkap+' \u00b7 '+p.nim);
  for(const select of [fields('schedule').kode,fields('add').course]) options(select,data.kuliah,'kode',c=>c.nama);
  options(fields('schedule').ruangan,data.ruang,'kode',r=>r.kode+' \u00b7 '+r.kapasitas+' kursi');
  const list=el('people');list.replaceChildren();
  if(!data.pendaftar.length)item(list,'Belum ada pendaftar.');
  for(const p of data.pendaftar){
    item(list,p.nama_lengkap+' \u00b7 '+(p.nim || 'Menunggu persetujuan'),'Setujui',p.status==='pending'?async()=>{
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
  for(const id of ['add','submitKrs','review','reopen'])el(id).hidden=true;
  if(!el('student').value){el('summary').textContent='Setujui pendaftar di menu Pendaftaran untuk membuat KRS.';return;}
  if(!el('semester').validity.valid || !el('semester').value){el('summary').textContent='Pilih semester mulai dari 1.';return;}
  let record;
  try{record=await api(krsPath()+'/validasi');}catch(e){if(e.status!==404)throw e;}
  if(request!==generation)return;
  current=record;
  el('summary').textContent=record?[statusText[record.status],record.total_sks+' SKS',record.catatan].filter(Boolean).join(' \u00b7 '):'Belum ada mata kuliah yang dipilih.';
  const editable=!record || ['draft','revision','approved'].includes(record.status);
  for(const code of record?.mata_kuliah || [])item(el('courses'),courseName(code),'Hapus',editable?async()=>{await editCourse(code,'DELETE');}:null);
  el('add').hidden=!editable;el('submitKrs').hidden=!editable || record?.status==='approved' || !record?.mata_kuliah.length;
  el('reopen').hidden=record?.status!=='approved';
  el('review').hidden=record?.status!=='submitted';
}
async function editCourse(code, method){
  const path=current?.status==='approved'
    ? '/koreksi/'+code+'?version='+current.version
    : '/mata-kuliah/'+code;
  try {await api(krsPath()+path,method);} finally {await loadKrs();}
}
async function transition(action){
  const body={version:current.version};
  if(['revise','reopen'].includes(action))body.catatan=fields(action).note.value;
  const headers=action==='submit'?{'X-Nim':el('student').value}:{'X-Dosen-Pa':current.dosen_pa_id};
  try{await api(krsPath()+'/'+action,'POST',body,headers);}finally{await loadKrs();}
}
const clock=n=>[Math.floor(n/60),n%60].map(i=>String(i).padStart(2,'0')).join(':');
const minutes=t=>Number(t.slice(0,2))*60+Number(t.slice(3));
function showConflicts(rows){
  const list=el('conflicts');list.replaceChildren();
  for(const r of rows){
    const types=r.types.filter(t=>t!=='time_overlap').map(t=>t==='room_conflict'?'ruangan sama':'dosen sama');
    item(list,r.jadwal.map(courseName).join(' / ')+' - '+types.join(', '));
  }
  if(!rows.length)item(list,'Tidak ada bentrok waktu, ruang, atau dosen.');
}
function showAlternatives(rows){
  const list=el('alternatives');
  list.replaceChildren();
  for(const r of rows)item(list,[days[r.hari-1],clock(r.mulai),r.ruangan,r.sumber,r.reason].join(' / '),'Pilih',()=>{
    const f=fields('schedule');
    f.kode.value=r.kode; f.hari.value=r.hari; f.mulai.value=clock(r.mulai);
    f.selesai.value=clock(r.selesai); f.ruangan.value=r.ruangan; f.dosen.value=r.dosen;
    list.replaceChildren();el('notice').textContent='Alternatif dipilih. Klik Simpan jadwal.';
  });
  if(!rows.length)item(list,'Belum ada alternatif yang memenuhi batasan.');
}
async function loadSlots(){
  showConflicts(await api('/jadwal/konflik'));
  const log=el('scheduleLog');log.replaceChildren();
  for(const r of await api('/jadwal/notifikasi'))item(log,[r.media,r.penerima,r.pesan].join(' / '));
  if(!log.children.length)item(log,'Belum ada notifikasi.');
  const rows=await api('/jadwal'), list=el('slots');list.replaceChildren();
  if(!rows.length)item(list,'Belum ada jadwal.');
  for(const r of rows)item(list,[courseName(r.kode),days[r.hari-1],clock(r.mulai)+'\u2013'+clock(r.selesai),r.ruangan,r.dosen].join(' \u00b7 '),'Hapus',async()=>{
    if(confirm('Hapus jadwal '+courseName(r.kode)+'?')){await api('/jadwal/'+r.kode,'DELETE');await loadSlots();}
  });
}
async function show(tab){
  for(const btn of document.querySelectorAll('[data-tab]')){
    const active=btn.dataset.tab===tab;btn.setAttribute('aria-current',String(active));el(btn.dataset.tab).hidden=!active;
  }
  if(tab==='presensi'){options(fields('buatQR').kode,data.kuliah,'kode',c=>c.nama);await attendanceReport();}
  if(tab==='spp')await loadFinance();
  if(tab==='nilai')await loadGrades();
  if(tab==='home'){await loadPeople();renderHome();}
  if(tab==='krs')await loadKrs();
  if(tab==='jadwal')await loadSlots();
}
el('signin').onsubmit=run(async()=>{
  key=fields('signin').key.value.trim();await loadPeople();el('signin').reset();
  el('login').hidden=true;el('logout').hidden=false;el('portal').hidden=false;await show('home');
});
el('logout').onclick=()=>location.reload();
for(const b of document.querySelectorAll('[data-tab]'))b.onclick=run(()=>show(b.dataset.tab));
el('register').onsubmit=run(async()=>{
  const body=Object.fromEntries(new FormData(el('register')));
  for(const k of ['jalur_masuk_id','program_studi_id'])body[k]=Number(body[k]);
  await api('/api/pmb/register','POST',body);el('register').reset();await loadPeople();el('notice').textContent='Pendaftar berhasil ditambahkan.';
});
for(const id of ['student','semester'])el(id).onchange=run(loadKrs);
el('add').onsubmit=run(async()=>{await editCourse(fields('add').course.value,'POST');});
el('submitKrs').onclick=run(()=>transition('submit'));
el('approve').onclick=run(()=>transition('approve'));
el('reopen').onsubmit=run(async()=>{await transition('reopen');el('reopen').reset();});
el('revise').onsubmit=run(()=>transition('revise'));
days.forEach((d,i)=>fields('schedule').hari.add(new Option(d,i+1)));
el('schedule').onsubmit=run(async()=>{
  const f=fields('schedule');
  el('alternatives').replaceChildren();
  await api('/jadwal/'+f.kode.value,'PUT',{hari:Number(f.hari.value),mulai:minutes(f.mulai.value),selesai:minutes(f.selesai.value),ruangan:f.ruangan.value,dosen:f.dosen.value});
  await loadSlots();el('notice').textContent='Jadwal tersimpan.';
});

el('retryMessages').onclick=run(async()=>{
  const result=await api('/jadwal/outbox/retry','POST');
  await loadSlots();el('notice').textContent='Notifikasi tertunda: '+result.pending;
});
el('calendarExport').onsubmit=run(async()=>{
  const query=new URLSearchParams(new FormData(el('calendarExport')));
  const response=await fetch('/jadwal/kalender.ics?'+query,{headers:{'X-Admin-Key':key}});
  if(!response.ok)throw new Error('Ekspor gagal. Periksa rentang tanggal semester.');
  const link=document.createElement('a');
  link.href=URL.createObjectURL(await response.blob());link.download='jadwal.ics';
  link.click();setTimeout(()=>URL.revokeObjectURL(link.href),1000);
});


let grades = [];
function selectedGrade() {return grades[el('gradeRow').selectedIndex];}
async function displayGrade() {
  const r=selectedGrade(), form=el('gradeForm');
  form.reset();
  el('history').replaceChildren();
  el('gpa').textContent='';
  form.hidden=!r || !r.dosen || r.presensi<75;
  el('gradeInfo').textContent=r ? (r.dosen || 'Atur dosen di menu Jadwal')+' | Presensi '+Number(r.presensi.toFixed(2))+'% | Nilai '+(r.nilai || 'belum diisi') : 'Setujui KRS terlebih dahulu.';
  if(!r)return;
  form.elements.huruf.value=r.nilai || 'A';
  form.elements.alasan.required=Boolean(r.nilai);
  const info=await api('/api/nilai/'+encodeURIComponent(r.nim)+'/'+r.semester);
  if(selectedGrade()!==r)return;
  el('gpa').textContent='IPS semester '+r.semester+' = '+info.ips+' | IPK sampai semester ini = '+info.ipk;
  for(const h of info.riwayat)item(el('history'),[h.waktu+' UTC',h.kode_mk,(h.lama || 'Kosong')+' → '+h.baru,h.dosen,h.alasan].filter(Boolean).join(' | '));
}
async function loadGrades() {
  grades=(await api('/api/nilai')).map(r=>({...r,key:r.id+'-'+r.kode_mk}));
  options(el('gradeRow'),grades,'key',r=>r.nim+' | Semester '+r.semester+' | '+r.nama);
  await displayGrade();
}
el('gradeRow').onchange=run(displayGrade);
el('gradeForm').onsubmit=run(async()=>{
  const r=selectedGrade();
  await api('/api/nilai/'+r.id+'/'+encodeURIComponent(r.kode_mk),'PUT',Object.fromEntries(new FormData(el('gradeForm'))));
  await loadGrades();
  el('notice').textContent='Nilai tersimpan.';
});


const rupiah = value => 'Rp'+value.toLocaleString('id-ID');
async function loadFinance() {
  const d=await api('/api/spp/dashboard');
  options(fields('payBill').bill,d.tagihan.filter(b=>b.sisa>0),'id',
    b=>b.nama_lengkap+' | '+b.awal+' | '+rupiah(b.sisa)+' | '+b.status);
  el('sppSummary').textContent='Penerimaan bulan ini '+rupiah(d.revenue)+'. Mahasiswa lunas '+d.collection_rate+'%. '+d.rekomendasi;
  for(const id of ['balances','rates','chart','arrears'])el(id).replaceChildren();
  for(const r of d.mahasiswa)item(el('balances'),r.nim+' | Tagihan '+rupiah(r.tagihan)+' | Dibayar '+rupiah(r.dibayar)+' | Sisa '+rupiah(r.sisa));
  for(const r of d.prodi)item(el('rates'),r.nama+' | '+r.persen+'%');
  for(const r of d.top)item(el('arrears'),r.nim+' | '+rupiah(r.tunggakan));
  const max=Math.max(1,...d.bulan.map(r=>r.jumlah));
  for(const r of d.bulan){
    item(el('chart'),r.bulan+' | '+rupiah(r.jumlah)+' ');
    const bar=document.createElement('meter');bar.max=max;bar.value=r.jumlah;
    el('chart').lastElementChild.append(bar);
  }
}
el('generateBill').onsubmit=run(async()=>{
  const res=await api('/api/spp/tagihan?awal='+fields('generateBill').awal.value,'POST');
  await loadFinance();el('notice').textContent=res.dibuat+' tagihan baru.';
});
let pendingPayment;
el('payBill').onsubmit=run(async()=>{
  const f=fields('payBill'), b=Number(f.bill.value), n=Number(f.amount.value);
  if(!pendingPayment || pendingPayment.billing_id!==b || pendingPayment.amount!==n)
    pendingPayment={transaction_id:crypto.randomUUID(),billing_id:b,amount:n};
  await api('/api/spp/bayar','POST',pendingPayment);
  pendingPayment=null;f.amount.value='';await loadFinance();el('notice').textContent='Pembayaran tercatat.';
});
setInterval(()=>{
  if(key && !el('portal').hidden && !el('spp').hidden && !document.hidden)
    run(loadFinance)();
},30000);


async function attendanceFile(path) {
  const r=await fetch(path,{headers:{'X-Admin-Key':key},cache:'no-store'});
  if(!r.ok)throw new Error((await r.json()).detail);
  return r;
}
el('buatQR').onsubmit=run(async()=>{
  const f=fields('buatQR');
  el('qrBox').hidden=true;
  const r=await attendanceFile('/attendance/qr/'+encodeURIComponent(f.kode.value)+'?'+new URLSearchParams({semester:f.semester.value,dosen:f.dosen.value}));
  if(el('qrImg').src)URL.revokeObjectURL(el('qrImg').src);
  el('qrImg').src=URL.createObjectURL(await r.blob());
  el('scanLink').href=r.headers.get('X-Scan-Link');
  el('qrBox').hidden=false;
});
async function attendanceReport(){
  const r=await api('/attendance/report');
  el('risk').textContent=r.rekap.length?r.jumlah_berisiko+' mahasiswa di bawah 75%.':'Rekap muncul setelah waktu presensi sesi pertama berakhir.';
  el('attendanceRows').replaceChildren();
  el('attendanceActions').replaceChildren();
  for(const p of r.rekap)item(el('attendanceRows'),p.nim+' | '+p.kode+' | Semester '+p.semester+' | '+p.persen+'% | Hadir '+p.hadir+', terlambat '+p.terlambat+', absen '+p.absen+(p.risiko?' | Peringatan':''));
  for(const action of r.actions)item(el('attendanceActions'),action);
}
el('attendanceRefresh').onclick=run(attendanceReport);
el('attendanceExcel').onclick=run(async()=>{
  const r=await attendanceFile('/attendance/report.xlsx'), link=document.createElement('a');
  link.href=URL.createObjectURL(await r.blob());link.download='presensi.xlsx';link.click();
  setTimeout(()=>URL.revokeObjectURL(link.href),1000);
});


function renderHome(){
  el('pendingCount').textContent=data.pendaftar.filter(p=>p.status==='pending').length;
  el('activeCount').textContent=data.pendaftar.filter(p=>p.nim).length;
  el('courseCount').textContent=data.kuliah.length;
  const list=el('catalog');list.replaceChildren();
  for(const c of data.kuliah){
    const group=c.kode.startsWith('SI')?'Sistem Informasi':c.kode.startsWith('TI')||c.kode==='IF201'?'Teknik Informatika':'Dasar bersama';
    if(el('catalogGroup').value==='Semua'||el('catalogGroup').value===group)
      item(list,c.kode+'  ·  '+c.nama+'  ·  '+c.sks+' SKS');
  }
  if(!list.children.length)item(list,'Belum ada mata kuliah dalam kelompok ini.');
}
el('catalogGroup').onchange=renderHome;
for(const button of document.querySelectorAll('[data-open]'))button.onclick=run(()=>show(button.dataset.open));
