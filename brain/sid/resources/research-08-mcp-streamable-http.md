# Research 08 — MCP Streamable HTTP

- **Source:** [MCP transport specification](https://modelcontextprotocol.io/specification/2025-11-25/basic/transports)
- **Reviewed:** 2026-11-27
- **Requirements:** NFR-OPS-01, CI-T, NFR-SEC-03

## Distilled findings

- MCP messages use JSON-RPC; Streamable HTTP uses HTTP POST and GET on one MCP
  endpoint, with optional server-sent events.
- Servers must validate incoming `Origin` headers to prevent DNS rebinding.
- For local execution, the specification recommends binding to localhost and
  recommends authentication for server connections.
- Docker networking may require the process inside a container to listen on all
  container interfaces while the host publishes the port only to loopback.

## Project implication

Bind Docker's host-side MCP port to `127.0.0.1` for local use; review MCP SDK
Origin enforcement and require authentication/TLS before remote deployment. See
[[docs/architecture/architecture]] and [[brain/sid/resources/second-brain-conventions]].
