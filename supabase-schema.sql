-- ==============================================================================
-- MURUGAN IMPEX — DENTAL PLATFORM & KNOWLEDGE HUB
-- SUPABASE POSTGRESQL PRODUCTION DATABASE SCHEMA
-- ==============================================================================
-- Complete migration from Firebase to Supabase
-- Includes:
-- 1. Profiles & Custom Claims (Free / Premium / Admin)
-- 2. Subscriptions & Payments
-- 3. Premium Content with Tier Gating
-- 4. Clinical Orders & GST Order Items
-- 5. Realtime Comments & Realtime Live Chat
-- 6. Storage Files Tracker & Bucket Policies
-- 7. Full Row-Level Security (RLS) & Helper Security Definers
-- 8. Realtime Replication Publications
-- ==============================================================================

-- Enable UUID extension if not already active
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ------------------------------------------------------------------------------
-- 1. PROFILES TABLE (Extends Supabase auth.users)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  email TEXT NOT NULL,
  full_name TEXT,
  phone TEXT,
  clinic_name TEXT,
  dci_number TEXT,                 -- Dental Council of India registration
  gstin TEXT,                      -- Clinic GST Number
  address TEXT,
  city TEXT,
  state TEXT,
  pincode TEXT,
  role TEXT NOT NULL DEFAULT 'free' CHECK (role IN ('free', 'premium', 'admin')),
  avatar_url TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- Trigger to auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION public.handle_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = timezone('utc'::text, now());
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS on_profiles_updated ON public.profiles;
CREATE TRIGGER on_profiles_updated
  BEFORE UPDATE ON public.profiles
  FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();

-- Trigger to automatically insert a profile when a new user signs up in auth.users
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.profiles (
    id,
    email,
    full_name,
    phone,
    clinic_name,
    dci_number,
    gstin,
    role
  ) VALUES (
    NEW.id,
    NEW.email,
    COALESCE(NEW.raw_user_meta_data->>'full_name', NEW.raw_user_meta_data->>'name', split_part(NEW.email, '@', 1)),
    COALESCE(NEW.raw_user_meta_data->>'phone', ''),
    COALESCE(NEW.raw_user_meta_data->>'clinic_name', ''),
    COALESCE(NEW.raw_user_meta_data->>'dci_number', ''),
    COALESCE(NEW.raw_user_meta_data->>'gstin', ''),
    CASE 
      WHEN NEW.email IN ('admin@muruganimpex.in', 'yuvas@muruganimpex.in') THEN 'admin'
      ELSE 'free'
    END
  )
  ON CONFLICT (id) DO UPDATE
  SET
    email = EXCLUDED.email,
    full_name = COALESCE(EXCLUDED.full_name, public.profiles.full_name);
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- Helper function: Check if current authenticated user is an Admin
CREATE OR REPLACE FUNCTION public.is_admin()
RETURNS BOOLEAN AS $$
BEGIN
  RETURN EXISTS (
    SELECT 1 FROM public.profiles
    WHERE id = auth.uid() AND role = 'admin'
  );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER STABLE;

-- Helper function: Check if current authenticated user is Premium or Admin
CREATE OR REPLACE FUNCTION public.is_premium_or_admin()
RETURNS BOOLEAN AS $$
BEGIN
  RETURN EXISTS (
    SELECT 1 FROM public.profiles p
    LEFT JOIN public.subscriptions s ON s.user_id = p.id AND s.status = 'active' AND s.current_period_end > now()
    WHERE p.id = auth.uid() AND (p.role IN ('premium', 'admin') OR s.id IS NOT NULL)
  );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER STABLE;

-- ------------------------------------------------------------------------------
-- 2. SUBSCRIPTIONS TABLE
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.subscriptions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
  plan TEXT NOT NULL CHECK (plan IN ('monthly', 'annual', 'lifetime')),
  status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'cancelled', 'expired', 'past_due')),
  amount NUMERIC(10, 2) NOT NULL,
  currency TEXT NOT NULL DEFAULT 'INR',
  current_period_start TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
  current_period_end TIMESTAMPTZ NOT NULL,
  stripe_customer_id TEXT,
  stripe_subscription_id TEXT,
  stripe_session_id TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

DROP TRIGGER IF EXISTS on_subscriptions_updated ON public.subscriptions;
CREATE TRIGGER on_subscriptions_updated
  BEFORE UPDATE ON public.subscriptions
  FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();

-- ------------------------------------------------------------------------------
-- 3. PAYMENTS TABLE
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.payments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
  order_id UUID,
  subscription_id UUID REFERENCES public.subscriptions(id) ON DELETE SET NULL,
  amount NUMERIC(10, 2) NOT NULL,
  currency TEXT NOT NULL DEFAULT 'INR',
  status TEXT NOT NULL DEFAULT 'completed' CHECK (status IN ('pending', 'completed', 'failed', 'refunded')),
  payment_method TEXT DEFAULT 'stripe_card',
  payment_intent_id TEXT,
  invoice_number TEXT,
  receipt_url TEXT,
  description TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- ------------------------------------------------------------------------------
-- 4. PREMIUM CONTENT / CLINICAL GUIDES
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.premium_content (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title TEXT NOT NULL,
  slug TEXT UNIQUE NOT NULL,
  category TEXT NOT NULL,
  tier TEXT NOT NULL DEFAULT 'free' CHECK (tier IN ('free', 'premium')),
  read_time TEXT DEFAULT '15 min',
  content_type TEXT DEFAULT 'Article',
  rating NUMERIC(3, 1) DEFAULT 4.9,
  excerpt TEXT NOT NULL,
  full_content TEXT NOT NULL,
  thumbnail_url TEXT,
  download_file_url TEXT,
  download_badge TEXT,
  published BOOLEAN NOT NULL DEFAULT true,
  author_name TEXT DEFAULT 'Dr. Murugan Impex Clinical Panel',
  created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

DROP TRIGGER IF EXISTS on_premium_content_updated ON public.premium_content;
CREATE TRIGGER on_premium_content_updated
  BEFORE UPDATE ON public.premium_content
  FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();

-- ------------------------------------------------------------------------------
-- 5. ORDERS TABLE (E-Commerce Storefront)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.orders (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  order_reference TEXT UNIQUE NOT NULL,
  user_id UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
  doctor_name TEXT NOT NULL,
  clinic_name TEXT NOT NULL,
  dci_number TEXT,
  gstin TEXT,
  shipping_address TEXT NOT NULL,
  shipping_city TEXT NOT NULL,
  shipping_state TEXT NOT NULL,
  shipping_pincode TEXT NOT NULL,
  awb_number TEXT NOT NULL,
  courier TEXT DEFAULT 'BlueDart Medical Express (Cold-Chain)',
  subtotal NUMERIC(10, 2) NOT NULL,
  gst_amount NUMERIC(10, 2) NOT NULL,
  total_amount NUMERIC(10, 2) NOT NULL,
  status TEXT NOT NULL DEFAULT 'processing' CHECK (status IN ('processing', 'dispatched', 'in_transit', 'delivered', 'cancelled')),
  invoice_number TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

DROP TRIGGER IF EXISTS on_orders_updated ON public.orders;
CREATE TRIGGER on_orders_updated
  BEFORE UPDATE ON public.orders
  FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();

-- ------------------------------------------------------------------------------
-- 6. ORDER ITEMS TABLE
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.order_items (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  order_id UUID NOT NULL REFERENCES public.orders(id) ON DELETE CASCADE,
  product_id INTEGER NOT NULL,
  product_title TEXT NOT NULL,
  origin TEXT,
  batch_lot TEXT,
  hsn_code TEXT,
  unit_price NUMERIC(10, 2) NOT NULL,
  quantity INTEGER NOT NULL DEFAULT 1,
  gst_rate NUMERIC(4, 2) DEFAULT 18,
  total_price NUMERIC(10, 2) NOT NULL
);

-- ------------------------------------------------------------------------------
-- 7. COMMENTS TABLE (Realtime Discussion on Articles)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.comments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  content_id UUID NOT NULL REFERENCES public.premium_content(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
  author_name TEXT NOT NULL,
  author_role TEXT DEFAULT 'Dental Surgeon',
  comment TEXT NOT NULL,
  rating INTEGER DEFAULT 5 CHECK (rating >= 1 AND rating <= 5),
  created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- ------------------------------------------------------------------------------
-- 8. CHAT MESSAGES TABLE (Realtime Support & Peer Inquiry)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.chat_messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  sender_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
  sender_name TEXT NOT NULL,
  sender_role TEXT DEFAULT 'member',
  recipient_id UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
  message TEXT NOT NULL,
  is_support BOOLEAN NOT NULL DEFAULT true,
  created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- ------------------------------------------------------------------------------
-- 9. STORAGE FILES TRACKER
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.files (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
  bucket_id TEXT NOT NULL,
  file_path TEXT NOT NULL,
  file_name TEXT NOT NULL,
  file_size BIGINT,
  mime_type TEXT,
  description TEXT,
  public_url TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- ==============================================================================
-- ROW LEVEL SECURITY (RLS) CONFIGURATION
-- ==============================================================================

-- 1. Profiles RLS
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Public profiles are viewable by authenticated users"
  ON public.profiles FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Users can update own profile"
  ON public.profiles FOR UPDATE
  TO authenticated
  USING (auth.uid() = id)
  WITH CHECK (auth.uid() = id);

CREATE POLICY "Admins can do everything on profiles"
  ON public.profiles FOR ALL
  TO authenticated
  USING (public.is_admin());

-- 2. Subscriptions RLS
ALTER TABLE public.subscriptions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own subscriptions"
  ON public.subscriptions FOR SELECT
  TO authenticated
  USING (auth.uid() = user_id OR public.is_admin());

CREATE POLICY "Service role and Admins can insert/update subscriptions"
  ON public.subscriptions FOR ALL
  TO authenticated
  USING (public.is_admin());

-- 3. Payments RLS
ALTER TABLE public.payments ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own payments"
  ON public.payments FOR SELECT
  TO authenticated
  USING (auth.uid() = user_id OR public.is_admin());

CREATE POLICY "Admins can manage all payments"
  ON public.payments FOR ALL
  TO authenticated
  USING (public.is_admin());

-- 4. Premium Content RLS
ALTER TABLE public.premium_content ENABLE ROW LEVEL SECURITY;

-- Free published articles are readable by ANYONE (even guests)
CREATE POLICY "Free published content is public"
  ON public.premium_content FOR SELECT
  TO anon, authenticated
  USING (tier = 'free' AND published = true);

-- Premium content is accessible ONLY by authenticated users with active premium/admin role
CREATE POLICY "Premium content viewable by subscribed users"
  ON public.premium_content FOR SELECT
  TO authenticated
  USING (published = true AND (tier = 'free' OR public.is_premium_or_admin()));

-- Content management only by admins
CREATE POLICY "Admins have full access to content"
  ON public.premium_content FOR ALL
  TO authenticated
  USING (public.is_admin());

-- 5. Orders RLS
ALTER TABLE public.orders ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own orders"
  ON public.orders FOR SELECT
  TO authenticated
  USING (auth.uid() = user_id OR public.is_admin());

-- Allow creating orders during checkout (authenticated or guest clinic checkout)
CREATE POLICY "Anyone can create orders"
  ON public.orders FOR INSERT
  TO anon, authenticated
  WITH CHECK (true);

CREATE POLICY "Admins can update orders"
  ON public.orders FOR UPDATE
  TO authenticated
  USING (public.is_admin());

-- 6. Order Items RLS
ALTER TABLE public.order_items ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view items of accessible orders"
  ON public.order_items FOR SELECT
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM public.orders o
      WHERE o.id = order_items.order_id
        AND (o.user_id = auth.uid() OR public.is_admin())
    )
  );

CREATE POLICY "Anyone can insert order items on order placement"
  ON public.order_items FOR INSERT
  TO anon, authenticated
  WITH CHECK (true);

-- 7. Comments RLS
ALTER TABLE public.comments ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Comments on published articles are readable by everyone"
  ON public.comments FOR SELECT
  TO anon, authenticated
  USING (true);

CREATE POLICY "Authenticated users can post comments"
  ON public.comments FOR INSERT
  TO authenticated
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete own comments or Admin can moderate"
  ON public.comments FOR DELETE
  TO authenticated
  USING (auth.uid() = user_id OR public.is_admin());

-- 8. Chat Messages RLS
ALTER TABLE public.chat_messages ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can read own chats or support channel"
  ON public.chat_messages FOR SELECT
  TO authenticated
  USING (sender_id = auth.uid() OR recipient_id = auth.uid() OR is_support = true OR public.is_admin());

CREATE POLICY "Authenticated users can insert chat messages"
  ON public.chat_messages FOR INSERT
  TO authenticated
  WITH CHECK (auth.uid() = sender_id);

-- 9. Files RLS
ALTER TABLE public.files ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own uploaded files"
  ON public.files FOR SELECT
  TO authenticated
  USING (user_id = auth.uid() OR public.is_admin());

CREATE POLICY "Users can record own uploaded files"
  ON public.files FOR INSERT
  TO authenticated
  WITH CHECK (user_id = auth.uid() OR public.is_admin());

CREATE POLICY "Users or Admins can delete files"
  ON public.files FOR DELETE
  TO authenticated
  USING (user_id = auth.uid() OR public.is_admin());

-- ==============================================================================
-- STORAGE BUCKETS SETUP
-- ==============================================================================
-- Buckets:
-- 1. clinical-files: User/Doctor case uploads, X-rays, CBCT scans
-- 2. content-media: Article thumbnails, clinical diagrams, downloadable PDFs
-- 3. avatars: User profile photos
-- 4. invoices: Downloadable PDF GST invoices

INSERT INTO storage.buckets (id, name, public)
VALUES 
  ('clinical-files', 'clinical-files', false),
  ('content-media', 'content-media', true),
  ('avatars', 'avatars', true),
  ('invoices', 'invoices', false)
ON CONFLICT (id) DO UPDATE SET public = EXCLUDED.public;

-- Storage RLS Policies
CREATE POLICY "Public media access"
  ON storage.objects FOR SELECT
  TO anon, authenticated
  USING (bucket_id IN ('content-media', 'avatars'));

CREATE POLICY "Authenticated users can upload clinical files"
  ON storage.objects FOR INSERT
  TO authenticated
  WITH CHECK (bucket_id IN ('clinical-files', 'avatars'));

CREATE POLICY "Users can read own clinical files"
  ON storage.objects FOR SELECT
  TO authenticated
  USING (bucket_id = 'clinical-files' AND (storage.foldername(name))[1] = auth.uid()::text OR public.is_admin());

CREATE POLICY "Admins can manage all storage files"
  ON storage.objects FOR ALL
  TO authenticated
  USING (public.is_admin());

-- ==============================================================================
-- SUPABASE REALTIME REPLICATION
-- ==============================================================================
-- Enable Realtime broadcasting for live discussions, chat, and order telemetry
BEGIN;
  DROP PUBLICATION IF EXISTS supabase_realtime;
  CREATE PUBLICATION supabase_realtime;
COMMIT;

ALTER PUBLICATION supabase_realtime ADD TABLE public.comments;
ALTER PUBLICATION supabase_realtime ADD TABLE public.chat_messages;
ALTER PUBLICATION supabase_realtime ADD TABLE public.orders;

-- ==============================================================================
-- SEED DATA: INITIAL CONTENT & DEMO ARTICLES
-- ==============================================================================
INSERT INTO public.premium_content (
  title, slug, category, tier, read_time, content_type, rating, excerpt, full_content, thumbnail_url, download_badge, download_file_url
) VALUES
(
  'Understanding SLA Surface Titanium Implants: Osseointegration Mechanisms',
  'sla-implant-guide',
  'implants',
  'free',
  '12 min',
  'Article',
  4.8,
  'Explore the science behind Sand-blasted, Large-grit, Acid-etched (SLA) surfaces and how micro-roughness promotes bone-to-implant contact in Indian clinical practice.',
  '## Introduction to SLA Surface Morphology
Sand-blasted, Large-grit, Acid-etched (SLA) titanium surfaces represent the gold standard in modern dental implantology. By combining mechanical corundum blasting (250–500 µm Al2O3) followed by concentrated HCl/H2SO4 acid etching, a hierarchical micro-rough surface is achieved (Ra = 1.8–2.2 µm).

### Cellular Osseointegration Dynamics
1. **Fibrin Network Retention:** The micro-pits (1–3 µm) trap and stabilize the peri-implant blood clot within the first 60 minutes post-osteotomy.
2. **Osteoblast Adhesion & Spreading:** Integrin receptors on osteoprogenitor cells bind specifically to titanium dioxide surface nanostructures.
3. **Woven to Lamellar Bone Transition:** Accelerated mineralization permits reliable early loading protocols at 6–8 weeks in Grade II and III bone density.',
  'assets/images/german-titanium-implants.jpg',
  '📥 Clinical Summary PDF',
  'assets/images/german-titanium-implants.jpg'
),
(
  'Introduction to β-TCP Bone Graft Granules: Indications & Case Selection',
  'btcp-intro',
  'biomaterials',
  'free',
  '15 min',
  'Article',
  4.9,
  'A beginner''s guide to synthetic bioceramic bone substitutes. Learn when to use β-TCP vs hydroxyapatite, and how to select appropriate granule sizes for socket preservation.',
  '## Phase-Pure β-Tricalcium Phosphate (β-TCP) Chemistry
β-TCP (Ca3(PO4)2) with a Ca/P ratio of 1.5 closely mimics the inorganic mineral phase of human bone. Unlike bovine xenografts which can persist indefinitely, phase-pure β-TCP resorbs at a rate parallel to new bone formation (typically 16–24 weeks).

### Key Clinical Indications
- **Alveolar Ridge Preservation:** Minimizes horizontal and vertical dimensional collapse following traumatic tooth extraction.
- **Periodontal Infrabony Defects:** Excellent osteoconductive scaffold for regenerative periodontal therapy.
- **Sinus Subantral Augmentation:** Blended with autogenous bone scrapings or PRP/PRF matrices.',
  'assets/images/swiss-bone-graft.jpg',
  '📥 Graft Protocol PDF',
  'assets/images/swiss-bone-graft.jpg'
),
(
  'Zirconia Milling Basics: Shade Selection & Pre-Sintering Workflow',
  'zirconia-basics',
  'cadcam',
  'free',
  '18 min',
  'Article',
  4.7,
  'Understand multi-layer zirconia disc anatomy, shade mapping, and milling parameters for achieving natural translucency in full-arch restorations using Japanese CAD/CAM systems.',
  '## Multi-Layered Dental Zirconia Physics
Modern 4Y-PSZ and 5Y-PSZ zirconia discs offer seamless transition from cervical strength (1100–1200 MPa) to incisal translucency (>49%). Understanding dry milling speeds, bur calibration, and green-state margin trimming ensures zero chipping during clinical delivery.',
  'assets/images/kyoto-zirconia-discs.jpg',
  '📥 Shade Guide PDF',
  'assets/images/kyoto-zirconia-discs.jpg'
),
(
  'Lateral & Transcrestal Sinus Lift: Complete Surgical Protocol with Case Library',
  'sinus-lift-masterclass',
  'biomaterials',
  'premium',
  '90 min',
  'Masterclass',
  5.0,
  '20+ documented clinical cases with intraoperative photos. Covers Schneiderian membrane management, simultaneous vs staged implant placement, and complication management.',
  '## Comprehensive Sinus Floor Elevation Manual
### 1. Pre-Operative CBCT Assessment
Evaluation of residual bone height (RBH), sinus septa (Underwood''s septa), membrane thickness, and patency of the osteomeatal complex (OMC).

### 2. Surgical Approaches
- **Transcrestal Osteotome / Densah Technique:** Indicated when RBH is 5–8 mm. Crestal hydro-dissection minimizes membrane perforation risk.
- **Lateral Window Antrostomy:** Indicated when RBH is < 4 mm. Piezoelectric ultrasonic instrumentation allows precise bony window osteotomy without tearing the 0.8mm Schneiderian membrane.

### 3. Membrane Perforation Rescue
Managing perforations using bovine pericardium collagen membranes (double-layer technique) or titanium micro-pins.',
  'assets/images/swiss-bone-graft.jpg',
  '📥 Full Surgical Masterclass PDF',
  'assets/images/swiss-bone-graft.jpg'
),
(
  'Immediate Loading Protocol for Full-Arch Implants: All-on-4 & All-on-6 Guide',
  'all-on-4-guide',
  'implants',
  'premium',
  '75 min',
  'Video Guide',
  4.9,
  'Patient selection criteria, bone density mapping with CBCT, implant angulation strategy, and provisionalization technique for same-day loading with titanium-zirconia hybrids.',
  '## All-on-4 and All-on-6 Immediate Loading Protocols
### Primary Stability & Insertion Torque
Achieving minimum insertion torque of 35–45 Ncm and ISQ (Implant Stability Quotient) ≥ 70 is mandatory before immediate cross-arch rigid splinting.

### Multi-Unit Abutment Selection
17° and 30° angulated multi-unit abutments compensate for distal implant inclination (up to 35–40° tilt avoiding mental foramina and maxillary sinuses).',
  'assets/images/german-titanium-implants.jpg',
  '📥 Full-Arch Protocol PDF',
  'assets/images/german-titanium-implants.jpg'
),
(
  'Full-Arch Zirconia Prosthetics: Digital Workflow from Scan to Final Delivery',
  'full-arch-zirconia',
  'cadcam',
  'premium',
  '60 min',
  'Protocol',
  4.8,
  'End-to-end digital protocol using IOS scanners, exocad/3Shape design software, and 5-axis milling. Fit assessment techniques and chairside adjustment protocols for implant-supported full arches.',
  '## Zero-Error CAD/CAM Zirconia Workflow
From verified photogrammetry / scan-body mesh alignment to sintered monolithic zirconia bridge cementation onto titanium bases. Includes furnace temperature ramp curve protocols.',
  'assets/images/kyoto-zirconia-discs.jpg',
  '📥 Lab Checklist PDF',
  'assets/images/kyoto-zirconia-discs.jpg'
),
(
  'Calcified Canal Management: CBCT-Guided Trephination & Ultrasonic Retreat',
  'calcified-canals',
  'endodontics',
  'premium',
  '55 min',
  'Masterclass',
  4.9,
  'Tackling the most challenging endo cases. Negotiating calcified canals using pre-curved hand files, ultrasonic tips, and CBCT image overlay techniques for impossible retreatments.',
  '## Micro-Endodontic Calcified Canal Protocol
Locating obliterated pulp chambers without iatrogenic furcal perforation using operating microscopes, Munce discovery burs, and active ultrasonic tips (Start-X / BDT).',
  'assets/images/swiss-rotary-files.jpg',
  '📥 Case Library PDF',
  'assets/images/swiss-rotary-files.jpg'
)
ON CONFLICT (slug) DO NOTHING;
