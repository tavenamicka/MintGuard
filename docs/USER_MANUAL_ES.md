# MintGuard — Guía del usuario

*Para que sus hijos exploren Internet con seguridad.*

Esta guía está dirigida a los padres. Para la instalación técnica, consulte [INSTALLATION.md](INSTALLATION.md).

---

## 1. ¿Qué es MintGuard?

MintGuard es una aplicación de control parental para Linux Mint. Funciona en dos partes:

- **Un programa de supervisión** que se inicia con el ordenador y aplica sus reglas de forma continua, incluso si nunca abre la ventana principal.
- **Una ventana de configuración** (la que abre para cambiar los ajustes y ver los informes): esta guía describe precisamente esa ventana.

MintGuard puede:
- **Bloquear sitios web** (redes sociales, juegos en línea, entretenimiento, o cualquier sitio que usted mismo añada).
- **Bloquear aplicaciones** (juegos, mensajería, etc.).
- **Limitar los horarios de uso del ordenador**, cerrando automáticamente la sesión fuera de las horas permitidas.
- **Mostrarle un resumen semanal** de lo que se ha bloqueado.

**Requisito importante**: MintGuard supone que cada hijo tiene **su propia cuenta Linux** en el ordenador (no una cuenta compartida con usted o entre hermanos). Es esta cuenta la que permite a MintGuard saber quién está usando el ordenador.

---

## 2. Primer inicio: el asistente de configuración

En el primer inicio, un asistente de 6 pasos le guía:

1. **Bienvenida** — una introducción rápida.
2. **¿A qué hijo quiere proteger?** — el nombre del hijo (para mostrar) y su **nombre de usuario Linux** (el nombre de la cuenta, no el nombre de pila — pregunte a un técnico si no lo conoce).
3. **Configuración rápida** — dos perfiles listos para usar según la edad:
   - **6-12 años**: 2 horas de acceso al día, redes sociales y juegos en línea bloqueados.
   - **13-18 años**: 3 horas de acceso al día, principales redes sociales limitadas (TikTok, Instagram, Snapchat).
   Podrá modificarlo todo después en Ajustes — son solo puntos de partida.
4. **Código PIN** — un código de 4 dígitos (hasta 8) que protege el acceso a Ajustes e Informes. **Anótelo y guárdelo en un lugar seguro**: consulte la sección [Seguridad y privacidad](#5-seguridad-y-privacidad) para saber qué ocurre si lo olvida.
5. **Cómo funciona** — un recordatorio visual del principio (MintGuard observa, aplica las reglas, le informa).
6. **¡Listo!** — la protección está activa, hacia el Panel de control.

---

## 3. El Panel de control

Esta es la pantalla principal, que se abre cada vez que inicia la aplicación.

- **Selector de hijo**: si ha configurado varios hijos, elija cuál mostrar.
- **Estado de protección**: `ACTIVA` si hay al menos una regla (horario o sitio bloqueado) configurada para este hijo, si no `INACTIVA`.
- **Horario de hoy**: las horas permitidas hoy para el hijo seleccionado, o «Acceso libre hoy» si no hay ninguna regla definida para ese día.
- **Última restricción**: el evento más reciente registrado (aplicación bloqueada, o límite de tiempo alcanzado).
- **Botones Ajustes / Informes**: piden su código PIN antes de abrirse.

---

## 4. Modificar los ajustes

Al hacer clic en **Ajustes** se le pide su código PIN y luego se abren tres pestañas.

### Pestaña Tiempo

Para cada día de la semana: activar/desactivar una franja horaria y definir la hora de inicio y fin. Fuera de esa franja, **la sesión del hijo se cierra automáticamente**. Un icono en la zona de notificación del hijo avisa unos minutos antes (10, 5 y luego 1 minuto) e informa de las aplicaciones cerradas por no estar permitidas — un aviso orientativo, no garantizado (depende del soporte de bandeja del escritorio): avise igualmente a su hijo de esta regla con antelación. Un día sin franja activada significa acceso libre ese día.

Los cambios solo se aplican tras hacer clic en **Guardar**.

### Pestaña Sitios

Categorías marcables (Redes sociales, Entretenimiento, Juegos en línea) y una lista de sitios personalizados que puede añadir/quitar libremente (p. ej. `tiktok.com`).

**Importante**: a diferencia de los horarios, el bloqueo de sitios se aplica a **todo el ordenador**, no solo a la cuenta del hijo seleccionado — porque un único sistema de bloqueo DNS cubre toda la máquina. Si varios hijos comparten el mismo ordenador, comparten la misma lista de sitios bloqueados.

Los cambios en esta pestaña se guardan **sin necesidad de botón Guardar** — pero cuente hasta unos treinta segundos antes de que el bloqueo esté realmente activo (el tiempo que tarda el servicio en segundo plano en releer la lista).

### Pestaña Aplicaciones

Cuatro aplicaciones sugeridas (Firefox, Chrome, Discord, Steam) para marcar, además de una lista personalizada para añadir otros nombres de programa. Una aplicación bloqueada que ya esté en ejecución se cierra automáticamente en cuestión de segundos. Como con los sitios, esto se aplica a todo el ordenador.

---

## 5. Seguridad y privacidad

- **El código PIN** protege el acceso a Ajustes e Informes. Se almacena de forma segura (nunca en texto plano).
- **¿Olvidó su PIN?** Haga clic en «¿Olvidó su PIN?» en la ventana de introducción. MintGuard le pedirá que confirme con **la contraseña de su propia cuenta** (la que usa para iniciar sesión en este ordenador) mediante una ventana del sistema — la misma que aparece, por ejemplo, al instalar una actualización. Esta contraseña nunca es gestionada ni almacenada por MintGuard. Una vez confirmada, podrá definir un nuevo PIN de inmediato.
- Los registros de actividad y la base de datos de MintGuard solo son legibles por una cuenta de administrador — su hijo no tiene acceso a ellos, aunque sepa dónde buscar.

---

## 6. Los informes

La pestaña **Informes** (protegida por PIN) muestra, de los últimos 7 días y por hijo:
- Las aplicaciones bloqueadas y cuántas veces se cerró cada una.
- El número de veces que se alcanzó el límite de tiempo (cierre automático de sesión).

**MintGuard no muestra el "tiempo total de pantalla utilizado"**: la aplicación no mide continuamente la duración de las sesiones, solo los eventos de bloqueo. Es una decisión deliberada — antes que inventar una cifra aproximada, preferimos no mostrar nada que usted no pudiera verificar completamente por sí mismo.

---

## 7. Lo que MintGuard no hace (límites que debe conocer)

Para ser honestos sobre lo que la protección cubre realmente:

- **Sin filtrado automático de "contenido para adultos".** Un filtrado fiable requeriría una lista de sitios de terceros mantenida y actualizada, que MintGuard no incluye por ahora. Puede añadir sitios manualmente en la pestaña Sitios.
- **Un hijo con conocimientos técnicos podría intentar eludir el bloqueo** configurando un servicio de resolución DNS cifrado ("DNS-over-HTTPS") directamente en su navegador. MintGuard bloquea el cambio a otro resolutor DNS clásico, pero no este método más avanzado.
- **El bloqueo de aplicaciones se basa en el nombre del programa**, no en un control más profundo del sistema — una aplicación renombrada podría pasar desapercibida.
- **MintGuard supone una cuenta Linux dedicada por hijo.** Si su hijo usa su propia sesión o una sesión compartida, la protección no se aplicará correctamente.
- **Un ordenador = una lista de sitios bloqueados compartida** entre todos los hijos que lo usan (véase la sección Sitios más arriba).

Estos límites se documentan a propósito en lugar de ocultarse: es mejor saber exactamente qué cubre realmente la protección.

---

## 8. ¿Necesita ayuda?

- Cada pantalla tiene botones **"?"** con una explicación sencilla en lenguaje corriente.
- Para un problema técnico (instalación, el daemon no arranca), consulte [INSTALLATION.md](INSTALLATION.md) o contacte con quien le instaló MintGuard.
