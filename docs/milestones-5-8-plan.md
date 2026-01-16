# Milestone 5-7: Shareable Analysis & Landing Page Redesign

## Overview

Transform Forging from a single-page tool into a multi-page platform with:
1. Shareable analysis links
2. All files stored in GCS (including large demo files)
3. New marketing landing page with community showcase
4. Dedicated analysis view page

---

## Milestone 5: GCS Upload for All Files + Firestore Storage

### Goal
Store all analysis data persistently so it can be shared and retrieved later.

### Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│  GCS Bucket: forging-uploads                                            │
│                                                                         │
│  analyses/{analysis_id}/                                                │
│  ├── video.mp4              (gameplay recording)                        │
│  ├── replay.aoe2record OR replay.dem  (optional replay/demo file)       │
│  ├── analysis.json          (tips, game summary, metadata)              │
│  └── thumbnail.jpg          (auto-generated for carousel)               │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│  Firestore Collection: analyses                                         │
│                                                                         │
│  Document ID: {analysis_id} (UUID)                                      │
│  {                                                                      │
│    "id": "abc123",                                                      │
│    "game_type": "aoe2" | "cs2",                                         │
│    "title": "1v1 Arabia - Franks vs Britons",                           │
│    "creator_name": "lucasdemoreno",                                     │
│    "players": ["lucasdemoreno", "_isma"],                               │
│    "map": "Arabia",                                                     │
│    "duration": "25:30",                                                 │
│    "video_object_name": "analyses/abc123/video.mp4",                    │
│    "thumbnail_url": "analyses/abc123/thumbnail.jpg",                    │
│    "tips_count": 8,                                                     │
│    "model_used": "gemini-2.5-flash",                                    │
│    "created_at": timestamp,                                             │
│    "is_public": true                                                    │
│  }                                                                      │
└─────────────────────────────────────────────────────────────────────────┘
```

### Backend Changes

**New files:**
- `backend/services/firestore.py` - Firestore client and CRUD operations
- `backend/services/thumbnail.py` - Extract thumbnail from video using ffmpeg

**Modified files:**
- `backend/models.py` - Add `AnalysisRecord`, `AnalysisListItem` models
- `backend/main.py` - New endpoints:
  - `POST /api/analysis` - Create and save analysis
  - `GET /api/analysis/{id}` - Retrieve saved analysis
  - `GET /api/analyses` - List recent public analyses (for carousel)
  - `POST /api/upload-url/replay` - GCS upload URL for replay/demo files

**New endpoints:**

```python
# Create analysis (saves to Firestore + GCS)
POST /api/analysis
Request: { video_object_name, replay_object_name?, game_type, model }
Response: { analysis_id, share_url, ...analysis_data }

# Get analysis by ID
GET /api/analysis/{analysis_id}
Response: { ...full_analysis_data, video_signed_url }

# List recent analyses for carousel
GET /api/analyses?limit=12
Response: { analyses: [...], total }
```

### Frontend Changes

**New hook:**
- `useReplayUpload.ts` - Similar to `useVideoUpload.ts` for demo/replay files

**Modified:**
- `FileUpload.tsx` - Upload replay to GCS before analysis (not in request body)

### Dependencies

```bash
# Backend
pip install google-cloud-firestore

# For thumbnail generation (already in Docker? check)
apt-get install ffmpeg
```

---

## Milestone 6: Shareable Analysis Pages

### Goal
Each analysis gets a unique URL that anyone can view.

### URL Structure

```
https://forging.gg/                     → Landing page (marketing)
https://forging.gg/new                  → Create new analysis (current home)
https://forging.gg/games/{analysis_id}  → View shared analysis
```

### Frontend Changes

**New pages:**
- `frontend/src/app/games/[id]/page.tsx` - Shared analysis viewer
- `frontend/src/app/new/page.tsx` - Move current home page here

**Modified:**
- `frontend/src/app/page.tsx` - Becomes landing page

### Analysis Page Features

- Video player with timestamped tips (existing component)
- Game summary panel
- Share button (copy link)
- "Create your own analysis" CTA
- SEO meta tags for social sharing (Open Graph)

---

## Milestone 7: Marketing Landing Page

### Goal
Professional landing page that showcases the product and displays community analyses.

### Design Direction
Clean/Minimal like Linear - subtle gradients, refined typography, professional feel.
Keep current dark theme but elevate the design.

### Page Sections

```
┌─────────────────────────────────────────────────────────────────────────┐
│  HEADER                                                                 │
│  [Forging Logo]                    [Try It Free] [GitHub]               │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│  HERO                                                                   │
│                                                                         │
│  "AI-Powered Game Coaching"                                             │
│  Get personalized feedback on your gameplay in minutes.                 │
│                                                                         │
│  [Analyze Your Game →]                                                  │
│                                                                         │
│  [Hero image/video: Screenshot of analysis results]                     │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│  SUPPORTED GAMES                                                        │
│                                                                         │
│  [AoE2 Card]  [CS2 Card]  [Coming Soon: Valorant] [Coming Soon: LoL]    │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│  HOW IT WORKS                                                           │
│                                                                         │
│  1. Upload your gameplay video                                          │
│  2. AI analyzes every moment                                            │
│  3. Get timestamped coaching tips                                       │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│  COMMUNITY ANALYSES (Carousel)                                          │
│                                                                         │
│  "See what others are learning"                                         │
│                                                                         │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐            │
│  │ thumb   │ │ thumb   │ │ thumb   │ │ thumb   │ │ thumb   │  →         │
│  │ AoE2    │ │ CS2     │ │ AoE2    │ │ CS2     │ │ AoE2    │            │
│  │ Player  │ │ Player  │ │ Player  │ │ Player  │ │ Player  │            │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘            │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│  FOOTER                                                                 │
│                                                                         │
│  Built for Gemini 3 Hackathon | GitHub | Twitter                        │
└─────────────────────────────────────────────────────────────────────────┘
```

### New Components

- `frontend/src/components/landing/Hero.tsx`
- `frontend/src/components/landing/SupportedGames.tsx`
- `frontend/src/components/landing/HowItWorks.tsx`
- `frontend/src/components/landing/CommunityCarousel.tsx`
- `frontend/src/components/landing/Footer.tsx`
- `frontend/src/components/AnalysisCard.tsx` - Thumbnail card for carousel

### Carousel Item Data

```typescript
interface AnalysisCard {
  id: string;
  game_type: "aoe2" | "cs2";
  title: string;
  creator_name: string;
  thumbnail_url: string;
  tips_count: number;
  created_at: string;
}
```

---

## Implementation Order

### Phase 1: Backend Infrastructure (Milestone 5)
1. Set up Firestore in GCP project
2. Create `firestore.py` service
3. Add replay upload endpoint (GCS for large files)
4. Update video analysis to save to Firestore
5. Add GET endpoints for retrieving analyses

### Phase 2: Shareable Pages (Milestone 6)
1. Create `/games/[id]` dynamic route
2. Move current page to `/new`
3. Update analysis flow to redirect to share URL after completion
4. Add share button and social meta tags

### Phase 3: Landing Page (Milestone 7)
1. Create landing page components
2. Implement carousel with API data
3. Add thumbnail generation (can be deferred - use placeholder initially)
4. Polish and responsive design

---

## Files to Create/Modify

| File | Action | Milestone |
|------|--------|-----------|
| `backend/services/firestore.py` | Create | 5 |
| `backend/services/thumbnail.py` | Create | 5 (or defer) |
| `backend/models.py` | Modify | 5 |
| `backend/main.py` | Modify | 5 |
| `backend/requirements.txt` | Modify | 5 |
| `frontend/src/hooks/useReplayUpload.ts` | Create | 5 |
| `frontend/src/components/FileUpload.tsx` | Modify | 5 |
| `frontend/src/app/games/[id]/page.tsx` | Create | 6 |
| `frontend/src/app/new/page.tsx` | Create (move from page.tsx) | 6 |
| `frontend/src/app/page.tsx` | Replace with landing | 7 |
| `frontend/src/components/landing/*.tsx` | Create | 7 |
| `frontend/src/components/AnalysisCard.tsx` | Create | 7 |

---

## Environment Variables (New)

```bash
# Backend
GOOGLE_CLOUD_PROJECT=project-48dfd3a0-58cd-43e5-ae7  # For Firestore
```

---

## Verification

### Milestone 5
1. Upload video + large demo file (168MB) - both go to GCS
2. Analysis saves to Firestore
3. Can retrieve analysis by ID

### Milestone 6
1. After analysis, get shareable URL
2. Open URL in incognito - loads analysis without auth
3. Share button copies URL

### Milestone 7
1. Landing page loads with hero, sections, carousel
2. Carousel shows recent community analyses
3. Click card → goes to analysis page
4. "Analyze Your Game" → goes to /new

---

## Notes

- Consider rate limiting on public endpoints
- Firestore has generous free tier (50k reads/day, 20k writes/day)
- GCS lifecycle policy already deletes after 24h - may need to extend for saved analyses

---

## Milestone 8: Thumbnail Generation (Optional Enhancement)

### Goal
Generate compelling thumbnails from gameplay videos to make the carousel visually engaging.

### Approach Options

**Option A: First Frame of Game Start**
- Extract frame from ~30s into video (after loading screens)
- Fast, simple, but may not show action

**Option B: Timestamp-Based (Recommended)**
- Use the first coaching tip timestamp as the extraction point
- This naturally captures a moment of interest
- Already have this data from analysis

**Option C: AI-Selected Frame**
- Use Gemini to identify "most visually interesting moment"
- Highest quality but adds API cost and complexity

### Implementation (Option B)

```python
# backend/services/thumbnail.py

import subprocess
import tempfile

def extract_thumbnail(video_path: str, timestamp_seconds: int = 30) -> str:
    """
    Extract a single frame from video at given timestamp.
    Returns path to generated thumbnail.
    """
    output_path = tempfile.mktemp(suffix=".jpg")

    # ffmpeg command to extract single frame
    subprocess.run([
        "ffmpeg",
        "-ss", str(timestamp_seconds),  # Seek to timestamp
        "-i", video_path,
        "-vframes", "1",                 # Extract 1 frame
        "-q:v", "2",                     # High quality JPEG
        "-vf", "scale=640:-1",           # Resize to 640px width
        output_path
    ], check=True)

    return output_path
```

### When to Generate

1. **During analysis** - After video analysis completes, extract thumbnail using first tip timestamp
2. **Upload to GCS** - Store as `analyses/{id}/thumbnail.jpg`
3. **Store URL in Firestore** - Reference in analysis record

### Performance Considerations

- ffmpeg frame extraction is fast (~1-2 seconds)
- Only downloads the portion of video needed (seeking is efficient)
- Run after analysis response is sent (async/background)
- Fallback to game logo if thumbnail generation fails

### Placeholder Strategy (Before Milestone 8)

Until thumbnails are implemented:
- Use game-specific placeholder images
- AoE2: Castle/knight artwork
- CS2: CT/T artwork or map screenshots

### Dependencies

```dockerfile
# Add to backend/Dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*
```

### Files to Modify

| File | Action |
|------|--------|
| `backend/services/thumbnail.py` | Create |
| `backend/Dockerfile` | Add ffmpeg |
| `backend/services/video_analyzer.py` | Call thumbnail generation |
| `backend/services/cs2_video_analyzer.py` | Call thumbnail generation |

---

# Milestone 9: YouTube-Style Video Player & Tips Panel Redesign

> **Status**: Planned
> **Priority**: Enhancement
> **Depends on**: Milestones 5-8 (completed)

## Overview

Upgrade the video player with YouTube-like custom controls and redesign the tips panel to match YouTube's recommended videos sidebar style for a more professional, familiar UX.

**Design choices:**
- Tips panel: **Clean Card** - YouTube-style horizontal cards with timestamp boxes
- Video controls: **Basic controls** - play/pause, progress bar, time, volume, fullscreen
- No external libraries - pure React + HTML5 video API

---

## Part A: Custom Video Player Controls

### Goal
Replace the native HTML5 video controls with a custom YouTube-style control bar.

### Control Bar Layout

```
+------------------------------------------------------------------+
| Video                                                             |
|                                                                   |
|                          [Play Icon]                              |
|                                                                   |
+------------------------------------------------------------------+
| [▶] =====[Red Progress Bar]=====  1:59 / 9:51    [🔊] [⛶]        |
+------------------------------------------------------------------+
```

### Features

| Feature | Description |
|---------|-------------|
| Play/Pause | Large center button + small control bar button |
| Progress Bar | Red fill with gray remaining, draggable scrubber dot |
| Time Display | Current time / Duration (e.g., "1:59 / 9:51") |
| Volume | Speaker icon + hover slider, click to mute |
| Fullscreen | Toggle button, uses Fullscreen API |
| Auto-hide | Controls fade after 3s inactivity, show on mouse move |

### Technical Implementation

**New component: `frontend/src/components/VideoControls.tsx`**

```tsx
interface VideoControlsProps {
  videoRef: RefObject<HTMLVideoElement>;
  isPlaying: boolean;
  currentTime: number;
  duration: number;
  onPlayPause: () => void;
  onSeek: (time: number) => void;
  onVolumeChange: (volume: number) => void;
  onFullscreen: () => void;
}
```

**State management:**
- `isPlaying` - derived from video.paused
- `currentTime` / `duration` - from video events
- `volume` (0-1) - persisted to localStorage
- `isMuted` - toggle state
- `showControls` - visibility with auto-hide timer

**Progress bar styling:**
```css
/* Red fill up to current position, gray for remaining */
background: linear-gradient(
  to right,
  #ff0000 0%,
  #ff0000 ${progress}%,
  #404040 ${progress}%,
  #404040 100%
);
```

### Modify: `frontend/src/components/VideoPlayer.tsx`

```diff
- <video controls ... />
+ <div className="group relative">
+   <video ... />
+   <VideoControls videoRef={videoRef} ... />
+ </div>
```

- Remove `controls` attribute from video element
- Add mouse event handlers for control visibility
- Pass video ref to VideoControls component

---

## Part B: Tips Panel Redesign (YouTube Sidebar Style)

### Goal
Transform the tips panel from full-width stacked cards to compact horizontal cards like YouTube's recommended videos sidebar.

### Current vs New Design

**Current:**
```
+--------------------------------------------------+
|  [2:15]  💰  Focus on constant villager...       |
|              economy                         ▶   |
+--------------------------------------------------+
```

**New (YouTube-style):**
```
+--------------------------------------------------+
|  +------+  Economy: Build Order                  |
|  | 💰   |  Focus on constant villager production |
|  | 2:15 |  [economy]                             |
|  +------+                                        |
+--------------------------------------------------+
```

### Card Structure

```
┌─────────────────────────────────────────────────┐
│ ┌────────┐                                      │
│ │  💰    │  Category: Tip Title (truncated)     │
│ │  2:15  │  Full tip text that can wrap to      │
│ └────────┘  two lines max... [category badge]   │
└─────────────────────────────────────────────────┘
```

### Design Specifications

| Element | Specification |
|---------|---------------|
| Card height | ~80px (compact) |
| Timestamp box | 60px × 50px, dark background, centered icon + time |
| Tip text | 2-line max with ellipsis truncation |
| Category badge | Small colored pill (existing colors) |
| Active state | Orange left border (4px) + brighter background |
| Hover state | Subtle gray background (#27272a) |
| Spacing | 8px gap between cards |

### Modify: `frontend/src/components/TimestampedTips.tsx`

Key changes:
1. Restructure card layout to horizontal (flex-row)
2. Create fixed-width timestamp box on left
3. Stack category title + tip text + badge on right
4. Add 2-line text truncation with CSS
5. Change active indicator from ring to left border
6. Add auto-scroll to active tip

**CSS for text truncation:**
```css
.tip-text {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
```

---

## Part C: Layout Updates

### Modify: `frontend/src/components/VideoAnalysisResults.tsx`

```diff
- <div className="grid gap-6 lg:grid-cols-2">
+ <div className="grid gap-6 lg:grid-cols-[1fr,380px]">
```

Changes:
1. Video player takes remaining space (1fr)
2. Tips panel has fixed 380px width (like YouTube sidebar)
3. Add custom scrollbar styling for tips panel
4. Implement scroll-to-active-tip behavior

---

## Files to Modify

| File | Action | Description |
|------|--------|-------------|
| `frontend/src/components/VideoControls.tsx` | **CREATE** | Custom YouTube-style control bar |
| `frontend/src/components/VideoPlayer.tsx` | Modify | Replace native controls with custom overlay |
| `frontend/src/components/TimestampedTips.tsx` | Modify | Complete redesign with card layout |
| `frontend/src/components/VideoAnalysisResults.tsx` | Modify | Update grid layout proportions |

---

## Implementation Order

1. **VideoControls.tsx** - Create the control bar component with all features
2. **VideoPlayer.tsx** - Integrate controls, remove native controls
3. **TimestampedTips.tsx** - Redesign to YouTube card style
4. **VideoAnalysisResults.tsx** - Update layout grid
5. **Testing** - Verify all features work together

---

## Verification Plan

### Video Controls
- [ ] Play/pause button toggles correctly
- [ ] Progress bar shows correct position
- [ ] Clicking progress bar seeks accurately
- [ ] Dragging scrubber works smoothly
- [ ] Volume slider adjusts audio
- [ ] Mute toggle works
- [ ] Fullscreen enters/exits properly
- [ ] Controls auto-hide after 3 seconds
- [ ] Controls show on mouse movement

### Tips Panel
- [ ] Cards display in new compact horizontal layout
- [ ] Timestamp box shows icon + time
- [ ] Tip text truncates to 2 lines
- [ ] Category badges display correctly
- [ ] Active tip has orange left border
- [ ] Clicking card seeks video
- [ ] Auto-scroll to active tip works
- [ ] Hover state applies correctly

### Integration
- [ ] Load analysis from `/games/[id]`
- [ ] Video plays with new controls
- [ ] Tips sync with video playback
- [ ] Responsive on mobile (controls stack, tips below video)
- [ ] Voice coaching still works

---

## Dependencies

None - uses only native HTML5 video API and existing React patterns.

---

## Notes

- No external video library needed for basic controls
- Consider adding keyboard shortcuts in future milestone (space=play, arrows=seek)
- Consider adding playback speed control in future milestone
- Mobile may need tap-to-show-controls instead of hover
