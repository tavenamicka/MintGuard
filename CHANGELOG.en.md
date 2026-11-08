# Changelog

[Français](CHANGELOG.md) · English

Each MintGuard version is described here, newest first. To see which version you have, look at the title of the MintGuard window. To update, see "Updating MintGuard" in the [README](README.en.md).

## 0.1.6 — 2026-11-08

- **Site blocking now repairs itself**: when the computer stops going through MintGuard to look up websites (e.g. after a reboot, or a conflict with the system's own network management), it now fixes itself automatically, instead of waiting for someone to open the Dashboard and click "Repair".

## 0.1.5 — 2026-10-18

- **Quota alert**: warnings for an application or a website now come at 10, 5 and 1 minute, like those for the session time.

## 0.1.4 — 2026-10-18

- **Child icon: demo mode and log**: running `mintguard-child-tray --demo` simulates the end of the allowed time (warnings at 5 then 1 minute, then the closing countdown) without cutting anything. The icon also writes a log to `~/.cache/mintguard/child-tray.log`.

## 0.1.3 — 2026-10-18

- **End-of-quota alert**: the child is warned 10, 5, then 1 minute before the allowed time for an application or a website runs out, and the alert is repeated if they come back after the computer was asleep.
- **Child account not found**: the Dashboard flags a child registered with an account that doesn't exist on the computer (no rule applies to them then), and offers "Fix the account" without losing their settings.

## 0.1.2 — 2026-10-11

### Fixes
- **Child's icon**: a click now opens a small window with the time left today (or "no time limit today"), the apps and websites blocked for the child (with the time left on their daily limit) and the last app that was closed. Before, the click sometimes showed nothing at all, and the child only saw blocked apps for 30 seconds.
- The child's notifications no longer read "Application bloquée : … has been closed" and use the child's language.

## 0.1.1 — 2026-10-11

### To do after updating from 0.1.0
- Open MintGuard. If the "Protection isn't active yet" card appears, click **"Activate protection now"**.
- If the "Website blocking is not working" card appears, click **"Turn on website blocking"**. Without this step, no website was actually blocked by 0.1.0 on a fresh installation.

### New
- **Website blocking checked and repairable**: the Dashboard and the notification-area icon show when the computer does not go through MintGuard to find websites, and a button fixes it. DNS now follows the current network (a laptop moving between Wi-Fi networks).
- **Free / Allowed hours / No access** for each day of the week, instead of a single checkbox.
- **A parent alone on the computer** is no longer subject to the websites blocked for their children. A child's rules apply as soon as they log in.
- **Better time-per-site counting**: a site keeps being counted for one minute after the last activity, and the domains that serve its content (for example YouTube videos) count for it and are blocked with it.
- **Copied or renamed apps**: a blocked app is recognised even if its program was copied under another name.
- **Version shown** in the window title.
- **After an update**, protection restarts by itself (from later updates on).

### Fixes
- Impossible time ranges (end before start, or crossing midnight) are refused instead of logging the child out all day.
- The Dashboard time bar is correct when a daily limit is shorter than the time range.
- Flatpak apps (for example Roblox via Sober, or ZapZap) are recognised under their real name.
- A child account name that does not exist (typo) is refused with a message.
- The protection service no longer stops on a transient error; a child who is not logged in is no longer targeted by logout attempts.
- Firewall DNS filtering is updated after removing a child and adding another.
- Uninstalling restores the computer's original DNS and removes all firewall rules (IPv6 included).
- "10/5/1 minutes left" warnings come back if you give the child more time.

## 0.1.0 — 2026-10-03

First published version: daily time limits, per-child blocked websites and apps, daily limits, reports, parent and child notification icons, interface in 4 languages.
