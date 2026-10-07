# Vice Side Roleplay — Android Client

Repositori ini berisi workflow otomasi build CI/CD (GitHub Actions) dan skrip penyiapan untuk menghasilkan **APK Klien Ramping (< 200 MB)** SA:MP Mobile / open.mp untuk **Vice Side Roleplay**, dengan sistem pengunduhan data game langsung (*in-app downloader*), dukungan resume otomatis (*HTTP Range*), dan impor manual via ZArchiver.

---

## 🚀 Fitur & Konfigurasi Klien

1. **1 Server Terkunci (Single-Server Mode):**
   - Host: `142.132.203.47`
   - Port: `10125`
   - Server Name: `Vice Side Roleplay`
   - UI launcher untuk menambah, mengedit, atau menghapus server dinonaktifkan secara permanen.

2. **Login Google UCP (CEF Bridge):**
   - Menggunakan alur CEF (*Chromium Embedded Framework*) in-game yang terhubung langsung ke backend Vercel (`GET /auth/google`).
   - Tidak memerlukan Google Sign-In SDK native di launcher Android.

3. **Layar Terkunci Landscape:**
   - Semua activity dikunci permanen pada orientasi `landscape` baik melalui `AndroidManifest.xml` maupun runtime enforcement (`setRequestedOrientation`).

4. **APK Ramping & Unduh Data Otomatis (Resume HTTP Range):**
   - APK tidak membundel data game sebesar 1.8 GB di dalam aset (`assets/game_data/` dihilangkan sepenuhnya), sehingga ukuran APK di bawah **200 MB**.
   - Saat aplikasi pertama kali dibuka (`EntryActivity`), client memeriksa `data-manifest.json` rilis resmi dan mengunduh paket data game tunggal (`CRMP.zip`, 1.07 GB) menggunakan engine **PRDownloader**.
   - **Resume Wajib:** Jika koneksi terputus atau aplikasi ditutup di tengah jalan, unduhan akan melanjutkan dari **byte terakhir** (`Range: bytes=offset-`), bukan mulai dari nol.
   - Status unduhan menampilkan: MB/MB, persentase %, kecepatan (MB/s), estimasi waktu selesai (ETA), serta tombol **BATAL / JEDA** (menyimpan posisi byte untuk dilanjutkan nanti).

5. **Dukungan Impor Manual ZArchiver (`Documents/SampMobile/`):**
   - Di Android 11+, folder `Android/data/` dibatasi oleh sistem sehingga aplikasi pihak ketiga (seperti ZArchiver) umumnya tidak dapat mengekstrak langsung ke sana.
   - Client menyediakan folder impor publik: `/storage/emulated/0/Documents/SampMobile/`.
   - Tombol **"Impor dari Folder"** memindai folder tersebut, memverifikasi kesesuaian **ukuran + SHA-256 byte-per-byte** terhadap manifest resmi, memindahkan file secara aman, dan langsung mengekstraknya tanpa perlu mengunduh lagi.
   - Tombol **"Salin Jalur"** memudahkan penyalinan alamat folder langsung ke clipboard pengguna.
   - Jika pengguna memodifikasi salah satu file, client akan menolak file yang tidak cocok dan hanya mengunduh file pengganti resmi yang diperlukan.

6. **Rilis Otomatis & Signed APK:**
   - Push tag versi (contoh: `v1.0.2`) secara otomatis memicu GitHub Actions untuk memvalidasi manifest, membangun APK, menandatangani (*sign*), dan mengunggahnya ke GitHub Releases.

---

## 🎮 Alur Pembaruan & Data Game (Manifest)

Sumber kebenaran pembaruan data game dikendalikan oleh file **`data-manifest.json`**:
URL Resmi: `https://github.com/tohbobo51/samp-game-data/releases/latest/download/data-manifest.json`

Format:
```json
{
  "version": 1,
  "title": "Vice Side Data v1",
  "files": [
    {
      "id": "crmp",
      "url": "https://github.com/tohbobo51/samp-game-data/releases/download/v1.0/CRMP.zip",
      "size": 1074673867,
      "sha256": "4854d4176df5a8da3da17bf4aaf58e374c395ab0e1cb68be0a83ab0f6889c7ec",
      "extract_to": "."
    }
  ]
}
```

### Cara Merilis Pembaruan Data Game:
1. Unggah berkas data baru/tambahan ke rilis `samp-game-data`.
2. Hitung ukuran (*size*) dalam byte dan SHA-256 dari berkas tersebut (`sha256sum <file>`).
3. Perbarui `data-manifest.json`:
   - Naikkan nilai integer `"version"` (misal dari `1` ke `2`).
   - Perbarui atau tambahkan entri berkas pada daftar `"files"`.
4. Unggah `data-manifest.json` terbaru ke rilis.
5. Client yang dibuka pengguna akan mendeteksi kenaikan versi, melewatkan berkas yang checksum-nya sudah cocok, dan hanya mengunduh berkas yang berubah atau baru. Berkas zip usang yang tidak ada di manifest akan otomatis dibersihkan dari penyimpanan.

---

## 📁 Panduan Impor Manual Menggunakan ZArchiver

Bagi pemain dengan kuota terbatas atau yang ingin menyalin data secara offline:
1. Unduh `CRMP.zip` (1.07 GB) dari rilis resmi.
2. Buka aplikasi **ZArchiver**.
3. Buat folder `SampMobile` di dalam folder `Documents` penyimpanan internal (`/storage/emulated/0/Documents/SampMobile/`).
4. Salin file `CRMP.zip` (atau ekstrak isinya) ke dalam folder `/storage/emulated/0/Documents/SampMobile/`.
5. Buka game **Vice Side Roleplay** → Pada layar pembaruan, klik tombol **"Impor dari Folder"**.
6. Client akan memvalidasi keaslian file (SHA-256):
   - Jika berkas cocok 100%, data akan dipindahkan dan diekstrak langsung ke direktori game tanpa mengunduh dari internet sama sekali.
   - Jika berkas telah dimodifikasi atau rusak, client akan menolak berkas tersebut dan otomatis mengunduh berkas asli.

---

## ⚠️ Catatan Kritis: Varian GPU (DXT vs ETC / PVR)

- **Karakteristik Paket `CRMP.zip` Saat Ini:**
  - `CRMP.zip` **hanya memuat varian `*.dxt.*` (27 berkas)** untuk seluruh basis data tekstur di `texdb/*`.
  - Format tekstur **DXT** kompatibel penuh pada GPU **Adreno** (Qualcomm Snapdragon) dan mayoritas perangkat modern.
  - Namun, terdapat potensi risiko tekstur berwarna hitam (*black texture*) atau gagal render pada GPU **Mali lama** atau **PowerVR** yang membutuhkan format kompresi tekstur **ETC** (`*.etc.*`) atau **PVR** (`*.pvr.*`).
- **Rekomendasi & Pengujian:**
  - Klien telah diuji dan berjalan optimal pada perangkat ber-GPU Adreno. Jika pemain dengan GPU Mali/PowerVR mengalami tekstur hitam, laporkan tipe chipset/GPU ke tim pengembang.
- **Jalur Cepat Menambahkan Varian ETC / PVR ke Rilis Berikutnya:**
  - Jika diperlukan dukungan penuh multi-GPU di masa mendatang, cukup salin folder tekstur varian `.etc.` dan `.pvr.` dari arsip base cache (`gtasa.2.10.cache.zip`) ke dalam arsip `CRMP.zip` (atau rilis sebagai patch zip terpisah di `data-manifest.json`).
  - Struktur klien **tidak perlu diubah sama sekali**, karena `GameDataVerifier` di dalam klien sudah secara bawaan mendukung pemeriksaan `hasTextureSet(..., "dxt" | "etc" | "pvr")`.

---

## 📱 Panduan Instalasi & Mengatasi Masalah "Aplikasi Tidak Terpasang"

Jika Anda mengalami kendala saat menginstal APK (*App not installed* / *Aplikasi tidak terpasang*):

1. **Copot Pemasangan (Uninstall) Versi Lama Terlebih Dahulu (Wajib):**
   - Jika di perangkat Anda sebelumnya sudah terinstal versi rilis terdahulu (seperti  atau APK dari build sebelumnya), Android akan menolak pemasangan pembaruan secara otomatis (*INSTALL_FAILED_UPDATE_INCOMPATIBLE*) karena perbedaan tanda tangan digital (*signature key*).
   - **Solusi:** Hapus/Uninstall aplikasi Vice Side yang ada di HP Anda terlebih dahulu, kemudian pasang APK yang baru.
2. **Peringatan Google Play Protect:**
   - Karena APK didistribusikan secara mandiri (bukan lewat Google Play Store), Play Protect mungkin akan menampilkan peringatan keamanan saat instalasi.
   - **Solusi:** Ketuk **Detail selengkapnya (More details)** lalu pilih **Tetap instal (Install anyway)**.
3. **Kompatibilitas Perangkat (Arsitektur 32-bit ):**
   - Mesin GTA San Andreas Mobile dan SA-MP dibangun menggunakan library native 32-bit (). Perangkat flagship generasi terbaru yang hanya mendukung 64-bit murni (*64-bit-only*, seperti Google Pixel 7/8/9) tidak dapat menginstal aplikasi 32-bit.

---

## 🛠️ GitHub Actions Secrets (Keystore & Release)

Untuk menghasilkan APK rilis resmi yang tertandatangani (*signed*), atur Secrets berikut pada menu **Settings > Secrets and variables > Actions**:

| Secret Name | Deskripsi | Contoh / Cara Mendapatkan |
|---|---|---|
| `KEYSTORE_BASE64` | File Keystore (`.jks` / `.keystore`) dalam format Base64 | `base64 -w 0 release.jks` |
| `KEYSTORE_PASSWORD` | Kata sandi Keystore | Kata sandi saat membuat Keystore |
| `KEY_ALIAS` | Alias key di dalam Keystore | Contoh: `viceside` |
| `KEY_PASSWORD` | Kata sandi key alias | Kata sandi key (jika berbeda dengan keystore) |

> **Catatan:** Jika `KEYSTORE_BASE64` belum disetel, workflow otomatis membuat keystore self-signed fallback agar proses build dan pengujian APK tetap berjalan tanpa hambatan.

---

## 🏷️ Memicu Rilis Baru

Untuk membuat rilis APK baru:
```bash
git tag v1.0.2
git push origin v1.0.2
```
Workflow GitHub Actions akan memvalidasi manifest, membangun APK (< 200 MB), memverifikasi ketiadaan bundel aset game internal, menandatangani APK, dan mengunggahnya ke GitHub Releases.
