# ADIKT — Klaviyo Flow System

Built from store data (Nov 6, 2026): 43 email subscribers, 194 customer records, 56 buyers, 22 repeat buyers (39% repeat rate), 0.09% site conversion, ~20 pop-up orders with no contact captured.

Placeholders: `[PRODUCT]` = launch piece (assumed Red Racing Zip Up, $120), `[COLOR 2]` / `[COLOR 3]` = the two colorways, `[DATE]` = launch date.

Voice: short, confident, a little raw. "Done the ADIKT way." "Built for repetition." "Inspired by life." No exclamation-mark spam, no "Hey friend!"

---

## 0. Setup (do this first — ~45 min)

1. **Integrations → Shopify**: confirm connected, *Sync email subscribers to Klaviyo* ON, *Collect email subscribers at checkout* ON, onsite tracking ON (needed for browse/abandon flows).
2. **Lists**
   - `Newsletter` — main list, all sign-ups.
   - `Drop Waitlist` — anyone who signs up for early access to `[PRODUCT]`/colorways.
   - `SMS` — phone opt-ins.
3. **Segments**
   - `VIP` — Placed Order ≥ 2 times all time (≈22 people today). These get early access first, every drop.
   - `Engaged 60d` — opened/clicked email OR viewed site in last 60 days. Send campaigns to this, not everyone.
   - `Buyers – never repeat` — Placed Order = 1.
   - `Pop-up buyers` — tag `pop-up` or source = POS.
4. **Signup form** (Klaviyo, replaces/augments Shopify form)
   - Desktop + mobile popup, shows after 8 seconds or 40% scroll, not on checkout.
   - Headline: **"Get in before it's gone."** Sub: "Early access to every ADIKT drop. Your list gets 24 hours before the public."
   - Step 1 email → Step 2 phone (optional, SMS). Adds to `Newsletter` + `Drop Waitlist`.
   - Also embed the same form on a `/pages/waitlist` page — **point warm-up ads here**, not the shop.
5. **Pop-ups / POS**: in Shopify POS, always add customer email/phone at checkout. Tag them `pop-up`. Put a QR code on the table → waitlist page.
6. **Sender**: from name `ADIKT`, verify a sending domain (e.g. `mail.adikt.site`) so emails don't land in spam.

---

## 1. Welcome Flow
**Trigger:** Added to list `Newsletter`. **Filter:** has not placed order.

**E1 — immediately**
- Subject: `You're in.`
- Preview: `First look, first access. Every drop.`
- Body: Welcome to ADIKT. Everything we make is limited — small runs, custom paint, embroidery, distressing done by hand. When it's gone, it's gone. Being on this list means you see drops 24 hours before anyone else. Next one: **[PRODUCT]**. Watch your inbox.
- CTA: `See what's live` → /collections/all

**Wait 2 days**

**E2 — the story**
- Subject: `JOJO means addict.`
- Preview: `Why we're called ADIKT.`
- Body: Short origin story — what ADIKT means to you, "built for repetition", "inspired by life". 1 photo of you / the process. End with: "This is for the ones who keep showing up."
- CTA: `Follow @adikt.co` → Instagram

**Wait 3 days**

**E3 — the easy first buy**
- Subject: `Start with the finishing piece.`
- Body: Crew socks ($10, mix & match Yellow / Red / White / Pink — bundle discount applies automatically) + Navy Mesh Gym Shorts ($45). Low-commitment first order.
- CTA: `Shop socks` → /collections/all
- *Exit if order placed.*

---

## 2. Drop / Launch Sequence (run for `[PRODUCT]`, then reuse for `[COLOR 2]`, `[COLOR 3]`)
Built as **campaigns** (scheduled), plus one flow. Send to `Drop Waitlist` + `Engaged 60d` unless noted.

| When | Audience | Subject | Content |
|---|---|---|---|
| T-7 | Waitlist + Engaged | `Something red is coming.` | Close-up/blurred detail shot. No price, no date. "[DATE]. List gets in first." |
| T-3 | Waitlist + Engaged | `[PRODUCT]: the details.` | Embroidery front to back, heavyweight, fit notes, size guide, price. "Limited run — [X] pieces." |
| T-1 | Waitlist + Engaged | `Tomorrow. You're first.` | Early-access time (e.g. 10am CT). "Set a reminder." |
| T-0, 10am CT | **VIP + Waitlist only** | `Early access is open.` | Direct product link. "Public gets it tomorrow. Your size won't wait." |
| T-0 +6h | Waitlist, did not order | `Sizes are moving.` | Real inventory status by size (pull from Shopify). |
| T+1, 10am CT | Everyone (Engaged 60d) | `[PRODUCT] is live.` | Public launch. Hero photo, on-body photos. |
| T+3 | Engaged, did not buy | `Last sizes.` | Only list sizes still in stock. Honest scarcity only. |
| T+7 | Did not buy | `If you missed it.` | Back-in-stock signup link + tease of `[COLOR 2]`. |

**SMS** (SMS list only, max 3 per drop): T-1 reminder, T-0 early access link, T+3 last sizes.

> Early access mechanics: publish product at T-0 but keep it out of nav/collections, send the direct link to list only. Or use a password-protected collection page.

---

## 3. Back in Stock Flow
**Trigger:** Klaviyo *Subscribed to Back in Stock* (enable the BIS button on sold-out product pages — Red Racing Zip Up is at 0 now).

- E1 (when restocked): Subject `It's back. Not for long.` — direct link, size reminder.
- SMS same message if they're SMS subscribed.

---

## 4. Abandoned Checkout
**Trigger:** Started Checkout. **Filter:** Placed Order zero times since starting flow.

- **Wait 1 hour → E1** — Subject: `You left something.` Body: product block, "Limited run — we can't hold it." CTA `Finish checkout`.
- **Wait 23 hours → E2** — Subject: `Still yours (for now).` Body: fit/size help, link to size guide, "reply to this email with questions — a real person answers."
- **Wait 2 days → E3** — Subject: `Last call on your cart.` Body: free shipping reminder (existing automatic free-shipping discount). No % discount — protects margin and brand.
- SMS after E1 if subscribed.

## 5. Browse Abandonment
**Trigger:** Viewed Product. **Filters:** not in Abandoned Checkout flow in last 7 days, not placed order in last 3 days, received this flow 0 times in 14 days.

- **Wait 2 hours → E1** — Subject: `Thinking about the {{ event.ProductName }}?` Body: product block + 2 on-body photos + "every piece is slightly different." CTA `Take another look`.

---

## 6. Post-Purchase
**Trigger:** Placed Order.

- **E1 — immediately** (branch: first order vs repeat)
  - First: Subject `Welcome to ADIKT.` — thank you, what happens next, ships in 3–5 business days, care instructions (cold wash, inside out, hang dry — protects paint/distressing).
  - Repeat: Subject `Back again. Respect.` — thank you + "you're VIP now: early access to every drop."
- **Trigger 2: Fulfilled Order → wait 7 days → E2** — Subject: `How's it fit?` Ask for a photo wearing it, tag @adikt.co, reply with size feedback. (UGC = free content for your weekly batch.)
- **Wait 14 days → E3** — Subject: `Complete the fit.` Cross-sell: socks / shorts / next colorway waitlist.

## 7. Win-Back
**Trigger:** Placed Order (wait 90 days). **Filter:** placed order 0 times since starting flow.

- E1 — Subject: `Been a minute.` What's new since their last order + next drop date.
- Wait 14 days → E2 — Subject: `Still on the list?` "Want to stay on? Click here." (Clean unengaged people off — protects deliverability.)

---

## Weekly check (Monday, 10 min in Klaviyo)
- List growth this week (target: +50/week during ads warm-up)
- Signup form conversion rate (target: 3–5% of visitors)
- Flow revenue by flow (abandoned checkout should be #1 or #2)
- Open rate on campaigns (target 35%+; below 25% → tighten to Engaged segment)

## Build order (priority)
1. Setup + signup form + `/pages/waitlist` → re-point ads there
2. Welcome flow
3. Back in Stock (Red Racing Zip Up already sold out)
4. Abandoned checkout
5. Drop sequence for `[PRODUCT]` (schedule once date is set)
6. Post-purchase
7. Browse abandonment + win-back
