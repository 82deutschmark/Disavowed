import json
import os
import logging
from typing import Any, AsyncGenerator, Dict, Generator, Iterable, Optional

from openai import AsyncOpenAI, OpenAI


class OpenAIIntegration:
    """Integration with OpenAI's Responses API for story generation."""

    BASE_INSTRUCTIONS = (
        "You are a professional game narrative designer creating high-stakes espionage choose-your-own-adventure "
        "experiences. Always follow the requested JSON schema exactly, keep tone bold and cinematic, and never add "
        "out-of-band commentary."
    )

    STREAM_EVENT_DELTA = "delta"
    STREAM_EVENT_RESPONSE = "response"
    STREAM_EVENT_ERROR = "error"

    def __init__(self) -> None:
        api_key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=api_key)
        self.async_client = AsyncOpenAI(api_key=api_key)
        self.model = os.getenv("OPENAI_TEXT_MODEL", "gpt-5-nano")
        self.default_temperature = 0.8
        self.default_max_output_tokens = 2048

        self.SCHEMA_LIMITS = {
            "mission_title": 200,
            "mission_description": 1000,
            "objective": 255,
            "deadline": 200,
            "setting": 255,
            "narrative_style": 100,
            "mood": 100,
            "opening_narrative": 1500,
            "choice_text": 255,
            "primary_conflict": 255,
            "narrative_text": 1500,
            "character_name": 200,
            "next_node_summary": 255,
        }

    def _collect_output_text(self, response: Any) -> str:
        text = getattr(response, "output_text", None)
        if text:
            return text

        collected: list[str] = []
        for item in getattr(response, "output", []) or []:
            for content in getattr(item, "content", []) or []:
                segment = getattr(content, "text", None)
                if segment:
                    collected.append(segment)

        if collected:
            return "".join(collected)

        data = getattr(response, "data", None)
        if isinstance(data, Iterable):
            for entry in data:
                message = getattr(entry, "message", None)
                if message and hasattr(message, "content"):
                    for content in message.content or []:
                        segment = getattr(content, "text", None)
                        if segment:
                            collected.append(segment)
        return "".join(collected)

    def _build_request_params(
        self,
        instructions: str,
        input_text: str,
        *,
        temperature: Optional[float] = None,
        max_output_tokens: Optional[int] = None,
        response_format: Optional[Dict[str, Any]] = None,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {
            "model": model or self.model,
            "instructions": instructions,
            "input": input_text,
            "temperature": temperature if temperature is not None else self.default_temperature,
            "max_output_tokens": max_output_tokens if max_output_tokens is not None else self.default_max_output_tokens,
        }
        if response_format:
            params["response_format"] = response_format
        return params

    def _request_response(
        self,
        *,
        instructions: str,
        input_text: str,
        temperature: Optional[float] = None,
        max_output_tokens: Optional[int] = None,
        response_format: Optional[Dict[str, Any]] = None,
        model: Optional[str] = None,
        stream: bool = False,
    ):
        params = self._build_request_params(
            instructions,
            input_text,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            response_format=response_format,
            model=model,
        )
        expect_json = response_format and response_format.get("type") == "json_object"

        if stream:
            return self._stream_response(params, expect_json=bool(expect_json))

        response = self.client.responses.create(**params)
        raw_text = self._collect_output_text(response)
        if expect_json:
            return self.safe_json_parse(raw_text)
        return raw_text

    def _stream_response(self, params: Dict[str, Any], *, expect_json: bool) -> Generator[Dict[str, Any], None, None]:
        def iterator() -> Generator[Dict[str, Any], None, None]:
            collected_chunks: list[str] = []
            with self.client.responses.stream(**params) as stream:
                for event in stream:
                    event_type = getattr(event, "type", "")
                    if event_type == "response.output_text.delta":
                        delta = getattr(event, "delta", "") or ""
                        if delta:
                            collected_chunks.append(delta)
                            yield {"type": self.STREAM_EVENT_DELTA, "text": delta}
                    elif event_type == "response.error":
                        error_detail = getattr(event, "error", None)
                        yield {"type": self.STREAM_EVENT_ERROR, "error": error_detail}
                final_response = stream.get_final_response()

            raw_text = "".join(collected_chunks) or self._collect_output_text(final_response)
            data = self.safe_json_parse(raw_text) if expect_json else raw_text
            yield {"type": self.STREAM_EVENT_RESPONSE, "data": data}

        return iterator()

    async def _request_response_async(
        self,
        *,
        instructions: str,
        input_text: str,
        temperature: Optional[float] = None,
        max_output_tokens: Optional[int] = None,
        response_format: Optional[Dict[str, Any]] = None,
        model: Optional[str] = None,
        stream: bool = False,
    ):
        params = self._build_request_params(
            instructions,
            input_text,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            response_format=response_format,
            model=model,
        )
        expect_json = response_format and response_format.get("type") == "json_object"

        if stream:
            return self._stream_response_async(params, expect_json=bool(expect_json))

        response = await self.async_client.responses.create(**params)
        raw_text = self._collect_output_text(response)
        if expect_json:
            return self.safe_json_parse(raw_text)
        return raw_text

    async def _stream_response_async(
        self, params: Dict[str, Any], *, expect_json: bool
    ) -> AsyncGenerator[Dict[str, Any], None]:
        collected_chunks: list[str] = []
        async with self.async_client.responses.stream(**params) as stream:
            async for event in stream:
                event_type = getattr(event, "type", "")
                if event_type == "response.output_text.delta":
                    delta = getattr(event, "delta", "") or ""
                    if delta:
                        collected_chunks.append(delta)
                        yield {"type": self.STREAM_EVENT_DELTA, "text": delta}
                elif event_type == "response.error":
                    error_detail = getattr(event, "error", None)
                    yield {"type": self.STREAM_EVENT_ERROR, "error": error_detail}
            final_response = await stream.get_final_response()

        raw_text = "".join(collected_chunks) or self._collect_output_text(final_response)
        data = self.safe_json_parse(raw_text) if expect_json else raw_text
        yield {"type": self.STREAM_EVENT_RESPONSE, "data": data}

    def safe_json_parse(self, raw_str: str):
        try:
            parsed_response = json.loads(raw_str)
            validated_data = self._validate_and_truncate(parsed_response)
            logging.info("Successfully parsed and validated OpenAI JSON response")
            return validated_data
        except json.JSONDecodeError as exc:
            logging.error("Unexpected JSON decode error: %s", exc)
            logging.error("Raw response: %s", raw_str)
            return None
        except Exception as exc:
            logging.error("Unexpected error in safe_json_parse: %s", exc)
            return None

    def _validate_and_truncate(self, data):
        if isinstance(data, dict):
            validated = {}
            for key, value in data.items():
                if isinstance(value, str) and key in self.SCHEMA_LIMITS:
                    max_length = self.SCHEMA_LIMITS[key]
                    if len(value) > max_length:
                        logging.warning(
                            "Truncating field '%s' from %s to %s characters", key, len(value), max_length
                        )
                        validated[key] = value[:max_length]
                    else:
                        validated[key] = value
                elif isinstance(value, (dict, list)):
                    validated[key] = self._validate_and_truncate(value)
                else:
                    validated[key] = value
            return validated
        if isinstance(data, list):
            return [self._validate_and_truncate(item) for item in data]
        return data



    def generate_full_mission_story(
        self,
        mission_giver,
        villain,
        partner,
        random_character,
        player_name,
        player_gender,
        narrative_style=None,
        mood=None,
        *,
        stream: bool = False,
    ):
        try:
            pronouns = {'he/him': 'he', 'she/her': 'she', 'they/them': 'they'}.get(player_gender, 'they')
            narrative_style = narrative_style or 'Modern Espionage Thriller'
            mood = mood or 'Action-packed and Suspenseful'

            def describe_character(char):
                if char.image_url:
                    desc = f"[See character image at {char.image_url}]"
                else:
                    desc = "Character appearance not described"

                traits = ""
                if char.character_traits:
                    if isinstance(char.character_traits, dict):
                        trait_list = []
                        for key, value in char.character_traits.items():
                            if value and value.strip():
                                trait_list.append(f"{key}: {value}")
                            else:
                                trait_list.append(key)
                        traits = ", ".join(trait_list)
                    elif isinstance(char.character_traits, list):
                        traits = ", ".join(char.character_traits)
                    else:
                        traits = str(char.character_traits)

                backstory = ""
                if char.backstory:
                    backstory = char.backstory if isinstance(char.backstory, str) else str(char.backstory)

                result = desc
                if traits:
                    result += f" TRAITS: {traits}."
                if backstory:
                    result += f" BACKSTORY: {backstory}"
                return result

            character_lines = "\n".join([
                f"- Mission Giver {mission_giver.character_name}: {describe_character(mission_giver)}",
                f"- Target/Villain {villain.character_name}: {describe_character(villain)}",
                f"- Partner {partner.character_name}: {describe_character(partner)}",
                f"- Additional Character {random_character.character_name}: {describe_character(random_character)}",
            ])

            instructions = (
                f"{self.BASE_INSTRUCTIONS} Return a JSON object describing a full mission package with metadata, an opening "
                "narrative, and three branching choices. Respect every length limit and schema requirement."
            )

            schema_description = (
                "Return JSON with this structure:\n"
                "{\n"
                '  "mission_title": "Brief mission title (<=200 chars)",\n'
                '  "mission_description": "2-3 paragraph mission briefing",\n'
                '  "objective": "Clear, actionable mission goal",\n'
                '  "difficulty": "low" | "medium" | "high",\n'
                '  "deadline": "Time constraint description (<=200 chars)",\n'
                '  "setting": "Concise location description (<=255 chars)",\n'
                f'  "narrative_style": "{narrative_style}",\n'
                f'  "mood": "{mood}",\n'
                '  "opening_narrative": "2-3 paragraphs setting the scene",\n'
                '  "choices": [\n'
                '    {"text": "Choice option", "character_used": "Name", "risk_level": "low|medium|high", "next_node_summary": "Outcome"}\n'
                '  ]\n'
                "}\n"
                "Never include extra fields or commentary."
            )

            requirements = (
                "Mission Requirements:\n"
                f"1. {mission_giver.character_name} briefs {player_name} on how to neutralize {villain.character_name}.\n"
                f"2. {partner.character_name} partners with the player.\n"
                f"3. Use {narrative_style} style and {mood} mood.\n"
                "4. The opening narrative should establish stakes and conclude at the first decision.\n"
                "5. Provide exactly three distinct choices with escalating risk."
            )

            input_text = (
                f"Player Profile:\n- Name: {player_name}\n- Pronouns: {pronouns}\n"
                f"- Preferred Style: {narrative_style}\n- Desired Mood: {mood}\n\n"
                f"Characters:\n{character_lines}\n\n"
                f"{requirements}\n\n"
                f"{schema_description}\nGenerate the mission package now."
            )

            response = self._request_response(
                instructions=instructions,
                input_text=input_text,
                max_output_tokens=2000,
                temperature=self.default_temperature,
                response_format={"type": "json_object"},
                stream=stream,
            )

            if stream:
                return response
            if not response:
                logging.error("Failed to obtain mission story data from OpenAI")
                return None

            logging.info("Successfully generated full mission story via Responses API")
            return response
        except Exception as exc:
            logging.error("Error in generate_full_mission_story: %s", exc)
            return None

    def generate_mission(self, mission_giver, *, stream: bool = False):
        try:
            instructions = (
                f"{self.BASE_INSTRUCTIONS} Produce a concise mission briefing that reflects the mission giver's personality. "
                "Return only the JSON schema described in the input."
            )

            character_profile = (
                f"Name: {mission_giver.character_name}\n"
                f"Role: {mission_giver.character_role}\n"
                f"Traits: {mission_giver.character_traits}\n"
                f"Backstory: {mission_giver.backstory}"
            )

            schema = (
                "Respond with JSON in this format:\n"
                "{\n"
                '  "title": "Mission title (<=200 chars)",\n'
                '  "description": "Brief mission description (2-3 sentences)",\n'
                '  "objective": "Clear objective statement",\n'
                '  "difficulty": "easy" | "medium" | "hard",\n'
                '  "deadline": "Narrative deadline description (<=200 chars)"\n'
                "}"
            )

            input_text = (
                "Mission Giver Profile:\n"
                f"{character_profile}\n\n"
                "Game tone: irreverent, high-stakes espionage.\n"
                "Craft an exciting mission that fits the character.\n\n"
                f"{schema}"
            )

            response = self._request_response(
                instructions=instructions,
                input_text=input_text,
                max_output_tokens=1000,
                temperature=self.default_temperature,
                response_format={"type": "json_object"},
                stream=stream,
            )

            if stream:
                return response
            return response or None
        except Exception as exc:
            logging.error("Error in generate_mission: %s", exc)
            return None

    def generate_story_opening(self, mission, mission_giver, *, stream: bool = False):
        try:
            character_name = mission_giver.character_name if mission_giver else "Unknown"
            instructions = (
                f"{self.BASE_INSTRUCTIONS} Write an opening scene that sets up the mission context. Return only the JSON schema "
                "provided."
            )

            input_text = (
                "Mission Context:\n"
                f"Title: {mission.title}\n"
                f"Description: {mission.description}\n"
                f"Mission Giver: {character_name}\n\n"
                "Write 2-3 paragraphs that build tension, brief the player, and conclude at the first decision point.\n"
                "Respond with JSON containing only {\n  \"opening_narrative\": \"...\"\n}."
            )

            response = self._request_response(
                instructions=instructions,
                input_text=input_text,
                max_output_tokens=1200,
                temperature=self.default_temperature,
                response_format={"type": "json_object"},
                stream=stream,
            )

            if stream:
                return response
            return response or None
        except Exception as exc:
            logging.error("Error in generate_story_opening: %s", exc)
            return None

    def generate_choices(
        self,
        current_narrative,
        character,
        game_state,
        available_characters=None,
        *,
        stream: bool = False,
    ):
        try:
            character_info = ""
            if character:
                character_info = f"Current character: {character.character_name} ({character.character_role})"

            character_pool = ""
            if available_characters:
                pool_lines = [
                    f"- {char.character_name}: {str(getattr(char, 'description', 'No description'))[:100]}"
                    for char in available_characters[:6]
                ]
                character_pool = "Available characters to feature:\n" + "\n".join(pool_lines) + "\n\n"

            instructions = (
                f"{self.BASE_INSTRUCTIONS} Provide exactly three espionage-themed choices with varied risk levels. Return only "
                "the specified JSON schema."
            )

            input_text = (
                f"Current narrative:\n{current_narrative}\n\n"
                f"{character_info}\n"
                f"Game state: {json.dumps(game_state) if game_state else 'Starting mission'}\n\n"
                f"{character_pool}"
                "Choices must mention different allies, outline consequences, and cover low/medium/high risk levels.\n"
                "Respond with {\n  \"choices\": [ { ... } ]\n}."
            )

            response = self._request_response(
                instructions=instructions,
                input_text=input_text,
                max_output_tokens=1500,
                temperature=self.default_temperature,
                response_format={"type": "json_object"},
                stream=stream,
            )

            if stream:
                return response
            return response or None
        except Exception as exc:
            logging.error("Error in generate_choices: %s", exc)
            return None

    def generate_story_continuation(
        self,
        previous_text,
        chosen_action,
        character,
        game_state,
        *,
        stream: bool = False,
    ):
        try:
            character_info = ""
            if character:
                character_info = f"Active character: {character.character_name}"

            instructions = (
                f"{self.BASE_INSTRUCTIONS} Continue the story based on the player's action. Return only the specified JSON "
                "schema."
            )

            input_text = (
                f"Previous narrative:\n{previous_text}\n\n"
                f"Player action: {chosen_action}\n"
                f"{character_info}\n"
                f"Game state: {json.dumps(game_state) if game_state else 'N/A'}\n\n"
                "Deliver a vivid continuation that shows consequences and sets up the next decision.\n"
                "Respond with {\n  \"narrative_text\": \"...\"\n}."
            )

            response = self._request_response(
                instructions=instructions,
                input_text=input_text,
                max_output_tokens=1500,
                temperature=self.default_temperature,
                response_format={"type": "json_object"},
                stream=stream,
            )

            if stream:
                return response
            return response or None
        except Exception as exc:
            logging.error("Error in generate_story_continuation: %s", exc)
            return None

    def generate_custom_choice_response(
        self,
        current_text,
        custom_action,
        character,
        game_state,
        *,
        stream: bool = False,
    ):
        try:
            character_info = ""
            if character:
                character_info = f"Active character: {character.character_name}"

            instructions = (
                f"{self.BASE_INSTRUCTIONS} Respond to an improvised player action. Return only the specified JSON schema."
            )

            input_text = (
                f"Current situation:\n{current_text}\n\n"
                f"Player's custom action: {custom_action}\n"
                f"{character_info}\n"
                f"Game state: {json.dumps(game_state) if game_state else 'N/A'}\n\n"
                "Acknowledge the action, portray consequences, and maintain espionage tone.\n"
                "Respond with {\n  \"narrative_text\": \"...\"\n}."
            )

            response = self._request_response(
                instructions=instructions,
                input_text=input_text,
                max_output_tokens=1500,
                temperature=self.default_temperature,
                response_format={"type": "json_object"},
                stream=stream,
            )

            if stream:
                return response
            return response or None
        except Exception as exc:
            logging.error("Error in generate_custom_choice_response: %s", exc)
            return None
