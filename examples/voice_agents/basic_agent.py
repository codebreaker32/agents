import logging
import os
import re
from dotenv import load_dotenv

from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    MetricsCollectedEvent,
    WorkerOptions,
    RunContext,
    cli,
    metrics,
    room_io,
)

from livekit.plugins import groq, elevenlabs, deepgram, silero
from livekit.agents.llm import function_tool
from livekit.plugins.turn_detector.multilingual import MultilingualModel

logger = logging.getLogger("interrupt-agent")
load_dotenv()

import platform, signal

if platform.system() == "Windows":
    signal.signal = lambda *args, **kwargs: None

IGNORED_WORDS = {
    re.sub(r"(.)\1+", r"\1", w.strip().lower())
    for w in os.getenv("IGNORED_WORDS", "uh,umm,ummm,hmm,haan,erm,mm").split(",")
}

INTERRUPT_COMMANDS = {
    re.sub(r"(.)\1+", r"\1", w.strip().lower())
    for w in os.getenv("INTERRUPT_COMMANDS", "stop,wait,hold on,pause,excuse me").split(",")
}

MIN_CONF = float(os.getenv("MIN_CONF", 0.60))


def normalize_words(text: str):
    # Lowercase everything
    text = text.lower()

    # Remove punctuation like "UMM??", "HMM!", "UH-HUH"
    text = re.sub(r"[^\w\s]", "", text)

  
    text = re.sub(r"(.)\1+", r"\1", text)

    # Return split words
    return text.split()


def is_only_fillers(words: list[str]) -> bool:
    return all(w in IGNORED_WORDS for w in words)


def contains_interrupt_command(words: list[str]) -> bool:
    return any(w in INTERRUPT_COMMANDS for w in words)



class MyAgent(Agent):
    def __init__(self):
        super().__init__(
            instructions=(
                "Your name is Kelly. "
                "You speak using voice only. "
                "Keep responses short and clear. "
                "No emojis. Friendly, witty, slightly curious."
            )
        )

    async def on_enter(self):
        self.session.generate_reply()

    @function_tool
    async def lookup_weather(
        self, context: RunContext, location: str, latitude: str, longitude: str
    ):
        logger.info(f"Looking up weather for {location}")
        return "sunny with a temperature around seventy degrees."



async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

    session = AgentSession(
        stt=deepgram.STTv2(
            model="flux-general-en",
            eager_eot_threshold=0.3,
        ),

        llm=groq.LLM(model="llama-3.3-70b-versatile"),

        tts=elevenlabs.TTS(
            model="eleven_turbo_v2",
            voice_id="ODq5zmih8GrVes37Dizd",
        ),

        vad=silero.VAD.load(),
        turn_detection=MultilingualModel(),

        preemptive_generation=True,
        resume_false_interruption=True,
        false_interruption_timeout=1.0,
    )


    @session.on("user_transcript")
    def _handle_speech(ev):
        if not ev.transcript:
            return

        words = normalize_words(ev.transcript)

        # CASE 1 — Agent silent → everything is valid speech
        if not session.is_speaking:
            logger.info(f"[REGISTERED SPEECH] '{ev.transcript}' (agent idle)")
            return

        # CASE 2 — Mixed filler + command → REAL interruption
        if contains_interrupt_command(words):
            logger.info(f"[REAL INTERRUPTION] '{ev.transcript}' → STOP AGENT")
            return

        # CASE 3 — Pure fillers → ignore
        if is_only_fillers(words):
            logger.info(f"[IGNORED FILLER] '{ev.transcript}' (normalized={words})")
            ev.stop_propagation()
            return

        # CASE 4 — Low-confidence noise → ignore
        if ev.confidence is not None and ev.confidence < MIN_CONF:
            logger.info(
                f"[LOW CONF SPEECH IGNORED] '{ev.transcript}' "
                f"(normalized={words}, conf={ev.confidence})"
            )
            ev.stop_propagation()
            return

        # CASE 5 — Everything else → real interruption
        logger.info(f"[VALID INTERRUPTION] '{ev.transcript}' (words={words})")
        return


    usage_collector = metrics.UsageCollector()

    @session.on("metrics_collected")
    def _metrics(ev: MetricsCollectedEvent):
        metrics.log_metrics(ev.metrics)
        usage_collector.collect(ev.metrics)

    async def log_usage():
        logger.info(f"Usage: {usage_collector.get_summary()}")

    ctx.add_shutdown_callback(log_usage)

    # Start Agent

    await session.start(
        agent=MyAgent(),
        room=ctx.room,
        room_options=room_io.RoomOptions(),
    )



if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
