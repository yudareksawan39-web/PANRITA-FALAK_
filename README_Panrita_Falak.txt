PANRITA FALAK
Aplikasi pembelajaran dan perhitungan ilmu falak

FITUR UTAMA
- Arah kiblat dan jarak geodesik ke Ka'bah.
- Waktu salat dan jadwal salat bulanan.
- Rashdul Kiblat serta kalkulator falak.
- Lokasi melalui GPS dan pemilihan titik pada peta.
- Reverse geocoding; koordinat tetap digunakan jika nama lokasi tidak dapat dimuat.
- Modul Teodolit Falak berbasis perhitungan: simulasi posisi Matahari dari tanggal, waktu, zona waktu, dan koordinat; hitung utara sejati serta data pengukuran.
- Catatan observasi dan ekspor laporan.

MENJALANKAN APLIKASI
1. Ekstrak ZIP dan buka folder SIMPANAN di VS Code.
2. Jalankan index.html melalui Live Server atau server lokal.
3. Untuk GPS, sensor, dan peta daring, gunakan HTTPS/localhost dan izinkan akses yang diminta.

CATATAN AKURASI
- Saat offline, koordinat GPS tetap dapat digunakan; nama tempat mungkin tidak tersedia.
- UTC (UTC+0) adalah zona waktu yang valid.
- Posisi Matahari merupakan model astronomis komputasional, bukan pembacaan kamera.
- Utara sejati berbeda dari utara magnetik (kompas) dan arah atas layar/peta.
- Hasil bergantung pada koordinat, jam perangkat, zona waktu, metode, dan kondisi pengamatan.
- Jangan melihat Matahari melalui teleskop/binokular tanpa filter Matahari khusus.

KONFIGURASI
- Lokasi bawaan dan koordinat Ka'bah berada di config.js.
- Peta dan reverse geocoding memerlukan koneksi internet.
