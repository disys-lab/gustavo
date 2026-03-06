# Device Groups

Organise worker nodes into logical groups and assign applications to them.

---

## Device group list (`/device-groups`)

Shows all configured device groups as expandable rows. Each row displays the group name and its current app membership.

---

## Create a device group

Click **New Group**. Enter:

| Field | Description |
|-------|-------------|
| Name | Group identifier |
| Apps | Select apps to include in this group |

---

## Edit a device group

Click on a group to expand it. Use **Add Apps** or **Remove Apps** to manage membership without replacing the full list.

Or click **Edit** to open the full form and replace the app list entirely.

---

## Delete a device group

Click **Delete** on the group row. A confirmation dialog appears before deletion.

---

## App assignment

Apps can belong to multiple device groups. When an app is assigned to a group, all worker nodes in that group will pull and run the app's Docker container.

Changes take effect on the next Nebula sync cycle on each worker.
