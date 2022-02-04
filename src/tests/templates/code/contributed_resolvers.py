from nmk.model.resolver import NmkStrConfigResolver


class StrResolver(NmkStrConfigResolver):
    def get_value(self, name: str) -> str:
        return "my dynamic value from python path"
