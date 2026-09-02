# MintGuard — User Guide

*So your children can explore the Internet safely.*

This guide is for parents. For technical installation, see [INSTALLATION.md](INSTALLATION.md).

---

## 1. What is MintGuard?

MintGuard is a parental control application for Linux Mint. It runs in two parts:

- **A monitoring program** that starts with the computer and enforces your rules continuously, even if you never open the main window.
- **A settings window** (the one you open to change settings and view reports): this is what this guide describes.

MintGuard can:
- **Block websites** (social media, online games, entertainment, or any site you add yourself).
- **Block applications** (games, chat apps, etc.).
- **Limit computer usage hours**, automatically closing the session outside allowed hours.
- **Show you a weekly summary** of what was blocked.

**Important prerequisite**: MintGuard assumes each child has **their own Linux account** on the computer (not a shared account with you or between children). This account is how MintGuard knows who is using the computer.

---

## 2. First launch: the setup wizard

On first launch, a 6-step wizard guides you through:

1. **Welcome** — a quick introduction.
2. **Which child do you want to protect?** — the child's first name (for display) and their **Linux username** (the account name, not the first name — ask a technician if you don't know it).
3. **Quick setup** — two ready-made profiles based on age:
   - **6-12 years old**: 2h of access per day, social media and online games blocked.
   - **13-18 years old**: 3h of access per day, major social media limited (TikTok, Instagram, Snapchat).
   You can change everything afterward in Settings — these are just starting points.
4. **PIN code** — a 4-digit code (up to 8) that protects access to Settings and Reports. **Write it down and keep it safe**: see the [Security and privacy](#5-security-and-privacy) section for what happens if you forget it.
5. **How it works** — a visual reminder of the principle (MintGuard watches, applies rules, informs you).
6. **All set!** — your settings are saved, on to the Dashboard.

**One possible last step**: if the Dashboard shows a banner saying **"Protection isn't active yet"**, click **"Activate protection now"**. A single system window opens to confirm (your usual password) — after which protection actually runs, even with the main window closed. This banner normally won't reappear afterwards (protection restarts on its own with the computer), unless something goes wrong at the system level — just click it again if it does.

---

## 3. The Dashboard

This is the main screen, opened every time you launch the application.

- **Child selector**: if you've set up multiple children, choose which one to display.
- **Protection status**: `ACTIVE` if at least one rule (time or blocked site) is configured for this child, otherwise `INACTIVE`.
- **Today's window**: the hours allowed today for the selected child, or "Free access today" if no rule is set for that day.
- **Last restriction**: the most recent recorded event (blocked application, or time limit reached).
- **Settings / Reports buttons**: ask for your PIN code before opening.

---

## 4. Changing settings

Clicking **Settings** asks for your PIN code, then opens three tabs.

### Time tab

For each day of the week: enable/disable a time window, and set start and end times. Outside that window, **the child's session closes automatically**. A notification-area icon in the child's session warns a few minutes ahead (10, 5, then 1 minute) and reports blocked applications that were closed — an advisory warning, not guaranteed (depends on the desktop's systray support): still let your child know about this rule in advance. A day with no window enabled means free access that day.

The moment the time is up, your child is **not disconnected without warning**: a screen appears on top with a countdown (about 1 to 2 minutes) inviting them to save their work before the session actually closes. Unlike the systray popup, this screen always appears, regardless of the desktop environment.

**Limit usage time per day**: on top of the time window, you can check "Limit usage time per day" to cap the total minutes used in the day (e.g. 120 min/day), even if the time window itself is wider. Once that quota is reached, the child's session closes automatically for the rest of the day, just like leaving the time window — the quota resets the next day.

Changes only take effect after clicking **Save**.

### Sites tab

Checkable categories (Social media, Entertainment, Online games) and a custom site list you can add to/remove from freely (e.g. `tiktok.com`).

**Important**: unlike time schedules, site blocking applies to the **entire computer**, not just the selected child's account — because a single DNS blocking system covers the whole machine. If several children share the same computer, they share the same blocked-site list.

**What your child actually sees**: MintGuard does not display a "This site is blocked" page. Blocking happens at the network level (DNS), before the page even starts loading — so your child sees their browser's usual error screen instead, something like "Unable to connect" or "This site can't be reached". That's normal: it means the block is working, not that there's a technical problem. It's worth explaining this to your child in advance, so they understand such a message is a limit you set, not an internet outage.

Changes on this tab are saved **with no Save button needed** — but allow up to about thirty seconds before the block actually takes effect (the time for the background service to re-read the list).

### Apps tab

Applications installed on the computer are detected automatically and offered as checkboxes by category, plus a custom list to add other program names. A blocked application already running is closed automatically within seconds. Like sites, this applies to the whole computer.

**Limit usage time per day (instead of a total block)**: for a checked application, you can enable "Limit usage time per day" instead of blocking it entirely. Your child can then use it up to the number of minutes per day you set (e.g. 30 min/day); once that time is exceeded, the application closes automatically and cannot be reopened until the next day.

---

## 5. Security and privacy

- **The PIN code** protects access to Settings and Reports. It is stored securely (never in plain text).
- **Forgot your PIN?** Click "Forgot your PIN?" in the entry window. MintGuard first shows a message explaining what's about to happen, before a system window opens — so that window isn't a surprise. You'll need to confirm with **your own account's password** (the one you use to log into this computer) through that system window — the same kind that appears, for example, to install an update. This password is never handled or stored by MintGuard itself. Once confirmed, you can set a new PIN right away.
- MintGuard's activity logs and database are only readable by an administrator account — your child cannot access them, even if they know where to look.

---

## 6. Reports

The **Reports** tab (PIN-protected) shows, over the last 7 days and per child:
- Blocked applications and how many times each was closed.
- The number of times the time limit was reached (automatic session closure) — whether from leaving the allowed time window or from exceeding a daily minutes quota.

**MintGuard does not show "total screen time used"**: the application does not continuously measure session duration, only blocking events. This is a deliberate choice — rather than making up an approximate number, we'd rather show nothing you couldn't fully verify yourself.

---

## 7. What MintGuard does not do (limitations to know about)

To stay honest about what the protection actually covers:

- **No automatic "adult content" filtering.** Reliable filtering would require a third-party, regularly updated site list, which MintGuard does not currently include. You can manually add sites in the Sites tab.
- **A technically savvy child could try to bypass blocking** by configuring an encrypted DNS service ("DNS-over-HTTPS") directly in their browser. MintGuard blocks switching to a different classic DNS resolver, but not this more advanced method.
- **Application blocking relies on the program's name**, not deeper system-level control — a renamed application could go unnoticed.
- **MintGuard assumes a dedicated Linux account per child.** If your child uses your own session or a shared session, protection will not apply correctly.
- **One computer = one shared list of blocked sites** across all children using it (see Sites section above).

These limitations are documented on purpose rather than hidden: it's better to know exactly what the protection actually covers.

---

## 8. Need help?

- Every screen has **"?"** buttons with a plain-language explanation.
- For a technical issue (installation, daemon not starting), see [INSTALLATION.md](INSTALLATION.md) or contact whoever installed MintGuard for you.
