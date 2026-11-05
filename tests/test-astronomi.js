/* Uji perhitungan astronomis Panrita Falak.
   Jalankan:  node tests/test-astronomi.js
   - solarPosition() diambil langsung dari script.js (kode yang sama dengan aplikasi).
   - Pembanding independen: Meeus "Astronomical Algorithms" bab 25 + waktu sideris (GMST), jadi
     sudut jam dihitung dari RA & waktu sideris, BUKAN dari Equation of Time seperti di aplikasi. */
const fs=require("fs"),path=require("path");
const src=fs.readFileSync(path.join(__dirname,"..","script.js"),"utf8");
const grab=(a,b)=>{const i=src.indexOf(a),j=src.indexOf(b,i);if(i<0||j<0)throw new Error("tidak ditemukan: "+a);return src.slice(i,j);};
const code=[
  "const norm360=d=>((d%360)+360)%360;",
  grab("function d2r(","function qiblaBearing"),
  grab("function formatDMS(","function d2r("),
  grab("function solarPosition(","function julianDay("),
  "return {solarPosition,formatDMS,norm360};"
].join("\n");
const {solarPosition,formatDMS}=new Function(code)();

const D=Math.PI/180,R=180/Math.PI,n360=x=>((x%360)+360)%360;
function reference(utcMs,lat,lon){ // Meeus bab 25 (akurasi ~0,01°) + GMST bab 12
  const jd=utcMs/86400000+2440587.5,T=(jd-2451545)/36525;
  const L0=n360(280.46646+36000.76983*T+0.0003032*T*T),M=n360(357.52911+35999.05029*T-0.0001537*T*T);
  const C=(1.914602-0.004817*T-0.000014*T*T)*Math.sin(M*D)+(0.019993-0.000101*T)*Math.sin(2*M*D)+0.000289*Math.sin(3*M*D);
  const om=125.04-1934.136*T,lam=L0+C-0.00569-0.00478*Math.sin(om*D);
  const eps=23.439291-0.0130042*T-1.64e-7*T*T+0.00256*Math.cos(om*D);
  const ra=n360(Math.atan2(Math.cos(eps*D)*Math.sin(lam*D),Math.cos(lam*D))*R);
  const dec=Math.asin(Math.sin(eps*D)*Math.sin(lam*D))*R;
  const gmst=n360(280.46061837+360.98564736629*(jd-2451545)+0.000387933*T*T);
  const H=n360(gmst+lon-ra);
  const alt=Math.asin(Math.sin(lat*D)*Math.sin(dec*D)+Math.cos(lat*D)*Math.cos(dec*D)*Math.cos(H*D))*R;
  const az=n360(Math.atan2(Math.sin(H*D),Math.cos(H*D)*Math.sin(lat*D)-Math.tan(dec*D)*Math.cos(lat*D))*R+180);
  return {dec,alt,az};
}
let pass=0,fail=0;
const ok=(c,m)=>{if(c){pass++;}else{fail++;console.log("GAGAL:",m);}};
const near=(a,b,t,m)=>ok(Math.abs(a-b)<=t,`${m}: ${a} vs ${b} (toleransi ${t})`);
const angDiff=(a,b)=>Math.abs(((a-b+540)%360)-180);
const pos=(y,mo,d,zone,secs,lat,lon)=>solarPosition(new Date(Date.UTC(y,mo-1,d)+secs*1000-zone*3600000),lat,lon,zone,secs/60);

// 1) Silang-uji dengan algoritma independen: banyak lokasi, tanggal, jam
const sites=[["Parepare",-4.0189,119.6238,8],["Jakarta",-6.2,106.85,7],["Jayapura",-2.53,140.7,9],["Makkah",21.4225,39.8262,3],["Oslo",59.91,10.75,1],["Quito",-0.18,-78.47,-5],["Sydney",-33.87,151.21,10]];
const dates=[[2026,3,20],[2026,6,21],[2026,9,23],[2026,12,21],[2026,11,5],[2027,2,11]];
let maxAz=0,maxAlt=0,maxDec=0,count=0;
for(const [nm,lat,lon,z] of sites)for(const [y,mo,d] of dates)for(let h=0;h<24;h+=0.5){
  const s=h*3600,a=pos(y,mo,d,z,s,lat,lon),b=reference(Date.UTC(y,mo-1,d)+s*1000-z*3600000,lat,lon);
  maxAlt=Math.max(maxAlt,Math.abs(a.altitude-b.alt));maxDec=Math.max(maxDec,Math.abs(a.decl-b.dec));
  // Azimut hanya bermakna bila Matahari di atas horizon; galat sudut-di-langit = Δazimut × cos(altitude)
  if(b.alt>0)maxAz=Math.max(maxAz,angDiff(a.azimuth,b.az)*Math.cos(b.alt*D));count++;
}
console.log(`Silang-uji ${count} titik: selisih maks altitude=${maxAlt.toFixed(4)}°, azimut(di langit, alt>0)=${maxAz.toFixed(4)}°, deklinasi=${maxDec.toFixed(5)}°`);
ok(maxAlt<0.05,"altitude vs referensi independen");ok(maxAz<0.03,"azimut vs referensi independen");ok(maxDec<0.005,"deklinasi vs referensi");

// 2) Nilai fisik yang dikenal
near(pos(2026,6,21,0,43200,0,0).decl,23.44,0.05,"deklinasi titik balik Juni");
near(pos(2026,12,21,0,43200,0,0).decl,-23.44,0.05,"deklinasi titik balik Desember");
near(pos(2026,3,20,0,43200,0,0).decl,0,0.4,"deklinasi ekuinoks Maret");
near(pos(2026,11,3,0,43200,0,0).eqTime,16.4,0.3,"Equation of Time ±3 Nov (≈ +16,4 mnt)");
near(pos(2026,2,11,0,43200,0,0).eqTime,-14.2,0.3,"Equation of Time ±11 Feb (≈ −14,2 mnt)");

// 3) Invarian geometri: kulminasi = 90 − |φ − δ|, azimut Timur/Barat saat ekuinoks di ekuator
{
  const lat=-4.0189,lon=119.6238,z=8;
  let t=43200;for(let k=0;k<5;k++){const sp=pos(2026,11,5,z,t,lat,lon);t=43200-(sp.eqTime+4*lon-60*z)*60;}
  const sp=pos(2026,11,5,z,t,lat,lon);
  near(sp.altitude,90-Math.abs(lat-sp.decl),0.01,"tinggi kulminasi = 90° − |φ − δ|");
  near(sp.ha,0,0.01,"sudut jam saat kulminasi = 0");
  near(angDiff(sp.azimuth,180),0,1.5,"azimut kulminasi Parepare 5 Nov ≈ Selatan (δ<0, |φ|<|δ|)");
  const trueNoonLocal=t/3600;
  console.log(`Parepare 5 Nov 2026: kulminasi ${Math.floor(trueNoonLocal)}:${String(Math.round((trueNoonLocal%1)*60)).padStart(2,"0")} WITA, h=${sp.altitude.toFixed(3)}°, δ=${sp.decl.toFixed(3)}°`);
}
{ // ekuinoks di ekuator: terbit ≈ Timur, terbenam ≈ Barat
  let rise=null,set=null,prev=pos(2026,3,20,0,0,0,10).altitude;
  for(let s=60;s<=86400;s+=60){const a=pos(2026,3,20,0,s,0,10).altitude;
    if(rise===null&&prev<0&&a>=0)rise=pos(2026,3,20,0,s,0,10).azimuth;
    if(set===null&&prev>=0&&a<0)set=pos(2026,3,20,0,s,0,10).azimuth;prev=a;}
  near(rise,90,1.0,"azimut terbit ekuinoks di ekuator ≈ 90°");near(set,270,1.0,"azimut terbenam ekuinoks di ekuator ≈ 270°");
}
// 4) Slider: posisi harus kontinu & berubah monoton (azimut naik, altitude naik lalu turun) di hari biasa
{
  const lat=-4.0189,lon=119.6238,z=8;let prevAz=null,maxStep=0,sawUp=false,sawDown=false,prevAlt=null,azMono=true;
  for(let m=0;m<=1440;m++){const sp=pos(2026,11,5,z,m*60,lat,lon);
    if(prevAz!==null){const d=sp.azimuth-prevAz;if(sp.altitude>0&&prevAlt>0){maxStep=Math.max(maxStep,Math.abs(d)>180?0:Math.abs(d));}}
    if(prevAlt!==null&&sp.altitude>0&&prevAlt>0){if(sp.altitude>prevAlt)sawUp=true;else sawDown=true;}
    prevAz=sp.azimuth;prevAlt=sp.altitude;}
  ok(sawUp&&sawDown,"altitude naik lalu turun sepanjang hari");ok(maxStep<2,`lompatan azimut per menit wajar (${maxStep.toFixed(3)}°/mnt)`);
}
// 5) Format derajat-menit-detik
const dms=[[0,"0° 00′ 00″"],[75.25,"75° 15′ 00″"],[284.75,"284° 45′ 00″"],[10.99999,"11° 00′ 00″"],[0.99999,"1° 00′ 00″"],[45.508333,"45° 30′ 30″"]];
for(const [v,e] of dms)ok(formatDMS(v)===e,`formatDMS(${v}) = ${formatDMS(v)} (harap ${e})`);
// 6) Rumus Utara Sejati (logika yang sama dengan calculateTrueNorth di script.js)
{
  const blk=grab("  let expression, raw;","  const out=norm360(");
  const f=new Function("a","time","dec","norm360",blk+"; return {expression,raw};");
  const n360b=n360;
  for(const a of [0.001,12.5,75.25,90,123.456,179.999,180,250,359.9]){
    for(const dec of ["north","south"]){
      const r=f(a,"morning",dec,n360b);
      ok(r.expression==="360° − A"&&Math.abs(r.raw-(360-a))<1e-9,`pagi/${dec}/A=${a} harus 360°−A (dapat ${r.expression}=${r.raw})`);
    }
  }
}
console.log(`\n${pass} lulus, ${fail} gagal`);process.exit(fail?1:0);
