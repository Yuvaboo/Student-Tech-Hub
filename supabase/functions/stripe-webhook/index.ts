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

Deno.serve(async (req: Request) => {
  const corsHeaders = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
  };

  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders });
  }

  // ── Stripe Webhook ──────────────────────────────────────────────────────
  if (req.method === 'POST' && req.headers.get('stripe-signature')) {
    return handleStripeWebhook(req);
  }

  // ── verify-payment REST API ─────────────────────────────────────────────
  try {
    const body = await req.json();
    const { action } = body;

    switch (action) {
      case 'create_checkout':
        return handleCreateCheckout(body, corsHeaders);
      case 'verify_session':
        return handleVerifySession(body, corsHeaders);
      default:
        return json({ error: 'Unknown action' }, 400, corsHeaders);
    }
  } catch (err) {
    return json({ error: 'Invalid request body' }, 400, corsHeaders);
  }
});

// ─── CREATE STRIPE CHECKOUT SESSION ────────────────────────────────────────
async function handleCreateCheckout(body: any, corsHeaders: Record<string, string>) {
  const { plan, priceId, userId, userEmail, successUrl, cancelUrl } = body;

  if (!plan || !userId || !userEmail) {
    return json({ error: 'Missing required fields: plan, userId, userEmail' }, 400, corsHeaders);
  }

  try {
    // Look up or create Stripe customer
    let customerId: string | undefined;
    const existingSubs = await supabaseAdmin
      .from('subscriptions')
      .select('stripe_customer_id')
      .eq('user_id', userId)
      .not('stripe_customer_id', 'is', null)
      .maybeSingle();

    if (existingSubs.data?.stripe_customer_id) {
      customerId = existingSubs.data.stripe_customer_id;
    } else {
      const customer = await stripe.customers.create({
        email: userEmail,
        metadata: { supabase_user_id: userId },
      });
      customerId = customer.id;
    }

    // Determine amount from plan
    const amounts: Record<string, number> = { monthly: 1499, annual: 12999 };
    const planAmount = amounts[plan] ?? 1499;

    // Create Checkout Session
    const session = await stripe.checkout.sessions.create({
      mode: 'payment',                 // one-time payment (use 'subscription' for recurring)
      customer: customerId,
      payment_method_types: ['card'],
      line_items: [
        {
          price_data: {
            currency: 'inr',
            unit_amount: planAmount * 100,  // paise
            product_data: {
              name: plan === 'annual'
                ? 'Murugan Impex Annual Fellowship — ₹12,999/year'
                : 'Murugan Impex Monthly Practice — ₹1,499/month',
              description: plan === 'annual'
                ? 'Annual dental knowledge fellowship with full premium access'
                : 'Monthly premium dental knowledge subscription',
            },
          },
          quantity: 1,
        },
      ],
      metadata: {
        supabase_user_id: userId,
        plan,
        amount: planAmount.toString(),
      },
      success_url: successUrl,
      cancel_url: cancelUrl,
    });

    return json({ url: session.url, sessionId: session.id }, 200, corsHeaders);
  } catch (err: any) {
    console.error('[verify-payment] create_checkout error:', err.message);
    return json({ error: err.message }, 500, corsHeaders);
  }
}

// ─── VERIFY COMPLETED SESSION ───────────────────────────────────────────────
async function handleVerifySession(body: any, corsHeaders: Record<string, string>) {
  const { sessionId, userId } = body;

  if (!sessionId || !userId) {
    return json({ error: 'Missing sessionId or userId' }, 400, corsHeaders);
  }

  try {
    const session = await stripe.checkout.sessions.retrieve(sessionId);

    if (session.payment_status !== 'paid') {
      return json({ error: 'Payment not completed', status: session.payment_status }, 402, corsHeaders);
    }

    const plan         = session.metadata?.plan ?? 'monthly';
    const amount       = parseFloat(session.metadata?.amount ?? '1499');
    const customerId   = typeof session.customer === 'string' ? session.customer : session.customer?.id;
    const periodStart  = new Date();
    const periodEnd    = new Date();

    if (plan === 'annual') {
      periodEnd.setFullYear(periodEnd.getFullYear() + 1);
    } else {
      periodEnd.setMonth(periodEnd.getMonth() + 1);
    }

    // Upsert subscription row
    const { data: sub, error: subError } = await supabaseAdmin
      .from('subscriptions')
      .upsert(
        {
          user_id:               userId,
          plan,
          status:                'active',
          amount,
          currency:              'INR',
          current_period_start:  periodStart.toISOString(),
          current_period_end:    periodEnd.toISOString(),
          stripe_customer_id:    customerId ?? null,
          stripe_session_id:     sessionId,
        },
        { onConflict: 'user_id,stripe_session_id' }
      )
      .select('id')
      .single();

    if (subError) {
      console.error('[verify-payment] subscription upsert error:', subError.message);
    }

    // Record payment
    const invoiceSeq    = Math.floor(10000 + Math.random() * 90000);
    const now           = new Date();
    const fy            = now.getMonth() >= 3
      ? `${now.getFullYear()}-${String(now.getFullYear() + 1).slice(-2)}`
      : `${now.getFullYear() - 1}-${String(now.getFullYear()).slice(-2)}`;
    const invoiceNumber = `INV/${fy}/${invoiceSeq}`;

    await supabaseAdmin.from('payments').insert({
      user_id:            userId,
      subscription_id:    sub?.id ?? null,
      amount,
      currency:           'INR',
      status:             'completed',
      payment_method:     'stripe_card',
      payment_intent_id:  typeof session.payment_intent === 'string' ? session.payment_intent : null,
      invoice_number:     invoiceNumber,
      receipt_url:        session.url,
      description:        `${plan} subscription - ${plan === 'annual' ? '12 months' : '1 month'} access`,
    });

    // Elevate user role to premium
    const { error: roleError } = await supabaseAdmin
      .from('profiles')
      .update({ role: 'premium' })
      .eq('id', userId);

    if (roleError) {
      console.error('[verify-payment] role update error:', roleError.message);
    }

    return json({
      success:       true,
      plan,
      periodEnd:     periodEnd.toISOString(),
      invoiceNumber,
    }, 200, corsHeaders);
  } catch (err: any) {
    console.error('[verify-payment] verify_session error:', err.message);
    return json({ error: err.message }, 500, corsHeaders);
  }
}

// ─── STRIPE WEBHOOK HANDLER ─────────────────────────────────────────────────
async function handleStripeWebhook(req: Request) {
  const webhookSecret = Deno.env.get('STRIPE_WEBHOOK_SECRET');
  if (!webhookSecret) {
    return new Response('Webhook secret not configured', { status: 500 });
  }

  const signature = req.headers.get('stripe-signature') ?? '';
  const body      = await req.text();

  let event: Stripe.Event;
  try {
    event = await stripe.webhooks.constructEventAsync(body, signature, webhookSecret);
  } catch (err: any) {
    console.error('[stripe-webhook] Signature verification failed:', err.message);
    return new Response(`Webhook signature error: ${err.message}`, { status: 400 });
  }

  console.log('[stripe-webhook] Event received:', event.type);

  switch (event.type) {
    case 'checkout.session.completed': {
      const session  = event.data.object as Stripe.Checkout.Session;
      const userId   = session.metadata?.supabase_user_id;
      const plan     = session.metadata?.plan ?? 'monthly';
      const amount   = parseFloat(session.metadata?.amount ?? '1499');

      if (!userId) {
        console.error('[stripe-webhook] No supabase_user_id in session metadata');
        break;
      }

      const periodStart = new Date();
      const periodEnd   = new Date();
      plan === 'annual'
        ? periodEnd.setFullYear(periodEnd.getFullYear() + 1)
        : periodEnd.setMonth(periodEnd.getMonth() + 1);

      const customerId = typeof session.customer === 'string' ? session.customer : session.customer?.id;

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
            stripe_session_id:    session.id,
          },
          { onConflict: 'user_id,stripe_session_id' }
        )
        .select('id')
        .single();

      const invoiceSeq    = Math.floor(10000 + Math.random() * 90000);
      const now           = new Date();
      const fy            = now.getMonth() >= 3
        ? `${now.getFullYear()}-${String(now.getFullYear() + 1).slice(-2)}`
        : `${now.getFullYear() - 1}-${String(now.getFullYear()).slice(-2)}`;

      await supabaseAdmin.from('payments').insert({
        user_id:           userId,
        subscription_id:   sub?.id ?? null,
        amount,
        currency:          'INR',
        status:            'completed',
        payment_method:    'stripe_card',
        payment_intent_id: typeof session.payment_intent === 'string' ? session.payment_intent : null,
        invoice_number:    `INV/${fy}/${invoiceSeq}`,
        receipt_url:       session.url,
        description:       `${plan} subscription via Stripe webhook`,
      });

      await supabaseAdmin
        .from('profiles')
        .update({ role: 'premium' })
        .eq('id', userId);

      console.log('[stripe-webhook] Subscription activated for user:', userId);
      break;
    }

    case 'customer.subscription.deleted': {
      // For recurring subscriptions — cancel in DB
      const sub        = event.data.object as Stripe.Subscription;
      const customerId = typeof sub.customer === 'string' ? sub.customer : sub.customer.id;

      const { data: existingSub } = await supabaseAdmin
        .from('subscriptions')
        .select('id, user_id')
        .eq('stripe_customer_id', customerId)
        .eq('status', 'active')
        .maybeSingle();

      if (existingSub) {
        await supabaseAdmin
          .from('subscriptions')
          .update({ status: 'cancelled' })
          .eq('id', existingSub.id);

        // Check if user still has another active sub before downgrading
        const { count } = await supabaseAdmin
          .from('subscriptions')
          .select('id', { count: 'exact', head: true })
          .eq('user_id', existingSub.user_id)
          .eq('status', 'active');

        if (!count || count === 0) {
          await supabaseAdmin
            .from('profiles')
            .update({ role: 'free' })
            .eq('id', existingSub.user_id);
        }

        console.log('[stripe-webhook] Subscription cancelled for customer:', customerId);
      }
      break;
    }

    case 'invoice.payment_failed': {
      const invoice    = event.data.object as Stripe.Invoice;
      const customerId = typeof invoice.customer === 'string' ? invoice.customer : invoice.customer?.id;

      if (customerId) {
        await supabaseAdmin
          .from('subscriptions')
          .update({ status: 'past_due' })
          .eq('stripe_customer_id', customerId)
          .eq('status', 'active');

        console.log('[stripe-webhook] Payment failed for customer:', customerId);
      }
      break;
    }

    default:
      console.log('[stripe-webhook] Unhandled event type:', event.type);
  }

  return new Response(JSON.stringify({ received: true }), {
    status: 200,
    headers: { 'Content-Type': 'application/json' },
  });
}

// ─── HELPER ────────────────────────────────────────────────────────────────
function json(data: unknown, status = 200, headers: Record<string, string> = {}) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { 'Content-Type': 'application/json', ...headers },
  });
}
