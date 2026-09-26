# Product Requirements Document — Invoicio

**Prepared by:** Priya Nair, Head of Product  
**Date:** May 2026  
**Version:** 2.0 — approved for development

---

## 1. Overview

Invoicio is a web application for freelancers and small agencies to create, send, and track invoices. The product replaces ad-hoc spreadsheet and PDF workflows with a structured tool that saves time on repetitive billing and reduces late payments through automated reminders.

**Target users:** Independent contractors and agencies with 1–10 members billing clients for time-based or fixed-price work.

**Business goal:** Reach 500 active monthly users within 6 months of launch, with a 60-day retention rate above 50%.

---

## 2. User roles

| Role | Description |
|---|---|
| **Member** | Creates and sends invoices, manages clients, views their own financial data |
| **Admin** | All Member permissions plus: invites team members, views team-wide financial dashboard, configures workspace settings |

A workspace is created by the first user (who becomes Admin). Admins can invite additional Members by email.

---

## 3. Core features

### 3.1 Client management

Members can create and manage a list of clients. Each client record stores:
- Company name (required)
- Primary contact name and email (required)
- Billing address (required for invoice generation)
- VAT / tax number (optional)
- Currency (default: USD; per-client override supported)
- Payment terms in days (default: 30; per-client override supported)

Clients are scoped to the workspace and visible to all Members.

### 3.2 Invoice creation

Members create invoices against a client. An invoice contains:
- Auto-generated invoice number (format: `INV-{YYYY}-{sequence}`, e.g. `INV-2026-0042`)
- Issue date (defaults to today)
- Due date (calculated from issue date + client payment terms; editable)
- Line items: description, quantity, unit price, tax rate (%)
- Discount: optional flat or percentage discount applied to the subtotal
- Notes field (plain text, appears on the invoice PDF)

Totals (subtotal, discount, tax, total due) are calculated server-side from the line items.

### 3.3 Invoice lifecycle

An invoice moves through the following statuses:

```
Draft → Sent → Viewed → Paid (terminal)
                      → Overdue (auto, when past due date and unpaid)
                      → Void (manual, by the Member who created it)
```

- **Draft:** editable; not visible to the client.
- **Sent:** triggers an email to the client with a PDF attachment and a payment link. The invoice becomes read-only.
- **Viewed:** set automatically when the client opens the payment link.
- **Overdue:** set automatically by a daily background job when `due_date < today` and status is `Sent` or `Viewed`.
- **Paid:** set manually by the Member (payment is recorded outside the app for now; Stripe integration is Phase 2).
- **Void:** removes the invoice from all totals; a void reason is required.

### 3.4 PDF generation

When an invoice is sent, the backend generates a PDF using the workspace's branding (logo, accent colour). The PDF is stored and re-served on subsequent views — it is not regenerated on every request.

The PDF layout includes: workspace logo, invoice number, issue and due dates, client details, line items table, totals, notes, and payment instructions.

### 3.5 Payment reminders

Automated email reminders are sent to the client:
- 3 days before the due date (if the invoice is still `Sent` or `Viewed`)
- On the due date (if unpaid)
- 7 days after the due date (if still unpaid and not Void)

Members can disable reminders per invoice. The reminder schedule is not currently configurable per workspace.

### 3.6 Financial dashboard

Admins see a workspace-level dashboard with:
- Total invoiced, total paid, total outstanding (this month and all time)
- Outstanding invoices by age bucket: 0–30 days, 31–60 days, 60+ days
- Top 5 clients by revenue (all time)

Members see the same dashboard scoped to their own invoices only.

### 3.7 Workspace settings

Admins configure:
- Workspace name and logo (uploaded image, max 2 MB, PNG or JPG)
- Default accent colour for PDF branding
- Default currency and payment terms (can be overridden per client)
- Invoice number prefix (default: `INV`; e.g. change to a company abbreviation)

### 3.8 Authentication

- Email and password registration with email verification.
- Password reset via email.
- Session tokens expire after 7 days of inactivity.
- Google OAuth login is out of scope for this release.

---

## 4. Non-functional requirements

| ID | Requirement |
|---|---|
| NF1 | All pages must load within 2 seconds on a standard broadband connection. |
| NF2 | The application must be responsive and usable on screens ≥ 375 px wide. |
| NF3 | All data in transit must use HTTPS. Passwords are stored as bcrypt hashes. |
| NF4 | The PDF generation endpoint must return within 5 seconds for invoices with up to 50 line items. |
| NF5 | The system must support up to 100 concurrent active users without degradation at launch. |

---

## 5. Out of scope for this release

- Online payment collection (Stripe or other gateway) — Phase 2
- Recurring invoices / subscription billing
- Expense tracking
- Multi-currency invoices (a single currency per invoice; the per-client currency setting handles this)
- Native mobile apps
- Accounting software integrations (QuickBooks, Xero)
- Time tracking built into the app

---

## 6. Acceptance criteria (high-level)

1. A user can register, create a workspace, add a client, create and send an invoice, and download the PDF in under 5 minutes on first use.
2. A sent invoice's status transitions to `Overdue` automatically within 24 hours of the due date passing.
3. A client receives the invoice email with a valid PDF attachment within 60 seconds of the Member clicking "Send."
4. An Admin can invite a Member, who can accept the invitation and log in within the same session.
5. The financial dashboard totals match the sum of the underlying invoice records (verifiable via export).

---

## 7. Data export

All invoice and client data is exportable by Admins as CSV. The export includes: invoice number, client, issue date, due date, status, subtotal, tax, total, paid date (if set).
