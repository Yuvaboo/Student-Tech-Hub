/**
 * MURUGAN IMPEX — verify-payment Edge Function
 *
 * Handles:
 *   POST { action: "create_checkout", plan, userId, userEmail, successUrl, cancelUrl }
 *     → Returns { url: string, sessionId: string }
 *
 *   POST { action: "verify_session", sessionId, userId }
 *     → Verifies payment, activates subscription, elevates profile role to premium
 *     → Returns { success, plan, periodEnd, invoiceNumber }
 *
 * Secrets required (set via: supabase secrets set KEY=value):
 *   STRIPE_SECRET_KEY
 *   SUPABASE_URL
 *   SUPABASE_SERVICE_ROLE_KEY
 */

import Stripe from 'https://esm.sh/stripe@14.21.0?target=deno';
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.45.4';

const stripe = new Stripe(Deno.env.get('STRIPE_SECRET_KEY') ?? '', {
  apiVersion: '2024-06-20',
  httpClient: Stripe.createFetchHttpClient(),
});

const supabaseAdmin = createClient(
  Deno.env.get('SUPABASE_URL') ?? '',
  Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
);

const CORS = {
  'Access-Control-Allow-Origin':  '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

function json(data: unknown, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { 'Content-Type': 'application/json', ...CORS },
  });
}

function makeInvoiceNumber(): string {
  const now = new Date();
  const fy  = now.getMonth() >= 3
    ? `${now.getFullYear()}-${String(now.getFullYear() + 1).slice(-2)}`
    : `${now.getFullYear() - 1}-${String(now.getFullYear()).slice(-2)}`;
  return `INV/${fy}/${Math.floor(10000 + Math.random() * 90000)}`;
}

Deno.serve(async (req: Request) => {
  // Preflight
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: CORS });
  }

  let body: Record<string, any>;
  try {
    body = await req.json();
  } catch {
    return json({ error: 'Invalid JSON body' }, 400);
  }

  const { action } = body;

  // ── create_checkout ───────────────────────────────────────────────────────
  if (action === 'create_checkout') {
    const { plan, priceId, userId, userEmail, successUrl, cancelUrl } = body;

    if (!plan || !userId || !userEmail || !successUrl || !cancelUrl) {
      return json({ error: 'Missing required fields' }, 400);
    }

    try {
      // Reuse Stripe customer if one exists for this user
      let customerId: string | undefined;
      const { data: existingSub } = await supabaseAdmin
        .from('subscriptions')
        .select('stripe_customer_id')
        .eq('user_id', userId)
        .not('stripe_customer_id', 'is', null)
        .maybeSingle();

      if (existingSub?.stripe_customer_id) {
        customerId = existingSub.stripe_customer_id;
      } else {
        const customer = await stripe.customers.create({
          email:    userEmail,
          metadata: { supabase_user_id: userId },
        });
        customerId = customer.id;
      }

      const planAmounts: Record<string, number> = { monthly: 1499, annual: 12999 };
      const amount = planAmounts[plan] ?? 1499;

      const planNames: Record<string, string> = {
        monthly: 'Murugan Impex Monthly Practice Subscription',
        annual:  'Murugan Impex Annual Fellowship Subscription',
      };
      const planDescriptions: Record<string, string> = {
        monthly: 'Monthly premium dental knowledge hub — ₹1,499 + 18% GST',
        annual:  'Annual fellowship with full premium access — ₹12,999 + 18% GST (Save ₹5,989/year)',
      };

      const session = await stripe.checkout.sessions.create({
        mode:                 'payment',
        customer:             customerId,
        payment_method_types: ['card'],
        line_items: [
          {
            price_data: {
              currency:     'inr',
              unit_amount:  amount * 100,
              product_data: {
                name:        planNames[plan]        ?? 'Murugan Impex Subscription',
                description: planDescriptions[plan] ?? '',
              },
            },
            quantity: 1,
          },
        ],
        metadata: {
          supabase_user_id: userId,
          plan,
          amount:           amount.toString(),
        },
        success_url: successUrl,
        cancel_url:  cancelUrl,
        locale:      'auto',
      });

      return json({ url: session.url, sessionId: session.id });
    } catch (err: any) {
      console.error('[verify-payment] create_checkout error:', err.message);
      return json({ error: err.message }, 500);
    }
  }

  // ── verify_session ────────────────────────────────────────────────────────
  if (action === 'verify_session') {
    const { sessionId, userId } = body;

    if (!sessionId || !userId) {
      return json({ error: 'Missing sessionId or userId' }, 400);
    }

    try {
      const session = await stripe.checkout.sessions.retrieve(sessionId);

      if (session.payment_status !== 'paid') {
        return json({ error: 'Payment not completed', status: session.payment_status }, 402);
      }

      const plan        = session.metadata?.plan ?? 'monthly';
      const amount      = parseFloat(session.metadata?.amount ?? '1499');
      const customerId  = typeof session.customer === 'string'
        ? session.customer
        : (session.customer as Stripe.Customer)?.id;

      const periodStart = new Date();
      const periodEnd   = new Date();
      plan === 'annual'
        ? periodEnd.setFullYear(periodEnd.getFullYear() + 1)
        : periodEnd.setMonth(periodEnd.getMonth() + 1);

      // Upsert subscription (idempotent — safe to call multiple times)
      const { data: sub } = await supabaseAdmin
        .from('subscriptions')
        .upsert(
          {
            user_id:              userId,
            plan,
            status:               'active',
            amount,
            currency:             'INR',
            current_period_start: periodStart.toISOString(),
            current_period_end:   periodEnd.toISOString(),
            stripe_customer_id:   customerId ?? null,
            stripe_session_id:    sessionId,
          },
          { onConflict: 'user_id,stripe_session_id' }
        )
        .select('id')
        .single();

      // Record payment ledger entry
      const invoiceNumber = makeInvoiceNumber();
      await supabaseAdmin.from('payments').insert({
        user_id:           userId,
        subscription_id:   sub?.id ?? null,
        amount,
        currency:          'INR',
        status:            'completed',
        payment_method:    'stripe_card',
        payment_intent_id: typeof session.payment_intent === 'string'
          ? session.payment_intent
          : null,
        invoice_number:    invoiceNumber,
        receipt_url:       session.url,
        description:       `${plan} subscription — ${plan === 'annual' ? '12 months' : '1 month'} premium access`,
      });

      // Elevate user role to premium
      const { error: roleError } = await supabaseAdmin
        .from('profiles')
        .update({ role: 'premium' })
        .eq('id', userId);

      if (roleError) {
        console.error('[verify-payment] role update failed:', roleError.message);
      }

      return json({
        success:       true,
        plan,
        periodEnd:     periodEnd.toISOString(),
        invoiceNumber,
      });
    } catch (err: any) {
      console.error('[verify-payment] verify_session error:', err.message);
      return json({ error: err.message }, 500);
    }
  }

  return json({ error: `Unknown action: ${action}` }, 400);
});
