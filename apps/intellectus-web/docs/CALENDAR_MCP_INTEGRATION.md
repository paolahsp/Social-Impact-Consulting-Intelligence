# Future calendar integration

The current MVP only constructs an official Google Calendar event-template URL
in the browser. It does not read a calendar, create an event or confirm that an
invitation was sent.

A future calendar integration may, with explicit consultant consent and a
human confirmation step:

- consult attendee availability;
- propose suitable times;
- create the agreed event;
- add confirmed attendees;
- update or cancel the event.

Before implementation, confirm provider permissions, timezone behavior,
attendee consent, audit requirements and the final confirmation interaction.
The consultant must be able to review all event details before any write.
