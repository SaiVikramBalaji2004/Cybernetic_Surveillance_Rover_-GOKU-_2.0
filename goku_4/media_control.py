import subprocess
import urllib.request
import urllib.parse
import re
import os
import threading
import logging
import socket
import time

logger = logging.getLogger('GOKU.Media')

YTDLP_PATHS = [
    '/home/sai/Desktop/goku_4/venv/bin/yt-dlp',
    '/usr/local/bin/yt-dlp',
    '/usr/bin/yt-dlp',
    'yt-dlp',
]

VLC_RC_PORT = 4212

def _find_ytdlp():
    for path in YTDLP_PATHS:
        try:
            result = subprocess.run([path, '--version'], capture_output=True, timeout=5)
            if result.returncode == 0:
                return path
        except:
            pass
    return None

class MediaControl:
    def __init__(self):
        self._playing = False
        self._paused = False
        self._stop_event = threading.Event()
        self._vlc_proc = None
        self._ytdlp_path = None
        self._current_song = None
        self._lock = threading.Lock()

    def initialize(self):
        self._ytdlp_path = _find_ytdlp()
        if self._ytdlp_path:
            logger.info(f"Media control initialized - yt-dlp: {self._ytdlp_path}")
        else:
            logger.warning("Media control initialized - yt-dlp not found, song search limited")
        return True

    def _send_rc_command(self, command):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            sock.connect(('127.0.0.1', VLC_RC_PORT))
            sock.sendall((command + '\n').encode())
            time.sleep(0.1)
            sock.close()
            return True
        except Exception as e:
            logger.warning(f"VLC RC command failed: {e}")
            return False

    def _search_youtube(self, query, max_results=3):
        if not self._ytdlp_path:
            logger.warning("yt-dlp not available for YouTube search")
            return None

        try:
            search_query = f"ytsearch{max_results}:{query}"
            cmd = [self._ytdlp_path, '--no-download', '--flat-playlist', '--print', 'id', search_query]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            if result.returncode == 0 and result.stdout.strip():
                video_ids = result.stdout.strip().split('\n')
                return [vid.strip() for vid in video_ids if vid.strip()][:max_results]
            return None
        except subprocess.TimeoutExpired:
            logger.warning("yt-dlp search timed out")
            return None
        except Exception as e:
            logger.warning(f"YouTube search failed: {e}")
            return None

    def _extract_video_id(self, query):
        m = re.search(r'(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})', query)
        return m.group(1) if m else None

    def play_song(self, query, language=None):
        with self._lock:
            if self._playing:
                self.stop()

            self._stop_event.clear()
            self._paused = False

            video_id = self._extract_video_id(query)
            if video_id:
                logger.info(f"Playing YouTube video ID: {video_id}")
                return self._start_playback(f"https://www.youtube.com/watch?v={video_id}", query)

            search_query = query
            if language:
                search_query = f"{query} {language} official music video"
            else:
                search_query = f"{query} official music video"

            logger.info(f"Searching for song: '{search_query}'")
            video_ids = self._search_youtube(search_query)

            if not video_ids:
                search_query = f"{query} song"
                logger.info(f"Retrying search: '{search_query}'")
                video_ids = self._search_youtube(search_query)

            if not video_ids:
                return f"Could not find '{query}'. Try a different name."

            video_id = video_ids[0]
            url = f"https://www.youtube.com/watch?v={video_id}"
            logger.info(f"Found video: {video_id}")
            self._current_song = query
            return self._start_playback(url, query)

    def _start_playback(self, url, display_name):
        def _play():
            try:
                cmd = [
                    'cvlc',
                    '--no-video',
                    '--play-and-exit',
                    '--network-caching=5000',
                    '--extraintf=rc',
                    f'--rc-host=127.0.0.1:{VLC_RC_PORT}',
                    url
                ]
                self._vlc_proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                self._playing = True
                logger.info(f"VLC started (PID: {self._vlc_proc.pid})")
                self._vlc_proc.wait()
                stdout, stderr = self._vlc_proc.communicate()
                if self._vlc_proc.returncode != 0:
                    logger.error(f"VLC exited with code {self._vlc_proc.returncode}")
                    logger.error(f"VLC stderr: {stderr.decode()[:200]}")
                logger.info("Playback finished")
            except Exception as e:
                logger.error(f"Playback error: {e}")
            finally:
                self._playing = False
                self._paused = False
                self._vlc_proc = None

        thread = threading.Thread(target=_play)
        thread.daemon = True
        thread.start()

        return f"Playing '{display_name}' now"

    def stop(self):
        with self._lock:
            if self._vlc_proc:
                try:
                    self._send_rc_command('quit')
                except:
                    pass
                try:
                    self._vlc_proc.terminate()
                except:
                    pass
                self._vlc_proc = None
            self._playing = False
            self._paused = False
            self._stop_event.set()
            logger.info("Music stopped")

    def pause(self):
        with self._lock:
            if not self._playing or self._paused:
                return False
            if self._send_rc_command('pause'):
                self._paused = True
                logger.info("Music paused")
                return True
            return False

    def resume(self):
        with self._lock:
            if not self._playing or not self._paused:
                return False
            if self._send_rc_command('play'):
                self._paused = False
                logger.info("Music resumed")
                return True
            return False

    def is_playing(self):
        return self._playing

    def is_paused(self):
        return self._paused

    def get_current_song(self):
        return self._current_song

    def process_command(self, command):
        cl = command.lower().strip()

        if "pause" in cl and self._playing:
            if self._paused:
                if self.resume():
                    return "Music resumed"
                return "Could not resume music"
            else:
                if self.pause():
                    return "Music paused"
                return "Could not pause music"

        if "resume" in cl and self._playing and self._paused:
            if self.resume():
                return "Music resumed"
            return "Could not resume music"

        music_keywords = [
            "play song", "play music", "play the song", "play some",
            "play a song", "play me", "play track",
            "song for", "music for", "track for",
        ]

        for kw in music_keywords:
            if kw in cl:
                query = cl
                for trigger in music_keywords:
                    query = query.replace(trigger, "").strip()

                for pre in ["play", "song", "music", "track", "the", "a", "me", "some"]:
                    if query.startswith(pre):
                        query = query[len(pre):].strip()

                if not query:
                    return "What song would you like me to play?"

                languages = {
                    "hindi": "hindi", "tamil": "tamil", "telugu": "telugu",
                    "malayalam": "malayalam", "kannada": "kannada",
                    "bengali": "bengali", "marathi": "marathi",
                    "punjabi": "punjabi", "gujarati": "gujarati",
                    "english": "english", "spanish": "spanish",
                    "french": "french", "german": "german",
                    "japanese": "japanese", "korean": "korean",
                    "chinese": "chinese", "arabic": "arabic",
                    "portuguese": "portuguese", "italian": "italian",
                    "russian": "russian", "urdu": "urdu",
                    "bhojpuri": "bhojpuri",
                }

                lang = None
                for lang_name, lang_code in languages.items():
                    if lang_name in cl:
                        lang = lang_code
                        break

                return self.play_song(query, language=lang)

        if cl.startswith("play ") and len(cl) > 5:
            song_name = cl[5:].strip()
            if song_name and not any(x in cl for x in ["pause", "resume", "stop"]):
                return self.play_song(song_name)

        if "stop music" in cl or "stop song" in cl or "stop playing" in cl or cl == "stop":
            self.stop()
            return "Music stopped"

        return None

media_control = MediaControl()
