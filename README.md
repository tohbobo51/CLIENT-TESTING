# Vice Side Roleplay — Android Client (All-in-One)

Repositori ini berisi workflow otomasi build dan skrip penyiapan untuk menghasilkan **satu file APK All-in-One** klien SA:MP Mobile / open.mp untuk **Vice Side Roleplay**.

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
4. **All-in-One APK (Offline First-Run Extraction):**
   - Seluruh data game (`gtasa.2.10.cache.zip` dan `CRMP.zip`) dibundel langsung di dalam aset APK (`assets/game_data/`).
   - Saat pertama kali aplikasi dibuka (`EntryActivity`), file diekstrak secara otomatis ke penyimpanan lokal (`Android/data/com.xyron.game/files`) dengan progress bar interaktif, verifikasi integritas, dan mekanisme penulisan aman (`.part` atomic rename).
   - Seluruh unduhan eksternal pihak ketiga (HuggingFace / server eksternal) telah dinonaktifkan.
5. **Rilis Otomatis & Signed APK:**
   - Push tag versi (contoh: `v1.0.0`) secara otomatis memicu GitHub Actions untuk memvalidasi isi APK, menandatangani (*sign*), dan mengunggahnya ke GitHub Releases.

---

## 🛠️ GitHub Actions Secrets (Keystore & Release)

Untuk menghasilkan APK rilis resmi yang tertandatangani (*signed*), atur Secrets berikut pada menu **Settings > Secrets and variables > Actions**:

| Secret Name | Deskripsi | Contoh / Cara Mendapatkan |
|---|---|---|
| `KEYSTORE_BASE64` | File Keystore (`.jks` / `.keystore`) dalam format Base64 | `base64 -w 0 release.jks` |
| `KEYSTORE_PASSWORD` | Kata sandi Keystore | Kata sandi saat membuat Keystore |
| `KEY_ALIAS` | Alias key di dalam Keystore | Contoh: `viceside` |
| `KEY_PASSWORD` | Kata sandi key alias | Kata sandi key (jika berbeda dengan keystore) |
| `RELEASE_UPLOAD_URL` *(Opsional)* | Endpoint CDN/VPS untuk upload file jika ukuran APK > 2 GiB | `https://cdn.viceside.com/api/upload` |

> **Catatan:** Jika `KEYSTORE_BASE64` belum disetel, workflow otomatis membuat keystore self-signed fallback agar proses build dan pengujian APK tetap berjalan tanpa hambatan.

---

## 📦 Ukuran APK & Persyaratan Perangkat

- **Ukuran File APK:** ± 1.95 – 2.00 GB (seluruh data GTA SA dan CRMP dibundel uncompressed `noCompress 'zip'` agar cepat saat ekstraksi).
- **Ruang Kosong Perangkat yang Dibutuhkan:** **Minimal 4.0 GB**.
  - ± 2 GB untuk file APK yang terpasang.
  - ± 1.8 GB untuk data permainan yang diekstrak ke direktori aplikasi.
- **Batasan Arsitektur 32-Bit (`armeabi-v7a`):**
  - Library native (`libGTASA.so`, `libomp_component_*.so`, `libomp_server_arm.so`) adalah binari 32-bit ARM.
  - Sebagian perangkat generasi terbaru dengan sistem operasi atau chipset yang hanya mendukung 64-bit (*64-bit-only without 32-bit execution support*) tidak dapat memasang atau menjalankan klien ini secara native.

---

## 🔧 Alur Kerja Build (GitHub Actions)

Workflow didefinisikan di `.github/workflows/build-apk.yml`:
1. Mengambil kode sumber klien rilis `Source.Code.Samp.v1.2.zip`.
2. Menerapkan patch CEF dan kunci server via `scripts/prepare_client.py`.
3. Menerapkan pengaman single-server, ekstraktor first-run, pengunci orientasi landscape, dan konfigurasi signing via `scripts/patch_single_server.py`.
4. Mengunduh dan memverifikasi data game `gtasa.2.10.cache.zip` dan `CRMP.zip` (dicache via `actions/cache`).
5. Mengoptimalkan gambar drawable ke format WebP via `scripts/optimize_drawables.py`.
6. Melakukan kompilasi `assembleRelease` dengan Gradle 8.6 & JDK 21.
7. Memverifikasi isi APK (`aapt dump badging`, orientasi landscape, kelengkapan `.so` 32-bit, `apksigner verify`).
8. Mengunggah artifact dan membuat GitHub Release otomatis saat push tag `v*`.

---

## 🏷️ Memicu Rilis Baru

Untuk membuat rilis APK baru:
```bash
git tag v1.0.1
git push origin v1.0.1
```
Workflow GitHub Actions akan otomatis berjalan dan menghasilkan file APK siap pasang.
