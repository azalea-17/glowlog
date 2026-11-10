# Panduan Langkah Lengkap (checklist pengerjaan)

Urutan yang disarankan. Semua perintah dijalankan di laptop Anda (butuh Docker Desktop + Git).

## 0. Persiapan
1. Install **Docker Desktop** dan **Git**. Cek: `docker --version`, `docker compose version`, `git --version`.
2. Atur identitas Git: `git config --global user.name "Nama Anda"` dan `git config --global user.email "email@anda"`.

## 1. Ambil kode dan jalankan di localhost
```bash
cd glowlog                      # folder projek ini
cp .env.example .env            # lalu ganti POSTGRES_PASSWORD
docker compose up -d --build
docker compose ps               # tunggu db & redis = healthy
```
Buka http://localhost:8000. Jika port 8000 terpakai, ubah `APP_PORT` di `.env`.

## 2. Ambil bukti (screenshot untuk PDF, README, artikel)
| # | Perintah / tindakan | Simpan sebagai |
|---|---|---|
| 1 | Browser http://localhost:8000 setelah menambah 2 rutinitas | `docs/screenshots/01-app.png` |
| 2 | `docker compose ps` | `docs/screenshots/02-compose-ps.png` |
| 3 | `curl -i http://localhost:8000/health` lalu POST (201) dan GET (200, `MISS` lalu `HIT`) | `docs/screenshots/03-curl.png` |
| 4 | Tambah data → `docker compose down` → `docker compose up -d` → data masih ada | `docs/screenshots/04-persistence.png` |
| 5 | `docker images glowlog-web` (ukuran image, tempel juga ke PDF 2b) | `docs/screenshots/05-images.png` |
| 6 | (opsional) `docker compose --profile tools up -d` → http://localhost:8080 | `docs/screenshots/06-adminer.png` |

Perintah POST untuk bukti 201:
```bash
curl -i -X POST http://localhost:8000/api/routines -H "Content-Type: application/json" \
  -d '{"title":"Weekday glow","period":"morning","products":"Cleanser -> SPF"}'
```
Gunakan data **dummy** saja. Jangan tampilkan isi `.env`.

## 3. Personalisasi (wajib, agar menjadi karya Anda)
* Ganti placeholder `<NAMA> <NIM> <KELAS> <LINK...>` di `README.md`.
* Baca `docs/video-script.md` bagian A dan B sampai Anda bisa menjelaskan **setiap baris** Dockerfile dan Compose dengan kata sendiri (syarat video).
* Sesuaikan paragraf **AI Usage Declaration** di README agar jujur sesuai yang Anda lakukan.
* Tambah motivasi pribadi di jawaban 1a dan artikel.

## 4. GitHub (public, dibuat selama periode ujian)
1. Buat repo kosong **Public** bernama `glowlog` di github.com (jangan centang README/.gitignore).
2. Riwayat commit sudah disiapkan (7+ commit bertahap). Agar commit tercatat atas nama Anda:
```bash
git rebase -r --root --exec 'git commit --amend --reset-author --no-edit'
```
3. Lanjutkan commit bertahap untuk perubahan Anda (screenshot, README), lalu:
```bash
git remote add origin https://github.com/USERNAME/glowlog.git
git push -u origin main
```
4. Cek `git ls-files | grep -i env` → hanya `.env.example`. Cek repo dalam jendela incognito (harus terbuka tanpa login).

## 5. Video YouTube
Rekam mengikuti `docs/video-script.md` (3–5 menit, suara sendiri, Public). Tempel tautan GitHub + artikel di deskripsi.

## 6. Artikel
Edit `docs/article.md` (isi placeholder, tambah screenshot), terbitkan di Medium / dev.to / Hashnode / LinkedIn Article. Pastikan publik dan tanpa paywall. Gambar diagram: `docs/architecture.png`.

## 7. Isi README dengan tautan artikel dan video, commit, push.

## 8. Bonus (+5): Redis cache sudah dibuat
Tunjukkan di video: header `X-Cache: MISS` lalu `HIT`, serta `docker compose ps` yang memperlihatkan redis `healthy`.
Opsional bonus kedua (+5, total maks +10): push ke Docker Hub
```bash
docker login
docker tag glowlog-web:1.0.0 USERNAME/glowlog-web:1.0.0
docker tag glowlog-web:1.0.0 USERNAME/glowlog-web:latest
docker push USERNAME/glowlog-web:1.0.0 && docker push USERNAME/glowlog-web:latest
```

## 9. PDF pengumpulan
Buka `UTS_COMP6991031_NIM_Nama_EDITABLE.docx`, isi identitas, tautan, tempel screenshot dan output `docker images`, lalu **Export PDF** dengan nama
`UTS_COMP6991031_<NIM>_<Nama>.pdf` dan unggah di exam apps.

## 10. Checklist akhir
- [ ] `git clone` repo di folder baru + `cp .env.example .env` + `docker compose up -d --build` berhasil
- [ ] Repo, artikel, video terbuka tanpa login (cek incognito)
- [ ] Tidak ada secret / data pribadi di commit, screenshot, atau video
- [ ] Tiga tautan tercantum di PDF
