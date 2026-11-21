# 06 — Stream Production

SIXFOLD is shot **two ways at once**, from one event:

1. **THE STREAM** is the live show. In the fiction, it's a pirate livestream: handheld, chat-driven,
   hosted, imperfect on purpose. It's the main product and the kayfabe frame.
2. **THE BROADCAST** is a traditional multi-cam shoot of the same night, cut afterwards into
   polished match videos, highlight packages and the archive.

Every camera feeds both. The difference is **how it's cut** and **what's on screen**.

---

## The camera plan

### Stream-native cameras (visible, in-fiction)
| Camera | Who | What it shoots |
|---|---|---|
| **Host Cam** | VALE's dedicated operator, close, always on him | The anchor shot. VALE talks straight to it and reads chat. |
| **Shadows** (×6–8) | Ride-along camera ops, one assigned per featured wrestler for the night | A vertical-friendly handheld that follows a wrestler from the car park, through the Lobby and the entrance, to the rim. They stop at the rim, because Shadows never enter the pit. |
| **Lobby Cam** | A fixed wide shot plus one roaming handheld | Backstage, always live. Confrontations, interviews, people just existing. |
| **Rim Bar Cam** | A fixed shot | The chat moderators reacting. |
| **Locker Cam** | Fixed, wide-angle and low-fi | The post-show stream. |

**Shadows are characters.** They have names, they're credited, and they occasionally get shoved or
spoken to on camera. When a wrestler is attacked backstage, the audience sees it *from their Shadow's
camera*: it drops, gets picked back up, and runs. Kayfabe rule: **Shadows never take sides and
never stop filming.**

### Traditional cameras (invisible, out of fiction)
| Camera | Position | Purpose |
|---|---|---|
| **Hard Cam** | On the riser opposite Post 1 | The master wide. The match of record. |
| **Halo** | Overhead, on a rig above the pit | A top-down hexagon shot. It's the signature SIXFOLD angle, and it makes exits readable. |
| **Rim Cams** (×6) | One small locked-off camera at the base of each post, looking along the rim | Floor-contact replays, used for rim judge calls and Shorts. |
| **Pit Handhelds** (×2) | Operators on the crash zone (outside the pit, never inside) | Close coverage of the action. |
| **Crowd Cams** (×2) | In the risers | Reactions. |
| **Entrance Jib** | At the entrance stair | Cape ritual coverage. |

**Mic plan:** a lav on the Warden (calls, counts, pit audio), boundary mics in the canvas, the
Booth, VALE, the Shadows' on-camera mics, and the crowd.

---

## Two feeds, one night

| | THE STREAM (live) | THE BROADCAST (post) |
|---|---|---|
| **Cut by** | A live switcher. The kayfabe "SIXFOLD control room" is sometimes shown on screen. | An edit team, after the event |
| **Framing** | Mixed: Host Cam and Shadows lead, with traditional cameras for match coverage | Traditional: Hard Cam, Halo, handhelds |
| **Aspect** | 16:9 main, with a vertical simulcast built from the Shadow feeds | 16:9 |
| **Overlays** | Full stream UI: chat, viewer count, Hush meter, alerts, faction watermarks | A clean feed. Minimal lower thirds, match graphics only |
| **Commentary** | The Booth plus VALE, who talks to chat | The Booth only, re-mixed. Optional added voiceover. |
| **Mistakes** | Kept in as part of the show | Cleaned up, unless they're story |
| **Purpose** | Being there. Chaos, community, kayfabe. | The record. Rewatchable, shareable, and good enough to be judged as wrestling |

---

## The stream UI (in-world overlays)

The overlay is a **diegetic interface**: the audience reads it as SIXFOLD's own streaming UI, and
the characters can affect it.

- **Viewer counter:** the real live count, framed as the in-world number.
- **The Hush Meter:** a live bar driven by the production team, mirroring the Warden's tablet. It
  spikes during near-exits and tense moments, and *flatlines* at story beats.
- **Chat:** real chat on screen, heavily moderated (see `07` for the safety rules).
- **Alerts:** subs, follows and memberships, styled as "**+1 in the Hush**."
- **Faction watermarks:** when the Accord appears, a government-style seal fades in at the corner.
- **Glitch hijacks:** pre-built corruption graphics, audio stingers and fake "connection lost"
  screens, triggered from the switcher on cue. They have to *look* like real failures while being
  fully controlled.

### Hijack rules
- Every hijack is pre-planned and rehearsed, and lasts under 90 seconds.
- **Never fake a technical failure while a match is at a dangerous moment.** The real safety feed
  stays clean to production at all times.
- Accessibility: make sure no hijack graphic flashes in a way that could trigger photosensitive
  viewers. Run graphics through a flash and pattern checker.

---

## The powers policy

**Powers are never shown live.** It's the first law, and it solves three problems at once:

- **Budget:** no live VFX.
- **Kayfabe:** the stream is *inside* the Hush.
- **Wrestling:** the matches stand on their own.

Powers appear only in **out-of-show content**:
| Format | Example |
|---|---|
| **Leaked footage** | "Accord bodycam" or "security camera" clips with VFX, released on social. Grainy, short, deniable. |
| **Aftermath** | A dented car in the car park. Frost on the Lobby door after HALCYON walks through. |
| **Implication** | Lights flicker, sound drops out, the Hush Meter spikes, and a wrestler's Shadow cam distorts. |
| **Lore videos** | Fully produced short films for character origins, tied to "story mode" (see `07`). |

---

## Run of show (a weekly SIXFOLD LIVE episode, ~2.5 hours)

| Time | Segment | Primary cameras |
|---|---|---|
| T−30:00 | **The Lobby**, the pre-show. Shadows pick up wrestlers on arrival. | Shadows, Lobby |
| 0:00 | **Cold open**: VALE on Host Cam, plus the episode's cold-open angle | Host Cam |
| 0:05 | Opener match | Traditional + Shadows on entrance |
| 0:20 | Lobby segment | Lobby, Shadow |
| 0:30 | Match 2 | Traditional |
| 0:45 | **Chat segment**: VALE reads (pre-screened) chat; a wrestler responds | Host Cam, Rim Bar |
| 0:55 | Match 3 / tag | Traditional |
| 1:15 | Story beat: a promo in the pit, an attack, or a hijack | Mixed |
| 1:30 | Match 4 | Traditional |
| 1:50 | **Main event**, with full cape ritual coverage | Traditional + entrance jib + Halo |
| 2:20 | Closing beat or cliffhanger | Mixed |
| 2:25 | Handover to **The Locker** (a separate stream) | Locker Cam |

---

## Crew as cast

| Character role | Real job | Notes |
|---|---|---|
| **VALE** | Host and lead talent | Needs real improv skills, since he reads live chat. |
| **The Booth** (2–3) | Commentators | One wrestling expert, one "cape historian" who explains lore, and one rotating guest. |
| **Shadows** | Camera ops | Named, recurring, and given personalities. Cast operators who are comfortable on camera. |
| **Wardens** | Referees | Real trained wrestling referees. |
| **Rim Judges** | Officials | Trained to spot the floor, and part of the safety team. |
| **Keeper of Posts** | Ring crew | Ceremonial on screen, a stagehand off it. |
| **Chat mods** | Moderators | Some appear on camera in the Rim Bar, others work purely off screen for safety. |
| **The Control Room** | The director and switcher | Occasionally shown on screen as "SIXFOLD Control," panicking during hijacks. |

---

## Post-production pipeline

| Output | Source | Turnaround |
|---|---|---|
| **Full stream VOD** | The stream feed, as aired | Immediate |
| **Match cuts** | The broadcast feed, re-edited with the Booth remixed | 24 hours |
| **Shadow cuts** | Raw ride-along footage, one wrestler's night from their Shadow's POV | 48 hours |
| **Replay Shorts** | Rim cams and Halo: floor-contact calls, teeters, exits | Same night |
| **Lobby clips** | Lobby cam | Same night |
| **Lore drops** | Separately produced VFX shorts | On the story calendar |
