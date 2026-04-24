# Somniac Artificial Consciousness - Master Implementation Plan

## 1. Project Architecture & Tech Stack

Sistem akan dibagi menjadi tiga komponen utama untuk memisahkan beban kerja dan mempermudah deployment:

- **Frontend (Main Web & Lab)**: Vite + React/Next.js, dijalankan dengan Bun untuk performa maksimal.
- **Backend (Core API & AC Engine)**: Python (FastAPI) untuk logic state machine AI dan kalkulasi model, digabung dengan Cloudflare Workers sebagai API Gateway.
- **WhatsApp Service**: Node.js/Bun microservice menggunakan library Baileys atau whatsapp-web.js untuk menjaga sesi koneksi Web Socket tetap hidup.

---

## 2. Repository & Deployment Routing

Routing akan dipetakan secara spesifik sesuai repositori untuk Continuous Integration / Continuous Deployment (CI/CD):

### Repo `Jeflacc/whatsapp-ai-frontend`:
- **Domain Utama**: `somniac.me` (Company Profile, News, Research).
- **Subdomain**: `lab.somniac.me` (The AC Playground).
- **Deployment**: Push ke `main` otomatis build menggunakan GitHub Actions dan di-deploy ke Cloudflare Pages.

### Repo `Jeflacc/whatsapp-ai-backend`:
- **Domain**: `api.somniac.me` (Endpoint utama) dan `wa.somniac.me` (WhatsApp service).
- **Deployment**: Push ke `main` akan memicu deploy Cloudflare Workers (untuk API ringan) dan deploy ke VPS/PaaS (seperti Railway/Render) untuk engine Python dan WhatsApp service yang butuh uptime 24/7.

---

## 3. Database & User Memory Isolation

Memastikan setiap pengguna memiliki instansi AI yang terisolasi secara memori dan state:

- **Relational Database (PostgreSQL)**: Menggunakan Supabase atau Neon. Menyimpan tabel `users`, `ai_instances`, dan `chat_history`.
- **Row Level Security (RLS)**: Diaktifkan secara default. Data AI milik `user_A` tidak akan pernah bisa diakses oleh `user_B`.
- **Vector Database (Pinecone/Qdrant)**: Menyimpan "ingatan jangka panjang" AI. Data dipisahkan menggunakan fitur Namespace (satu `user_id` = satu namespace).

---

## 4. Authentication & Security

- **Provider**: Clerk atau Supabase Auth.
- **Flow**: Pengguna masuk ke `lab.somniac.me`, melakukan registrasi via Google/Email, lalu sistem membuatkan `user_id` unik dan generate instansi AI baru (Evelyn/AURA) di database.
- **API Security**: Semua request dari frontend ke backend harus menyertakan JWT Bearer Token di header.

---

## 5. Frontend Features: The AC Playground

Halaman `lab.somniac.me` dirancang layaknya dashboard tingkat industri:

- **Dynamic Pages**: Sistem URL `/lab/chat/[session_id]` untuk multi-obrolan.
- **Left Sidebar**: Navigasi riwayat obrolan (History), Settings, dan integrasi perangkat.
- **Center Panel**: UI obrolan utama tempat user berinteraksi dengan AI.
- **Right Sidebar (AC Dashboard)**: Menampilkan variabel real-time AI:
  - **Biology**: Indikator energi, tingkat rasa lapar (komputasi), dan fokus.
  - **Mood**: Status emosional saat ini (misal: Analytic, Tired, Curious).
  - **Current Activity**: Menampilkan apa yang AI sedang lakukan di background (misal: "Idle", "Processing memories", "Reading news").

---

## 6. WhatsApp Integration Pipeline

Fitur menyambungkan "otak" AI dari dashboard ke nomor WhatsApp pribadi/bisnis:

- **QR Code Generation**: Di dashboard `lab.somniac.me/integrations/whatsapp`, frontend meminta backend untuk generate QR Code.
- **Scanning Process**: User melakukan scan menggunakan aplikasi WhatsApp di HP mereka.
- **Session Management**: Kredensial login WhatsApp dienkripsi dan disimpan di database dengan referensi ke `user_id`.
- **Message Routing**: Saat ada pesan masuk ke nomor WA tersebut, microservice akan menangkap teksnya, mengirimkannya ke backend AC Engine bersama `user_id`, lalu AI membalas langsung ke WhatsApp pengirim.

---

## 7. Main Website: The "OpenAI" Look

Halaman `somniac.me` difokuskan untuk branding dan public relations:

- **Design Language**: UI bersih, minimalis, tipografi tegas, dan dark mode (menggunakan Tailwind CSS & shadcn/ui) dengan sentuhan **neubrutalism**.
- **News & Research Section**: Terhubung dengan Headless CMS (Sanity/Payload) agar tim bisa mempublikasikan pembaruan teknis atau paper riset tentang machine consciousness dengan mudah.
