# 🌩️ LiveKit Filler-Aware Interruption Handler  

This branch enhances a LiveKit real-time conversational agent by adding a **filler-aware interruption handler**.  
The system distinguishes **meaningful user interruptions** from **irrelevant filler speech**, while preserving real-time responsiveness and without modifying any core LiveKit SDK components.

All changes were implemented in:

```
examples\voice_agents\basic_agent.py
examples\voice_agents\README.md
README.md
```

---

# 🛠 What Changed  
### Overview of New Modules, Parameters, and Logic

### ✔ 1. Filler Interruption Layer  
A full interruption-handling system was added inside the LiveKit event loop using:

```
@session.on("user_transcript")
```

This layer:
- ignores filler-only utterances while agent is speaking  
- registers fillers normally when agent is silent  
- detects commands even if surrounded by fillers  
- suppresses low-confidence noise  
- handles mixed filler + command cases correctly  

### ✔ 2. Normalization Utilities  
STT transcripts:
- Converted to lowercase  
- Removed punctuation  
- Compressed repeated letters (UMMMM → um, UHHHH → uh) using regex

This makes the filler detection robust across accents and noisy speech.

### ✔ 3. Dynamic Configuration (via `.env`)  
Parameters added:

```
IGNORED_WORDS
INTERRUPT_COMMANDS
MIN_CONF
```
(.env.example is attached)
Allows runtime updates without editing code.

### ✔ 4. Low-Confidence Noise Filtering  
If STT confidence < `MIN_CONF`, the speech is ignored:
```
[LOW CONF SPEECH IGNORED]
```

### ✔ 5. Windows Signal Patch  
LiveKit workers crash on Windows due to signal handling.  
Added:

```python
if platform.system() == "Windows":
    signal.signal = lambda *args, **kwargs: None
```

Ensures stable execution.

## ✔ 6. Behavior Details (Important)

#### 1.  Interruption Uses session.interrupt()

When an interruption command is detected:

- Ongoing TTS halts

- Pending LLM generation cancels

- Audio flushes

- Agent waits for EOU before replying

The result: zero overlapping speech.

#### 2. Filler Ignored Using ev.stop_propagation()

If filler is detected while the agent is speaking:

```
ev.stop_propagation()
```

This prevents the event from reaching:

- EOU detector

- LLM

- Interruption manager

- Any downstream handlers

Meaning filler simply vanishes.

---

# ✅ What Works  

- Filler-only speech ignored while agent is speaking  
- Filler words treated as valid speech when agent is idle  
- Command phrases (`stop`, `wait`, `pause`, etc.) trigger instant interruption  
- Mixed filler + command works (`umm okay stop`)  
- Low-confidence utterances filtered out properly  

---

# ⚠ Known Issues  

- Some mixed Hindi-English utterances may be misrecognized by Deepgram  
- Very noisy environments may require increasing `MIN_CONF`  
- EOU may be further enhanced

---

# 🧪 Steps to Test  

## 1. Install the dependencies
```
pip install -r examples/voice_agents/requirements.txt
```

## 2. Start the Agent  
```
python examples/voice_agents/basic_agent.py console[/dev][/start]
```

## 3. Join Room  
Use LiveKit Cloud → open room in browser with microphone enabled.( Only for dev or start mode)

---

# 🗣 Test Cases  

### **A. Filler while agent is speaking**
Speak:
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

### **B. Real interruption**
Speak:
```
stop
wait
pause
hold on
```
Expected:
```
[REAL INTERRUPTION]
```

---

### **C. Mixed filler + command**
Speak:
```
umm okay stop
```
Expected:
```
[REAL INTERRUPTION]
```

---

### **D. Background noise**
(soft mumble / tap mic)

Expected:
```
[LOW CONF SPEECH IGNORED]
```

---

### **E. Filler while agent is silent**
Speak:
```
umm
```
Expected:
```
[REGISTERED SPEECH]
```

---

# 📊 Log Samples (Reference)  

Real logs captured during testing:

```
    Agents   Starting console mode 🚀

    18:57:35 DEBUG  asyncio          Using proactor: IocpProactor  
             INFO   livekit.agents   starting worker {"version": "1.3.2", "rtc-version": "1.0.19"}
             INFO   livekit.agents   starting inference executor  
             INFO   livekit.agents   initializing process {"pid": 72284, "inference": true}
    18:57:50 INFO   livekit.agents   process initialized {"pid": 72284, "inference": true, "elapsed_time": 15.26}
             INFO   livekit.agents   initializing job runner {"tid": 75040}
             INFO   livekit.agents   job runner initialized {"tid": 75040, "elapsed_time": 0.0}
             DEBUG  asyncio          Using proactor: IocpProactor  
    18:57:52 DEBUG  livekit.agents   http_session(): creating a new httpclient ctx {"room": "mock_room"}
             DEBUG  livekit.agents   using audio io: `Console` -> `AgentSession` -> `Console` {"room": "mock_room"}
             WARNI… livekit.agents   resume_false_interruption is enabled    {"room": "mock_room", "audio_output":   
                                     but audio output does not support       "Console"}                              
                                     pause, it will be ignored                                                       
             DEBUG  livekit.agents   using transcript io: `AgentSession` -> (none) {"room": "mock_room"}
    18:57:53 INFO   livekit.agents   LLM metrics {"room": "mock_room", "model_name": "llama-3.3-70b-versatile",      
                                                 "model_provider": "api.groq.com", "ttft": 0.9, "prompt_tokens": 62, 
                                                 "prompt_cached_tokens": 0, "completion_tokens": 10,                 
                                                 "tokens_per_second": 10.99}                                         
             DEBUG  livekit.plugins… Established new Deepgram STT WebSocket  {"room": "mock_room", "headers":        
                                     connection:                             {"dg-project-id":                       
                                                                             "63574080-6bad-418b-8773-88a03c274c64", 
                                                                             "dg-request-id":                        
                                                                             "d63afbbd-15df-48e8-8fa6-9de7527d4eb4", 
                                                                             "Date": "Wed, 19 Nov 2025 13:27:53      
                                                                             GMT"}}                                  
             INFO   livekit.agents   TTS metrics {"room": "mock_room", "model_name": "eleven_turbo_v2",              
                                                 "model_provider": "ElevenLabs", "ttfb": 0.6903447000076994,         
                                                 "audio_duration": 1.62}                                             
    18:57:57 INFO   livekit.agents   STT metrics {"room": "mock_room", "model_name": "flux-general-en",              
                                                 "model_provider": "Deepgram", "audio_duration": 3.1}                
    18:57:58 DEBUG  livekit.agents   received user preflight transcript {"room": "mock_room", "user_transcript":     
                                                                        "What's your name?", "language": "en"}       
             DEBUG  livekit.agents   received user transcript {"room": "mock_room", "user_transcript": "What's your  
                                                              name?", "language": "en", "transcript_delay":          
                                                              0.28481197357177734}                                   
             INFO   livekit.agents   LLM metrics {"room": "mock_room", "model_name": "llama-3.3-70b-versatile",      
                                                 "model_provider": "api.groq.com", "ttft": 0.17, "prompt_tokens": 86,
                                                 "prompt_cached_tokens": 0, "completion_tokens": 11,                 
                                                 "tokens_per_second": 60.44}                                         
             DEBUG  livekit.plugins… eou prediction {"room": "mock_room", "eou_probability": 0.6224233508110046,     
                                                    "duration": 0.145, "input": "<|im_start|>assistant\nhello how can
                                                    i help you today<|im_end|>\n<|im_start|>user\nwhat's your name"} 
             DEBUG  livekit.agents   using preemptive generation {"room": "mock_room", "preemptive_lead_time":       
                                                                 0.3871724605560303}                                 
             INFO   livekit.agents   EOU metrics {"room": "mock_room", "model_name": "multilingual",                 
                                                 "model_provider": "livekit", "end_of_utterance_delay": 0.67,        
                                                 "transcription_delay": 0.29}                                        
    18:57:59 INFO   livekit.agents   TTS metrics {"room": "mock_room", "model_name": "eleven_turbo_v2",              
                                                 "model_provider": "ElevenLabs", "ttfb": 0.5704415999935009,         
                                                 "audio_duration": 2.14}                                             
    18:58:02 INFO   livekit.agents   STT metrics {"room": "mock_room", "model_name": "flux-general-en",              
                                                 "model_provider": "Deepgram", "audio_duration": 5.0}                
    18:58:04 DEBUG  livekit.agents   received user preflight transcript {"room": "mock_room", "user_transcript":     
                                                                        "Read me a three line code.", "language":    
                                                                        "en"}                                        
             DEBUG  livekit.agents   received user preflight transcript {"room": "mock_room", "user_transcript":     
                                                                        "Read me a three line phone.", "language":   
                                                                        "en"}                                        
             INFO   livekit.agents   LLM metrics {"room": "mock_room", "model_name": "llama-3.3-70b-versatile",      
                                                 "model_provider": "api.groq.com", "ttft": 0.15, "prompt_tokens": 0, 
                                                 "prompt_cached_tokens": 0, "completion_tokens": 0,                  
                                                 "tokens_per_second": 0.0}                                           
    18:58:17 INFO   livekit.agents   STT metrics {"room": "mock_room", "model_name": "flux-general-en",              
                                                 "model_provider": "Deepgram", "audio_duration": 5.0}                
    18:58:22 INFO   livekit.agents   STT metrics {"room": "mock_room", "model_name": "flux-general-en",              
                                                 "model_provider": "Deepgram", "audio_duration": 5.0}                
    18:58:24 DEBUG  livekit.agents   received user preflight transcript {"room": "mock_room", "user_transcript":     
                                                                        "Continue.", "language": "en"}               
             DEBUG  livekit.agents   received user transcript {"room": "mock_room", "user_transcript": "Continue.",  
                                                              "language": "en", "transcript_delay":                  
                                                              0.7034423351287842}                                    
             INFO   livekit.agents   LLM metrics {"room": "mock_room", "model_name": "llama-3.3-70b-versatile",      
                                                 "model_provider": "api.groq.com", "ttft": 0.37, "prompt_tokens":    
                                                 184, "prompt_cached_tokens": 0, "completion_tokens": 17,            
                                                 "tokens_per_second": 40.74}                                         
             DEBUG  livekit.plugins… eou prediction {"room": "mock_room", "eou_probability": 0.1680351048707962,     
                                                    "duration": 0.353, "input": "<|im_start|>assistant\nmy name is   
                                                    lilly nice to meet you<|im_end|>\n<|im_start|>user\nread me a    
                                                    three line phone<|im_end|>\n<|im_start|>assistant\ni think you   
                                                    meant poem here it is the sun sets slow and paints the sky the   
                                                    stars come out and twinkle high a night of rest a peaceful       
                                                    sigh<|im_end|>\n<|im_start|>user\nso<|im_end|>\n<|im_start|>assi…
                                                    what's on your mind<|im_end|>\n<|im_start|>user\ncontinue"}      
             DEBUG  livekit.agents   using preemptive generation {"room": "mock_room", "preemptive_lead_time":       
                                                                 0.5683598518371582}                                 
             INFO   livekit.agents   EOU metrics {"room": "mock_room", "model_name": "multilingual",                 
                                                 "model_provider": "livekit", "end_of_utterance_delay": 1.12,        
                                                 "transcription_delay": 0.72}                                        
    18:58:25 INFO   livekit.agents   TTS metrics {"room": "mock_room", "model_name": "eleven_turbo_v2",              
                                                 "model_provider": "ElevenLabs", "ttfb": 0.7243157000048086,         
                                                 "audio_duration": 4.73}                                             
    18:58:27 INFO   livekit.agents   STT metrics {"room": "mock_room", "model_name": "flux-general-en",              
                                                 "model_provider": "Deepgram", "audio_duration": 5.0}                
    18:58:32 INFO   livekit.agents   STT metrics {"room": "mock_room", "model_name": "flux-general-en",              
                                                 "model_provider": "Deepgram", "audio_duration": 5.0}                
   Microphone Array (Intel® Smart    ▁ ▁ ▁ ▁ ▁ ▁ ▁ ▁ ▁ ▁ ▁ ▁ ▁ ▁  <Ctrl+T> Text Mode
```

---

# 🌍 Environment Details  

### Python Version  
```
Python 3.10+
```

### Dependencies  
- livekit-agents  
- deepgram STT (`flux-general-en`)  
- groq LLM (`llama-3.3-70b-versatile`)  
- elevenlabs TTS (`eleven_turbo_v2`)  
- silero VAD  
- multilingual turn detector  
- python-dotenv

### Config Instructions

- Create .env file and populate with appropriate API keys
- You can pupulate **LiveKit** credentials using LiveKit CLI
  ```
  lk app env -w
  ```

```
IGNORED_WORDS=uh,umm,ummm,hmm,haan,erm,mm
INTERRUPT_COMMANDS=stop,wait,pause,hold on,excuse me
MIN_CONF=0.60
and related API KEYS
```

---

# 🏁 Conclusion  
This implementation delivers a **smart, human-like interruption system** for LiveKit voice agents.  
Filler speech is ignored intelligently, commands are recognized instantly, and noise is filtered — making conversations smoother and more natural.

References:https://docs.livekit.io/agents/
