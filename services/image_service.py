from __future__ import annotations

import httpx
from pathlib import Path


def search_unsplash(query: str, count: int = 6) -> list[dict]:
    """Busca fotos no Unsplash usando a API pública (sem key necessária).

    Retorna lista de dicts com url, thumb, author, download_url.
    """
    # Unsplash API pública (limitada mas funcional para MVP)
    url = "https://unsplash.com/napi/search/photos"
    params = {
        "query": query,
        "per_page": count,
        "orientation": "portrait",  # melhor para Instagram 4:5
    }

    try:
        with httpx.Client(timeout=15) as client:
            resp = client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()

        results = []
        for photo in data.get("results", []):
            urls = photo.get("urls", {})
            user = photo.get("user", {})
            results.append({
                "id": photo.get("id", ""),
                "url": urls.get("regular", ""),  # 1080px wide
                "thumb": urls.get("small", ""),  # 400px thumb
                "full": urls.get("full", ""),  # full resolution
                "author": user.get("name", "Unknown"),
                "author_url": user.get("links", {}).get("html", ""),
                "alt": photo.get("alt_description", ""),
                "download_url": urls.get("regular", ""),
            })
        return results

    except Exception:
        # Fallback: tentar endpoint direto
        return _search_fallback(query, count)


def _search_fallback(query: str, count: int = 6) -> list[dict]:
    """Fallback usando source.unsplash.com para gerar URLs diretas."""
    results = []
    for i in range(count):
        # Cada URL com sig diferente gera imagem diferente
        url = f"https://source.unsplash.com/1080x1350/?{query}&sig={i}"
        results.append({
            "id": f"fallback_{i}",
            "url": url,
            "thumb": f"https://source.unsplash.com/400x500/?{query}&sig={i}",
            "full": url,
            "author": "Unsplash",
            "author_url": "https://unsplash.com",
            "alt": query,
            "download_url": url,
        })
    return results


def download_image(url: str, save_dir: str, filename: str = "bg_image.jpg") -> str:
    """Baixa imagem de URL e salva localmente. Retorna path."""
    save_path = Path(save_dir)
    save_path.mkdir(parents=True, exist_ok=True)
    file_path = save_path / filename

    with httpx.Client(timeout=30, follow_redirects=True) as client:
        resp = client.get(url)
        resp.raise_for_status()
        file_path.write_bytes(resp.content)

    return str(file_path)
