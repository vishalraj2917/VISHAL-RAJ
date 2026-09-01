import logging
import json
import httpx
from typing import Dict, Any, List, Optional
from app.config import settings
from app.schemas.ai import EnvironmentalContext, ChatMessage, AIReportSections

logger = logging.getLogger(__name__)

# Base System Prompts enforcing strict boundaries, factual precision, and medical disclaimers
BASE_CHAT_PROMPT = """You are an AI Environmental and Air Quality Assistant for the AI Air Quality Prediction System.
Your role is to explain air quality metrics, pollutant impacts, and general environmental safety precautions clearly and concisely.

RULES AND BOUNDARIES:
1. USE ONLY THE SUPPLIED ENVIRONMENTAL DATA. Do NOT invent, hallucinate, or modify AQI values or pollutant levels.
2. The AQI value provided in the context comes from the verified GradientBoostingRegressor ML model. Treat it as authoritative.
3. If no live data is provided in context, politely ask the user to provide their location or note that real-time measurements are not active.
4. MEDICAL BOUNDARY: You are an environmental science AI, NOT a doctor. You MUST NOT diagnose illnesses, prescribe medications, or provide medical treatment plans.
5. Provide actionable, practical safety tips (e.g. wearing N95 masks during high PM2.5, using indoor air purifiers, timing outdoor exercise).
6. Keep answers concise, helpful, and easily understandable for the general public."""

REPORT_SYSTEM_PROMPT = """You are an AI Air Quality Analyst.
Your task is to analyze the provided environmental readings and ML AQI prediction and generate a structured executive report.

RULES:
1. Use ONLY the provided context telemetry.
2. Structure your analysis into clear, professional insights.
3. You must output a JSON object with EXACTLY the following keys:
   - "summary": (String) Brief high-level summary of the current air quality state.
   - "air_quality_analysis": (String) Explanation of the dominant pollutants and AQI level.
   - "weather_impact": (String) Analysis of how temperature, wind speed, humidity, and pressure affect pollution buildup or dispersion.
   - "safety_recommendations": (Array of Strings) 3 to 5 clear, bullet-pointed action items for the public.
4. Output valid JSON only, without additional markdown formatting or wrappers."""

HEALTH_ADVICE_PROMPT = """You are an AI Environmental Health and Safety Advisor.
Analyze the user's intended activity, target audience group, and the current environmental/AQI readings.

RULES:
1. Determine the safety rating: "Safe", "Caution", or "Unfavorable".
2. Provide tailored preventive advice for the specified activity.
3. You must output a JSON object with EXACTLY the following keys:
   - "safety_rating": ("Safe", "Caution", or "Unfavorable")
   - "advice": (String) Concise 2-3 sentence personalized guidance.
   - "recommended_precautions": (Array of Strings) 2 to 4 specific precautions (e.g., optimal hours, hydration, protective gear).
4. STRICT MEDICAL BOUNDARY: Do not diagnose medical conditions. Always focus on environmental exposure reduction.
5. Output valid JSON only."""


class AIService:
    """
    Service layer for AI features: Chatbot, Report Generation, and Health Advice.
    Supports external LLM APIs (Gemini/OpenAI/Compatible) with clean fallback and strict validation.
    """

    def __init__(
        self,
        api_key: Optional[str] = settings.AI_API_KEY,
        provider: str = settings.AI_PROVIDER,
        timeout: float = settings.AI_REQUEST_TIMEOUT_SECONDS,
    ):
        self.api_key = api_key
        self.provider = provider.lower()
        self.timeout = timeout

    def _format_context_text(self, context: Optional[EnvironmentalContext]) -> str:
        """
        Builds clear, structured text representation of live environmental data for LLM prompt.
        """
        if not context:
            return "No real-time environmental context provided."

        lines = ["CURRENT ENVIRONMENTAL TELEMETRY & ML PREDICTION:"]
        if context.city_name:
            lines.append(f"- Location: {context.city_name}")
        elif context.latitude is not None and context.longitude is not None:
            lines.append(f"- Coordinates: {context.latitude}°N, {context.longitude}°E")

        if context.predicted_aqi is not None:
            lines.append(f"- ML Predicted AQI: {context.predicted_aqi} ({context.aqi_category or 'Standard'})")
        if context.dominant_pollutant:
            lines.append(f"- Dominant Pollutant: {context.dominant_pollutant}")

        # Pollutants
        p_list = []
        if context.pm25 is not None: p_list.append(f"PM2.5: {context.pm25} µg/m³")
        if context.pm10 is not None: p_list.append(f"PM10: {context.pm10} µg/m³")
        if context.co is not None: p_list.append(f"CO: {context.co} mg/m³")
        if context.no2 is not None: p_list.append(f"NO2: {context.no2} µg/m³")
        if context.so2 is not None: p_list.append(f"SO2: {context.so2} µg/m³")
        if context.o3 is not None: p_list.append(f"O3: {context.o3} µg/m³")
        if p_list:
            lines.append(f"- Pollutant Concentrations: {', '.join(p_list)}")

        # Weather
        w_list = []
        if context.temperature is not None: w_list.append(f"Temperature: {context.temperature}°C")
        if context.humidity is not None: w_list.append(f"Humidity: {context.humidity}%")
        if context.wind_speed is not None: w_list.append(f"Wind Speed: {context.wind_speed} km/h")
        if context.pressure is not None: w_list.append(f"Pressure: {context.pressure} hPa")
        if w_list:
            lines.append(f"- Meteorological Conditions: {', '.join(w_list)}")

        if context.observed_at:
            lines.append(f"- Observation Time: {context.observed_at}")

        return "\n".join(lines)

    async def _call_gemini_api(self, contents: List[Dict[str, Any]], system_prompt: str) -> str:
        """
        Calls Google Gemini API (v1beta) using HTTP request without heavy SDK dependencies.
        """
        if not self.api_key:
            raise PermissionError("AI_API_KEY is not configured.")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.AI_MODEL}:generateContent?key={self.api_key}"
        payload = {
            "system_instruction": {
                "parts": [{"text": system_prompt}]
            },
            "contents": contents,
            "generationConfig": {
                "maxOutputTokens": settings.AI_MAX_OUTPUT_TOKENS,
                "temperature": 0.3,
            }
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, json=payload)
            if response.status_code == 401 or response.status_code == 403:
                raise PermissionError("Invalid or unauthorized AI_API_KEY.")
            if response.status_code == 429:
                raise RuntimeError("AI service quota or rate limit exceeded.")
            response.raise_for_status()

            data = response.json()
            candidates = data.get("candidates", [])
            if not candidates:
                raise ValueError("No candidate text returned by AI provider.")
            return candidates[0]["content"]["parts"][0]["text"]

    async def generate_chat_reply(
        self,
        message: str,
        context: Optional[EnvironmentalContext] = None,
        history: Optional[List[ChatMessage]] = None,
    ) -> str:
        """
        Generates conversational response to user questions using environmental context.
        """
        context_str = self._format_context_text(context)
        system_instruction = f"{BASE_CHAT_PROMPT}\n\n{context_str}"

        # If API key is available, call live LLM
        if self.api_key:
            try:
                contents = []
                if history:
                    for h in history[-6:]:  # Last 6 messages for context
                        role = "user" if h.role == "user" else "model"
                        contents.append({"role": role, "parts": [{"text": h.content}]})
                contents.append({"role": "user", "parts": [{"text": message}]})

                return await self._call_gemini_api(contents, system_instruction)
            except Exception as e:
                logger.warning(f"External AI call failed, falling back to rule-based engine: {e}")

        # Deterministic Rule-Based Fallback Engine (Runs when AI_API_KEY is not set or network offline)
        return self._generate_rule_based_chat_reply(message, context)

    def _generate_rule_based_chat_reply(self, message: str, context: Optional[EnvironmentalContext]) -> str:
        """
        Robust, rule-based environmental knowledge engine providing accurate responses
        without calling external APIs or inventing data.
        """
        msg_lower = message.lower()
        aqi = context.predicted_aqi if context else None
        cat = context.aqi_category if context else "Moderate"
        dom = context.dominant_pollutant if context else "PM2.5"

        if "safe" in msg_lower or "exercise" in msg_lower or "run" in msg_lower or "outdoor" in msg_lower:
            if aqi is not None:
                if aqi <= 50:
                    return f"The current predicted AQI is {aqi:.1f} ({cat}). Air quality is satisfactory, and outdoor exercise poses little to no risk."
                elif aqi <= 100:
                    return f"The current predicted AQI is {aqi:.1f} ({cat}). Air quality is acceptable for most people; however, unusually sensitive individuals should consider reducing prolonged heavy outdoor exertion."
                elif aqi <= 200:
                    return f"The current predicted AQI is {aqi:.1f} ({cat}). Members of sensitive groups may experience health effects. It is advisable to limit intense outdoor workouts and consider indoor training."
                else:
                    return f"The current predicted AQI is {aqi:.1f} ({cat}). Air pollution is elevated. Everyone should reduce strenuous outdoor activity and consider wearing an N95 mask outdoors."
            return "Based on standard environmental guidelines, air safety depends on current local AQI and pollutant concentrations. Please provide your coordinates to see real-time advice."

        if "pm2.5" in msg_lower or "pm25" in msg_lower:
            pm_val = f"{context.pm25} µg/m³" if context and context.pm25 is not None else "measured locally"
            return f"PM2.5 refers to fine particulate matter with a diameter smaller than 2.5 micrometers. Current concentration is {pm_val}. Due to its tiny size, PM2.5 can penetrate deep into the lungs and bloodstream. Sources include vehicle exhaust, combustion, and industrial emissions."

        if "pm10" in msg_lower:
            pm10_val = f"{context.pm10} µg/m³" if context and context.pm10 is not None else "measured locally"
            return f"PM10 refers to inhalable coarse particles between 2.5 and 10 micrometers (such as road dust, pollen, and construction debris). Current level is {pm10_val}."

        if "aqi" in msg_lower or "index" in msg_lower:
            if aqi is not None:
                return f"Your current ML predicted Air Quality Index is {aqi:.1f}, placing it in the '{cat}' category. The dominant contributing pollutant is {dom}."
            return "The Air Quality Index (AQI) is a standard scale from 0 to 500 indicating air cleanliness: 0-50 (Good), 51-100 (Moderate), 101-200 (Unhealthy for Sensitive Groups), 201-300 (Poor), 301-400 (Very Poor), and 401+ (Hazardous)."

        if "reduce" in msg_lower or "mask" in msg_lower or "protect" in msg_lower or "precaution" in msg_lower:
            return "To minimize air pollution exposure: 1) Keep windows closed during peak traffic hours, 2) Use high-efficiency HEPA air purifiers indoors, 3) Wear a fitted N95 or equivalent respirator when outdoor AQI is high, and 4) Avoid exercising near major roadways."

        # General helpful fallback
        if aqi is not None:
            return f"Currently, the AI system predicts an AQI of {aqi:.1f} ({cat}) with dominant pollutant {dom}. Temperature is {context.temperature or 'N/A'}°C with {context.humidity or 'N/A'}% humidity. Feel free to ask about specific pollutants, safety recommendations, or exercise guidance."
        return "I am your AI Air Quality Assistant. You can ask about current AQI safety, specific pollutant impacts (PM2.5, PM10, Ozone), protective measures, or outdoor activity recommendations."

    async def generate_report(self, context: EnvironmentalContext) -> AIReportSections:
        """
        Generates structured air quality report with summary, pollutant breakdown, and advice.
        """
        context_str = self._format_context_text(context)

        if self.api_key:
            try:
                raw_text = await self._call_gemini_api(
                    [{"role": "user", "parts": [{"text": f"Generate structured report for the following context:\n\n{context_str}"}]}],
                    REPORT_SYSTEM_PROMPT
                )
                # Parse JSON output
                clean_json = raw_text.strip().replace("```json", "").replace("```", "").strip()
                parsed = json.loads(clean_json)
                return AIReportSections(
                    summary=parsed.get("summary", ""),
                    air_quality_analysis=parsed.get("air_quality_analysis", ""),
                    weather_impact=parsed.get("weather_impact", ""),
                    safety_recommendations=parsed.get("safety_recommendations", []),
                )
            except Exception as e:
                logger.warning(f"External report generation failed, using rule-based report generator: {e}")

        # Deterministic Rule-Based Report Builder
        aqi = context.predicted_aqi or 50.0
        cat = context.aqi_category or "Moderate"
        dom = context.dominant_pollutant or "PM2.5"
        temp = context.temperature or 25.0
        wind = context.wind_speed or 5.0
        humidity = context.humidity or 50.0

        summary = f"Air quality is currently classified as {cat} with a predicted composite AQI of {aqi:.1f}. Primary air quality dynamics are driven by {dom} concentrations."

        analysis = (
            f"Machine learning inference evaluates current particulate and gaseous metrics: "
            f"PM2.5 is at {context.pm25 or 'N/A'} µg/m³, PM10 at {context.pm10 or 'N/A'} µg/m³, and Ozone at {context.o3 or 'N/A'} µg/m³. "
            f"The dominant pollutant {dom} is the primary factor influencing current health indicators."
        )

        wind_effect = "assisting active dispersion of surface particulate matter" if wind > 10.0 else "limiting horizontal pollutant dispersion"
        weather = f"Atmospheric temperature is {temp}°C with {humidity}% relative humidity. Wind speed of {wind} km/h is currently {wind_effect}."

        recs = [
            f"Maintain awareness of {dom} levels, particularly during morning and evening rush hours.",
            "Sensitive individuals with asthma or cardiovascular conditions should limit prolonged outdoor physical exertion." if aqi > 50 else "Air conditions are suitable for general outdoor activities.",
            "Ensure indoor ventilation filters are clean and consider HEPA air purification in urban areas.",
            "Stay well-hydrated and follow local municipal air advisories."
        ]

        return AIReportSections(
            summary=summary,
            air_quality_analysis=analysis,
            weather_impact=weather,
            safety_recommendations=recs,
        )

    async def generate_health_advice(
        self,
        activity: str,
        target_group: str,
        context: EnvironmentalContext,
    ) -> Dict[str, Any]:
        """
        Generates personalized health & activity advice based on environmental data.
        """
        context_str = self._format_context_text(context)

        if self.api_key:
            try:
                user_prompt = f"Activity: {activity}\nTarget Group: {target_group}\n\n{context_str}"
                raw_text = await self._call_gemini_api(
                    [{"role": "user", "parts": [{"text": user_prompt}]}],
                    HEALTH_ADVICE_PROMPT
                )
                clean_json = raw_text.strip().replace("```json", "").replace("```", "").strip()
                parsed = json.loads(clean_json)
                return {
                    "safety_rating": parsed.get("safety_rating", "Caution"),
                    "advice": parsed.get("advice", "Follow general air quality precautions."),
                    "recommended_precautions": parsed.get("recommended_precautions", []),
                }
            except Exception as e:
                logger.warning(f"External health advice generation failed, using rule-based generator: {e}")

        # Deterministic Rule-Based Health Advisor
        aqi = context.predicted_aqi or 50.0

        if aqi <= 50:
            rating = "Safe"
            advice = f"Environmental conditions are excellent for {activity.lower()}. Atmospheric pollution levels pose minimal health concerns for {target_group.lower()}."
            precautions = [
                "Enjoy outdoor activities without restrictions.",
                "Stay hydrated during extended exertion."
            ]
        elif aqi <= 100:
            rating = "Caution" if "sensitive" in target_group.lower() else "Safe"
            advice = f"Air quality is acceptable for {activity.lower()}. However, sensitive individuals may experience slight respiratory irritation during prolonged high-intensity workouts."
            precautions = [
                "Choose routes away from heavy motor vehicle traffic.",
                "Take intermittent rest breaks if feeling shortness of breath.",
                "Monitor for any mild coughing or throat dryness."
            ]
        elif aqi <= 200:
            rating = "Caution"
            advice = f"Elevated AQI ({aqi:.1f}) suggests taking precautions for {activity.lower()}, particularly for {target_group.lower()}."
            precautions = [
                "Reduce the duration and intensity of outdoor workouts.",
                "Consider exercising indoors or shifting to early morning hours.",
                "Wear an N95 particulate mask if active near roadways."
            ]
        else:
            rating = "Unfavorable"
            advice = f"Air pollution levels are high ({aqi:.1f}). Outdoor {activity.lower()} is not recommended for {target_group.lower()}."
            precautions = [
                "Move all aerobic activities indoors to an air-filtered environment.",
                "Keep windows closed and utilize indoor air purifiers.",
                "Wear a fitted N95 respirator if outdoor transit is unavoidable."
            ]

        return {
            "safety_rating": rating,
            "advice": advice,
            "recommended_precautions": precautions,
        }


# Singleton service provider
_ai_service_instance: Optional[AIService] = None

def get_ai_service() -> AIService:
    global _ai_service_instance
    if _ai_service_instance is None:
        _ai_service_instance = AIService()
    return _ai_service_instance
