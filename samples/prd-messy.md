# Product Requirements Document — ShelfMate

**Prepared by:** Marcus Holt, Founder  
**Date:** June 2026  
**Version:** 1.4 (latest)

---

## What we want to build

ShelfMate is an app for people who read books. The idea is simple: you scan a book's barcode and it gets added to your collection. You can see all your books, mark them as read or unread, and share your shelf with friends. We also want recommendations based on what you've read.

Actually the most important thing is the social side. People should be able to follow each other and see what their friends are reading right now. That is more important than the barcode scanner honestly. Both are important. The barcode scanner is critical for launch.

We've had a lot of feedback that people want to track their reading progress — like page 47 of 312 — not just finished or not finished. So that should be in there too. It should update automatically as you read but we're not sure how that would work technically.

---

## Core features

### Books and shelves

Users add books to their personal shelf. A book can be in one of these states: Want to Read, Currently Reading, Finished, Did Not Finish. We might add more states later, maybe "Lent to a friend" but that's not confirmed.

You should be able to add a book by:
- scanning the barcode with your phone camera
- searching by title or author
- entering the ISBN manually

When you add a book the app should look it up automatically and fill in the cover, title, author, description and number of pages. We will use the Google Books API for this. Or maybe Open Library. Whichever is free and has better data. The team should decide.

Books should have a cover image. If there's no cover available show a placeholder. The placeholder should look nice, not just a grey box.

---

### Reading progress

Users can log their current page number. The shelf shows a progress bar for books in "Currently Reading." Progress is stored per user per book. You shouldn't be able to set your page to more than the total pages in the book.

Actually we've also been asked about logging by percentage instead of page numbers, because ebooks don't always have real page numbers. So maybe the user can choose between page and percentage. This is important for ebook readers.

We thought about integrating with Kindle to sync progress automatically but that's probably too complex. Leave it out for now. But maybe add a note somewhere in the app that it's coming.

---

### Social features

Users can follow other users. When you follow someone you see their activity in a feed: books they added, status changes, reviews they wrote.

You should be able to search for other users by username or email. Finding friends should be easy.

The feed should be in reverse chronological order. We also want an "interesting" feed that shows popular books among the people you follow but that's a stretch goal and only if there's time.

Reviews: users can write a review and give a star rating (1 to 5) for any book they've finished. Reviews are public by default. There should be a way to make a review private but we haven't decided how that setting works — is it per review or per account? Both options seem useful.

---

### Notifications

Users should get notified when:
- someone follows them
- a friend adds a book to their shelf
- a friend finishes a book they're also currently reading
- someone likes their review

Notifications should be in-app. We also want push notifications on mobile but that's for the mobile app. This is the web app so just in-app for now. But design it so push can be added later without rewriting everything.

---

### Discovery

There should be a way to discover new books. We're thinking a "Trending this week" section based on how many people added a book in the last 7 days. Also "Popular in your network" based on follows. And "Because you read X" recommendations — personalised recommendations based on the user's shelf.

The personalised recommendations are the most exciting part for investors. They should be on the home screen. We don't have an ML team so this would need to use an external API or a simple algorithm. We haven't decided. It needs to feel smart though.

---

### Search

Search should cover books (title, author, ISBN), other users, and reviews. Results from all three should appear together in a single search box. The search should be fast — under 500ms for most queries.

---

## What the app looks like

Clean, minimal, like Goodreads but better. No clutter. The home screen has the feed, the shelf is one tab, discovery is another tab. Profile is accessible from the top corner.

Mobile-first but it has to work on desktop too because some users will use it on a computer. The layout should adapt. Not a native app — a web app, but it should feel like an app.

Dark mode is important. A lot of our target users read at night. Dark mode should be the default actually. Or maybe let the user choose and default to their system setting. Yes, follow the system setting by default.

---

## Technical stuff

We want this to be fast. Pages should load in under 2 seconds. The book lookup (barcode or ISBN) should return results in under 1 second — users are standing in a bookshop and don't want to wait.

No ads. We will monetise through a premium tier later (unlimited shelf size, export to CSV, maybe a browser extension to add books while shopping online — this is a future idea). For now everything is free.

User data is private by default. Users can make their shelf public or keep it private. If a shelf is private, followers can only see the activity feed items but not browse the full shelf. Wait, actually should followers always see the shelf? We need to decide this. Maybe there are two settings: shelf visibility and activity visibility separately.

All user data must be exportable. Users can download their full shelf and reading history as a JSON or CSV file. This is important for trust.

Accounts: email and password. Google login would be nice but it's optional. No anonymous browsing — you have to sign up to see anything.

---

## Things we're not building yet

- Native iOS and Android apps (web only for now)
- Kindle / Apple Books sync
- A browser extension
- A premium tier
- Group reading / book clubs (a lot of people asked for this, add it to the backlog)

---

## Launch

We want to launch in 3 months. We have a designer who will provide Figma files but they're not ready yet. The backend team is 2 engineers. The frontend is 1 engineer. There's no dedicated QA.

The most important thing for the launch is that the core loop works perfectly: add a book, track progress, share with a friend, see their activity. Everything else is secondary.

---

## Open questions (from our last meeting)

- Do we use Google Books API or Open Library? Need to decide this week.
- How does privacy work for reviews — per review or account-level setting?
- Should followers always see the full shelf, or do we need two separate visibility settings?
- What algorithm or API do we use for personalised recommendations?
- "Lent to a friend" shelf state — is this in scope for launch?
