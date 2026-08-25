"""
Lanzador para F5.

Cada estudio de caso de este repo tiene que ejecutarse con el directorio de
trabajo puesto en su propia carpeta, porque hace `import settings` y
`from src...` relativos a ella. Este script recibe la ruta del archivo que
tengas abierto en el editor, sube por el arbol hasta encontrar el `main.py`
del proyecto al que pertenece, y lo ejecuta desde ahi.

Se usa `runpy` en vez de lanzar un proceso aparte a proposito: asi el juego
corre DENTRO de este mismo proceso y los breakpoints que pongas en cualquier
archivo del juego siguen funcionando.
"""

import os
import runpy
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def find_project_root(start: Path) -> Path:
    """Sube desde `start` hasta encontrar una carpeta con main.py."""
    start = start if start.is_dir() else start.parent

    for directory in (start, *start.parents):
        if (directory / "main.py").is_file():
            return directory

        # No salirse del repo buscando main.py en el resto del disco.
        if directory == REPO_ROOT:
            break

    games = sorted(
        p.parent.name for p in REPO_ROOT.glob("*/main.py")
    )
    sys.exit(
        f"\nNo encontre un main.py subiendo desde:\n  {start}\n\n"
        "Abri un archivo que este DENTRO de la carpeta de un juego y volve a\n"
        "darle F5. Los juegos disponibles son:\n"
        + "".join(f"  - {g}\n" for g in games)
    )


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit("Uso: run_current_game.py <ruta-de-un-archivo-del-juego>")

    project = find_project_root(Path(sys.argv[1]).resolve())
    entry_point = project / "main.py"

    print(f"Ejecutando {project.name} ...\n")

    # Replicar exactamente lo que pasa al hacer `cd <juego> && python main.py`:
    # el cwd y la primera entrada de sys.path apuntan a la carpeta del juego.
    os.chdir(project)
    sys.path.insert(0, str(project))
    sys.argv = [str(entry_point)]

    runpy.run_path(str(entry_point), run_name="__main__")


if __name__ == "__main__":
    main()
