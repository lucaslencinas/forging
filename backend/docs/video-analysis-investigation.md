# Video Analysis Investigation

## Overview

This document captures initial research on adding video recording/analysis capabilities to the game coaching platform, covering both legal considerations and infrastructure/cost implications.

---

## 1. Legal Considerations

### Game Publisher Policies

#### Valve (CS2)
- Generally permissive for community content
- Policy allows videos/streams for personal, non-commercial use
- Commercial use (like a paid coaching app) enters gray area
- Historically tolerant of analytics tools (Leetify, Scope.gg exist)

#### Microsoft (AoE2)
- Has "Game Content Usage Rules" policy
- Allows content creation with restrictions
- Commercial use typically requires explicit permission

### Legal Risk Assessment

| Risk | Level | Notes |
|------|-------|-------|
| DMCA takedowns | Medium | If hosting gameplay clips publicly |
| Terms of Service violation | Medium | Could result in API access revoked |
| Copyright claims | Low-Medium | Game footage is derivative work |
| Trademark issues | Low | If using game logos/branding |

### How Similar Companies Handle This

| Company | Approach | Notes |
|---------|----------|-------|
| Leetify | Demo parsing only | No video storage |
| Scope.gg | Demo parsing only | No video storage |
| Mobalytics | API data + user screenshots | User-provided content |
| Insights.gg | User-uploaded clips | Shifts liability to user |

### Safer Approaches

1. **User-uploaded content** - Users upload their own recordings, shifting liability
2. **Local recording** - Record/analyze locally on user's machine, never upload
3. **Analysis tools only** - Provide tools, don't host copyrighted content

---

## 2. Storage & Infrastructure Costs

### Video Size Reference

| Quality | Bitrate | 1 Hour | 30-min Match |
|---------|---------|--------|--------------|
| 1080p30 (compressed) | ~5 Mbps | ~2.25 GB | ~1.1 GB |
| 1080p60 | ~8 Mbps | ~3.6 GB | ~1.8 GB |
| 720p30 | ~2.5 Mbps | ~1.1 GB | ~550 MB |

### Monthly Storage Projections

Assuming **720p30** compressed clips (not full matches):

| Users | Clips/User/Month | Clip Length | Storage/Month | Cost (S3) |
|-------|------------------|-------------|---------------|-----------|
| 100 | 10 | 2 min | ~55 GB | ~$1.25 |
| 1,000 | 10 | 2 min | ~550 GB | ~$12.50 |
| 10,000 | 10 | 2 min | ~5.5 TB | ~$125 |

**Storage accumulates!** After 12 months with 10k users: **~66 TB = $1,500/month**

### AWS Cost Breakdown

| Service | Cost | Notes |
|---------|------|-------|
| S3 Storage | $0.023/GB/month | S3 Standard |
| Egress | $0.09/GB | When users watch videos |
| Transcoding | $0.015-0.030/minute | If processing video |
| CDN (CloudFront) | $0.085/GB | Video delivery |

### Egress Cost Example

If each user watches 10 clips/month (50 MB each):
- 10,000 users × 500 MB = 5 TB egress = **$450/month** just for viewing

### Break-even Pricing Model

| Tier | Monthly Fee | Storage Allowance | Notes |
|------|-------------|-------------------|-------|
| Free | $0 | No video / 7-day retention | Loss leader |
| Pro | $10/month | 5 GB / 30-day retention | Break-even ~200 users |
| Team | $30/month | 25 GB / 90-day retention | Break-even ~100 users |

---

## 3. Alternative Approaches to Video

Instead of full video upload/storage, consider:

### 3.1 Local-Only Video Analysis
- User records locally (OBS, ShadowPlay, etc.)
- App analyzes frames locally but doesn't upload
- Zero storage cost, zero legal risk

### 3.2 Clip Extraction
- Only upload 10-30 second highlights, not full matches
- Significantly reduces storage
- Can auto-detect "interesting" moments from demo data

### 3.3 Frame Thumbnails
- Store key frames as images, not video
- ~100KB per frame vs ~50MB per minute of video
- 1000x reduction in storage

### 3.4 Ephemeral Storage
- Auto-delete after 7-14 days unless user pays
- Keeps storage bounded
- Encourages upgrade to paid tier

### 3.5 User's Own Storage
- Integrate with Google Drive / Dropbox / OneDrive
- User provides their own storage
- Zero infrastructure cost

---

## 4. Recommended MVP Approach

1. **Phase 1: No video storage**
   - Parse demos/replays only
   - Provide text/data analysis
   - Zero legal/cost risk

2. **Phase 2: Local video analysis**
   - User points app at their local recording
   - Extract insights without uploading
   - Add value without infrastructure cost

3. **Phase 3: Optional clip upload (paid feature)**
   - Short clips only (30 sec max)
   - Retention limits (30 days default)
   - User-uploaded = user's content

4. **Phase 4: Extended storage (premium)**
   - Longer retention for paying users
   - Higher storage limits
   - Sustainable unit economics

---

## 5. Open Questions

- [ ] Get explicit legal opinion on commercial use of game footage
- [ ] Research Valve's specific commercial use policy for CS2
- [ ] Research Microsoft's Game Content Usage Rules in detail
- [ ] Evaluate local video analysis libraries (OpenCV, ffmpeg)
- [ ] Prototype clip detection from demo timestamps
- [ ] Calculate actual unit economics for target pricing

---

## 6. References

- Valve's Video Policy: https://store.steampowered.com/video_policy
- Microsoft Game Content Usage Rules: https://www.xbox.com/en-US/developers/rules
- AWS S3 Pricing: https://aws.amazon.com/s3/pricing/
- AWS CloudFront Pricing: https://aws.amazon.com/cloudfront/pricing/

---

*Document created: January 2026*
*Last updated: January 2026*
