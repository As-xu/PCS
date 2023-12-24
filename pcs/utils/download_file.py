from typing import Any
import m3u8


class M3u8Downloader:
    def __init__(self, m3u8_url:str, params:Any=None) -> None:
        self.url = m3u8_url
        self.params = params

    def download(self):
        async with aiohttp.ClientSession() as session:


class M3u8Parser:
    def __init__(self, m3u8_url:str, params:Any=None) -> None:
        self.url = m3u8_url
        self.params = params

    def parse(self) -> Any:
        playlist = self._parse(self.url)
        if playlist:
            return self.get_file_urls_and_paths(playlist)

        return None

    def _parse(self, m3u8_url):
        playlist = m3u8.load(m3u8_url)
        if playlist.is_variant:
            playlists = playlist.playlists
            if len(playlists) > 0:
                subPlaylist = playlists[0]  # 默认取第一个，有多个的情况，其实可以优化（应该是选择分辨率高的）
                subM3u8Url = subPlaylist.absolute_uri
                return self._parse(subM3u8Url)
            else:
                return None
        else:
            return playlist

    def get_file_urls_and_paths(self, playlist) -> object:
        all_paths = []
        temp_path = 'F:/data'
        for seg in playlist.segments:
            if not seg: break

            all_paths.append({
                "m3u8_url": seg.absolute_uri,
                "local_path": temp_path + '/' + self.get_url_last_path(seg.uri)
            })

        for key in playlist.keys:
            if not key: break

            all_paths.append({
                "m3u8_url": key.absolute_uri,
                "local_path": temp_path + '/' + self.get_url_last_path(key.uri)
            })
        return all_paths

    def get_url_last_path(self, uri):
        return uri

if __name__ == '__main__':

    url = 'https://s5.bfbfvip.com/video/xiangyaochengweiyingzhishilizhedierji/%E7%AC%AC01%E9%9B%86/index.m3u8'
    m  = M3u8Parser(url)
    m.parse()
    pass