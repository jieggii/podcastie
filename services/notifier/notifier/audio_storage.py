import asyncio
import os.path
import random
import string

import aiofiles
import aiohttp
from pydub import AudioSegment


def _compress_mp3_sync(input_path: str, output_path: str, target_size: int) -> None:
    """Target_size in bytes."""
    audio = AudioSegment.from_file(input_path)
    duration_sec = int(len(audio) / 1000)

    target_size_bits = target_size * 8
    target_bitrate = int((target_size_bits / duration_sec) / 1000)

    audio.export(output_path, format="mp3", bitrate=f"{target_bitrate}k", parameters=["-vbr", "4"])


async def _compress_file(input_path: str, output_path: str, target_size: int):
    await asyncio.to_thread(
        _compress_mp3_sync,
        input_path,
        output_path,
        target_size,
    )


async def _download_file(url: str, output_path: str, chunk_size: int, timeout: int):
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
        async with session.get(url) as response:
            response.raise_for_status()  # todo?
            async with aiofiles.open(output_path, mode="wb") as file:
                async for chunk in response.content.iter_chunked(chunk_size):
                    await file.write(chunk)


def _generate_filename() -> str:
    random_part = "".join([random.choice(string.ascii_letters) for _ in range(7)])
    return f"{random_part}.mp3"


def _generate_compressed_filename(original_filename: str) -> str:
    return f"{original_filename[:len(original_filename)-4]}_compressed.mp3"


class AudioStorage:
    path: str

    def __init__(self, path: str):
        self.path = path

    def get_file_path(self, filename: str):
        return os.path.join(self.path, filename)

    async def download(self, url: str, chunk_size: int, timeout: int) -> str:
        filename = _generate_filename()
        filepath = os.path.join(self.path, filename)

        await _download_file(url, filepath, chunk_size=chunk_size, timeout=timeout)
        return filename

    async def compress_file(self, filename: str, target_size: int) -> str:
        """Compresses file, target_size in bytes."""
        original_filepath = self.get_file_path(filename)
        compressed_filepath = self.get_file_path(_generate_compressed_filename(filename))

        await _compress_file(original_filepath, compressed_filepath, target_size)
        return compressed_filepath
