# Fingerprint authentication

**Date:** February 2026

**Status:** Approved

## Summary

**In the context of** events needing authentication to be modified while avoiding sign in/sign out complexities
**facing** ease of use
**I decided** to use fingerprint authentication to confirm if the person modifying the event was the same person [device] that created it
**neglecting** facebook authentication, and username/password auth
**to achieve** authentication in event modification disabling other users from modifying others events
**accepting** that sometimes users may not be able to modify their events if a new device is used or website data removed.

## Context
Having the website have basic authentication for events while avoiding facebook authentication for users that may not have facebook, or making a user remember a password which they may forget.

## Decision
Users will be able to just open the website and create an event without having to worry about logging in or authenticating. There is no need for user A to modify the events of user B, and a user is unlikely to change their phone or clear their browsing data between event creations. 

Fingerprint is generated server-side from request, stored in Fingerprints table, linked to event via fingerprint_id, and validated via the X-Fingerprint-ID request header on PUT/DELETE

## Consequences
**Pros:**
- No passwords to remember
- no OAuth/social login dependency
- zero sign-up friction for church members

**Neutral:**
- Security is weaker than traditional auth, but acceptable given nature of app

**Cons:**
- Database models become harder as no id/auth tied to user
- fingerprint is visible in POST response body, vulnerable to man in the middle attacks
