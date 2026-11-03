# Automation capabilities — verified 2026-10-25

| Mechanism | Status | Evidence / limit |
|---|---|---|
| Native Codex automation | AVAILABLE | Exposed automation_update supports local heartbeat and project cron. Not invoked to create an active run during bootstrap. |
| Local project access | AVAILABLE | list_projects returns local project 3c121365-2c66-45ec-9810-4a0f3081e982 at this exact workspace; actual reads/writes succeed. |
| Local Codex tasks | AVAILABLE | create_thread / read_thread / wait_threads tools exposed. No worker started during bootstrap. |
| Scheduled Work | NEEDS USER UI SETUP | Official docs support desktop local schedules; account-specific Work UI and execution not tested. |
| Event-triggered Work | NEEDS USER UI SETUP | Official support for selected app events, not a documented arbitrary local-file event. No local-folder event hook established. |
| Local filesystem event→Work task | NOT AVAILABLE | No exposed supported mechanism in this session. Use polling. |
| Codex Cloud shared local folder | NOT AVAILABLE | Cloud has separate workspace; local files not automatically shared. |
| Cloud environment setup | NEEDS USER UI SETUP | Published environment needed; not configured/inspected, unnecessary here. |
| Python supervisor directly launches Work worker | NOT AVAILABLE | No supported client launch interface exposed to this CLI. Native scheduler/runner supplies reasoning. |
| macOS launchd heartbeat | AVAILABLE | Prepared plist only, not installed; routing and status only. |

Evidence: current exposed tool schemas, list_projects result, actual filesystem access; [Scheduled tasks](https://learn.chatgpt.com/docs/automations), [Codex environments](https://learn.chatgpt.com/docs/environments/modes). Documentation establishes product capability, not this account's Work entitlement or successful unattended execution. No internal client database, preferences or private endpoints inspected.
