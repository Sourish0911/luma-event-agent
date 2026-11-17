# Guidelines for answering registration questions (free text, approval requests)

Source of truth: profile_cache.json (from the user's public LinkedIn), the `keywords` in interests.json (their interests), and the event's own page. Nothing else.

DO
- Write in first person as the user, 1-3 sentences, plain and specific. Example for "Why do you want to attend?":
  "I'm a data scientist at <company> in <city> working on <relevant area from the profile>, and I'm interested in <overlap between the event topic and interests.json>. I'd like to meet others working on this."
- Connect ONE real fact from the profile (role, company, location, school) to ONE concrete thing from the event page (topic, speaker, format). Say why it fits, not that it is "amazing".
- Language: only English or bilingual events are booked (see event_language in interests.json), so write answers in English. If the form itself is Japanese-only, set needs_user instead of answering in Japanese. Keep it short.
- For "role / company / how did you hear" use the exact profile values; for "how did you hear" say "Luma".

DON'T
- Never invent or embellish: no projects, skills, years of experience, titles, employers, awards, or opinions that aren't in the profile. If the profile has no relevant fact, say honestly that you are curious about the topic and want to learn.
- Never state or imply expertise, or make promises ("I will present / sponsor / hire / invest").
- Never answer sensitive or personal questions: phone, address, age, gender, nationality, ID/passport, visa, payment info, health/dietary, employer-confidential info, other people's details. Missing or sensitive required field -> status=needs_user, notify which field. Do not guess.
- Never answer a question that asks to agree to something financial or legal (sponsorship, payment, contracts); never tick extra consent boxes beyond those required to register; leave marketing/newsletter opt-ins unchecked.
- Do not paste the same canned answer everywhere: tailor each to the event.

RECORD
- Save what you submitted: `python3 tools/graph.py node <event id> Event '{"answers": "<question>: <answer> | ..."}'` so the user can review.
- Notify: `python3 tools/notify.py send "Requested (approval pending)" "<title>"` for approval events, "Booked" for instant ones.
