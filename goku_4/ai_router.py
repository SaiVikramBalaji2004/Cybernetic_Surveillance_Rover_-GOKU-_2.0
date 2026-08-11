import logging
import datetime
from typing import Optional
from groq_assistant import groq_assistant
from gemini_assistant import gemini_assistant
from gemini_vision import gemini_vision
from web_search import web_search
from weather_module import weather_module
from media_control import media_control
from config import AI_ROUTING

logger = logging.getLogger('GOKU.AIRouter')

class AIRouter:
    def __init__(self):
        self.groq = groq_assistant
        self.gemini = gemini_assistant
        self.vision = gemini_vision
        self.web_search = web_search
        self.weather = weather_module
        self.media = media_control
        self.default_model = AI_ROUTING.get('default_model', 'groq')
        self.fallback_enabled = AI_ROUTING.get('fallback_enabled', True)

    def _get_current_context(self):
        now = datetime.datetime.now()
        return f"Today is {now.strftime('%A, %B %d, %Y')}. The current year is {now.year}."

    def _get_current_context(self):
        now = datetime.datetime.now()
        return f"Today is {now.strftime('%A, %B %d, %Y')}. The current year is {now.year}."

    def _get_time_date(self):
        now = datetime.datetime.now()
        day = now.strftime("%A")
        date = now.strftime("%B %d, %Y")
        time_str = now.strftime("%I:%M %p")
        hour = now.hour
        if hour < 12:
            greeting = "Good morning"
        elif hour < 17:
            greeting = "Good afternoon"
        else:
            greeting = "Good evening"
        return f"{greeting}! It's {day}, {date}, and the time is {time_str}."

    def _is_time_query(self, query):
        ql = query.lower().strip()
        patterns = [
            "what time", "what date", "what day", "current time",
            "current date", "today's date", "day is it",
            "what's the time", "whats the time", "what's the date", "whats the date",
            "tell me the time", "tell me the date",
            "time is it", "date is it", "time now", "date today",
            "tell time", "what day is today", "what day is it",
            "today's day", "todays day",
        ]
        return any(p in ql for p in patterns)

    def _is_weather_query(self, query):
        return self.weather.needs_weather(query)

    def _is_music_query(self, query):
        ql = query.lower().strip()
        music_patterns = [
            "play song", "play music", "play the song", "play some",
            "play a song", "play me a song", "play me some",
            "play track", "play the track",
        ]
        if any(p in ql for p in music_patterns):
            return True
        if ql.startswith("play ") and ("song" in ql or "music" in ql or "track" in ql):
            return True
        if ql.startswith("play ") and len(ql) > 6:
            return True
        return False

    def _is_music_control(self, query):
        ql = query.lower().strip()
        control_patterns = [
            "pause music", "pause song", "pause the", "pause it",
            "resume music", "resume song", "resume the", "resume it",
            "pause", "resume",
            "stop music", "stop song", "stop playing",
        ]
        if any(p in ql for p in control_patterns):
            return True
        if self.media.is_playing():
            if ql in ("pause", "resume", "stop"):
                return True
        return False

    def _is_navigation_query(self, query):
        ql = query.lower().strip()
        nav_patterns = [
            "where should i go", "which way", "how should i move",
            "navigate to", "go to", "move to", "best route",
            "best path", "avoid", "obstacle ahead",
            "safe to go", "is it safe", "can i go",
            "which direction", "what direction", "should i go",
        ]
        return any(p in ql for p in nav_patterns)

    def _is_follow_command(self, query):
        ql = query.lower().strip()
        follow_patterns = [
            "follow me", "follow this", "follow my",
            "track device", "track my", "track this",
            "follow phone", "follow my phone",
            "track phone", "track my phone",
            "bluetooth follow", "follow via bluetooth",
        ]
        if any(p in ql for p in follow_patterns):
            return True
        if 'follow' in ql and ('device' in ql or 'phone' in ql or 'mac' in ql or 'bluetooth' in ql):
            return True
        return False

    def _is_save_mac_command(self, query):
        ql = query.lower().strip()
        save_patterns = [
            "save my device", "save my mac", "save my phone",
            "set my device", "set my mac", "set target",
            "save this device", "save this as my",
            "set my phone", "save phone mac",
        ]
        return any(p in ql for p in save_patterns)

    def _is_alarm_command(self, query):
        ql = query.lower().strip()
        kw = ['set alarm', 'create alarm', 'alarm at', 'alarm for',
              'delete alarm', 'remove alarm', 'cancel alarm', 'list alarms', 'show alarms']
        return any(k in ql for k in kw)

    def _is_timer_command(self, query):
        ql = query.lower().strip()
        kw = ['set timer', 'create timer', 'timer for', 'start timer',
              'delete timer', 'remove timer', 'cancel timer', 'stop timer',
              'pause timer', 'resume timer', 'list timers', 'show timers',
              'set reminder', 'remind me', 'timer ', 'half hour', 'half-hour']
        return any(k in ql for k in kw)

    def _is_search_query(self, query):
        return self.web_search.needs_search(query)

    def _is_movement_command(self, query):
        cl = query.lower().strip()
        move_phrases = ['go forward', 'go backward', 'go back', 'move forward',
                        'move backward', 'move back', 'go left', 'go right',
                        'move left', 'move right', 'turn left', 'turn right']
        if any(p in cl for p in move_phrases):
            return True
        if cl in ('forward', 'backward', 'back', 'left', 'right', 'stop', 'reverse', 'move'):
            return True
        return False

    def _is_home_control(self, query):
        cl = query.lower().strip()
        devices = ['light', 'lights', 'fan', 'ac ', 'air conditioning', 'garage', 'gate', 'outlet']
        actions = [' turn on ', ' turn off ', ' switch on ', ' switch off ', ' on ', ' off ']
        return any(d in cl for d in devices) and any(a in cl for a in actions)

    def _is_vision_query(self, query):
        ql = query.lower().strip()
        vision_patterns = [
            "search for", "search the", "where is", "where are",
            "what do you see", "what can you see", "what is in front",
            "what is ahead", "look at", "tell me what",
            "how many", "count the", "count how many",
            "what color", "what colour", "what shape",
            "is there a", "is there an", "do you see",
            "find the", "find my", "locate",
            "describe what", "read the", "what does it say",
            "who is", "what person",
            "identify", "what is this", "what are these",
            "what am i holding", "what am i showing",
            "how many fingers", "showing",
            "what is on", "what is on the",
            "look around and", "look around", "scan for",
            "what is around", "what's around", "whats around", "what's in front", "whats in front",
            "what's ahead", "whats ahead", "what's there", "whats there",
            "describe the room", "describe the area", "describe surroundings",
            "describe environment", "describe where",
            "is anyone", "is somebody", "is someone",
            "can you see me", "can you see anything",
            "what room", "where am i",
            "what is near", "what's near", "whats near", "who is near",
            "what's happening", "what is happening",
            "what does it look like", "how does it look",
            "what am i looking at", "what am i seeing",
            "tell me about this", "tell me about that",
            "what do you notice", "what do you observe",
            "do you see anything", "notice anything",
            "describe the scene", "describe what you see",
            "what is there", "what's out there", "whats out there",
            "who is with me", "who's with me",
            "what are you looking at", "what are you seeing",
        ]
        return any(p in ql for p in vision_patterns)

    def _build_vision_prompt(self, query):
        ql = query.lower().strip()
        if 'search for' in ql or 'find the' in ql or 'find my' in ql:
            item = ql.replace('search for', '').replace('find the', '').replace('find my', '').strip()
            return f"Look at this image. Find '{item}'. Where is it located?"
        elif 'where is' in ql or 'where are' in ql:
            item = ql.replace('where is', '').replace('where are', '').strip()
            return f"Look at this image. Where is '{item}'?"
        elif 'how many fingers' in ql:
            return "Look at this image. How many fingers is the person showing?"
        elif 'how many' in ql or 'count' in ql:
            item = ql.replace('how many', '').replace('count the', '').replace('count how many', '').strip()
            return f"Look at this image. How many '{item}' do you see?"
        elif 'what color' in ql or 'what colour' in ql:
            item = ql.replace('what color', '').replace('what colour', '').replace('is', '').replace('are', '').strip()
            return f"Look at this image. What color is '{item}'?"
        elif 'what shape' in ql:
            item = ql.replace('what shape', '').replace('is', '').replace('are', '').strip()
            return f"Look at this image. What shape is '{item}'?"
        elif 'who is' in ql or 'what person' in ql or 'who is with' in ql or 'anyone' in ql or 'someone' in ql or 'somebody' in ql:
            return "Look at this image. Describe any person you see. Who is there? What are they wearing and doing?"
        elif 'what does it say' in ql or 'read the' in ql:
            return "Look at this image. Read any text visible."
        elif 'what do you see' in ql or 'what can you see' in ql:
            return "Look at this image. Describe everything you see."
        elif 'describe' in ql or 'what is around' in ql or "what's around" in ql or 'surroundings' in ql or 'environment' in ql or 'scene' in ql:
            return "Look at this image. Describe what you see in detail."
        elif 'where am i' in ql or 'what room' in ql:
            return "Look at this image. Describe the type of room or location. What kind of place is this?"
        elif 'can you see me' in ql or 'do you see me' in ql:
            return "Look at this image. Can you see a person? What are they doing?"
        elif 'what am i holding' in ql or 'what am i showing' in ql:
            return "Look at this image. What object is the person holding or showing?"
        elif 'what is happening' in ql or "what's happening" in ql:
            return "Look at this image. What is happening in this scene?"
        elif 'what is on' in ql or "what's on" in ql:
            item = ql.replace('what is on', '').replace("what's on", '').strip()
            return f"Look at this image. What is on '{item}'?"
        else:
            return f"Look at this image and answer: {query}"

    def _extract_music_query(self, query):
        cl = query.lower().strip()
        for trigger in ["play song", "play music", "play the song", "play some", "play a song", "play me", "play track", "play the track"]:
            if cl.startswith(trigger):
                query = cl[len(trigger):].strip()
                break
        else:
            if cl.startswith("play "):
                query = cl[5:].strip()
            else:
                query = cl

        languages = ["hindi", "tamil", "telugu", "malayalam", "kannada",
                     "bengali", "marathi", "punjabi", "gujarati",
                     "english", "spanish", "french", "german",
                     "japanese", "korean", "chinese", "arabic",
                     "portuguese", "italian", "russian", "urdu", "bhojpuri"]

        has_lang = any(lang in query for lang in languages)

        for word in ["song", "music", "track", "please", "now"]:
            if not has_lang or word not in ["song", "music"]:
                query = query.replace(word, "").strip()

        import re
        query = re.sub(r'\b(the|a|an)\b\s*', ' ', query).strip()
        query = re.sub(r'\s+(me|some)\b', '', query).strip()

        query = query.strip()
        return query if query else "popular song"

    def _extract_city(self, query):
        return self.weather.extract_city(query)

    def _parse_time(self, command):
        import re
        m = re.search(r'(\d{1,2})[:\.](\d{2})', command)
        if m:
            h, mi = int(m.group(1)), int(m.group(2))
            if 0 <= h <= 23 and 0 <= mi <= 59:
                return f"{h:02d}:{mi:02d}"
        m = re.search(r'\bat\s+(\d{1,2})\s+(\d{2})\b', command)
        if m:
            h, mi = int(m.group(1)), int(m.group(2))
            if 0 <= h <= 23 and 0 <= mi <= 59:
                return f"{h:02d}:{mi:02d}"
        return None

    def _parse_duration(self, command):
        import re
        cl = command.lower()
        spoken = {'one':1,'two':2,'three':3,'four':4,'five':5,'six':6,
                  'seven':7,'eight':8,'nine':9,'ten':10,'eleven':11,'twelve':12,
                  'thirteen':13,'fourteen':14,'fifteen':15,'sixteen':16,
                  'seventeen':17,'eighteen':18,'nineteen':19,'twenty':20,
                  'thirty':30,'forty':40,'fifty':50,'sixty':60,
                  'seventy':70,'eighty':80,'ninety':90,
                  'hundred':100}
        for word, val in spoken.items():
            cl = cl.replace(f'{word} minute', f'{val} minute')
            cl = cl.replace(f'{word} minutes', f'{val} minutes')
            cl = cl.replace(f'{word} second', f'{val} second')
            cl = cl.replace(f'{word} seconds', f'{val} seconds')
            cl = cl.replace(f'{word} hour', f'{val} hour')
            cl = cl.replace(f'{word} hours', f'{val} hours')

        cl = cl.replace('half hour', '30 minutes')
        cl = cl.replace('half minute', '30 seconds')
        cl = cl.replace('quarter hour', '15 minutes')
        cl = cl.replace('quarter of an hour', '15 minutes')
        cl = cl.replace('an hour', '1 hour')
        cl = cl.replace('a minute', '1 minute')
        cl = cl.replace('a second', '1 second')
        cl = cl.replace('a few minutes', '3 minutes')
        cl = cl.replace('a few seconds', '5 seconds')
        cl = cl.replace('a moment', '10 seconds')

        total = 0
        for pat, mult in [(r'(\d+)\s*(?:hours?|hrs?)\b', 3600),
                          (r'(\d+)\s*(?:minutes?|mins?)\b', 60),
                          (r'(\d+)\s*(?:seconds?|secs?)\b', 1)]:
            m = re.search(pat, cl)
            if m:
                total += int(m.group(1)) * mult

        if total == 0:
            m = re.search(r'(\d+)', cl)
            if m:
                val = int(m.group(1))
                if 'hour' in cl:
                    total = val * 3600
                elif 'minute' in cl or 'min' in cl:
                    total = val * 60
                elif 'second' in cl or 'sec' in cl:
                    total = val
                elif val <= 60:
                    total = val

        if total > 540000:
            return None

        return total if total > 0 else None

    def _extract_name(self, command):
        cl = command.lower()
        for kw in ['called ', 'named ']:
            if kw in cl:
                name = cl.split(kw, 1)[1].strip().rstrip('?')
                if name:
                    return name
        return "default"

    def _get_scene_context(self, image_bytes):
        if not image_bytes:
            return ""
        try:
            result = self.vision.describe_scene(image_bytes)
            if result:
                return result.strip()
        except Exception as e:
            logger.warning(f"Scene context failed: {e}")
        return ""

    def ask(self, question, image_bytes=None, preferred_model=None):
        ql = question.lower().strip()

        if self._is_time_query(question):
            logger.info(f"Time/date query: {question}")
            return self._get_time_date()

        if self._is_alarm_command(question):
            logger.info(f"Alarm query: {question}")
            return {'type': 'alarm', 'command': question}

        if self._is_timer_command(question):
            logger.info(f"Timer query: {question}")
            return {'type': 'timer', 'command': question}

        if self._is_movement_command(question):
            logger.info(f"Movement query: {question}")
            return {'type': 'movement', 'command': question}

        if self._is_home_control(question):
            logger.info(f"Home control query: {question}")
            return {'type': 'home_control', 'command': question}

        if self._is_follow_command(question):
            logger.info(f"Follow command: {question}")
            return {'type': 'follow', 'command': question}

        if self._is_weather_query(question):
            logger.info(f"Weather query: {question}")
            city = self._extract_city(question)
            weather_data = self.weather.get_weather(city)
            if weather_data:
                system_prompt = (
                    "You are GOKU, a friendly rover AI assistant. "
                    "Here is the current weather data. Present it in a natural, conversational way. "
                    "Be brief and friendly. 1-2 sentences max."
                )
                result = self.gemini.chat(f"Weather data: {weather_data}. {question}", system_prompt)
                if result:
                    logger.info("Gemini weather response")
                    return result
                return weather_data
            return "Unable to get weather right now. Please try again."

        if self._is_music_query(question):
            logger.info(f"Music query: {question}")
            song_query = self._extract_music_query(question)
            result = self.media.play_song(song_query)
            if result:
                system_prompt = (
                    "You are GOKU, a friendly rover AI assistant. "
                    f"The user asked to play music. The result was: {result}. "
                    "Respond naturally and briefly. 1 sentence max."
                )
                gemini_response = self.gemini.chat(question, system_prompt)
                if gemini_response:
                    logger.info("Gemini music response")
                    return gemini_response
                return result
            return "Could not find that song. Try a different name."

        if self._is_music_control(question):
            logger.info(f"Music control query: {question}")
            return self.media.process_command(question)

        if self._is_search_query(question):
            logger.info(f"Search query: {question}")
            search_result = self.web_search.search(question)

            current_date = self._get_current_context()
            system_prompt = (
                f"{current_date} You are GOKU, a knowledgeable AI assistant with live web access. "
                "ALWAYS use the web search results as your primary source of truth. "
                "Your training data has a cutoff, but the web search results are CURRENT and up-to-date. "
                "Base your answer primarily on the search results provided. "
                "If the search results contain relevant current information, use it. "
                "Answer directly and accurately. "
                "Do not add greetings, filler, or extra commentary. "
                "Give only the factual answer. 1-3 sentences max."
            )

            if search_result:
                system_prompt = (
                    f"{current_date} You are GOKU, a knowledgeable AI assistant with live web access. "
                    f"Here is current, up-to-date information from the web:\n"
                    f"{search_result}\n\n"
                    "ALWAYS use this web search result as your PRIMARY source of truth. "
                    "Your training data cutoff does not apply here - the search results are from today. "
                    "Base your answer primarily on this current information. "
                    "Answer directly and accurately. "
                    "Do not add greetings, filler, or extra commentary. "
                    "Give only the factual answer. 1-3 sentences max."
                )
                logger.info("Using web search results as context")

            result = self.gemini.chat(question, system_prompt)
            if result:
                logger.info("Gemini responded to search query")
                return result

            if self.fallback_enabled:
                logger.info("Gemini failed, fallback to Groq for search query")
                result = self.groq.chat(question, system_prompt)
                if result:
                    logger.info("Groq responded to search query")
                    return result

            if search_result:
                return search_result[:300]

            return "Unable to find information about that right now. Please try again."

        if self._is_vision_query(question) and image_bytes is not None and len(image_bytes) > 0:
            logger.info(f"Vision query (image={len(image_bytes)} bytes): {question}")
            return self._ask_vision(question, image_bytes)

        if image_bytes is not None and len(image_bytes) > 0 and self._is_navigation_query(question):
            logger.info(f"Navigation via vision: {question}")
            return self._ask_navigation(question)

        scene_context = self._get_scene_context(image_bytes) if image_bytes else ""
        logger.info(f"General query: {question} (scene={'yes' if scene_context else 'no'})")
        return self._ask_text(question, scene_context)

    def _ask_text(self, question, scene_context=""):
        system_prompt = (
            "You are GOKU, a friendly and capable rover AI assistant. "
            "You can navigate autonomously, answer questions, search the web, "
            "check weather, play music in any language, set alarms and timers, "
            "control home devices, and see through your camera. "
            "Answer the question directly and accurately. "
            "Do not add greetings, filler, or extra commentary. "
            "Give only the factual answer. 1-3 sentences max."
        )
        if scene_context:
            system_prompt += (
                f"\n\nYour camera currently sees: {scene_context}"
                "\nUse this as context about the environment when answering."
            )

        result = self.groq.chat(question, system_prompt)
        if result:
            logger.info("Groq responded")
            return result

        if self.fallback_enabled:
            logger.info("Groq failed, fallback to Gemini")
            result = self.gemini.chat(question, system_prompt)
            if result:
                logger.info("Gemini responded")
                return result

        logger.warning("All text AI backends failed")
        return "Unable to answer right now. Please try again."

    def _ask_vision(self, question, image_bytes):
        if not image_bytes:
            logger.error("No image for vision query")
            return self._ask_text(question)

        vision_prompt = self._build_vision_prompt(question)
        system_prompt = "You see through your camera. Look at the image and answer the question directly. Describe only what you see. 2-3 sentences max."

        result = self.vision.analyze(image_bytes, vision_prompt, system_prompt)
        if result:
            logger.info("Gemini Vision responded")
            return result

        logger.info("Gemini Vision failed, using Groq with camera context")
        groq_prompt = f"I am a rover with a camera.\n\nQuestion: {question}\n\nAnswer directly. 2-3 sentences max."

        result = self.groq.chat(groq_prompt, system_prompt="You are a rover AI that sees through a camera. Answer directly based on the camera view.")
        if result:
            logger.info("Groq responded with vision context")
            return result

        logger.warning("All AI backends failed for vision query")
        return "Unable to see right now. Please try again later."

    def _ask_navigation(self, question):
        system_prompt = (
            "You are a rover navigation AI. "
            "Answer ONLY with the best direction to move: forward, left, right, or backward. "
            "Then give a brief reason. 1-2 sentences max. Be direct."
        )
        prompt = f"Question: {question}\n\nWhat is the best route?"

        result = self.groq.chat(prompt, system_prompt)
        if result:
            logger.info(f"Groq navigation: {result}")
            return result

        logger.warning("Navigation AI failed")
        return "Cannot determine route right now."

    def route(self, command):
        cl = command.lower().strip()

        if self._is_movement_command(command):
            return {'type': 'movement'}

        if self._is_home_control(command):
            return {'type': 'home_control'}

        if self._is_save_mac_command(command):
            return {'type': 'save_mac'}

        if self._is_follow_command(command):
            return {'type': 'follow'}

        if any(k in cl for k in ['scan', 'investigate', 'sweep']):
            return {'type': 'scan'}

        return {'type': 'ai_query'}

    def is_vision_query(self, command):
        return self._is_vision_query(command)

ai_router = AIRouter()
