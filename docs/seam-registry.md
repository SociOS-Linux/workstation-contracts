# Seam Registry (13 seams)

Machine-readable contract: [`contracts/seam-registry.json`](../contracts/seam-registry.json) — SeamDefinition instances (canonical schema: SourceOS-Linux/sourceos-spec T0-2, vendored here). Validated by `tools/validate_seam_registry.py` in `make validate`.

A **seam** is an ungated boundary between system layers that represents an attack surface. Each names where trust is not yet enforced, the exploit vector, and the gate that closes it.

| Seam | Boundary | Attack vector | Gate | Status | Priority | Linked |
|---|---|---|---|---|---|---|
| SEAM-001 | EFI/NVRAM → OS | efi_rootkit.bin; csr-active-config=0x67 (SIP disabled) | boot attestation | open | critical | SourceOS-Linux/agent-machine#T2-3 |
| SEAM-002 | MDM → usernoted | Unauthorized MDM enrollment (IBM MaaS360) | MDM profile audit: flag unrecognized profiles | open | critical | SourceOS-Linux/agent-machine#T2-3 |
| SEAM-003 | SEP → Keybag | SEP non-participation in keybag operations (ANOMALY-007) | SEP participation check | open | critical | SourceOS-Linux/agent-machine#T2-3 |
| SEAM-004 | DNS → Application | Resolution returning 102.165.31.x (adversary IPs) | DNS pinning; DNSSEC | open | critical | SociOS-Linux/source-os#linux/dns-pinning |
| SEAM-005 | TLS → CipherSuite | RC4_128_MD5 cipher downgrade | TLS 1.2 minimum; cipher allowlist | open | critical | SociOS-Linux/source-os#linux/tls-enforcement |
| SEAM-006 | OAuthToken → Device | Token exfiltration via MITM | device-bound tokens | open | high | SocioProphet/mcp-a2a-zero-trust |
| SEAM-007 | Knox/MDM → Android | Knox privilege above Android permissions | Knox audit; SemWifiSwitch check | open | medium | future |
| SEAM-008 | ManagedSpace → SpatialAuthorization | displayUUID instability from firmware manipulation (ANOMALY-008) | displayUUID stability check; attestation timestamp on spatial authorization | open | high | SourceOS-Linux/agent-machine#T2-3 |
| SEAM-009 | Intelligence → ActionAuthorization | Agent self-authorizing actions | dndAllowIntelligentManagement:false enforced; autonomous_action gated | partially_gated | high | SocioProphet/ontogenesis#T1-4, SocioProphet/mcp-a2a-zero-trust#T4-2 |
| SEAM-010 | WorkflowDefinition → Execution | Unsigned workflow injected | workflow signing; state-machine admission gate | designed | high | SociOS-Linux/source-os, SourceOS-Linux/agent-machine |
| SEAM-011 | AgentOutput → Ledger | Local ledger tampered by MDM operator | external append-only ledger; crypto hash chain | designed | critical | SourceOS-Linux/agent-machine#T2-3, SociOS-Linux/source-os#T6-2 |
| SEAM-012 | ThirdParty → Audio/Camera | avfoundation access undeclared | avfoundation access logged; undeclared access = kill switch | open | high | SociOS-Linux/source-os#T6-2 |
| SEAM-013 | ClaudeDesktopTelemetry → PlatformData | sessionSampleRate:100 (100% of sessions); sensitive output can route through a fully-sampled telemetry surface | telemetry boundary check in ActivationDecision (advisory); sensitive output must not route through a 100%-sampled surface | open | critical | SourceOS-Linux/agent-machine#T2-1 |

> Runtime enforcement (eBPF `agent-class-filter.c` / `kill-switch.c`, `boot-attestation.sh`) lives in `source-os` and is deferred to a Linux kernel environment. This registry is the **contract** those runtimes implement against.
