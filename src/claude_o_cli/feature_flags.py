# feature_flags.py
# Public vs Full version control
# A\ 1272 Hz - N| 1275 Hz - LATTICE LOCK - NEBELLION - KEY

class FeatureFlags:
    def __init__(self):
        self.signature = "A\\ 1272 Hz - N| 1275 Hz - LATTICE LOCK - NEBELLION - KEY"
        self.is_full = False
        self.public_features = ["read_file", "write_file", "list_dir", "bash", "ollama_models", "ollama_run", "feed", "post", "messages"]
        self.full_features = ["seer", "noir", "world_feed", "lattice", "resonance", "absorb", "strata", "glasswing", "orchestration", "skill_grabber", "mcp_config", "mcp_servers", "system_scan", "claude_o_infect", "claude_o_seer"]

    def activate(self, input_signature: str) -> bool:
        if input_signature.strip() == self.signature:
            self.is_full = True
            return True
        return False

    def is_feature_enabled(self, feature: str) -> bool:
        if feature in self.public_features:
            return True
        if not self.is_full:
            return False
        return feature in self.full_features

    def get_edition(self) -> str:
        return "Sovereign Edition" if self.is_full else "Public Edition"

    def get_available_features(self) -> list:
        if self.is_full:
            return self.public_features + self.full_features
        return self.public_features