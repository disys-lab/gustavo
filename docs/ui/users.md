# Users

The **Users** section (sidebar, admin-only) is where the platform admin
manages accounts and roles. It's backed entirely by Nebula's own
`users`/`user_groups` API — see [Users API](../api/users.md) and
[Authentication](../api/auth.md) for the underlying model.

## Users page (`/users`)

A table of every Nebula user: username, which group(s) they belong to, and
whether they're an admin (derived from group membership, not a separate
flag on the user).

- **Create user** — pick a username and, optionally, a group to add them
  to. Submitting shows the new `username:secret` login credential exactly
  once, in a copy-and-confirm dialog — it can't be retrieved again, only
  regenerated. A user with no group can log in but can't do anything yet:
  they need to belong to at least one group before they can create apps.
- **Regenerate token** (key icon) — issues a brand-new credential for that
  user, invalidating the old one immediately. There's no password-reset
  flow to build here; this *is* the reset flow.
- **Delete** — removes the user from Nebula and from any groups they
  belonged to.

## Groups page (`/users/groups`)

Groups are roles. Each one has:

- **Members** — usernames in this group (comma-separated in the form).
- **Admin** — if checked, every member bypasses all per-app/device-group
  permission checks (same as the break-glass admin, just as a regular
  Nebula account instead of the fixed `nebula`/`nebula` credential).
- **Pruning allowed** — lets members prune unused images.
- **App / device-group grants** — listed on each group's row, and directly
  manageable via that row's **Grants** button. These are usually set
  automatically the first time: when a non-admin user creates an app or
  device group, Gustavo grants their own group `rw` on it immediately after
  creation (see [Apps API](../api/apps.md)). The **Grants** dialog covers
  everything after that — pick an app or device group; if it's not yet
  granted to this group, choose a permission and **Grant** it; if it's
  already granted, the dialog shows the current permission and lets you
  either change it (**Update**) or **Revoke** it entirely. Adding, changing,
  or removing one grant never disturbs the group's other grants. Admins can
  also see which group(s) hold access to a given app from that app's detail
  page (read-only there — manage it from the Groups page).

## Self-service credential rotation

Every logged-in user (not just admins) can rotate their own credential from
the **My credential** action in the sidebar, without needing an admin —
useful after accidentally sharing a credential, or just as routine hygiene.
