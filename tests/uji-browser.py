"""Uji integrasi di browser (Chromium via Playwright).
Jalankan dari folder proyek:  python3 tests/uji-browser.py
Server lokal sementara dibuka otomatis pada port 8765."""
import http.server, threading, socketserver, os, sys, re, json, functools
from playwright.sync_api import sync_playwright

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.environ.get("UJI_OUT", "/tmp/uji")
os.makedirs(OUT, exist_ok=True)

class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
socketserver.TCPServer.allow_reuse_address = True
httpd = socketserver.TCPServer(("127.0.0.1", 8765), functools.partial(Q, directory=ROOT))
threading.Thread(target=httpd.serve_forever, daemon=True).start()

res = []
def check(cond, msg):
    res.append((bool(cond), msg)); print(("LULUS  " if cond else "GAGAL  ") + msg)

def num(t):  # ambil angka desimal dari teks seperti "75° 15′ 00″" atau "78.3584°"
    return float(re.search(r"-?\d+(?:\.\d+)?", t.replace("−", "-")).group(0))

with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2, locale="id-ID",
                        timezone_id="Asia/Makassar", permissions=[])
    pg = ctx.new_page()
    errors = []
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.on("console", lambda m: errors.append(m.text) if m.type == "error" and "net::" not in m.text and "Failed to load resource" not in m.text else None)
    pg.route(re.compile(r"^https?://(?!127\.0\.0\.1).*"), lambda r: r.abort())
    pg.goto("http://127.0.0.1:8765/index.html")
    pg.click('[data-action="start"]')
    T = lambda i: pg.inner_text("#" + i)
    def go(page):
        if pg.viewport_size["width"] <= 800:
            pg.click('.mobile-menu'); pg.wait_for_timeout(250)
        pg.click(f'.nav-item[data-page="{page}"]'); pg.wait_for_timeout(120)
    go('sun')
    pg.wait_for_selector("#spSvg path.sp-path")

    # --- struktur & fitur wajib
    check(pg.query_selector("#spSvg path.sp-path") is not None, "garis lengkung lintasan Matahari tergambar")
    check(pg.query_selector("#spSvg .sp-horizon") is not None and "Horizon 0°" in pg.text_content("#spSvg"), "garis horizon 0° tampil")
    svgtxt = pg.text_content("#spSvg")
    check("Terbit" in svgtxt and "Kulminasi" in svgtxt and "Terbenam" in svgtxt, "penanda terbit, kulminasi, terbenam tampil")
    check(pg.query_selector("#spSun") is not None, "objek Matahari ada")
    check("T" in svgtxt and "B" in svgtxt, "label arah Timur(T) dan Barat(B) tampil")

    # --- slider mengubah semuanya sekaligus
    def snap():
        return dict(clock=T("spClock"), az=num(T("spAzDec")), alt=num(T("spAltDec")),
                    cx=float(pg.get_attribute("#spSun", "cx")), cy=float(pg.get_attribute("#spSun", "cy")),
                    tag=pg.text_content("#spTagAz")+"|"+pg.text_content("#spTagAlt"))
    pg.fill("#spDate", "2026-11-05")
    pg.select_option("#spZone", "8")
    def set_slider(sec):
        pg.eval_on_selector("#spSlider", "(e,v)=>{e.value=v;e.dispatchEvent(new Event('input',{bubbles:true}))}", str(sec))
        pg.wait_for_timeout(120)
    set_slider(6*3600); a = snap()
    set_slider(12*3600); c = snap()
    set_slider(17*3600+30*60); d = snap()
    check(a["clock"] == "06:00:00" and c["clock"] == "12:00:00" and d["clock"] == "17:30:00", f"jam di layar mengikuti slider: {a['clock']}, {c['clock']}, {d['clock']}")
    check(a["cx"] < c["cx"] < d["cx"] or a["cx"] > c["cx"] > d["cx"], "posisi Matahari bergerak horizontal bersama slider")
    check(c["cy"] < a["cy"] and c["cy"] < d["cy"], "Matahari paling tinggi saat tengah hari (posisi vertikal ikut slider)")
    check(a["az"] != c["az"] != d["az"] and a["alt"] != c["alt"] != d["alt"], f"azimut & altitude berubah: {a['az']},{c['az']},{d['az']} / {a['alt']},{c['alt']},{d['alt']}")
    check(a["az"] < 120 and d["az"] > 240, "pagi di sisi Timur (<120°), sore di sisi Barat (>240°)")
    check(str(round(c["az"], 2)) in c["tag"] and str(round(c["alt"], 2)) in c["tag"], "label di dekat Matahari memuat azimut & ketinggian yang sama")
    # cocokkan dengan perhitungan murni
    ref = pg.evaluate("()=>{const s=window.PanritaSunPath.compute(2026,11,5,8,12*3600,%f,%f);return {az:s.azimuth,alt:s.altitude}}" % tuple(pg.evaluate("()=>[-4.0189,119.6238]")))
    check(abs(ref["alt"] - c["alt"]) < 1e-3, f"altitude layar = hasil hitung (tengah hari): {c['alt']} vs {ref['alt']:.4f}")

    # --- Play / Pause / Reset
    set_slider(8*3600); pg.click("#spPlay"); pg.wait_for_timeout(800)
    p1 = snap(); pg.wait_for_timeout(600); p2 = snap()
    check(p1["clock"] != p2["clock"] and p2["az"] != p1["az"], f"Play menggerakkan waktu & Matahari: {p1['clock']} → {p2['clock']}")
    check(pg.is_disabled("#spPlay") and not pg.is_disabled("#spPause"), "status tombol saat Play benar")
    pg.click("#spPause"); pg.wait_for_timeout(150); q1 = snap(); pg.wait_for_timeout(500); q2 = snap()
    check(q1["clock"] == q2["clock"] and q1["cx"] == q2["cx"], "Pause menghentikan gerak")
    pg.click("#spReset"); pg.wait_for_timeout(200)
    r = snap()
    check(pg.input_value("#spDate") == pg.evaluate("()=>{const t=new Date(Date.now()+8*3600000);return t.toISOString().slice(0,10)}"), "Reset mengembalikan tanggal ke hari ini")
    check(abs(int(pg.input_value("#spSlider")) - pg.evaluate("()=>{const t=new Date(Date.now()+8*3600000);return t.getUTCHours()*3600+t.getUTCMinutes()*60+t.getUTCSeconds()}")) < 5, "Reset mengembalikan slider ke jam sekarang")
    set_slider(0); pg.click("#spPlay"); pg.wait_for_timeout(300); pg.click("#spReset")
    check(pg.is_disabled("#spPause") and not pg.is_disabled("#spPlay"), "Reset menghentikan putaran")

    # --- slider digeser saat Play → otomatis pause, tidak melompat balik
    pg.click("#spPlay"); pg.wait_for_timeout(200); set_slider(15*3600); pg.wait_for_timeout(400)
    check(T("spClock") == "15:00:00", "geser slider saat Play menghentikan otomatis dan menetap di waktu pilihan")

    # --- mengikuti tanggal
    pg.fill("#spDate", "2026-06-21"); pg.wait_for_timeout(100); set_slider(12*3600); jun = snap()
    pg.fill("#spDate", "2026-12-21"); pg.wait_for_timeout(100); set_slider(12*3600); dec = snap()
    check(jun["alt"] != dec["alt"] and abs(num(T("spDeclDec")) + 23.44) < 0.1, f"tanggal mengubah hasil (21 Jun {jun['alt']:.2f}° vs 21 Des {dec['alt']:.2f}°, δ Des {T('spDeclDec')})")
    # --- mengikuti zona waktu (jam sama, zona beda → posisi beda)
    pg.fill("#spDate", "2026-11-05"); set_slider(12*3600)
    z8 = snap(); pg.select_option("#spZone", "7"); pg.wait_for_timeout(100); z7 = snap()
    check(z8["alt"] != z7["alt"] and "WIB" in T("spTz"), f"zona waktu mengubah hasil: WITA {z8['alt']:.2f}° vs WIB {z7['alt']:.2f}°")
    pg.select_option("#spZone", "8")
    # --- mengikuti lokasi (ubah di Pengaturan → simpan)
    before = snap()
    go('settings')
    pg.fill("#latInput", "-6.2"); pg.fill("#lonInput", "106.85")
    pg.once("dialog", lambda d: d.accept())
    pg.click('[data-action="save-location"]')
    go('sun'); pg.wait_for_timeout(300)
    set_slider(12*3600); after = snap()
    check(abs(after["alt"] - before["alt"]) > 0.5 and "-6.2" in T("spLoc").replace("−", "-") or "6.2000° LS" in T("spLoc"), f"lokasi baru memengaruhi simulasi: {before['alt']:.2f}° → {after['alt']:.2f}°; {T('spLoc')}")
    ev = pg.evaluate("()=>{const e=window.PanritaSunPath.events(2026,11,5,8,-6.2,106.85);return {rise:e.rise,set:e.set,transit:e.transit,riseAz:e.spR.azimuth,setAz:e.spS.azimuth}}")
    check(ev["rise"] < ev["transit"] < ev["set"], f"urutan terbit < kulminasi < terbenam (Jakarta, WITA): {ev['rise']/3600:.3f} < {ev['transit']/3600:.3f} < {ev['set']/3600:.3f} jam")
    check(abs((ev["transit"] - ev["rise"]) - (ev["set"] - ev["transit"])) < 300, "terbit dan terbenam simetris terhadap kulminasi (<5 menit)")

    # --- visual mobile + desktop
    pg.select_option("#spZone", "7"); pg.fill("#spDate", "2026-11-05"); set_slider(15*3600+20*60)
    pg.eval_on_selector("#sunPathCard", "e=>e.scrollIntoView({block:'start'})"); pg.wait_for_timeout(300)
    pg.locator("#sunPathCard").screenshot(path=f"{OUT}/sunpath-mobile.png")
    overflow = pg.evaluate("()=>document.documentElement.scrollWidth>document.documentElement.clientWidth+1")
    check(not overflow, "tidak ada gulir horizontal di layar 390 px")

    # --- Utara Sejati
    go('theodolite')
    def tn(a, time, dec):
        pg.fill("#trueNorthSunAz", str(a)); pg.select_option("#trueNorthTime", time); pg.select_option("#trueNorthDeclination", dec)
        pg.click('[data-action="true-north-calc"]')
        return T("trueNorthFormula"), T("trueNorthResult")
    for a in [75.25, 100.0, 12.345678, 0.001, 179.9999]:
        f, rr = tn(a, "morning", "south")
        exp = (360 - a) % 360
        check(f == "360° − A" and abs(num(rr.split("(")[1]) - exp) < 0.0006, f"pagi + deklinasi Selatan, A={a}: rumus '{f}', hasil '{rr}', harapan {exp:.4f}°")
    f, rr = tn(75.25, "morning", "south")
    check(rr.startswith("284° 45′ 00″"), f"DMS 360°−75,25° = 284° 45′ 00″ (tampil: {rr})")
    f, rr = tn(75.25, "morning", "north")
    check(f == "360° − A" and rr.startswith("284° 45′ 00″"), "pagi + Utara tetap 360° − A")
    f, rr = tn(0.0001, "morning", "south"); check("360° 00′" not in rr and "60″" not in rr, f"tidak muncul '360° 00′ 00″' / '60″' (tampil: {rr})")
    pg.screenshot(path=f"{OUT}/theodolite-mobile.png", full_page=False)

    # --- desktop screenshot
    pg.set_viewport_size({"width": 1280, "height": 900})
    go('sun'); pg.wait_for_timeout(300)
    pg.locator("#sunPathCard").screenshot(path=f"{OUT}/sunpath-desktop.png")
    # --- halaman lama masih ada
    for page in ["home","qibla","theodolite","rashdul","sun","prayer","monthly","calc","map","settings","info"]:
        go(page)
        check(pg.is_visible(f"#page-{page}"), f"halaman lama '{page}' tetap dapat dibuka")
    check(not errors, f"tidak ada galat JavaScript di konsol {errors[:3]}")
    b.close()

httpd.shutdown()
bad = [m for ok, m in res if not ok]
print(f"\n{len(res)-len(bad)} lulus, {len(bad)} gagal")
sys.exit(1 if bad else 0)
