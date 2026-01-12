# UI Polish Checklist for Submission

Priority levels:
- **P0**: Must have for submission (blocks demo)
- **P1**: Should have (significantly improves impression)
- **P2**: Nice to have (if time permits)

---

## Landing Page

- [ ] **P0** - Clear headline explaining what the app does
- [ ] **P0** - Upload button prominently visible
- [ ] **P1** - Brief "How it works" section (3 steps)
- [ ] **P1** - Sample analysis preview (so judges see value before uploading)
- [ ] **P2** - Testimonial or example quote from analysis
- [ ] **P2** - Footer with GitHub link

## Upload Experience

- [ ] **P0** - Upload progress indicator works correctly
- [ ] **P0** - Clear error messages if upload fails
- [ ] **P0** - File type validation (only accept video formats)
- [ ] **P1** - Drag-and-drop support
- [ ] **P1** - File size indicator / limit warning
- [ ] **P2** - Estimated analysis time display

## Analysis Loading State

- [ ] **P0** - Loading indicator while Gemini processes
- [ ] **P0** - User knows something is happening (not a frozen screen)
- [ ] **P1** - Estimated time remaining or progress steps
- [ ] **P1** - Fun loading messages ("Scouting your dark age...", "Analyzing your castle timing...")
- [ ] **P2** - Cancel option

## Results Page

- [ ] **P0** - Game summary displays correctly
- [ ] **P0** - Timestamped feedback is readable and clear
- [ ] **P0** - Improvement priorities are visible
- [ ] **P1** - Visual hierarchy (most important info stands out)
- [ ] **P1** - Timestamps are clickable or clearly formatted
- [ ] **P1** - Categories/sections are collapsible or organized
- [ ] **P1** - Export or share option
- [ ] **P2** - Print-friendly view
- [ ] **P2** - Dark mode support

## Mobile Responsiveness

- [ ] **P1** - App doesn't break on tablet/mobile (judges might test)
- [ ] **P2** - Fully responsive design

## Error Handling

- [ ] **P0** - API errors show user-friendly message
- [ ] **P0** - Network errors handled gracefully
- [ ] **P1** - Retry option on failure
- [ ] **P1** - Clear messaging if video is too long/unsupported

## Performance

- [ ] **P0** - Page loads quickly (no huge unoptimized assets)
- [ ] **P0** - No console errors visible
- [ ] **P1** - Loading states don't flicker

## Branding & Polish

- [ ] **P1** - Consistent color scheme
- [ ] **P1** - Professional-looking fonts
- [ ] **P1** - No placeholder text ("Lorem ipsum", "TODO", etc.)
- [ ] **P1** - Favicon set
- [ ] **P2** - Custom Open Graph image for social sharing
- [ ] **P2** - Page title is descriptive

---

## Pre-Submission Smoke Test

Run through this exact flow before submitting:

1. [ ] Open app in incognito/private browser
2. [ ] Verify landing page loads correctly
3. [ ] Upload a test video
4. [ ] Confirm upload progress displays
5. [ ] Wait for analysis to complete
6. [ ] Verify results display correctly
7. [ ] Check on mobile device
8. [ ] Test with a second video to ensure it's repeatable

---

## Quick Wins (High Impact, Low Effort)

If short on time, prioritize these:

1. **Loading messages** - Add 3-4 fun AoE2-themed messages during analysis
2. **Hero section** - One strong headline + one sentence description
3. **Sample result** - Screenshot or embedded example of a good analysis
4. **Error boundaries** - Wrap main components so crashes show friendly error
5. **Favicon** - Takes 2 minutes, looks unprofessional without one
