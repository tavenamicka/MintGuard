# MintGuard installation guide

[Français](INSTALLATION.md) · [Deutsch](INSTALLATION.de.md) · [Español](INSTALLATION.es.md)

## Installation for parents (no technical knowledge needed)

This guide walks you through, step by step. If something does not go as expected, jump to "If something goes wrong" below: none of these situations is serious, and nothing can be damaged.

**Before you start**, check that:
- your computer runs **Linux Mint** (or Ubuntu) and is connected to the Internet;
- you know the **password** you type to log in;
- each child has **their own account** on the computer.

### Step 1 — Download the installation file

1. Open the [MintGuard releases page](https://github.com/tavenamicka/MintGuard/releases/latest).
2. Scroll down to the **"Assets"** area.
3. Click `mintguard_0.1.0-1_all.deb`. This file is the "installer": the `.deb` extension is the one used for installers on Linux Mint.

The file is saved in the **Downloads** folder.

### Step 2 — Install

1. Open the **Downloads** folder and double-click the `mintguard…deb` file.
2. A software manager window opens. Click **Install**.
3. Type your password, then confirm. Wait until it finishes, about one minute.

*Double-click does nothing?* Right-click the file, then **Open With** and **GDebi Package Installer**. If that still does not work, use the **other method** described below.

### Step 3 — Open MintGuard

Click the computer's menu (bottom left), type "MintGuard" then click the icon.

### Step 4 — Answer the assistant's questions

On first launch, MintGuard guides you. It asks for:
- your child's **first name** and the **name of their account** on the computer;
- a **profile** based on their age (6-12 or 13-18): you can change everything afterwards;
- a **PIN code** (4 digits or more). Write it down on paper and keep it safe: it protects your settings, and your children must not know it.

### Step 5 — Turn on protection

If the message **"Protection isn't active yet"** appears, click **"Activate protection now"**, then type your password. Protection is now running and restarts by itself with the computer.

For what comes next (setting time slots, blocking websites or apps), read the guide: [Français](USER_MANUAL_FR.md) · [English](USER_MANUAL_EN.md) · [Deutsch](USER_MANUAL_DE.md) · [Español](USER_MANUAL_ES.md).

### Other method: install with the terminal

Use this only if double-clicking does not work. The **terminal** is a window where you give instructions to the computer by typing them.

1. Press the `Ctrl`, `Alt` and `T` keys at the same time: the terminal opens.
2. Copy and paste this line, then press `Enter`:

```bash
cd ~/Downloads
```

3. Copy and paste this one, then `Enter`:

```bash
sudo apt install ./mintguard_0.1.0-1_all.deb
```

4. The terminal asks for your password. **Nothing appears while you type it, not even dots: this is normal.** Type it anyway, then press `Enter`.
5. If you are asked to confirm, type `Y` then `Enter`. Wait until the line ending in `$` comes back: the installation is finished.

(`sudo` means "run as administrator", and `apt` is the tool that installs programs on Linux Mint.)

### If something goes wrong

| What you see | What is happening | What to do |
|---|---|---|
| MintGuard does not appear in the menu | The menu has not refreshed yet. | Log out and log back in, or restart the computer. |
| A message mentions "dependencies" or a missing package | The computer could not download something MintGuard needs. | Check that you are connected to the Internet, then try the installation again. |
| The message "Protection isn't active yet" comes back | Protection did not start. | Click "Activate protection now" again. If that fails, open the terminal and type `sudo systemctl start mintguard-daemon`. |
| You forgot the PIN code | This happens often, and there is a solution. | In the code window, click "Forgot your code?" (see the user guide). |
| You want to uninstall | — | In the terminal, type `sudo apt remove mintguard` (your settings are kept) or `sudo apt purge mintguard` (everything is deleted). |

If none of this solves your problem, ask the person who recommended MintGuard to you, or open a request on the [issues page](https://github.com/tavenamicka/MintGuard/issues).

---

Developers and administrators: the technical installation (building the package, development setup) is described in the [French guide](INSTALLATION.md#installation-technique-développeurs-et-administrateurs).
