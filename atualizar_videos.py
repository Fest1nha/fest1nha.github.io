"""Busca os vídeos mais recentes do canal e salva em videos.json."""
import json
import os
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET

CHANNEL_ID = "UCIYMd5BLAl2Cz1rsfmWdSFg"
FEED = f"https://www.youtube.com/feeds/videos.xml?channel_id={CHANNEL_ID}"
QTD = 3  # quantos vídeos mostrar
# Para mostrar só vídeos longos (sem Shorts), mude "sim" para "nao":
INCLUIR_SHORTS = os.environ.get("INCLUIR_SHORTS", "sim").lower() != "nao"

NS = {"a": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015"}
UA = {"User-Agent": "Mozilla/5.0 (compatible; atualizar-videos)"}


def ler_feed(xml_bytes):
    raiz = ET.fromstring(xml_bytes)
    videos = []
    for e in raiz.findall("a:entry", NS):
        vid = e.findtext("yt:videoId", namespaces=NS)
        titulo = e.findtext("a:title", namespaces=NS)
        data = e.findtext("a:published", namespaces=NS) or ""
        if vid and titulo:
            videos.append({"id": vid, "title": titulo.strip(), "published": data})
    videos.sort(key=lambda v: v["published"], reverse=True)
    return videos


class SemRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def eh_short(video_id):
    """Shorts abrem direto em /shorts/ID; vídeos comuns são redirecionados."""
    req = urllib.request.Request(f"https://www.youtube.com/shorts/{video_id}", headers=UA)
    try:
        with urllib.request.build_opener(SemRedirect).open(req, timeout=20) as r:
            return r.status == 200
    except Exception:
        return False


def escolher(videos):
    if INCLUIR_SHORTS:
        return videos[:QTD]
    escolhidos = []
    for v in videos:
        if not eh_short(v["id"]):
            escolhidos.append(v)
        if len(escolhidos) == QTD:
            break
    return escolhidos


def main():
    req = urllib.request.Request(FEED, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        videos = ler_feed(r.read())
    lista = [{"id": v["id"], "title": v["title"]} for v in escolher(videos)]
    if not lista:
        sys.exit("Nenhum vídeo encontrado; videos.json não foi alterado.")
    with open("videos.json", "w", encoding="utf-8") as f:
        json.dump(lista, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"{len(lista)} vídeos salvos.")


if __name__ == "__main__":
    main()
