# Capítulo 4

## Gravedad, Estados de Juego y gale.state



> "Cualquiera puede clonar la aplicación por su simplicidad, pero nunca harán otro Flappy Bird."
> -Dong Nguyen, Entrevista con David Kushner, Rolling Stone, 2014
> 
> 

Pong no tiene ni principio ni fin: arranca en marcha y nunca termina, y la única pantalla que existe es la del juego mismo. Flappy Bird sí tiene estructura narrativa: una pantalla de título que espera al jugador, una breve cuenta regresiva antes de empezar, la partida propiamente dicha, y el regreso a esa cuenta regresiva cuando el ave choca. Esa diferencia obliga a introducir la primera abstracción de control de flujo del libro: la máquina de estados finitos ($FSM^{1}$).

Este capítulo tiene dos metas igual de importantes. La primera es física: entender la gravedad como una aceleración constante que se integra cuadro a cuadro, en lugar de una velocidad fija, y ver cómo esa única línea de código produce la trayectoria parabólica característica del aleteo. La segunda, más estructural, es agotar en profundidad el módulo `gale.state`, en particular su clase `StateMachine`. Es la primera vez que aparece en el libro, y todos los juegos que siguen la dan por conocida, salvo cuando se necesite algo más elaborado, como la pila de estados del Capítulo 8.

---

### 4.1. Contexto histórico: el ave que su propio creador retiró



Flappy Bird fue creado por Dong Nguyen, programador y diseñador independiente vietnamita, bajo el sello de su pequeño estudio GEARS, con sede en Hanói. Nguyen desarrolló el juego en 2013, inspirándose, según relató él mismo, en la estética minimalista de los juegos de Nintendo de su infancia. Lo publicó de forma gratuita en la App Store de iOS el 24 de mayo de 2013, sin campaña de marketing, y durante varios meses pasó prácticamente inadvertido (Kushner, 2014).

El fenómeno viral se produjo de manera abrupta a comienzos de 2014, casi ocho meses después del lanzamiento, cuando Flappy Bird escaló al primer puesto de las listas de descargas gratuitas en más de cien países. Su mecánica era extremadamente simple: un toque de pantalla para que un ave pixelada esquivara tuberías, gobernada por la misma gravedad-como-aceleración-constante que este capítulo estudia. Esa simplicidad, combinada con una dificultad deliberadamente punitiva, lo convirtió en un caso paradigmático de diseño "hyper-casual": ciclos de juego brevísimos, curva de aprendizaje casi nula y una frustración calibrada que empujaba a la repetición compulsiva (Duran & Bil, 2024; Pizzo, 2023).

El 8 de febrero de 2014, en pleno apogeo del éxito, Nguyen anunció por Twitter su intención de retirar el juego. La retirada efectiva de las tiendas de aplicaciones ocurrió al día siguiente. En una entrevista posterior concedida a la revista Rolling Stone, explicó que el juego "fue diseñado para jugarse pocos minutos, cuando uno está relajado", pero que se había convertido en "un producto adictivo" que él mismo consideraba un problema. Agregó que la fama repentina y no deseada había alterado profundamente su vida cotidiana (Kushner, 2014; Nguyen, 2014).

Más allá de la anécdota biográfica, Flappy Bird suele citarse como uno de los primeros ejemplos masivos, y sin duda el más mediático, del género hyper-casual que despegaría comercialmente pocos años después. Ilustra, de forma temprana, las tensiones éticas del diseño basado en mecánicas repetitivas y de dificultad calibrada al límite de la frustración.

---

### 4.2. Conceptos nuevos



* **Gravedad como aceleración constante**: la velocidad vertical del ave crece cada cuadro en lugar de mantenerse constante ($v_{y}+=g\cdot\Delta t$), y por qué ese es un caso particular, mucho más simple, del mismo principio que sostiene la física completa del Capítulo 10.


* **Máquina de estados finitos aplicada al flujo del juego**: cada pantalla (título, cuenta regresiva, partida) es un objeto con su propio `enter`/`exit`/`on_input`/`update`/`render`, y transicionar entre ellas es sustituir cuál de esos objetos recibe los eventos del bucle principal.


* **Paso de datos entre estados**: cómo una transición puede llevar consigo información (por ejemplo, el mundo ya construido) para que el estado siguiente no tenga que reconstruirla desde cero.


* **Generación procedural simple**: troncos espaciados aleatoriamente, y por qué conviene parametrizar esa aleatoriedad (rango de alturas, espaciado, tiempo entre apariciones) en lugar de fijarla arbitrariamente en el código.



---

### 4.3. Gravedad: de velocidad constante a aceleración constante



En Pong (Capítulo 3) la pelota se mueve a rapidez constante: su velocidad no cambia entre un cuadro y el siguiente, solo su dirección al rebotar. El ave de Flappy Bird es la primera entidad del libro cuya velocidad sí cambia con el tiempo, y lo hace de la manera más simple posible: aumenta a una tasa constante llamada gravedad.

La Figura 4.1 muestra esta idea como una forma antes de verla en código: mientras el ave cae libremente, $v_{y}$ crece en línea recta (aceleración constante); en el instante del salto, en lugar de seguir esa recta, el valor cae abruptamente a un negativo fijo, un reemplazo instantáneo de la velocidad, no un impulso que se suma a lo que ya había.

**[ESPACIO PARA IMAGEN AQUÍ - Figura 4.1: Gráfico cartesiano de la velocidad vertical del ave ($v_{y}$) en función del tiempo bajo gravedad constante. Muestra una línea ascendente (pendiente = $g$) que cae abruptamente a un valor negativo en los momentos de "salto", formando un patrón de sierra.]**

La clase `Bird`, en `src/Bird.py` de Flappy Bird (02-flappy_bird en el repositorio), lo expresa así:

```python
def update (self, dt: float) -> None:
    self.vy += settings.GRAVITY * dt

    if self.jumping:
        settings.SOUNDS["jump"].play()
        self.vy = -settings.JUMP_TAKEOFF_SPEED
        self.jumping = False

    self.y += self.vy * dt

```

La primera línea es la integración de Euler de la aceleración, es decir, en cada cuadro, a la velocidad vertical `vy` se le suma `GRAVITY * dt`, donde `GRAVITY = 980` (en `settings.py`) son píxeles por segundo al cuadrado y `dt` es, como en todo el libro desde la Sección 2.3, el tiempo transcurrido desde el cuadro anterior. Nótese que esto ocurre siempre, en cada llamada a `update`, sin condición: el ave está permanentemente en caída libre.

Lo único que la interrumpe es el salto. Cuando `jump()` marca `self.jumping = True`, el siguiente `update` no suma un impulso a la velocidad existente, sino que la reemplaza de golpe por `-JUMP_TAKEOFF_SPEED`, negativa: en la convención de pantalla del Capítulo 1, subir es restar en y.

El valor está derivado del de la gravedad, `JUMP_TAKEOFF_SPEED = GRAVITY / 6`, de modo que ambas constantes se ajustan juntas si algún día se cambia la sensación general del juego. Finalmente, la posición se actualiza integrando la velocidad ya corregida: `self.y += self.vy * dt`.

El resultado de este par de líneas —una velocidad que crece sin freno y una posición que seguía a esa velocidad— es, sin que el código lo diga explícitamente en ningún lado, una trayectoria parabólica. Cada salto es una parábola completa, con el pico en el instante en que `vy` vuelve a valer cero.

Este es exactamente el mismo principio —aceleración constante integrada en velocidad, velocidad integrada en posición— que sostiene la física completa de proyectiles del Capítulo 10. Aquí aparece en su forma más reducida posible, con una sola dimensión y una sola fuerza, precisamente para que se puedan reconocer sus dos líneas de código cuando reaparezcan generalizadas a dos dimensiones y a fuerzas arbitrarias.

---

### 4.4. Máquinas de estados finitos para el flujo del juego



Antes de formalizar la idea con el vocabulario propio de Flappy Bird, conviene verla en su forma más desnuda, sin código de por medio. Considérese el ejemplo más simple posible: un bombillo. En cualquier instante, el bombillo está en exactamente una de dos condiciones, encendido o apagado, y nunca en una intermedia: no existe un "medio encendido" que sea a la vez las dos cosas. Bastaría con una única variable, por ejemplo `state`, que solo puede tomar uno de esos dos valores, y un evento externo, presionar el interruptor, que la hace saltar de un valor al otro. No hay nada más que decir sobre este sistema: dos estados, un evento, una transición que va de cada estado al otro. Eso, en su forma más reducida, ya es una máquina de estados finitos, tal como se ve en la Figura 4.2.

**[ESPACIO PARA IMAGEN AQUÍ - Figura 4.2: Diagrama de la máquina de estados finitos más simple posible con dos círculos ("Apagado" y "Encendido") conectados bidireccionalmente por flechas etiquetadas "interruptor".]**

¿Qué pasa si un sistema necesita más de dos condiciones? Considérese una célula de un autómata celular simple que, en lugar de estar solamente viva o muerta, puede encontrarse en tres condiciones: viva, muriendo y muerta. Sigue habiendo una sola variable que nombra la condición actual, pero ahora puede tomar tres valores en lugar de dos. Las reglas que deciden cuándo se pasa de una a otra ya no se reducen a "invertir" el valor anterior: una célula viva pasa a muriendo si tiene muy pocos o demasiados vecinos vivos a su alrededor; una célula muriendo pasa a muerta en el paso siguiente, sin condición adicional; y una célula muerta puede volver a estar viva si el número de vecinos vivos a su alrededor es el adecuado, como resume la Figura 4.3.

**[ESPACIO PARA IMAGEN AQUÍ - Figura 4.3: Diagrama de estados para una célula de autómata celular. Muestra nodos para "Viva", "Muriendo" y "Muerta" con flechas de transición indicando las condiciones de cambio (ej: "muy pocos o demasiados vecinos", "siempre", "vecinos adecuados").]**

Nótese que la idea de fondo no cambió al agregar un estado más: sigue habiendo una variable que nombra en cuál de un conjunto fijo de condiciones se encuentra el sistema, y una lógica separada que decide, mirando el entorno o el tiempo transcurrido, cuándo corresponde moverse a otra. Lo único que hizo falta formalizar, al crecer de dos estados a tres, fue enumerar explícitamente cuáles son todos los estados posibles y qué dispara cada transición entre ellos. Esa formalización, llevada a su forma más general, es exactamente lo que se entiende por una máquina de estados finitos: un conjunto finito y conocido de antemano de estados, más una función de transición que, dado el estado actual y un evento, determina el estado siguiente.

Antes de ver esta máquina en funcionamiento con las tres pantallas reales de Flappy Bird, conviene fijar la relación estructural, a nivel de clases, entre las piezas que `gale.state` pone a disposición para implementarla. La Figura 4.4 muestra ese diagrama de clases.

**[ESPACIO PARA IMAGEN AQUÍ - Figura 4.4: Diagrama de clases UML de gale.state. Muestra la clase StateMachine conectada a BaseState, la cual actúa como padre de TitleScreenState y PlayingState, detallando sus atributos y métodos (enter, exit, update, render, on_input).]**

`StateMachine` no contiene el código de ningún estado en particular, sino que mantiene un diccionario de clases candidatas (`states`) y una referencia al estado activo (`current`). Cada estado concreto, como `TitleScreenState` o `PlayingState`, hereda en cambio de `BaseState` el contrato mínimo que se detalla más adelante en este capítulo.

Flappy Bird, en su versión más simple, tiene tres estados:

* **Título**: muestra el nombre del juego y espera a que el jugador presione una tecla para empezar.


* **Cuenta regresiva**: un breve compás de espera ("3, 2, 1") antes de que el ave empiece a caer, para dar tiempo a ubicarse visualmente.


* **Partida**: el juego en sí, el ave cae y salta, los troncos se generan y se desplazan, se detectan colisiones y se acumula el puntaje.



En todo momento hay exactamente un estado activo, y solo ese estado recibe los eventos de entrada y las llamadas a `update`/`render` del cuadro actual. Pasar de un estado a otro no es más que cambiar cuál objeto ocupa ese lugar: el estado anterior deja de existir (o, al menos, de recibir eventos) y uno nuevo pasa a recibirlos.

**[ESPACIO PARA IMAGEN AQUÍ - Figura 4.5: Máquina de estados finitos del flujo de Flappy Bird. Diagrama con tres nodos (title, count_down, playing) y flechas de transición ("confirmar", "contador = 0", "colisión").]**

**[ESPACIO PARA IMAGEN AQUÍ - Figura 4.6: Diagrama de secuencia UML de StateMachine.change("playing", world=...). Muestra la interacción entre CountDownState, StateMachine y PlayingState, ejecutando exit() primero y enter() sobre el nuevo estado al final.]**

---

### 4.5. gale.state.StateMachine en profundidad



El módulo `gale.state`, dentro del paquete `gale` que se ha venido usando desde el Capítulo 2 para el bucle de juego y desde el Capítulo 3 para el manejo de entrada, define tres clases: `BaseState`, `StateMachine` y `StateStack`.

#### 4.5.1. El contrato de un estado: BaseState



Todo estado extiende `BaseState`, que define el contrato mínimo que una máquina de estados espera poder invocar sobre su estado activo:

```python
class BaseState:
    def __init__(self, state_machine: TypeVar("StateMachine")) -> None:
        self.state_machine: TypeVar("StateMachine") = state_machine

    def enter(self, *args, **kwargs) -> None:
        pass

    def exit(self) -> None:
        pass

    def on_input(self, input_id: str, input_data: InputData) -> None:
        pass

    def update(self, dt: float) -> None:
        pass

    def render(self, surface: pygame.Surface) -> None:
        pass

```

Cinco métodos, cada uno con un propósito preciso:

* El constructor recibe la máquina de estados que lo contiene y la guarda en `self.state_machine`.


* `enter` se ejecuta una sola vez, justo cuando el estado se vuelve el activo. Es el lugar natural para inicializar todo lo que ese estado necesita, y acepta argumentos posicionales y de palabra clave arbitrarios.


* `exit` se ejecuta una sola vez, justo antes de que el estado deje de ser el activo.


* `on_input`, `update` y `render` tienen la misma firma que sus homónimos en `gale.game.Game` (Capítulo 2).



#### 4.5.2. StateMachine: construcción y cambio de estado



```python
class StateMachine:
    def __init__(self, states=None) -> None:
        self.states: Dict[str, BaseState] = states if states is not None else {}
        # The initial state is the empty state
        self.current = BaseState(self)

    def change(self, state_name: str, *args, **kwargs) -> None:
        self.current.exit()
        self.current = self.states[state_name](self)
        self.current.enter(*args, **kwargs)

    def on_input(self, input_id: str, input_data: InputData) -> None:
        self.current.on_input(input_id, input_data)

    def update(self, dt: float) -> None:
        self.current.update(dt)

    def render(self, surface: pygame.Surface) -> None:
        self.current.render(surface)

```

El método `change` es el corazón de la clase, y vale la pena leer sus tres líneas una por una:

1. `self.current.exit()`: se le avisa al estado saliente que está a punto de dejar de estar activo.


2. `self.current = self.states[state_name](self)`: se busca la clase asociada al nombre pedido y se instancia, pasándole `self`.


3. `self.current.enter(*args, **kwargs)`: se ejecuta la inicialización del estado entrante, reenviándole cualquier argumento adicional.



---

### 4.6. Construcción de Flappy Bird



Con la teoría cubierta, se puede leer la construcción completa del juego, pieza por pieza, entendiendo por qué cada una tiene la forma que tiene.

**[ESPACIO PARA IMAGEN AQUÍ - Figura 4.7: Captura de pantalla de una partida en curso de Flappy Bird mostrando el ave volando entre tuberías/troncos, un entorno de cielo azul y montañas de fondo, y el texto "Score: 0" en la esquina superior izquierda.]**

#### 4.6.1. La clase principal y el registro de estados



`FlappyBird`, en `src/FlappyBird.py`, extiende `Game` (Capítulo 2) y en su init construye la máquina de estados con los tres nombres que le interesan al juego:

```python
class FlappyBird(Game):
    def init(self) -> None:
        pygame.mixer.music.play(loops=-1)
        self.state_machine = StateMachine(
            {
                "title": states.TitleScreenState,
                "count_down": states.CountDownState,
                "playing": states.PlayingState,
            }
        )
        self.state_machine.change("title")

    def update(self, dt: float) -> None:
        self.state_machine.update(dt)

    def render(self, surface: pygame.Surface) -> None:
        surface.fill(settings.COLOR_BACKGROUND)
        self.state_machine.render(surface)

    def on_input(self, input_id: str, input_data: InputData) -> None:
        if input_id == "quit" and input_data.pressed:
            self.quit()
        else:
            self.state_machine.on_input(input_id, input_data)

```

Nótese que las tres claves del diccionario son las clases mismas (`TitleScreenState`, `CountDownState`, `PlayingState`), no instancias: es `StateMachine.change` quien decide, en el momento de la transición, instanciar la que corresponda.

#### 4.6.2. TitleScreenState: esperar al jugador



```python
class TitleScreenState(BaseState):
    def enter(self) -> None:
        self.world = World()

    def update(self, dt: float) -> None:
        self.world.update(dt)

    def render(self, surface: pygame.Surface) -> None:
        self.world.render(surface)
        render_text(
            surface, "Flappy Bird", settings.FONTS["flappy"],
            settings.VIRTUAL_WIDTH / 2, settings.VIRTUAL_HEIGHT / 3,
            settings.COLOR_WHITE, center=True, shadowed=True,
        )
        render_text(
            surface, "Press Enter to start", settings.FONTS["medium"],
            settings.VIRTUAL_WIDTH / 2, 2 * settings.VIRTUAL_HEIGHT / 3,
            settings.COLOR_WHITE, center=True, shadowed=True,
        )

    def on_input(self, input_id: str, input_data: InputData) -> None:
        if input_id == "confirm" and input_data.pressed:
            self.state_machine.change("count_down")

```

En `enter` se crea un `World` con su parámetro `generate_logs` en su valor por omisión (`False`). El único evento que le importa a este estado es `"confirm"`, la acción asociada a la tecla Enter. Al recibirlo, pide a su máquina de estados la transición a `"count_down"`.

#### 4.6.3. CountDownState: una transición con temporizador y datos



```python
class CountDownState(BaseState):
    def enter(self) -> None:
        self.world = World(generate_logs=False)
        self.counter = 3
        self.timer = 0.0

    def update(self, dt: float) -> None:
        self.timer += dt

        if self.timer >= 1.0:
            self.timer = 0.0
            self.counter -= 1

        if self.counter == 0:
            self.state_machine.change("playing", world=self.world)
            return

        self.world.update(dt)

    def render(self, surface: pygame.Surface) -> None:
        self.world.render(surface)
        render_text(
            surface, str(self.counter), settings.FONTS["huge"],
            settings.VIRTUAL_WIDTH / 2, settings.VIRTUAL_HEIGHT / 2,
            settings.COLOR_WHITE, center=True, shadowed=True,
        )

```

Este estado introduce dos ideas nuevas. La primera es un temporizador manual: `self.timer` acumula `dt` en cada cuadro, y cuando llega a un segundo se reinicia y se descuenta una unidad de `self.counter`. La segunda idea es el paso de datos entre estados: cuando el contador llega a cero, la transición a `"playing"` no se hace con `change("playing")` a secas, sino con `change("playing", world=self.world)`.

#### 4.6.4. World y LogPair: desplazamiento y generación procedural



La clase `World` (`src/World.py`) agrupa todo lo que se mueve de fondo: el fondo mismo, el suelo, y la lista de troncos. Su `update` resuelve tres desplazamientos independientes y, cuando corresponde, la generación de un tronco nuevo:

```python
def update(self, dt: float) -> None:
    if self.generate_logs:
        self.logs_spawn_timer += dt
        if self.logs_spawn_timer > settings.TIME_TO_SPAWN_LOGS:
            self.logs_spawn_timer = 0.0
            y = max(
                -settings.LOG_HEIGHT + 10,
                min(
                    self.last_log_y + random.randint(-20, 20),
                    settings.VIRTUAL_HEIGHT + 90 - settings.LOG_HEIGHT,
                ),
            )
            self.last_log_y = y
            self.logs.append(self.log_pair_factory.create(settings.VIRTUAL_WIDTH, y))

    self.background_x -= settings.BACK_SCROLL_SPEED * dt
    if self.background_x <= -settings.BACKGROUND_LOOPING_POINT:
        self.background_x = 0

    self.ground_x -= settings.MAIN_SCROLL_SPEED * dt
    if self.ground_x <= -settings.VIRTUAL_WIDTH:
        self.ground_x = 0

    for log_pair in self.logs:
        log_pair.update(dt)

    self.logs = [lp for lp in self.logs if not lp.is_out_of_game()]

```

Cada elemento de `self.logs` es una instancia de `LogPair` (`src/LogPair.py`), que modela un par de troncos, uno superior y uno inferior, separados verticalmente por una abertura fija de `LOGS_GAP` píxeles (90):

```python
def get_top_rect(self) -> pygame.Rect:
    return pygame.Rect(round(self.x), round(self.y), settings.LOG_WIDTH, settings.LOG_HEIGHT)

def get_bottom_rect(self) -> pygame.Rect:
    return pygame.Rect(
        round(self.x),
        round(self.y + settings.LOGS_GAP + settings.LOG_HEIGHT),
        settings.LOG_WIDTH,
        settings.LOG_HEIGHT,
    )

```

#### 4.6.5. El patrón Factory: gale.factory



`World` no construye el `LogPair` directamente con `LogPair(x, y)`; lo pide, en cambio, a un objeto dedicado a construirlos:

```python
from gale.factory import Factory

class World:
    def __init__(self, generate_logs: bool = False) -> None:
        self.log_pair_factory: Factory = Factory(LogPair)

```

`Factory` (`gale.factory`) es una implementación pequeña y genérica del patrón Factory: envuelve un prototipo y expone un único método, `create(x, y, properties=None)`, que arma la instancia:

```python
def create(self, x, y, properties=None) -> T:
    if properties is None:
        properties = {}
    properties = {**properties, "x": x, "y": y}
    return self._prototype(**properties)

```

**[ESPACIO PARA IMAGEN AQUÍ - Figura 4.8: Diagrama ilustrando el patrón Factory. Muestra la clase World utilizando una Factory (vía log_pair_factory) que a su vez instancia y crea objetos LogPair.]**

#### 4.6.6. Colisión y puntaje



La detección de colisión combina dos chequeos independientes, resueltos en dos clases distintas. Contra el suelo en `World.collides`:

```python
def collides(self, rect: pygame.Rect) -> bool:
    if rect.bottom >= settings.VIRTUAL_HEIGHT:
        return True
    return any(log_pair.collides(rect) for log_pair in self.logs)

```

y contra cada par de troncos, en `LogPair.collides`:

```python
def collides(self, rect: pygame.Rect) -> bool:
    return self.get_top_rect().colliderect(rect) or self.get_bottom_rect().colliderect(rect)

```

Ambos chequeos se usan en el `update` de `PlayingState`:

```python
def update(self, dt: float) -> None:
    self.bird.update(dt)
    self.world.update(dt)

    if self.world.collides(self.bird.get_rect()):
        settings.SOUNDS["explosion"].play()
        settings.SOUNDS["hurt"].play()
        self.state_machine.change("count_down")
        return

    if self.world.update_scored(self.bird.get_rect()):
        self.score += 1
        settings.SOUNDS["score"].play()

```

---

### 4.7. Ejercicios propuestos



1. El juego, tal como está construido, no muestra el puntaje final al chocar: pasa directo de `PlayingState` a `CountDownState`. Añadir un cuarto estado, `GameOverState`, que reciba el puntaje final por parámetro de `enter` (de la misma manera en que `CountDownState` recibe el mundo), lo muestre en pantalla, y transicione a `CountDownState` solo cuando el jugador presione una tecla.


2. Añadir un estado de pausa que se active con una tecla, congele la actualización del juego sin perder su estado, y pueda reanudarse exactamente donde quedó. Discutir por qué, con una `StateMachine` simple, este estado de pausa necesita poder reconstruir o recibir todo lo que `PlayingState` tenía en el momento de pausar, y cómo cambiaría esa necesidad si en cambio se usara una `StateStack` (Capítulo 8).


3. Explicar, en términos del código de `StateMachine.change` mostrado en este capítulo, por qué dos estados distintos nunca pueden quedar activos simultáneamente en una `StateMachine`, y por qué esa garantía es exactamente lo que la distingue de una `StateStack`.


4. Modificar `World.update` para que `TIME_TO_SPAWN_LOGS` y el rango de variación vertical entre troncos consecutivos (actualmente `random.randint(-20, 20)`) se combinen de forma que, a medida que el puntaje crece, el espaciado disminuya y la variación aumente, incrementando gradualmente la dificultad.