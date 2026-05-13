pkgname=dfuse-adb-gui
pkgver=1.0.0
pkgrel=1
pkgdesc="ADB WiFi and Android utility GUI"
arch=('x86_64')
url="https://github.com/dfuse43/DFUSE-ADB-GUI"
license=('MIT')
depends=('android-tools')

source=('dfuse-adb.png'
        'dfuse-adb-gui.desktop'
        'LICENSE')

sha256sums=('SKIP'
            'SKIP'
            'SKIP')

package() {
    install -Dm755 "$startdir/dist/dfuse-adb-gui" \
        "$pkgdir/usr/bin/dfuse-adb-gui"

    install -Dm644 "$startdir/dfuse-adb.png" \
        "$pkgdir/usr/share/pixmaps/dfuse-adb-gui.png"

    install -Dm644 "$startdir/dfuse-adb-gui.desktop" \
        "$pkgdir/usr/share/applications/dfuse-adb-gui.desktop"

    install -Dm644 "$startdir/LICENSE" \
        "$pkgdir/usr/share/licenses/$pkgname/LICENSE"
}
