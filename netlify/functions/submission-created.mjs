// Runs on every verified Netlify Forms submission (Netlify calls a function
// with this exact name). For the "newsletter" form: add the address to the
// Brevo list, then send the welcome email that build.py publishes at
// /email/welcome.html. Spam caught by the honeypot never reaches this point.
//
// Environment (Netlify > Site configuration > Environment variables):
//   BREVO_API_KEY, BREVO_LIST_ID, NEWSLETTER_FROM, NEWSLETTER_REPLY_TO (optional)

const API = "https://api.brevo.com/v3";

async function brevo(path, payload) {
  const res = await fetch(API + path, {
    method: "POST",
    headers: { "api-key": process.env.BREVO_API_KEY, "content-type": "application/json", accept: "application/json" },
    body: JSON.stringify(payload),
  });
  const text = await res.text();
  return { ok: res.ok, status: res.status, text };
}

export const handler = async (event) => {
  const { payload } = JSON.parse(event.body || "{}");
  if (!payload || payload.form_name !== "newsletter") return { statusCode: 200, body: "not the newsletter form" };

  const email = String(payload.data?.email || payload.email || "").trim().toLowerCase();
  if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) return { statusCode: 200, body: "no valid email" };
  if (!process.env.BREVO_API_KEY) {
    console.log("BREVO_API_KEY missing: subscriber kept in Netlify Forms only");
    return { statusCode: 200, body: "not configured" };
  }

  // 1. The list. 204/201 = added; "duplicate_parameter" = already there, then no second welcome.
  const contact = await brevo("/contacts", { email, listIds: [Number(process.env.BREVO_LIST_ID)], updateEnabled: false });
  if (!contact.ok) {
    if (contact.text.includes("duplicate_parameter")) {
      await brevo("/contacts/lists/" + process.env.BREVO_LIST_ID + "/contacts/add", { emails: [email] });
      return { statusCode: 200, body: "already subscribed" };
    }
    console.log("Brevo contact error", contact.status, contact.text);
    return { statusCode: 200, body: "contact error" };
  }

  // 2. The welcome email, as published with the site.
  const site = process.env.URL || "https://hospitality-signals.com";
  const [html, meta] = await Promise.all([
    fetch(site + "/email/welcome.html").then((r) => r.text()),
    fetch(site + "/email/welcome.json").then((r) => r.json()),
  ]);
  const from = process.env.NEWSLETTER_FROM;
  const sent = await brevo("/smtp/email", {
    sender: { name: "Hospitality Signals", email: from },
    replyTo: { email: process.env.NEWSLETTER_REPLY_TO || from },
    to: [{ email }],
    subject: meta.subject,
    htmlContent: html,
    textContent: meta.text,
    tags: ["welcome"],
  });
  if (!sent.ok) console.log("Brevo welcome error", sent.status, sent.text);
  return { statusCode: 200, body: sent.ok ? "welcomed" : "welcome error" };
};
