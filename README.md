# Murugan Impex™ — Dental Platform & Knowledge Hub (Supabase Edition)

> Complete migration from **Firebase to Supabase**.
> Preserves 100% of the UI design while providing a production-grade PostgreSQL backend, Supabase Auth, Row Level Security (RLS), Supabase Storage, and Supabase Realtime.

---

## 🚀 Key Implemented Features

### 1. 🔐 Authentication & Profiles (Supabase Auth)
- **Email & Password Login / Signup** with dental doctor & clinic fields:
  - Doctor Name, Clinic Name, DCI Registration Number, Clinic GSTIN, Phone, Address.
- **Google OAuth** Workspace sign-in via `supabase.auth.signInWithOAuth`.
- **Automatic Profile Synchronization**: A database trigger on `auth.users` automatically inserts/updates the `public.profiles` table upon signup.
- **Role-Based Access Control**: `free`, `premium`, and `admin` roles enforced server-side.

### 2. 💳 Payment & Subscription System
- **Pricing Tiers**:
  - *Monthly Practice*: ₹1,499 / month + 18% GST (ITC claimable).
  - *Annual Fellowship*: ₹12,999 / year (Save ₹5,989/year).
- **Server-Side Verification**:
  - `supabase/functions/verify-payment/index.ts`: Edge function that verifies transaction integrity using server secrets, records completed transactions in `public.payments`, and elevates user roles in `public.subscriptions` and `public.profiles`.
  - `supabase/functions/stripe-webhook/index.ts`: Receives asynchronous Stripe webhooks (`checkout.session.completed`, `customer.subscription.deleted`).
  - **Secrets are NEVER exposed to the frontend**.

### 3. 📚 Premium & Paid Clinical Content
- **Access Control via RLS**:
  - Free published articles are readable by anyone (guests & members).
  - Premium surgical masterclasses, all-on-4/6 protocols, and CAD/CAM guides require an active `premium` subscription or `admin` role checked directly by the database policy `is_premium_or_admin()`.
- Interactive Article Reader with downloadable clinical protocol PDFs and Certificates of Analysis (CoAs).

### 4. 📊 Admin Dashboard (`admin.html`)
- **Restricted Access**: Enforces `requireAdminAccess()` and database security definer `is_admin()`.
- **KPI Metrics**: Realtime metrics for registered clinics, active fellowships, dispatched cargo orders, and ARR.
- **User Management**: View doctor profiles, DCI numbers, clinic GSTINs, and promote/demote user tiers (`free`, `premium`, `admin`).
- **Content Management**: Form to author and publish new clinical articles with custom slugs, categories, and free/premium gating.
- **Orders & Logistics**: Manage clinic cargo orders, view GST breakdown, and update shipment status (`processing`, `dispatched`, `in_transit`, `delivered`).
- **Payment Telemetry**: Live transaction ledger.
- **Storage Explorer**: View objects across `clinical-files`, `content-media`, and `avatars`.
- **Support Desk**: Live chat monitor to converse with doctors in real time.

### 5. 📁 Supabase Storage
- **Configured Storage Buckets**:
  - `clinical-files`: Authenticated uploads for doctor case studies, X-rays, and CBCT scans.
  - `content-media`: Publicly viewable article illustrations and procedure photos.
  - `avatars`: User clinic profile photos.
  - `invoices`: Computerized GST tax invoices.
- File upload tracker in `public.files` table.

### 6. 💬 Comments & Realtime Live Chat (Supabase Realtime)
- **Discussion on Articles**:
  - When a doctor submits a comment or clinical query, it broadcasts via `supabase.channel('public:comments')` and updates other readers' screens in real time without refreshing.
- **Support Chat**:
  - Realtime messaging between doctors and the Murugan Impex clinical desk.

### 7. 🛒 Orders, Order History & Order Status
- **Storefront Checkout**: When an order is placed from the Amazon-style cart in `index.html`:
  - Saves the order to `public.orders` with AWB number and GST invoice reference.
  - Saves line items to `public.order_items`.
- **Order History**: In `dashboard.html`, doctors view all past orders, courier tracking (BlueDart Medical Cold-Chain), and download computerized tax invoices.

---

## 🗄️ Database Setup Instructions

1. Log into your [Supabase Dashboard](https://supabase.com/dashboard).
2. Open the **SQL Editor**.
3. Open `supabase-schema.sql` from this project, copy its entire contents, and click **Run**.
4. The script will:
   - Create tables: `profiles`, `subscriptions`, `payments`, `premium_content`, `orders`, `order_items`, `comments`, `chat_messages`, `files`.
   - Setup triggers, functions (`is_admin`, `is_premium_or_admin`).
   - Enable Row Level Security (RLS) and apply all security policies.
   - Create storage buckets (`clinical-files`, `content-media`, `avatars`, `invoices`).
   - Enable Supabase Realtime publication on `comments`, `chat_messages`, and `orders`.
   - Seed initial free and premium clinical guides.

---

## ⚙️ Environment Variables & Configuration

Copy `.env.example` to `.env` or set environment variables:

```env
# Frontend (Client-Safe)
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGciOi...
STRIPE_PUBLISHABLE_KEY=pk_test_...

# Supabase Edge Functions & Secrets (Server-Side ONLY)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOi...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

*Note: In the browser, you can also click the floating **⚡ Supabase Status Pill** at the bottom-left of the screen to dynamically enter your Supabase URL and Anon Key.*

---

## 🚢 Deploying Supabase Edge Functions

Install the Supabase CLI and run:

```bash
# Deploy verify-payment function
supabase functions deploy verify-payment --project-ref your-project-ref

# Deploy stripe-webhook function
supabase functions deploy stripe-webhook --project-ref your-project-ref

# Set secrets in Supabase
supabase secrets set STRIPE_SECRET_KEY=sk_test_... SUPABASE_SERVICE_ROLE_KEY=...
```

---

## 📂 Project Structure

```
├── admin.html               # Admin Dashboard (Users, Orders, Content, Payments, Storage)
├── app.js                   # E-Commerce storefront logic with Supabase order creation
├── assets/images/           # High-resolution clinical and product images
├── auth.js                  # Shared Supabase Auth, DB, Realtime & Storage module
├── dashboard.html           # Doctor/Clinic Portal (Profile, Orders, Storage, Chat)
├── index.html               # Main E-Commerce Storefront (CDSCO certified dental imports)
├── knowledge.css            # Stylesheet for Knowledge Hub and clinical portals
├── knowledge.html           # Dental Knowledge Hub homepage (Free guides & reviews)
├── knowledge.js             # Knowledge Hub logic with Supabase Realtime comments
├── login.html               # Clinic Login & Registration portal
├── payment-success.html     # Post-payment verification and activation
├── premium-content.html     # Gated Fellowship surgical masterclasses
├── pricing.html             # Subscription plans and checkout
├── styles.css               # Storefront Amazon-style stylesheet
├── supabase-config.js       # Supabase client initialization & environment loader
├── supabase-schema.sql      # Complete PostgreSQL migration schema with RLS
└── supabase/
    ├── config.toml          # Supabase CLI project config
    └── functions/
        ├── verify-payment/  # Server-side payment verification Edge Function
        └── stripe-webhook/  # Stripe event receiver Edge Function
```
