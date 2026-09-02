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
6. **¡Listo!** — sus ajustes están guardados, hacia el Panel de control.

**Posible último paso**: si el Panel de control muestra un aviso de **«La protección aún no está activada»**, haga clic en **«Activar la protección ahora»**. Se abrirá una única ventana del sistema para confirmar (su contraseña habitual) — a partir de ahí la protección funciona de verdad, incluso con la ventana principal cerrada. Este aviso normalmente no volverá a aparecer después (la protección se reinicia sola con el ordenador), salvo que haya un problema del sistema — en ese caso, basta con volver a hacer clic.

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

En el momento en que se acaba el tiempo, su hijo/a **no se desconecta sin avisar**: aparece una pantalla en primer plano con una cuenta atrás (aproximadamente 1 a 2 minutos) invitándole a guardar su trabajo antes de que la sesión se cierre de verdad. A diferencia del aviso emergente de la bandeja del sistema, esta pantalla siempre aparece, sea cual sea el entorno de escritorio.

**Limitar el tiempo de uso por día**: además de la franja horaria, puede marcar «Limitar el tiempo de uso por día» para fijar un máximo de minutos usados en el día (por ejemplo, 120 min/día), incluso si la franja horaria en sí es más amplia. En cuanto se alcanza ese límite, la sesión del hijo se cierra automáticamente por el resto del día, igual que al salir de la franja horaria — el límite se reinicia al día siguiente.

Los cambios solo se aplican tras hacer clic en **Guardar**.

### Pestaña Sitios

Categorías marcables (Redes sociales, Entretenimiento, Juegos en línea) y una lista de sitios personalizados que puede añadir/quitar libremente (p. ej. `tiktok.com`).

**Importante**: a diferencia de los horarios, el bloqueo de sitios se aplica a **todo el ordenador**, no solo a la cuenta del hijo seleccionado — porque un único sistema de bloqueo DNS cubre toda la máquina. Si varios hijos comparten el mismo ordenador, comparten la misma lista de sitios bloqueados.

**Lo que su hijo/a ve en realidad**: MintGuard no muestra una página de «Este sitio está bloqueado». El bloqueo ocurre a nivel de red (DNS), antes incluso de que la página empiece a cargarse — así que su hijo/a verá la pantalla de error habitual de su navegador, algo como «No se puede establecer conexión» o «No se puede acceder a este sitio». Es normal: significa que el bloqueo está funcionando, no que haya un problema técnico. Conviene explicárselo a su hijo/a con antelación, para que entienda que ese mensaje es un límite que usted ha fijado, y no una avería de internet.

Los cambios en esta pestaña se guardan **sin necesidad de botón Guardar** — pero cuente hasta unos treinta segundos antes de que el bloqueo esté realmente activo (el tiempo que tarda el servicio en segundo plano en releer la lista).

### Pestaña Aplicaciones

Las aplicaciones instaladas en el ordenador se detectan automáticamente y se ofrecen para marcar por categoría, además de una lista personalizada para añadir otros nombres de programa. Una aplicación bloqueada que ya esté en ejecución se cierra automáticamente en cuestión de segundos. Como con los sitios, esto se aplica a todo el ordenador.

**Limitar el tiempo de uso por día (en lugar de un bloqueo total)**: para una aplicación marcada, puede activar «Limitar el tiempo de uso por día» en lugar de bloquearla por completo. Su hijo podrá entonces usarla hasta el número de minutos por día que fije (por ejemplo, 30 min/día); en cuanto se supere ese tiempo, la aplicación se cerrará automáticamente y no podrá volver a abrirse hasta el día siguiente.

---

## 5. Seguridad y privacidad

- **El código PIN** protege el acceso a Ajustes e Informes. Se almacena de forma segura (nunca en texto plano).
- **¿Olvidó su PIN?** Haga clic en «¿Olvidó su PIN?» en la ventana de introducción. MintGuard muestra primero un mensaje explicando lo que va a pasar, antes de que se abra una ventana del sistema — para que esa ventana no sea una sorpresa. Deberá confirmar con **la contraseña de su propia cuenta** (la que usa para iniciar sesión en este ordenador) mediante esa ventana del sistema — la misma que aparece, por ejemplo, al instalar una actualización. Esta contraseña nunca es gestionada ni almacenada por MintGuard. Una vez confirmada, podrá definir un nuevo PIN de inmediato.
- Los registros de actividad y la base de datos de MintGuard solo son legibles por una cuenta de administrador — su hijo no tiene acceso a ellos, aunque sepa dónde buscar.

---

## 6. Los informes

La pestaña **Informes** (protegida por PIN) muestra, de los últimos 7 días y por hijo:
- Las aplicaciones bloqueadas y cuántas veces se cerró cada una.
- El número de veces que se alcanzó el límite de tiempo (cierre automático de sesión) — ya sea por salir de la franja horaria permitida o por superar un límite diario de minutos.

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
