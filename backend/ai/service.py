"""
NILA AI Service
Orchestrates grounded question answering, tool execution, and natural language explanation.
Owned by: Gugaan
"""

import json
import re
from typing import Optional, Dict, Any, Tuple
from backend.ai.schemas import AskRequest, AskResponse, ToolExecutionResult
from backend.ai.client import GeminiClient
from backend.ai.tools import NilaTools
from backend.ai.prompts import SYSTEM_PROMPT, format_tool_explanation_prompt


def _extract_scenario_params(question: str) -> Dict[str, Any]:
    """
    Deterministically extracts what-if simulation parameters from natural language.
    """
    params: Dict[str, Any] = {
        "attendance_multiplier": 1.0,
        "rain_probability": 0.0,
        "event_delay_minutes": 0,
        "bus_failure": 0
    }
    q_lower = question.lower()

    # Attendance percentage increase: e.g. "increases by 30%", "attendance increases by 30%", "30% increase"
    att_match = re.search(r'(?:increase[sd]?|attendance)\s*(?:by\s*)?(\d+)\s*%', q_lower)
    if not att_match:
        att_match = re.search(r'(\d+)\s*%\s*(?:increase|more|attendance|higher)', q_lower)
    if att_match:
        pct = float(att_match.group(1))
        params["attendance_multiplier"] = round(1.0 + (pct / 100.0), 2)

    # Rain percentage: e.g. "rain 70%", "70% rain", "it rains 70%"
    rain_match = re.search(r'(\d+)\s*%\s*(?:rain|chance of rain|precipitation)', q_lower)
    if not rain_match:
        rain_match = re.search(r'(?:rain|rains|precipitation)\s*(?:by|at|of)?\s*(\d+)\s*%', q_lower)
    if rain_match:
        params["rain_probability"] = float(rain_match.group(1))
    elif "rain" in q_lower or "monsoon" in q_lower:
        params["rain_probability"] = 60.0

    # Delay in minutes: e.g. "ends 30 minutes late", "delayed by 45 min"
    delay_match = re.search(r'(\d+)\s*(?:minutes|mins|min)\s*(?:late|delay|delayed)', q_lower)
    if not delay_match:
        delay_match = re.search(r'(?:delay|delayed)\s*(?:by)?\s*(\d+)\s*(?:minutes|mins|min)', q_lower)
    if delay_match:
        params["event_delay_minutes"] = int(delay_match.group(1))

    # Bus failure: e.g. "1 bus breaks down", "2 buses fail"
    bus_match = re.search(r'(\d+)\s*(?:bus|buses)\s*(?:fail|break down|breakdown|unavailable)', q_lower)
    if not bus_match:
        bus_match = re.search(r'(?:fail|failure|breakdown)\s*(?:of)?\s*(\d+)\s*(?:bus|buses)', q_lower)
    if bus_match:
        params["bus_failure"] = int(bus_match.group(1))

    return params


class NilaAIService:
    """
    Grounded AI copilot service.
    Orchestrates intent routing, tool execution, and grounded explanation.
    """

    def __init__(
        self,
        gemini_client: Optional[GeminiClient] = None,
        tools: Optional[NilaTools] = None
    ):
        self.client = gemini_client if gemini_client else GeminiClient()
        self.tools = tools if tools else NilaTools()

    def route_and_execute_tool(
        self,
        question: str,
        festival_id: str
    ) -> Tuple[str, ToolExecutionResult, str]:
        """
        Determines the appropriate backend tool based on the question and executes it.
        Returns: (tool_name, tool_result, source_name)
        """
        q = question.lower()

        # 1. Trade-offs and Bus Movement Inquiries
        if any(w in q for w in ("tradeoff", "trade-off", "why move", "moving a bus", "reposition")):
            res = self.tools.get_tradeoffs(festival_id)
            return "get_tradeoffs", res, "NILA optimization engine"

        # 2. Optimization Plan Inquiries
        if any(w in q for w in ("bus plan", "allocation", "fleet plan", "recommend")):
            res = self.tools.get_current_plan(festival_id)
            return "get_current_plan", res, "NILA optimization engine"

        # 3. What-if Scenario Simulations
        if any(w in q for w in ("what happens if", "what if", "scenario", "delay", "increases by", "breaks down")):
            params = _extract_scenario_params(question)
            res = self.tools.simulate_scenario(
                festival_id=festival_id,
                attendance_multiplier=params["attendance_multiplier"],
                rain_probability=params["rain_probability"],
                event_delay_minutes=params["event_delay_minutes"],
                bus_failure=params["bus_failure"]
            )
            return "simulate_scenario", res, "NILA simulation engine"

        # 4. Risk and Bottleneck Inquiries
        if any(w in q for w in ("risk", "critical", "highest risk", "bottleneck", "choke point", "pressure", "why is")):
            res = self.tools.get_risk_analysis(festival_id)
            return "get_risk_analysis", res, "NILA prediction engine"

        # 5. Timing, Peaks, and Crowd Forecast
        if any(w in q for w in ("peak", "when will", "crowd forecast", "how many people", "attendance", "timeline")):
            res = self.tools.get_crowd_forecast(festival_id)
            return "get_crowd_forecast", res, "NILA prediction engine"

        # 6. Festival details
        if any(w in q for w in ("festival", "temple", "gate", "how many stops", "stops")):
            res = self.tools.get_festival_details(festival_id)
            return "get_festival_details", res, "NILA festival registry"

        # Default fallback to risk analysis
        res = self.tools.get_risk_analysis(festival_id)
        return "get_risk_analysis", res, "NILA prediction engine"

    def _generate_fallback_summary(
        self,
        question: str,
        tool_name: str,
        tool_result: ToolExecutionResult
    ) -> str:
        """
        Generates a crisp, deterministic control-room summary if Gemini is unreachable.
        Never fabricates AI text; directly translates mathematical tool metrics into an operator brief.
        """
        if tool_result.status == "unavailable":
            return tool_result.data.get("message", "Service temporarily unavailable.")

        if tool_result.status == "error":
            return f"NILA Backend Notice: {tool_result.error}"

        data = tool_result.data

        if tool_name == "get_risk_analysis":
            overall_lvl = data.get("overall_risk_level", "MODERATE")
            overall_score = data.get("overall_risk_score", 0)
            high_stops = data.get("high_risk_stops", [])
            crit_stops = data.get("critical_stops", [])
            peak_t = data.get("peak_time", "N/A")

            lines = [
                f"[Grounded NILA Forecast Brief]",
                f"Overall Network Risk: {overall_lvl} (Score: {overall_score}/100) peaking at {peak_t}.",
            ]
            if crit_stops:
                lines.append(f"Critical Bottleneck Stops: {', '.join(crit_stops)}.")
            elif high_stops:
                lines.append(f"High Risk Stops: {', '.join(high_stops)}.")
            else:
                lines.append("All transport terminals operating within baseline capacity.")
            return " ".join(lines)

        elif tool_name == "simulate_scenario":
            changes = data.get("changes", {})
            scen = data.get("scenario", {})
            peak_change = changes.get("peak_crowd_change", 0)
            pct_change = changes.get("peak_crowd_change_percent", 0.0)
            risk_change = changes.get("risk_score_change", 0)
            new_crit = changes.get("new_critical_stops", [])

            lines = [
                f"[Grounded NILA Simulation Brief]",
                f"Under this scenario (Attendance: {scen.get('attendance_multiplier')}x, "
                f"Rain: {scen.get('rain_probability')}%, Delay: +{scen.get('event_delay_minutes')}m), "
                f"Peak crowd shifts by {peak_change:+,} ({pct_change:+0.1f}%), elevating network risk score by {risk_change:+d} points."
            ]
            if new_crit:
                lines.append(f"Newly Critical Terminals: {', '.join(new_crit)}.")
            return " ".join(lines)

        elif tool_name == "get_crowd_forecast":
            peak_c = data.get("peak_crowd", 0)
            peak_t = data.get("peak_time", "N/A")
            return (
                f"[Grounded NILA Forecast Brief] Festival crowd is projected to peak at "
                f"{peak_c:,} attendees at approximately {peak_t}."
            )

        elif tool_name == "get_festival_details":
            name = data.get("name", "Festival")
            stops = [s["name"] for s in data.get("stops", [])]
            return f"[Grounded NILA Brief] {name} is configured with {len(stops)} bus terminals: {', '.join(stops)}."

        return f"[Grounded NILA Brief] Authoritative data loaded for {tool_name}."

    def ask(self, request: AskRequest) -> AskResponse:
        """
        Main query entrypoint matching the planned POST /api/ai/ask contract.
        """
        festival_id = request.festival_id
        tool_name, tool_result, source_name = self.route_and_execute_tool(
            request.question, festival_id
        )

        tool_data_json = json.dumps(tool_result.data, indent=2)

        # 1. Attempt generation with Gemini if available
        if self.client.is_available():
            prompt = format_tool_explanation_prompt(
                question=request.question,
                tool_name=tool_name,
                tool_output=tool_data_json
            )
            ai_answer = self.client.generate(
                prompt=prompt,
                system_instruction=SYSTEM_PROMPT
            )
            if ai_answer:
                return AskResponse(
                    answer=ai_answer,
                    tool_used=tool_name,
                    tool_calls=[tool_name],
                    grounded=True,
                    sources=[source_name],
                    fallback_used=False
                )

        # 2. Graceful fallback when Gemini is not configured, unreachable, or errors
        fallback_answer = self._generate_fallback_summary(
            request.question, tool_name, tool_result
        )
        return AskResponse(
            answer=fallback_answer,
            tool_used=tool_name,
            tool_calls=[tool_name],
            grounded=True,
            sources=[source_name],
            fallback_used=True
        )
