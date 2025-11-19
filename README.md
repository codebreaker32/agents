# 🌩️ LiveKit Filler-Aware Interruption Handler  

This branch extends the LiveKit real-time voice agent to intelligently distinguish **meaningful user interruptions** from **irrelevant filler speech**, without modifying LiveKit’s core SDK.

All changes were made in the following file:

```
examples/voice_agents/basic_agent.py
```

---

# 🛠 What Changed

### ✔ Filler-aware interruption filter  
Filler words are ignored **only when the agent is speaking**, preventing accidental pauses.  
Ignored fillers (configurable):

```
uh, umm, ummmm, hmm, haan, mm, erm
```

### ✔ Repetition normalization  
Handles human variations:

- `UMMMM` → `um`
- `UHHHHH` → `uh`
- `HAAAAN` → `haan`

### ✔ Command-based interruption detection  
Commands force an interruption instantly:

```
stop, wait, pause, hold on, excuse me
```

### ✔ Low-confidence speech filtering  
If STT confidence < `MIN_CONF`, speech is treated as background noise.

### ✔ Dynamic configuration via `.env`
Environment variables:

```
IGNORED_WORDS
INTERRUPT_COMMANDS
MIN_CONF
```

### ✔ Windows-safe signal override  
Prevents:

```
ValueError: signal only works in main thread of the main interpreter
```

Patch:

```python
if platform.system() == "Windows":
    signal.signal = lambda *args, **kwargs: None
```

### ✔ Rich logs for debugging  
The agent logs all decisions:

```
[IGNORED FILLER]
[REAL INTERRUPTION]
[VALID INTERRUPTION]
[REGISTERED SPEECH]
[LOW CONF SPEECH IGNORED]
```

---

# 🧪 Log Samples (Real References)

Below are **actual sample logs** produced during testing for reference:

```
01:32:21 INFO   livekit.agents   STT metrics {"room": "playground-0VVK-GKZ2",
                                             "model_name": "flux-general-en",
                                             "model_provider": "Deepgram",
                                             "audio_duration": 0.6}

01:32:22 DEBUG  livekit.agents   received user transcript {"room": "playground-0VVK-GKZ2",
                                                           "user_transcript": "Thanks, Kelly.",
                                                           "language": "en",
                                                           "transcript_delay": 0.0453}

01:32:23 INFO   livekit.agents   LLM metrics {"room": "playground-0VVK-GKZ2",
                                             "model_name": "llama-3.3-70b-versatile",
                                             "model_provider": "api.groq.com",
                                             "ttft": 0.29,
                                             "completion_tokens": 10}

01:32:24 DEBUG  livekit.plugins.eou  prediction {"room": "playground-0VVK-GKZ2",
                                                "eou_probability": 0.55,
                                                "duration": 0.452}

01:32:25 INFO   livekit.agents   TTS metrics {"room": "playground-0VVK-GKZ2",
                                             "model_name": "eleven_multilingual_v2",
                                             "audio_duration": 1.52}

01:32:31 INFO   livekit.agents   STT metrics {"room": "playground-0VVK-GKZ2",
                                             "model_name": "flux-general-en",
                                             "audio_duration": 5.0}
```

These logs help confirm:
- STT is running  
- TTS is generating  
- LLM responses are streaming  
- EOU predictions are active  
- Transcript handler is firing  

---

# ▶️ Steps to Run

### 1. Activate the environment
```
.venv\Scripts\activate
```

### 2. Start the agent
```
python examples/voice_agents/basic_agent.py console/dev/start
```

### 3. Join the room  
Use LiveKit Cloud → open the room in browser (Only for dev & start mode)

---

# 🧪 Steps to Test Interruption Behavior

### **Filler while agent speaking (should be ignored):**
```
umm
hmm
ummmmm
haan
```
Expected:
```
[IGNORED FILLER]
```

---

### **Real interruption:**
```
stop
wait
pause
hold on
```
Expected:
Agent stops immediately.

---

### **Mixed filler + command:**
```
umm okay stop
```
Expected:
```
[REAL INTERRUPTION]
```

---

### **Background noise / mumbling:**
Expected:
```
[LOW CONF SPEECH IGNORED]
```

---

### **Filler when agent is silent:**
```
umm
```
Expected:
```
[REGISTERED SPEECH]
```

---

# 🌍 Environment Details

| Component | Configuration |
|----------|---------------|
| STT | Deepgram `flux-general-en` |
| LLM | Groq `llama-3.3-70b-versatile` |
| TTS | ElevenLabs `eleven_turbo_v2` |
| VAD | Silero |
| Turn Detection | LiveKit Multilingual |
| OS | Windows (patched), Linux, macOS |
| Python | 3.10+ |

---

# 🏁 Conclusion

This implementation enhances the LiveKit voice agent with **precision interruption handling**, supporting dynamic filler filtering, command detection, low-confidence suppression, and Windows-safe execution—mirroring natural human conversation flow.

