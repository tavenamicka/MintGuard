# Guía de instalación de MintGuard

[Français](INSTALLATION.md) · [English](INSTALLATION.en.md) · [Deutsch](INSTALLATION.de.md)

## Instalación para padres (sin conocimientos técnicos)

Esta guía le acompaña paso a paso. Si algo no sale como esperaba, vaya a «Si algo no funciona» más abajo: ninguna de estas situaciones es grave y no se puede estropear nada.

**Antes de empezar**, compruebe que:
- su ordenador funciona con **Linux Mint** (o Ubuntu) y está conectado a Internet;
- conoce la **contraseña** que escribe para iniciar sesión;
- cada hijo tiene **su propia cuenta** en el ordenador.

### Paso 1 — Descargar el archivo de instalación

1. Abra la [página de versiones de MintGuard](https://github.com/tavenamicka/MintGuard/releases/latest).
2. Baje hasta la zona **«Assets»**.
3. Haga clic en `mintguard_0.1.0-1_all.deb`. Este archivo es el «instalador»: la extensión `.deb` es la que usan los instaladores en Linux Mint.

El archivo se guarda en la carpeta **Descargas**.

### Paso 2 — Instalar

1. Abra la carpeta **Descargas** y haga doble clic en el archivo `mintguard…deb`.
2. Se abre una ventana del gestor de software. Haga clic en **Instalar**.
3. Escriba su contraseña y confirme. Espere a que termine, alrededor de un minuto.

*¿El doble clic no hace nada?* Haga clic derecho en el archivo, luego **Abrir con** e **Instalador de paquetes GDebi**. Si tampoco funciona, use el **otro método** descrito más abajo.

### Paso 3 — Abrir MintGuard

Haga clic en el menú del ordenador (abajo a la izquierda), escriba «MintGuard» y haga clic en el icono.

### Paso 4 — Responder a las preguntas del asistente

En el primer inicio, MintGuard le guía. Le pide:
- el **nombre** de su hijo y el **nombre de su cuenta** en el ordenador;
- un **perfil** según su edad (6-12 o 13-18 años): podrá cambiarlo todo después;
- un **código PIN** (4 dígitos o más). Anótelo en papel y guárdelo en un lugar seguro: protege sus ajustes y sus hijos no deben conocerlo.

### Paso 5 — Activar la protección

Si aparece el mensaje **«La protección aún no está activada»**, haga clic en **«Activar la protección ahora»** y escriba su contraseña. La protección ya está en marcha y se reinicia sola con el ordenador.

Para lo que sigue (definir franjas horarias, bloquear sitios web o aplicaciones), lea la guía: [Français](USER_MANUAL_FR.md) · [English](USER_MANUAL_EN.md) · [Deutsch](USER_MANUAL_DE.md) · [Español](USER_MANUAL_ES.md).

### Otro método: instalar con el terminal

Úselo solo si el doble clic no funciona. El **terminal** es una ventana donde se dan instrucciones al ordenador escribiéndolas.

1. Pulse a la vez las teclas `Ctrl`, `Alt` y `T`: se abre el terminal.
2. Copie y pegue esta línea y pulse `Intro`:

```bash
cd ~/Descargas
```

3. Copie y pegue esta otra y pulse `Intro`:

```bash
sudo apt install ./mintguard_0.1.0-1_all.deb
```

4. El terminal le pide su contraseña. **No aparece nada mientras la escribe, ni siquiera puntos: es normal.** Escríbala igualmente y pulse `Intro`.
5. Si le piden confirmar, escriba `S` y pulse `Intro`. Espere a que vuelva la línea que termina en `$`: la instalación ha terminado.

(`sudo` significa «ejecutar como administrador» y `apt` es la herramienta que instala programas en Linux Mint.)

### Si algo no funciona

| Lo que ve | Lo que ocurre | Qué hacer |
|---|---|---|
| MintGuard no aparece en el menú | El menú aún no se ha actualizado. | Cierre la sesión y vuelva a abrirla, o reinicie el ordenador. |
| Un mensaje habla de «dependencias» o de un paquete no encontrado | El ordenador no pudo descargar algo que MintGuard necesita. | Compruebe que está conectado a Internet y vuelva a intentar la instalación. |
| Vuelve el mensaje «La protección aún no está activada» | La protección no se inició. | Haga clic de nuevo en «Activar la protección ahora». Si falla, abra el terminal y escriba `sudo systemctl start mintguard-daemon`. |
| Ha olvidado el código PIN | Pasa a menudo y hay una solución. | En la ventana del código, haga clic en «¿Olvidaste tu código?» (véase la guía del usuario). |
| Quiere desinstalar | — | En el terminal, escriba `sudo apt remove mintguard` (se conservan sus ajustes) o `sudo apt purge mintguard` (se borra todo). |

Si nada de esto resuelve su problema, pregunte a la persona que le recomendó MintGuard o abra una solicitud en la [página de problemas](https://github.com/tavenamicka/MintGuard/issues).

---

Desarrolladores y administradores: la instalación técnica (construir el paquete, entorno de desarrollo) se describe en la [guía en francés](INSTALLATION.md#installation-technique-développeurs-et-administrateurs).
