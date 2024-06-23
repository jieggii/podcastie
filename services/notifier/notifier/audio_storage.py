import asyncio
import os.path
import random
import string

import aiofiles
import aiohttp
from pydub import AudioSegment


class _Downloader:
    chunk_size: int
    http_session: aiohttp.ClientSession

    def __init__(self, chunk_size: int, timeout: int):
        self.chunk_size = chunk_size
        self.http_session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout))

    async def download_file(self, url: str, output_path: str):
        async with self.http_session.get(url) as response:
            response.raise_for_status()
            async with aiofiles.open(output_path, mode="wb") as file:
                async for chunk in response.content.iter_chunked(self.chunk_size):
                    await file.write(chunk)

    async def close(self):
        await self.http_session.close()


class _Compressor:
    def __init__(self):
        pass

    @staticmethod
    def _compress_file_sync(input_path: str, output_path: str, target_size: int) -> None:
        """Target_size in bytes."""
        audio = AudioSegment.from_file(input_path)
        duration_sec = int(len(audio) / 1000)

        target_size_bits = target_size * 8
        target_bitrate = int((target_size_bits / duration_sec) / 1000)

        audio.export(output_path, format="mp3", bitrate=f"{target_bitrate}k", parameters=["-vbr", "4"])

    async def compress_file(self, input_path: str, output_path: str, target_size: int):
        await asyncio.to_thread(
            self._compress_file_sync,
            input_path,
            output_path,
            target_size,
        )


def _generate_filename() -> str:
    random_part = "".join([random.choice(string.ascii_letters) for _ in range(7)])
    return f"{random_part}.mp3"


def _generate_compressed_filename(original_filename: str) -> str:
    return f"{original_filename[:len(original_filename)-4]}_compressed.mp3"


class AudioStorage:
    path: str
    downloader: _Downloader
    compressor: _Compressor

    def __init__(self, path: str, download_chunk_size: int, download_timeout: int):
        self.path = path

        self.downloader = _Downloader(download_chunk_size, download_timeout)
        self.compressor = _Compressor()

    def get_file_path(self, filename: str):
        return os.path.join(self.path, filename)

    async def download(self, url: str) -> str:
        filename = _generate_filename()
        filepath = os.path.join(self.path, filename)

        await self.downloader.download_file(url, filepath)
        return filename

    async def compress_file(self, filename: str, target_size: int) -> str:
        """Compresses file, target_size in bytes."""
        original_filepath = self.get_file_path(filename)
        compressed_filepath = self.get_file_path(_generate_compressed_filename(filename))

        await self.compressor.compress_file(original_filepath, compressed_filepath, target_size)
        return compressed_filepath

    async def close(self):
        await self.downloader.close()
