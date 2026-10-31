"""Busca os vídeos mais recentes do canal e salva em videos.json.

Por padrão, os Shorts são ignorados: só entram vídeos comuns (horizontais).
"""
import json
import os
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET

CHANNEL_ID = "UCIYMd5BLAl2Cz1rsfmWdSFg"
FEED = f"https://www.youtube.com/feeds/videos.xml?channel_id={CHANNEL_ID}"
QTD = 3  # quantos vídeos mostrar
# Para voltar a incluir os Shorts, mude "nao" para "sim":
INCLUIR_SHORTS = os.environ.get("INCLUIR_SHORTS", "nao").lower() == "sim"

NS = {"a": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015"}
UA = {"User-Agent": "Mozilla/5.0 (compatible; atualizar-videos)", "Accept-Language": "pt-BR,pt;q=0.9"}


def ler_feed(xml_bytes):
    raiz = ET.fromstring(xml_bytes)
    videos = []
    for e in raiz.findall("a:entry", NS):
        vid = e.findtext("yt:videoId", namespaces=NS)
        titulo = e.findtext("a:title", namespaces=NS)
        data = e.findtext("a:published", namespaces=NS) or ""
        link = ""
        for l in e.findall("a:link", NS):
            if l.get("rel", "alternate") == "alternate":
                link = l.get("href", "")
        if vid and titulo:
            videos.append({"id": vid, "title": titulo.strip(), "published": data, "link": link})
    videos.sort(key=lambda v: v["published"], reverse=True)
    return videos


class SemRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def verificar_short(video_id):
    """True = Short, False = vídeo comum, None = não deu para saber.

    Um Short abre direto em /shorts/ID; um vídeo comum é redirecionado
    para /watch?v=ID.
    """
    req = urllib.request.Request(f"https://www.youtube.com/shorts/{video_id}", headers=UA)
    try:
        with urllib.request.build_opener(SemRedirect).open(req, timeout=20) as r:
            return True if r.status == 200 else None
    except urllib.error.HTTPError as e:
        if e.code in (301, 302, 303, 307, 308) and "/watch" in e.headers.get("Location", ""):
            return False
        return None
    except Exception:
        return None


def escolher(videos):
    if INCLUIR_SHORTS:
        return videos[:QTD]
    escolhidos = []
    for v in videos:
        if "/shorts/" in v.get("link", ""):
            print(f"Ignorado (Short): {v['title']}")
            continue
        resultado = verificar_short(v["id"])
        if resultado is False:
            escolhidos.append(v)
        else:
            motivo = "Short" if resultado else "não deu para verificar"
            print(f"Ignorado ({motivo}): {v['title']}")
        if len(escolhidos) == QTD:
            break
    return escolhidos


def main():
    req = urllib.request.Request(FEED, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        videos = ler_feed(r.read())
    lista = [{"id": v["id"], "title": v["title"]} for v in escolher(videos)]
    if not lista:
        sys.exit("Nenhum vídeo comum encontrado; videos.json não foi alterado.")
    with open("videos.json", "w", encoding="utf-8") as f:
        json.dump(lista, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"{len(lista)} vídeos salvos.")


if __name__ == "__main__":
    main()
