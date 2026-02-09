# Forging - Hackathon Video Script

**Total Duration: ~3:30 minutes**

---

| Time | Script / Narration | Visual |
|------|-------------------|--------|
| **0:00 - 0:30** | **THE HOOK** | |
| 0:00-0:15 | "Every esports player watches replays to improve their game. But spotting your mistakes? That takes hours of analysis and coaching expertise most players don't have access to." | **Slide:** Split screen showing:<br>• Left: Frustrated player rewatching replay<br>• Right: Clock ticking, hours passing<br><br>OR show brief clips of pro players reviewing replays |
| 0:15-0:30 | "Forging changes that. Upload your gameplay video, and in minutes, get AI-powered coaching tips timestamped to the exact moments you need to improve." | **Demo:** Quick montage (3-4 seconds each):<br>1. Upload interface<br>2. Processing animation<br>3. Results with timestamps<br>4. Video player jumping to moment |
| **0:30 - 1:00** | **THE PROBLEM** | |
| 0:30-0:45 | "The problem is real: Manual replay analysis is time-consuming. Generic stats tell you WHAT happened, but not WHY. And casual players have no accessible way to get personalized, expert-level coaching." | **Slide:** Three pain points with icons:<br>• ⏰ Time-consuming analysis<br>• 📊 Generic stats lack context<br>• 🚫 No accessible coaching<br><br>OR show generic stats dashboard vs what coaching actually requires |
| 0:45-1:00 | "With over 3 billion gamers worldwide and esports growing exponentially, the coaching gap is massive. We built Forging to bridge it using Gemini's multimodal AI." | **Slide:** Simple stat graphic:<br>• "3B+ gamers worldwide"<br>• "Growing esports market"<br>• Forging logo appears |
| **1:00 - 3:00** | **THE DEMO** | |
| 1:00-1:20 | "Let me show you how it works. Here's our live deployment. We currently support Counter-Strike 2 and Age of Empires II, with Rocket League, Dota 2, and League of Legends coming soon." | **Demo - Homepage:**<br>• Show forging-frontend URL<br>• Highlight supported games section<br>• Hover over game cards<br>• Click "Analyze Your Game" |
| 1:20-1:40 | "Upload is simple - either a replay file like a CS2 demo or .aoe2record, or a raw MP4 video up to 700MB and 30 minutes. We use Gemini's File API to handle these large multimodal inputs." | **Demo - Upload Page:**<br>• Show file upload interface<br>• Demonstrate drag & drop<br>• Show file size/duration limits<br>• Click upload and show progress bar |
| 1:40-2:10 | "Here's where the magic happens. Gemini analyzes your entire gameplay - identifying critical moments, mistakes, and opportunities. For CS2, we parse demo files to extract round data, deaths, and positioning. For video, Gemini's multimodal understanding sees everything: crosshair placement, utility usage, decision-making." | **Demo - Results Page:**<br>• Show completed analysis<br>• Scroll through the coaching tips section<br>• Highlight the timestamp badges<br>• Point out round indicators (CS2)<br>• Show the tip categories/themes |
| 2:10-2:30 | "But here's what makes Forging different - every tip is clickable and jumps you directly to that moment in your video. Click round 3, boom - you're watching that round. Click a tip about a positioning mistake at 2:47, and you're right there seeing exactly what the AI coach is talking about." | **Demo - Interactive Features:**<br>• Click a timestamp in a tip<br>• Show video player seeking to that moment<br>• Play 2-3 seconds of the actual moment<br>• Click a round number, show it jumping<br>• Demonstrate 2-3 different tip clicks |
| 2:30-2:50 | "And we didn't stop there. You can chat with your AI coach - ask follow-up questions about your gameplay. 'Why did I lose that fight?' 'How should I have played that round?' The AI has full context of your match and can explain nuances." | **Demo - Chat Feature:**<br>• Scroll to chat interface<br>• Show a pre-written question being asked<br>• Display AI response coming in<br>• Show 1-2 back-and-forth exchanges |
| 2:50-3:00 | "We also built a community carousel so you can browse other players' analyses, learn from their mistakes, and share your own progress." | **Demo - Community:**<br>• Scroll to community carousel<br>• Show thumbnail previews<br>• Click into one analysis example<br>• Quick 2-second preview |
| **3:00 - 3:30** | **TECHNICAL DEPTH & VISION** | |
| 3:00-3:15 | "Under the hood, we're orchestrating Gemini across multiple steps: parsing replay files with specialized libraries, uploading videos via the File API, running multi-turn reasoning with domain-specific coaching knowledge bases, and streaming responses for the chat experience." | **Slide/Animation:** Architecture diagram:<br>• Upload → Parse → Analyze → Generate<br>• Show Gemini File API integration<br>• Highlight multi-step orchestration<br>• Show knowledge base modules |
| 3:15-3:30 | "Looking ahead, we're integrating Gemini Live API for voice coaching - imagine watching your replay and just asking questions out loud, getting spoken tips in real-time. We're also building economy coaching, personalized training drills, and even hand-cam analysis for mechanics improvement. Forging isn't just a hackathon project - it's the future of accessible esports coaching." | **Slide:** Roadmap visual:<br>• ✅ Video Analysis (Done)<br>• 🚀 Gemini Live Voice (Next)<br>• 💰 Economy Coaching<br>• 🎯 Training Drills<br>• ⌨️ Hand-cam Analysis<br><br>End with Forging logo + "Built for Gemini 3 Hackathon" |

---

## Notes for Recording

### Pacing
- Speak clearly but naturally - no need to rush
- Pause briefly between major sections
- Let key moments breathe (especially demo clicks)

### Demo Preparation
- Have the analysis pre-loaded and ready
- Use a compelling gameplay example (close match, interesting moments)
- Test all click interactions beforehand
- Clear browser cache for clean UI

### Transitions
- Use simple fade or slide transitions between sections
- 0.5-1 second max per transition
- Consider a subtle "whoosh" sound effect for section changes

### Energy
- Start strong with confident tone
- Build excitement during the demo
- End with vision and enthusiasm
- Smile when talking (it comes through in voice)