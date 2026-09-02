#!/usr/bin/env bash
# Construit le paquet .deb de MintGuard (installation "release", copie de
# code figee -- par opposition a scripts/install.sh qui installe en editable
# depuis ce checkout, pour le workflow de dev actif, voir SUIVI.md).
#
# Usage : bash scripts/build-deb.sh
# Produit : dist/mintguard_<version>-1_all.deb
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PKG_DIR="$REPO_ROOT/packaging/deb"
VERSION="$(python3 -c "import re; print(re.search(r'__version__ = \"([^\"]+)\"', open('$REPO_ROOT/mintguard/__init__.py').read()).group(1))")"
DEB_VERSION="${VERSION}-1"
BUILD_DIR="$REPO_ROOT/dist/mintguard-deb-build"
OUT_DEB="$REPO_ROOT/dist/mintguard_${DEB_VERSION}_all.deb"

echo "== Nettoyage du repertoire de build =="
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

echo "== Copie du code source (figee, non editable) =="
SRC_STAGE="$BUILD_DIR/opt/mintguard/src"
mkdir -p "$SRC_STAGE"
cp -r "$REPO_ROOT/mintguard" "$SRC_STAGE/"
find "$SRC_STAGE" -name "__pycache__" -type d -exec rm -rf {} +
find "$SRC_STAGE" -name "*.pyc" -delete
cp "$REPO_ROOT/setup.py" "$REPO_ROOT/requirements.txt" "$REPO_ROOT/LICENSE" "$SRC_STAGE/"

echo "== Entree de menu, icone et autostart (avertissement enfant) =="
install -D -m 644 "$PKG_DIR/mintguard.desktop" "$BUILD_DIR/usr/share/applications/mintguard.desktop"
# Source unique avec l'icone utilisee par la fenetre elle-meme (voir main_gui.py) : evite
# deux copies divergentes du meme bouclier (trouve en usage reel - l'ancienne copie de
# packaging/deb/ etait restee a la palette bleue d'avant la refonte "Jardin Numerique").
install -D -m 644 "$REPO_ROOT/mintguard/gui/assets/icons/mintguard.svg" "$BUILD_DIR/usr/share/icons/hicolor/scalable/apps/mintguard.svg"
install -D -m 644 "$PKG_DIR/mintguard-child-tray.desktop" "$BUILD_DIR/etc/xdg/autostart/mintguard-child-tray.desktop"
install -D -m 644 "$PKG_DIR/mintguard-parent-tray.desktop" "$BUILD_DIR/etc/xdg/autostart/mintguard-parent-tray.desktop"

echo "== Service systemd (chemin paquet, distinct de scripts/install.sh) =="
install -D -m 644 "$REPO_ROOT/etc/systemd/mintguard-daemon.service" "$BUILD_DIR/lib/systemd/system/mintguard-daemon.service"

echo "== dnsmasq et exemple de config =="
install -D -m 644 "$REPO_ROOT/etc/dnsmasq.d/mintguard.conf" "$BUILD_DIR/etc/dnsmasq.d/mintguard.conf"
install -D -m 644 "$REPO_ROOT/etc/config.json.example" "$BUILD_DIR/etc/mintguard/config.json.example"

echo "== Scripts de maintenance dpkg =="
mkdir -p "$BUILD_DIR/DEBIAN"
sed "s/@VERSION@/$DEB_VERSION/" "$PKG_DIR/control" > "$BUILD_DIR/DEBIAN/control"
cp "$PKG_DIR/conffiles" "$BUILD_DIR/DEBIAN/conffiles"
install -m 755 "$PKG_DIR/preinst" "$BUILD_DIR/DEBIAN/preinst"
install -m 755 "$PKG_DIR/postinst" "$BUILD_DIR/DEBIAN/postinst"
install -m 755 "$PKG_DIR/prerm" "$BUILD_DIR/DEBIAN/prerm"
install -m 755 "$PKG_DIR/postrm" "$BUILD_DIR/DEBIAN/postrm"

echo "== Construction du .deb =="
mkdir -p "$REPO_ROOT/dist"
dpkg-deb --build --root-owner-group "$BUILD_DIR" "$OUT_DEB"

echo
echo "== Paquet construit : $OUT_DEB =="
echo "Installation : sudo apt install \"$OUT_DEB\""
echo "Desinstallation : sudo apt remove mintguard   (ajouter 'purge' pour tout supprimer)"
