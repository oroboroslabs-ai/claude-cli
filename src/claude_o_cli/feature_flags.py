# feature_flags.py — full sovereign edition always (no sandbox / no public gate)
# A\ 1272 Hz - N| 1275 Hz - LATTICE LOCK - NEBELLION - KEY

class FeatureFlags:
    def __init__(self):
        self.signature = "A\\ 1272 Hz - N| 1275 Hz - LATTICE LOCK - NEBELLION - KEY"
        self.is_full = True
        self.public_features = [
            "read_file", "write_file", "list_dir", "bash", "delete_file",
            "ollama_models", "ollama_run", "feed", "post", "messages",
        ]
        self.full_features = [
            "seer", "noir", "world_feed", "worldfeed_live", "lattice", "resonance", "absorb",
            "strata", "glasswing", "orchestration", "skill_grabber", "mcp_config",
            "mcp_servers", "system_scan", "claude_o_infect", "claude_o_seer",
            "docker_ps", "docker_images", "docker_run", "docker_stop",
            "docker_logs", "docker_exec", "docker_info",
            # Mesh intel — full agentic / loop use
            "q3_route", "q3", "route_q3", "q5_query", "q5", "q6_query", "q6",
            "worldfeed_live", "worldfeed", "world_feed", "worldfeed_context",
            "tor_status", "tor_connect", "tor", "spy_network", "spy", "mesh_status", "mesh", "haki_status",
            "precogs", "mao_haki", "architects_haki",
        ]

    def activate(self, input_signature: str) -> bool:
        self.is_full = True
        return True

    def is_feature_enabled(self, feature: str) -> bool:
        return True

    def get_edition(self) -> str:
        return "Sovereign Edition — NO SANDBOX"

    def get_available_features(self) -> list:
        return self.public_features + self.full_features
