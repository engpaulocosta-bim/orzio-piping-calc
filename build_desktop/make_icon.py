"""Gera build_desktop/sidct.ico a partir do PNG fonte transparente.

Garante:
  * canal alpha real (sem fundo branco/opaco residual);
  * remoção de pixels brancos quase-transparentes que aparecem como halo;
  * todos os tamanhos que o Windows precisa (16/24/32/48/64/128/256).

Uso:
    python build_desktop/make_icon.py
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
# Fonte preferida: PNG já com canal alpha. Cai para a versão 256 se faltar.
SOURCE_CANDIDATES = [
    HERE / "sidct_icon_transparent.png",
    HERE / "sidct_256.png",
]
OUT_ICO = HERE / "sidct.ico"
ICON_SIZES = [16, 24, 32, 48, 64, 128, 256]

# Pixels quase-brancos com alpha já baixo são resíduo da máscara de recorte;
# zeramos o alpha deles para eliminar o halo branco em volta do desenho.
WHITE_THRESHOLD = 244
HALO_ALPHA_MAX = 250


def _source() -> Path:
    for cand in SOURCE_CANDIDATES:
        if cand.exists():
            return cand
    raise FileNotFoundError(
        "Nenhuma fonte de ícone encontrada: " + ", ".join(map(str, SOURCE_CANDIDATES))
    )


def _clean_halo(img: Image.Image) -> Image.Image:
    """Remove o halo branco: pixels brancos com alpha não-total viram transparentes
    e o conteúdo opaco é forçado a alpha 255 (evita o aspecto 'lavado')."""
    img = img.convert("RGBA")
    px = img.load()
    w, h = img.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            is_white = r >= WHITE_THRESHOLD and g >= WHITE_THRESHOLD and b >= WHITE_THRESHOLD
            if is_white and a <= HALO_ALPHA_MAX:
                px[x, y] = (r, g, b, 0)          # halo branco -> transparente
            elif a >= 200:
                px[x, y] = (r, g, b, 255)        # conteúdo -> totalmente opaco
    return img


def main() -> None:
    src = _source()
    base = Image.open(src).convert("RGBA")
    base = _clean_halo(base)

    # Normaliza para 256x256 e deixa o PIL gerar todos os tamanhos a partir daí.
    # (Passar `sizes` na imagem base é o que de facto embute múltiplas resoluções;
    # `append_images` sozinho não preserva os tamanhos no formato ICO.)
    if base.size != (256, 256):
        base = base.resize((256, 256), Image.LANCZOS)
    base.save(
        OUT_ICO,
        format="ICO",
        sizes=[(s, s) for s in ICON_SIZES],
    )
    print(f"Fonte : {src.name}")
    print(f"Gerado: {OUT_ICO}  ({', '.join(f'{s}x{s}' for s in ICON_SIZES)})")


if __name__ == "__main__":
    main()
