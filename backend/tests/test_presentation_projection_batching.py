from app.services.presentation_projection import PresentationProjectionService


class Result:
    def __init__(self, data):
        self.data = data


class Query:
    def __init__(self, client, table):
        self.client = client
        self.table = table

    def select(self, *_args, **_kwargs):
        return self

    def eq(self, *_args, **_kwargs):
        return self

    def order(self, *_args, **_kwargs):
        return self

    def in_(self, column, values):
        assert self.table == "evidence_bindings"
        assert column == "claim_id"
        self.client.requested_claim_ids = list(values)
        return self

    def execute(self):
        self.client.execute_counts[self.table] = self.client.execute_counts.get(self.table, 0) + 1
        return Result(self.client.rows[self.table])


class Client:
    def __init__(self):
        self.execute_counts = {}
        self.requested_claim_ids = []
        self.rows = {
            "claims": [
                {
                    "claim_id": "claim.setup",
                    "rule_id": "rule.setup",
                    "normalized_payload": {"statement": "Set up the board."},
                    "lifecycle_status": "accepted",
                },
                {
                    "claim_id": "claim.end",
                    "rule_id": "rule.end",
                    "normalized_payload": {"statement": "End after the final round."},
                    "lifecycle_status": "accepted",
                },
            ],
            "evidence_bindings": [
                {"claim_id": "claim.setup", "source_id": "source.rules", "relation": "supports"},
                {"claim_id": "claim.end", "source_id": "source.rules", "relation": "supports"},
            ],
        }

    def table(self, table):
        return Query(self, table)


def test_projection_batches_evidence_bindings_for_all_claims():
    client = Client()

    eligible = PresentationProjectionService._load_eligible_rule_claims(client, "ruleset-1")

    assert client.execute_counts == {"claims": 1, "evidence_bindings": 1}
    assert client.requested_claim_ids == ["claim.setup", "claim.end"]
    assert eligible["rule.setup"][0]["source_ids"] == ["source.rules"]
    assert eligible["rule.end"][0]["source_ids"] == ["source.rules"]
