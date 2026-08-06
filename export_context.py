#!/usr/bin/env python3

from pathlib import Path
import argparse


SEPARATOR = "=" * 80


def export_context(output: str, paths: list[str]) -> None:
    """
    Exporta el contenido de archivos y directorios a un único archivo.
    """

    output_path = Path(output)

    with output_path.open("w", encoding="utf-8") as out:

        for item in paths:
            path = Path(item)

            if path.is_dir():
                for file in sorted(path.rglob("*")):
                    if file.is_file():

                        out.write("\n")
                        out.write(f"{SEPARATOR}\n")
                        out.write(f"FILE: {file}\n")
                        out.write(f"{SEPARATOR}\n")

                        try:
                            out.write(file.read_text(encoding="utf-8"))
                        except UnicodeDecodeError:
                            out.write("[Archivo binario omitido]")

                        out.write("\n")

            elif path.is_file():

                out.write("\n")
                out.write(f"{SEPARATOR}\n")
                out.write(f"FILE: {path}\n")
                out.write(f"{SEPARATOR}\n")

                try:
                    out.write(path.read_text(encoding="utf-8"))
                except UnicodeDecodeError:
                    out.write("[Archivo binario omitido]")

                out.write("\n")

            else:
                print(f"No encontrado: {path}")

    print(f"Generado: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Exporta archivos y directorios a un único archivo de contexto."
    )

    parser.add_argument(
        "output",
        nargs="?",
        default="contexto.txt",
        help="Archivo de salida",
    )

    parser.add_argument(
        "paths",
        nargs="+",
        help="Archivos o directorios a exportar",
    )

    args = parser.parse_args()

    export_context(args.output, args.paths)


if __name__ == "__main__":
    main()