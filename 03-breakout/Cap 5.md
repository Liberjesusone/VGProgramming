¡Claro que sí! Aquí tienes la transcripción completa y estructurada en formato Markdown. He limpiado el código de los números de línea para que sea válido, formateado las matemáticas con LaTeX, y dejado los bloques listos con marcadores descriptivos para que puedas insertar tus imágenes. Todo el contenido ha sido adaptado para que Claude Code lo entienda a la perfección.

---

# Capítulo 5: Colisiones Precisas: Breakout



> "Para ahorrar componentes, no dejo que ninguna pieza se desperdicie, y hago diseños ingeniosos que resultan difíciles de seguir para un ingeniero corriente. Una vez que lo entiendes, es muy fácil, porque hay tan pocas piezas que resulta más sencillo de comprender."
> -Steve Wozniak, Entrevista con Benj Edwards, Gamasutra, 2007
> 
> 

La colisión AABB del Capítulo 3 solo necesitó responder una pregunta binaria -¿se solapan estos dos rectángulos, sí o no?, porque a Pong le bastaba con invertir la velocidad de la pelota sin importar el detalle. Breakout lleva esa misma prueba a un escenario donde esa respuesta ya no alcanza. Hace falta saber, además, por qué lado ocurrió el contacto, para que la pelota rebote en la dirección correcta y no simplemente se invierta por completo.

Es también el primer juego cuya entrada deja de ser trivial, ya que la paleta necesita responder de forma más elaborada que las raquetas de Pong. Por eso este capítulo se detiene, antes de la pelota, a formalizar el patrón de diseño que Pong ya usaba sin explicar cómo `gale.input_handler` desacopla una tecla física de la acción que produce.

## 5.1. Contexto histórico: de Pong a un muro de ladrillos



Breakout fue diseñado en 1975 y lanzado comercialmente por Atari el 13 de mayo de 1976, como evolución conceptual directa de Pong (1972). Mientras que Pong enfrentaba a dos jugadores con palas verticales que se devolvían una pelota, Breakout reformuló la mecánica en un desafío de un solo jugador: destruir, con una única pala horizontal y una pelota rebotante, un muro de ladrillos de colores dispuesto en la parte superior de la pantalla. Ese giro de diseño, transformar un juego competitivo de dos jugadores en un reto individual contra un muro, se señala habitualmente como un punto de inflexión que amplió el vocabulario de mecánicas posibles del videojuego arcade. Con él se sentaron las bases del subgénero conocido después como *block breaker* (Donovan, 2010).

El desarrollo de Breakout está documentado, además, por su vínculo con los orígenes de Apple Computer. Según relatan tanto Steve Wozniak en su autobiografía *iWoz* como Walter Isaacson en su biografía de Steve Jobs, Nolan Bushnell y su vicepresidente de ingeniería, Steve Bristow, encargaron a Jobs, entonces técnico de Atari, el diseño de una versión de un solo jugador de Pong con mecánica de destrucción de bloques. Le ofrecieron, además, un bono por cada chip de lógica que lograra eliminar del circuito (Isaacson, 2011; Wozniak & Smith, 2006). Jobs, sin conocimientos profundos de electrónica digital, reclutó a su amigo Wozniak, entonces ingeniero en Hewlett-Packard, para resolver el diseño. Wozniak relata haber completado el circuito en cuatro días, prácticamente sin dormir, logrando una placa con muchos menos chips de los habituales en los juegos de Atari de la época (Wozniak & Smith, 2006).

El episodio tiene, además, una dimensión anecdótica que se ha vuelto parte del folclore fundacional de Apple. Según el propio relato de Wozniak, corroborado por Isaacson a partir de entrevistas con ambos protagonistas, Atari pagó a Jobs un bono adicional por el ahorro de chips que este no reveló a Wozniak, entregándole en su lugar solo una fracción del pago acordado originalmente por el trabajo. Fue un antecedente temprano de la compleja relación entre ambos fundadores de Apple, ocurrido meses antes de que la compañía existiera (Isaacson, 2011; Wozniak & Smith, 2006).

## 5.2. Entrada y eventos: Observer, Command y gale.input_handler



Un juego no decide cuándo llega la entrada del jugador; el sistema operativo se la entrega cuando ocurre, en el orden en que ocurre. `pygame`, como casi cualquier framework gráfico, expone esto como una cola de eventos, así que en cada vuelta del bucle de juego (Capítulo 2) hay que preguntar "¿llegó algo nuevo?" y, si llegó, decidir qué hacer con ello.

El problema de diseño es que esa pregunta ocurre en un solo lugar (el bucle principal), mientras que las respuestas relevantes están dispersas por todo el juego. La paleta necesita saber si se presionó la flecha izquierda, el menú necesita saber si se presionó Enter, el estado de pausa necesita saber si se presionó Escape. Sin un mecanismo intermedio, el bucle principal terminaría lleno de `ifs` conociendo los detalles internos de cada objeto del juego. Además, cada objeto del juego terminaría conociendo los detalles del sistema de eventos de `pygame`. Esta sección estudia dos patrones de diseño de software, patrón Observer y patrón Command, como dos respuestas distintas a ese mismo problema: "¿cómo conecto un evento de bajo nivel (una tecla, un click) con el código de alto nivel que debe reaccionar a él, sin que ambos queden entrelazados?".

### 5.2.1. El patrón Observer



La idea del patrón Observer es que los objetos interesados en un evento, los observadores, se registran ante una fuente de eventos, el sujeto u observable, que los notifica a todos cuando el evento ocurre. El sujeto no necesita conocer de antemano quiénes son ni cuántos son, solo mantiene una lista de observadores y, cuando algo relevante sucede, recorre esa lista llamando a un método que todos los observadores están obligados a implementar. Un esbozo mínimo, puramente ilustrativo y sin relación directa con el código real de `gale`, deja ver la forma del patrón:

```python
class Subject:
    def __init__(self):
        self.observers = []

    def register(self, observer):
        self.observers.append(observer)

    def notify(self, event):
        for observer in self.observers:
            observer.on_event(event)


class Logger:
    def on_event(self, event):
        print(f"Occurred: {event}")

```

Cualquier número de `Loggers` (o de cualquier otra clase que implemente `on_event`) puede registrarse ante el mismo `Subject`, y ninguno de ellos necesita saber que existen los demás. El sujeto, a su vez, no necesita saber nada sobre lo que cada observador hace con la notificación, sino que solo se compromete a avisar.

### 5.2.2. El patrón Command



El patrón Command ataca el mismo problema desde otro ángulo: en vez de que el evento se propague directamente hacia quien reacciona a él, primero se traduce en un objeto que representa una acción, por ejemplo, "mover paleta a la izquierda" o "lanzar la bola". Esto desacopla por completo la tecla física concreta de qué hace esa acción. El mismo comando puede reasignarse a otra tecla sin tocar el código que reacciona a él, o incluso ejecutarse sin que exista tecla alguna detrás (una repetición grabada, un control por inteligencia artificial, un botón en pantalla). Un esbozo igualmente ilustrativo:

```python
KEY_BINDINGS = {
    "ArrowLeft": "move_left",
    "ArrowRight": "move_right",
}

def handle_key_press(key, listener):
    action_id = KEY_BINDINGS.get(key)
    if action_id is not None:
        listener.on_action(action_id)

```

Lo esencial es que `listener.on_action` nunca recibe "se presionó ArrowLeft"; recibe "ocurrió move_left". Si mañana se decide que la tecla para mover la paleta a la izquierda debe ser la letra A en vez de la flecha, el único cambio está en el diccionario `KEY_BINDINGS`.

El código que reacciona a `move_left` no se entera del cambio, porque nunca conoció la tecla física en primer lugar.

Antes de seguir, vale la pena dejar una advertencia: la Figura 5.1 traduce esta idea a un diagrama de clases, pero no dibuja la jerarquía clásica de Command con métodos `execute()`/`undo()` que suele aparecer en los libros de patrones de diseño. Esto es porque ésa no es la forma en que `gale.input_handler` implementa el patrón, algo que se confirma en detalle en la Subsección 5.2.3. Su versión de Command es más modesta, pues no hay objetos-acción, solo un diccionario que traduce una tecla a un nombre. Lo único que hay para dibujar, entonces, es la relación real entre quien guarda ese diccionario y notifica (`InputHandler`) y la interfaz mínima que cualquier objeto debe implementar para recibir esas notificaciones (`InputListener`).

¿Cuándo conviene uno u otro? Observer brilla cuando varios objetos independientes necesitan reaccionar al mismo evento sin coordinarse entre sí (un logro que debe actualizar el marcador, reproducir un sonido y disparar una animación, todo a la vez). Command, en cambio, resulta superior cuando la acción en sí, no solo su ejecución inmediata, necesita existir como valor: para reasignar controles en tiempo de ejecución, para encolarla y ejecutarla más tarde, o para poder deshacerla. En la práctica, como se ve a continuación, un buen sistema de entrada de un juego termina siendo ambos a la vez: usa Command para traducir la tecla física en una acción con nombre, y usa Observer para notificar esa acción a cuantos objetos del juego estén escuchando.

La Tabla 5.1 resume esa comparación en una sola mirada, antes de entrar al código real de `gale.input_handler` que combina ambos patrones.

| Patrón

 | Qué viaja como valor

 | Quién decide qué hacer

 | Cuándo conviene

 |
| --- | --- | --- | --- |
| Observer

 | El evento en sí ("ocurrió un click", "se rompió un ladrillo")

 | Cada observador registrado, de forma independiente y sin coordinarse con los demás

 | Varios objetos deben reaccionar al mismo evento sin conocerse entre sí (marcador, sonido, animación)

 |
| Command

 | La acción resultante, ya traducida ("move_left", no "se presionó la flecha izquierda")

 | Quien recibe la acción, sin conocer jamás el disparador físico que la originó

 | La acción misma necesita existir como valor: reasignar controles, encolarla, deshacerla

 |
| *Cuadro 5.1: Observer y Command frente al mismo problema, desacoplar el evento de bajo nivel de quien reacciona a él: difieren en qué viaja como valor entre ambas partes.*<br> |  |  |  |

### 5.2.3. Cómo lo implementa gale: gale.input_handler



El Input Handler (`gale.input_handler.InputHandler`) es, en esencia, esa combinación: un traductor Command de entrada física a acciones con nombre, envuelto en un despachador Observer que notifica a quien esté registrado. El propio módulo lo describe así en su docstring:

```python
"""
This file contains InputHandler, an observer-pattern-based dispatcher
mapping keyboard (including modifier combos), mouse (clicks, wheel,
motion), and gamepad (buttons, axes, hotplug) input to named actions,
notifying every registered InputListener when one fires...
"""

```

La mitad Command del diseño vive en un diccionario de *bindings*, organizado por tipo de dispositivo, y en los métodos que lo pueblan:

```python
input_binding: Dict[str, Dict] = {
    KeyboardData.get_action_name(): {},
    MouseClickData.get_action_name(): {},
    MouseWheelData.get_action_name(): {},
    MouseMotionData.get_action_name(): {},
    GamepadButtonData.get_action_name(): {},
    GamepadAxisData.get_action_name(): {},
}

@classmethod
def set_keyboard_action(cls, key: int, action_id: str, modifiers: int = MOD_NONE) -> None:
    cls.input_binding[KeyboardData.get_action_name()][(_normalize_modifiers(modifiers), key)] = action_id

@classmethod
def set_mouse_click_action(cls, button: int, action_id: str) -> None:
    cls.input_binding[MouseClickData.get_action_name()][button] = action_id

```

`set_keyboard_action(KEY_LEFT, "move_left")` no ejecuta nada, sino que simplemente anota, en el diccionario correspondiente a teclado, que la combinación (sin modificadores, `KEY_LEFT`) corresponde al identificador de acción `"move_left"`. `set_mouse_click_action` hace exactamente lo mismo para clicks del mouse. Esta es la parte Command, ya que la tecla física queda registrada como el disparador de un valor, una cadena de texto, que representa la acción. Ese valor es lo único que el resto del juego llegará a conocer.

La mitad Observer vive en la lista de listeners y en el método `notify`:

```python
listeners: List[InputListener] = []

@classmethod
def register_listener(cls, listener: InputListener) -> None:
    if not hasattr(listener, "on_input"):
        raise InvalidListenerException(
            "Listener should implement the method on_input(input_id, input_data)"
        )
    cls.listeners.append(listener)

@classmethod
def notify(cls, action_id: str, action_data: InputData) -> None:
    for l in cls.listeners.copy():
        l.on_input(action_id, action_data)

```

Cualquier objeto que implemente `on_input(input_id, input_data)` puede registrarse con `register_listener`. `notify` recorrerá la lista completa avisando a todos por igual, sin necesitar saber qué tipo de objeto es cada uno: es el mismo esbozo de `Subject.notify` de la subsección anterior, ahora con nombres reales. Nótese que `notify` itera sobre `cls.listeners.copy()` y no sobre `cls.listeners` directamente. Esto es porque un listener podría registrarse o des-registrarse a sí mismo (o a otro) como reacción a la propia notificación, por ejemplo, un estado que cambia a otro estado apenas recibe cierta entrada. Modificar una lista mientras se está recorriendo produce errores difíciles de rastrear o directamente saltea elementos. Iterar sobre una copia aísla ese recorrido de cualquier modificación concurrente a la lista original.

Falta la pieza que conecta ambas mitades: `handle_input`, que se invoca una vez por cada evento crudo que `pygame` entrega en el bucle principal:

```python
@classmethod
def handle_input(cls, event: pygame.event.Event) -> None:
    if event.type == pygame.CONTROLLERDEVICEADDED:
        cls._open_gamepad(event.device_index)
        return
    if event.type == pygame.CONTROLLERDEVICEREMOVED:
        cls._close_gamepad(event.instance_id)
        return

    data_class: Optional[Type] = cls.INPUT_DATA_TABLE.get(event.type)
    if data_class is None:
        return

    bindings = cls.input_binding[data_class.get_action_name()]
    action_key = data_class.get_action_key(event)
    action: Optional[str] = bindings.get(action_key)

    if action is None and data_class is KeyboardData and action_key[0] != MOD_NONE:
        # No binding matched the exact combo of modifiers held, fall
        # back to a plain binding for the key without modifiers.
        action = bindings.get((MOD_NONE, action_key[1]))
        # analogous cases for mouse motion and gamepad omitted here

    if action is not None:
        data = data_class(event)
        cls.notify(action, data)

```

El recorrido es siempre el mismo. A partir del `event.type` crudo de `pygame` (`KEYDOWN`, `MOUSEBUTTONDOWN`, etc.) se decide qué clase de datos (`KeyboardData`, `MouseClickData`, ...) describe ese evento. Con esa clase se calcula una clave de acción (para teclado, el par modificadores-tecla; para un click, el número de botón), y esa clave se busca en el diccionario de bindings que `set_keyboard_action` y compañía fueron poblando. Si hay una coincidencia, se construye el objeto de datos concreto y se llama a `notify` con el `action_id` encontrado. El resultado que llega a cada listener, en su método `on_input(input_id, input_data)`, ya está completamente desacoplado del dispositivo físico que lo originó. Es decir, no importa si `"move_left"` vino de la flecha izquierda, de la tecla A, o, si el juego lo decidiera, de un botón de un control.

Esta es exactamente la pieza que Pong (Capítulo 3) ya usaba sin que se explicara: sus raquetas se registraban como listeners y reaccionaban a `"move_up"` y `"move_down"` sin conocer jamás una tecla concreta. La paleta de Breakout, construida en la Sección 5.7, sigue usando la misma pieza de la misma forma, y le añade un comportamiento nuevo: distinguir cuándo la tecla se presiona de cuándo se suelta.

La Figura 5.2 vuelve a recorrer esa misma cadena, pero ahora como diagrama de secuencia UML: el mismo `handle_input` que se acaba de leer, el auto-llamado a `notify` que dispara la mitad Observer, y la notificación final a un listener real del juego, la paleta, todo en un solo vistazo.

## 5.3. Colisión resuelta por lado



Pong resolvía cada colisión con un único gesto: cuando la pelota tocaba una raqueta o un borde, bastaba con invertir la componente de velocidad correspondiente, porque la geometría de la mesa hacía que esa componente fuera siempre la misma (horizontal contra las raquetas, vertical contra los bordes superior e inferior). Breakout rompe esa comodidad, porque la pelota puede golpear un ladrillo por arriba, por abajo, por la izquierda o por la derecha, y en cada caso debe rebotar de forma distinta.

Invertir siempre ambas componentes de la velocidad, el atajo perezoso, produce rebotes que se ven mal: una pelota que entra casi rasante por un costado saldría disparada hacia atrás en vertical, en vez de deslizarse en la dirección esperada. Hace falta, entonces, resolver la colisión por lado: averiguar por cuál de los cuatro lados entró la pelota, y sólo invertir la componente de velocidad que corresponde a ese lado.

La Figura 5.3 plantea el razonamiento en términos puramente geométricos, antes de traducirlo a código: cuando la pelota se solapa con un ladrillo, ese solape tiene un tamaño distinto en cada eje, y el eje donde el solape es menor es, precisamente, el lado por el que la pelota entró.

### 5.3.1. Calcular la intersección entre dos rectángulos



El primer paso, en `src/Ball.py`, es un método que, dado que ya se sabe que dos rectángulos colisionan, calcula cuánto se solapan en cada eje:

```python
@staticmethod
def get_intersection(r1: pygame.Rect, r2: pygame.Rect) -> Optional[Tuple[int, int]]:
    if r1.x > r2.right or r1.right < r2.x or r1.bottom < r2.y or r1.y > r2.bottom:
        # There is no intersection
        return None

    # Compute x shift
    if r1.centerx < r2.centerx:
        x_shift = r2.x - r1.right
    else:
        x_shift = r2.right - r1.x

    # Compute y shift
    if r1.centery < r2.centery:
        y_shift = r2.y - r1.bottom
    else:
        y_shift = r2.bottom - r1.y

    return (x_shift, y_shift)

```

`x_shift` es la distancia (con signo) que `r1` tendría que desplazarse en el eje $x$ para dejar de solaparse con `r2` por ese eje; `y_shift` es la misma idea para el eje $y$. Si `r1` está a la izquierda del centro de `r2` (`r1.centerx < r2.centerx`), el desplazamiento necesario es negativo, hacia la izquierda (`r2.x - r1.right`, que da un valor negativo o cero cuando hay solapamiento); si está a la derecha, es positivo. El mismo razonamiento, aplicado al eje vertical, produce `y_shift`.

### 5.3.2. Decidir el lado con el menor desplazamiento



El método `rebound`, también en `Ball`, usa esos dos desplazamientos para decidir qué componente de la velocidad invertir:

```python
def rebound(self, another: Any):
    br = self.get_collision_rect()
    sr = another.get_collision_rect()

    r = self.get_intersection(br, sr)
    if r is None:
        return

    shift_x, shift_y = r
    min_shift = min(abs(shift_x), abs(shift_y))

    if min_shift == abs(shift_x):
        # Collision happened from left or right
        self.x += shift_x
        self.vx *= -1
    else:
        # Collision happened from top or bottom
        self.y += shift_y
        self.vy *= -1

```

La idea clave está en `min_shift`: de los dos desplazamientos necesarios para separar los rectángulos, el eje con la magnitud menor es el que determina por dónde entró la pelota. Esto tiene una lectura geométrica sencilla: si la pelota se solapa muy poco en $x$ pero mucho en $y$, es porque apenas rozó un borde vertical del ladrillo (entró por la izquierda o la derecha); si se solapa poco en $y$ pero mucho en $x$, entró por arriba o por abajo.

El eje con menor solapamiento es, entonces, el eje por el que hay que corregir la posición (`self.x += shift_x` o `self.y += shift_y`, para sacar a la pelota de dentro del ladrillo) e invertir la velocidad (`self.vx *= -1` o `self.vy *= -1`). La otra componente de la velocidad se deja intacta: si la pelota entró por un lado horizontal, seguirá subiendo o bajando exactamente igual que antes, solo que ahora se aleja en vez de acercarse en el eje horizontal.

Es este cálculo, y no una tabla de casos escrita a mano para "arriba", "abajo", "izquierda" y "derecha", el que hace que el mismo método `rebound` sirva sin cambios tanto para la colisión contra un ladrillo como contra la paleta, en `PlayState.update`:

```python
# Check collision with the paddle
if ball.collides(self.paddle):
    settings.SOUNDS["paddle_hit"].stop()
    settings.SOUNDS["paddle_hit"].play()
    ball.rebound(self.paddle)
    ball.push(self.paddle)

# Check collision with brickset
if not ball.collides(self.brickset):
    continue

brick = self.brickset.get_colliding_brick(ball.get_collision_rect())
if brick is None:
    continue

brick.hit()
self.score += brick.score()
ball.rebound(brick)

```

Nótese, además, que después de rebotar contra la paleta se llama a `ball.push(paddle)`, un efecto adicional, no una corrección de colisión. Este efecto empuja horizontalmente a la pelota según qué tan lejos del centro de la paleta ocurrió el contacto y hacia dónde se estaba moviendo la paleta misma en ese instante (`paddle.vx`). Como resultado, golpear la bola con el borde de la paleta en movimiento la desvía más que golpearla con el centro de una paleta quieta.

## 5.4. Composición sobre herencia: el ladrillo como objeto



Un diseño ingenuo para los ladrillos de Breakout tentaría a construir una jerarquía de clases: `BrickAzul`, `BrickVerde`, `BrickDeUnGolpe`, `BrickDeTresGolpes`, y así sucesivamente, multiplicando clases por cada combinación de color y resistencia. El código real en `src/Brick.py` evita esa trampa por completo: hay una sola clase `Brick`, y lo que en la jerarquía ingenua serían subclases distintas aquí son, simplemente, valores distintos de dos atributos:

```python
class Brick:
    def __init__(self, x: int, y: int) -> None:
        self.x = x
        self.y = y
        self.width = 32
        self.height = 16
        self.texture = settings.TEXTURES["spritesheet"]
        self.tier = 0 # [0, 3]
        self.color = 0 # [0, 4]
        # To decide whether render it or not and collision detection
        self.active = True
        self.broken = False

```

`color` decide qué tan valioso es el ladrillo y con qué frame se dibuja; `tier`, de 0 a 3, es, en la práctica, un contador de golpes restantes dentro de ese color. Toda la lógica de "qué pasa cuando me golpean" vive en un único método, `hit`, en vez de estar repartida entre subclases:

```python
def hit(self) -> None:
    settings.SOUNDS["brick_hit_2"].stop()
    settings.SOUNDS["brick_hit_2"].play()

    r, g, b = COLOR_PALETTE[self.color]
    self.particle_system.set_colors([(r, g, b, 10), (r, g, b, 50)])
    self.particle_system.generate()

    if self.tier == 0:
        if self.color == 0:
            self.broken = True
            settings.SOUNDS["brick_hit_1"].stop()
            settings.SOUNDS["brick_hit_1"].play()
        else:
            self.tier = 3
            self.color -= 1
    else:
        self.tier -= 1

```

Cuando el ladrillo está en el tier más bajo (0) y ya es del color más bajo (0, el azul), el siguiente golpe lo rompe (`self.broken = True`). Si está en tier 0 pero todavía no es azul, el golpe lo "degrada" de color y lo repone al tier más alto (3); visualmente, un ladrillo dorado que se golpea lo suficiente termina convirtiéndose, color por color, en uno azul, y ese si se rompe al siguiente golpe. Si el tier es mayor que 0, el golpe simplemente lo reduce en uno. El método `score` completa el cuadro leyendo esos mismos dos atributos para decidir cuántos puntos vale romper ese ladrillo en ese estado exacto:

```python
def score(self):
    return self.tier * 200 + (self.color + 1) * 25

```

Ninguna subclase, ningún `isinstance`, ninguna jerarquía: toda la variedad de comportamiento, cuántos golpes aguanta un ladrillo, cuánto vale, cómo se ve, sale de combinar dos enteros dentro de una única clase. Esto es composición sobre herencia en su forma más directa: en vez de modelar la variación como una jerarquía de tipos, se modela como datos dentro de un mismo tipo, y el comportamiento se deriva de esos datos en tiempo de ejecución. La ventaja práctica es doble. Agregar un color nuevo a la paleta no exige escribir una clase nueva, solo agregar una entrada a `COLOR_PALETTE` y ajustar el rango de color. Además, cualquier código que ya sepa procesar un `Brick` (colisión, dibujo, cálculo de puntaje) sigue funcionando sin cambios para cualquier combinación de color y tier que exista.

## 5.5. Gestionar una colección de objetos que se destruyen en tiempo de ejecución



Los ladrillos, a diferencia de la mesa de Pong, se destruyen mientras el juego corre. `BrickSet`, el contenedor que agrupa todos los ladrillos de un nivel, necesita una estrategia clara para eliminarlos sin corromper la estructura que los guarda. El error clásico es modificar una colección mientras se la recorre. Quitar un elemento de un diccionario o una lista dentro de un `for` que itera sobre ese mismo diccionario o lista puede saltear elementos, lanzar una excepción, o simplemente producir resultados inconsistentes según el lenguaje y la estructura concretos. El código real de `src/BrickSet.py` evita el problema separando el recorrido de la eliminación en dos pasos:

```python
def update(self, dt: float) -> None:
    to_del = []
    for pos, brick in self.bricks.items():
        brick.update(dt)
        if not brick.active:
            to_del.append(pos)
            
    for pos in to_del:
        self._del_brick(pos)

```

El primer bucle sólo lee: actualiza cada ladrillo (lo que avanza su sistema de partículas, entre otras cosas) y, si ya no está activo, anota su posición en una lista aparte, `to_del`, sin tocar todavía `self.bricks`. Recién en el segundo bucle, ya fuera del recorrido original, se eliminan efectivamente esas posiciones. `brick.active` en sí depende de `brick.broken` más una condición extra: el ladrillo sigue activo mientras su sistema de partículas, la pequeña explosión de fragmentos de color que dispara `hit`, todavía tiene partículas vivas en pantalla, aunque ya esté roto:

```python
def update_active():
    self.active = not self.broken

self.particle_system = ParticleSystem(
    self.x + 16, self.y + 8, 64, update_active
)

```

Es decir, "activo" no es sinónimo inmediato de "no roto". El ladrillo permanece en la colección, y por lo tanto se sigue actualizando y dibujando su explosión de partículas, hasta que esa animación termina. Solo entonces `BrickSet.update` lo retira definitivamente.

`PlayState.update`, por su parte, aplica exactamente el mismo patrón de dos pasos, reconstruir en vez de mutar, para la lista de pelotas y la lista de power-ups en juego:

```python
# Removing all balls that are not in play
self.balls = [ball for ball in self.balls if ball.active]

# Remove powerups that are not in play
self.powerups = [p for p in self.powerups if p.active]

```

Aquí la reconstrucción se hace de una sola vez con una comprensión de lista. En vez de ir eliminando elementos uno por uno mientras se recorre `self.balls`, se construye una lista completamente nueva que contiene solo los que siguen activos, y esa lista nueva reemplaza a la anterior. Es el mismo principio que el de `BrickSet.update`, separar "decidir qué sobrevive" de "modificar la colección", expresado de la forma más idiomática en Python.

Vale la pena notar que ninguna de las dos variantes es intrínsecamente superior: el enfoque de `BrickSet` (lista auxiliar de índices o claves a borrar, más un segundo bucle) es preferible cuando la eliminación en sí tiene un costo o efectos colaterales que conviene controlar explícitamente (aquí, sacar una clave de un diccionario). La comprensión de lista, en cambio, es más directa cuando alcanza con filtrar un criterio booleano sobre una lista simple. Lo que ambas comparten, y lo que realmente importa retener, es que ninguna resuelve "¿quién sigue vivo?" modificando la colección desde dentro del bucle que la recorre.

## 5.6. Power-ups: efecto inmediato hoy, vencimiento formal más adelante



Breakout incluye un único power-up, `TwoMoreBall`, definido sobre una clase base `PowerUp` en `src/powerups/PowerUp.py`. Vale la pena ser preciso sobre qué hace exactamente, porque no es lo que el nombre "power-up con vencimiento" podría sugerir. Este power-up no concede una ventaja temporal que se apaga sola después de cierto tiempo, pues no hay ningún temporizador involucrado. Lo que expira, en cambio, es su existencia como objeto recolectable en pantalla:

```python
class PowerUp:
    def __init__(self, x: int, y: int, frame: int) -> None:
        self.x = x
        self.y = y
        self.vy = settings.POWERUP_SPEED
        self.active = True
        self.frame = frame

    def update(self, dt: float) -> None:
        if self.y > settings.VIRTUAL_HEIGHT:
            self.active = False
        self.y += self.vy * dt

    def take(self, play_state: TypeVar("PlayState")) -> None:
        raise NotImplementedError

```

Cuando un ladrillo se rompe hay una probabilidad de que `PlayState` genere uno de estos power-ups en su posición (`if random.random() < 0.1`). A partir de ahí cae a velocidad constante (`POWERUP_SPEED`) hacia la parte inferior de la pantalla, exactamente igual que cualquier otro objeto con posición y velocidad de este libro. Su `active` se apaga, y por lo tanto se lo retira de la lista de power-ups en juego mediante el mismo patrón de reconstrucción de lista ya visto para ladrillos y pelotas. Esto sucede si sale de la pantalla por abajo sin haber sido recogido, o si la paleta lo toca y su método `take` decide que ya cumplió su función:

```python
class TwoMoreBall(PowerUp):
    def take(self, play_state: TypeVar("PlayState")) -> None:
        paddle = play_state.paddle
        for _ in range(2):
            b = self.ball_factory.create(paddle.x + paddle.width / 2 - 4, paddle.y - 8)
            play_state.balls.append(b)
        self.active = False

```

En `PlayState.update`, la comprobación es simétrica a la de las demás colecciones destructibles del capítulo:

```python
for powerup in self.powerups:
    powerup.update(dt)
    if powerup.collides(self.paddle):
        powerup.take(self)

self.powerups = [p for p in self.powerups if p.active]

```

Dicho todo esto con honestidad: este Breakout no implementa un power-up cuyo efecto dure un intervalo de tiempo y luego se desactive solo (por ejemplo, "la paleta es más ancha durante diez segundos"). Lo que sí ilustra, con claridad, es el ciclo de vida completo de un objeto efímero generado dinámicamente durante la partida. Aparece condicionado a un evento del juego, se mueve por su cuenta, se puede recoger o perder, y se retira de la colección de power-ups activos siguiendo exactamente el mismo patrón de reconstrucción de lista ya visto para ladrillos y pelotas.

El mecanismo que falta, un efecto que se activa y, tras un intervalo de tiempo explícito, se revierte automáticamente, es precisamente lo que el Capítulo 6 formaliza como una pieza de infraestructura propia, `gale.timer`, en la Sección 6.3. Este power-up puede leerse como el anticipo informal de ese problema, antes de que exista la herramienta genérica para resolverlo.

## 5.7. Construcción de Breakout



Con las tres piezas anteriores, entrada por comandos, colisión resuelta por lado, ladrillos por composición, ya es posible recorrer la construcción completa de Breakout (`03-breakout` en el repositorio) de punta a punta.

### 5.7.1. Los bindings de entrada



Igual que en Pong, los bindings de teclado se registran una sola vez, al cargar `settings.py`, mucho antes de que exista ningún objeto del juego que reaccione a ellos:

```python
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_ESCAPE, "quit")
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_RETURN, "enter")
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_UP, "move_up")
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_RIGHT, "move_right")
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_DOWN, "move_down")
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_LEFT, "move_left")
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_SPACE, "pause")

```

Nótese que esto vive fuera de cualquier clase de juego: es configuración pura, la traducción Command de tecla física a identificador de acción, completamente separada de quién terminará reaccionando a `"move_left"` o a `"pause"`.

### 5.7.2. La paleta como listener



`Paddle` en sí (`src/Paddle.py`) no implementa `on_input`: es un objeto de datos y física pura, con posición, tamaño, velocidad horizontal y un método `update` que integra esa velocidad respetando los bordes de la pantalla:

```python
def update(self, dt: float) -> None:
    next_x = self.x + self.vx * dt
    if self.vx < 0:
        self.x = max(0, next_x)
    else:
        self.x = min(settings.VIRTUAL_WIDTH - self.width, next_x)

```

Quien escucha las acciones de entrada y decide qué velocidad asignarle a la paleta es el estado activo del juego, `PlayState` durante la partida, `ServeState` mientras se espera a que el jugador saque la pelota, cada uno implementando `on_input(input_id, input_data)` de forma casi idéntica:

```python
def on_input(self, input_id: str, input_data: InputData) -> None:
    if input_id == "move_left":
        if input_data.pressed:
            self.paddle.vx = -settings.PADDLE_SPEED
        elif input_data.released and self.paddle.vx < 0:
            self.paddle.vx = 0
    elif input_id == "move_right":
        if input_data.pressed:
            self.paddle.vx = settings.PADDLE_SPEED
        elif input_data.released and self.paddle.vx > 0:
            self.paddle.vx = 0
    elif input_id == "pause" and input_data.pressed:
        self.state_machine.change("pause", ...)

```

Este fragmento es, en sí mismo, la primera diferencia real de Breakout respecto a Pong en materia de entrada: no basta con reaccionar a que la tecla se presionó. `input_data.pressed` arranca el movimiento, pero `input_data.released`, disponible porque `KeyboardData` distingue `pygame.KEYDOWN` de `pygame.KEYUP`, debe detenerlo. Hace falta, además, la guarda `self.paddle.vx < 0` (o `> 0`) para evitar un error sutil: si el jugador presiona izquierda y, sin soltarla, presiona también derecha, soltar la primera tecla no debe frenar el movimiento que la segunda tecla sigue produciendo. Sin esa guarda, soltar cualquiera de las dos teclas pondría `vx` en cero aunque la otra siguiera presionada.

**Los "..." de `change("pause", ...)` esconden un problema real**


Pausar con `StateMachine.change` exige reconstruir `PauseState` pasándole, a mano, todo lo que `PlayState` necesitará para seguir exactamente donde quedó cuando se vuelva a cambiar de regreso: posición de la pelota, de la paleta, puntaje, qué ladrillos quedan. Esto es porque `change` destruye el estado saliente por completo (Sección 8.2.1 del Capítulo 8). Para un juego de una sola pantalla como Breakout es manejable, aunque tedioso; para un juego con mucho más estado en pantalla, empieza a doler.

El Capítulo 8 resuelve esta tensión de raíz con una pieza de infraestructura nueva, la pila de estados, en vez de seguir pasando cada vez más datos a mano por los `*args` de `enter`.

Breakout (la clase de juego en `src/Breakout.py`) resuelve además la acción `"quit"` en su propio `on_input`, antes de delegar cualquier otra cosa a la máquina de estados:

```python
def on_input(self, input_id: str, input_data: InputData) -> None:
    if input_id == "quit" and input_data.pressed:
        self.quit()
    else:
        self.state_machine.on_input(input_id, input_data)

```

Esto es otra instancia del mismo patrón Observer: tanto Breakout como cada estado activo se registran (indirectamente, a través de la maquinaria de `gale.state`) como listeners de `InputHandler`, y cada uno reacciona solo a los `input_id` que le interesan, ignorando el resto.

### 5.7.3. La partida completa



Con la paleta controlada por entrada y la colisión resuelta por lado ya explicadas, el ciclo de `PlayState.update` amarra el resto del juego. Cada pelota se mueve y se prueba contra los bordes del mundo (`solve_world_boundaries`, que usa la misma idea de invertir solo la componente que corresponde al borde tocado), contra la paleta, y contra el conjunto de ladrillos. Esta última prueba pasa por `brickset.get_colliding_brick`, que localiza el ladrillo concreto bajo el rectángulo de colisión de la pelota usando la fila y columna de la grilla en vez de comparar contra cada ladrillo uno por uno.

Cada golpe contra un ladrillo puede, además de sumar puntaje, otorgar una vida extra (`points_to_next_live`), hacer crecer la paleta (`paddle.inc_size`, que ajusta también su ancho de colisión), o generar un power-up. Cuando la última pelota sale de la pantalla se pierde una vida. Si quedan vidas, la paleta se encoge (`paddle.dec_size`) y el juego vuelve a `ServeState` para esperar el siguiente saque; si no quedan, el juego termina en `GameOverState`. El nivel se completa cuando queda exactamente un ladrillo en `brickset` y ese ladrillo ya está roto, condición que `PlayState.update` comprueba explícitamente antes de avanzar a `VictoryState`. Los niveles sucesivos, por su parte, generan disposiciones de ladrillos distintas a través de `src/utilities/level_maker.py`.

Estos cuatro estados, serve, play, game_over y victory, son la misma idea de máquina de estados finitos que el Capítulo 4 introdujo para el flujo de Flappy Bird, solo que aplicada esta vez al ciclo completo de una partida de Breakout en vez de a sus pantallas. La Figura 5.5 dibuja las transiciones reales entre ellos.

## 5.8. Ejercicios propuestos



1. Extender el manejo de entrada para soportar una acción que se ejecuta solo mientras la tecla se mantiene presionada (no solo al presionarla), y otra que se ejecuta solo al soltarla, sin depender de comprobar `input_data.pressed/released` manualmente en cada `on_input`: proponer una capa sobre `InputHandler` que ofrezca, por ejemplo, `is_action_held(action_id)`.


2. Implementar un ladrillo que requiera más de un golpe para romperse, cambiando su apariencia según el daño acumulado, el mismo concepto de niveles de daño que reaparece, con física real detrás, en el Capítulo 10.


3. Explicar por qué invertir ambas componentes de la velocidad en cualquier colisión (en vez de resolver por lado) produce comportamientos visualmente incorrectos, con un ejemplo concreto de posiciones donde eso se nota (por ejemplo, una pelota que roza apenas la esquina superior de un ladrillo).


4. Diseñar (sin necesidad de implementar el temporizador subyacente, que es tema del Capítulo 6) un power-up nuevo cuyo efecto sí tenga vencimiento, por ejemplo, una paleta más ancha durante un intervalo fijo de segundos, especificando qué estado adicional necesitaría guardar `PlayState` para saber cuándo revertir el efecto.