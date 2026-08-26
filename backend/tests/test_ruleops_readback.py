from app.scripts import ruleops_readback


def test_readback_game_passes_source_bound_public_contract(monkeypatch):
    def fake_get_json(url: str, timeout_seconds: float):
        if url.endswith('/rule-sets'):
            return 200, {
                'rulesets': [
                    {
                        'status': 'active',
                        'is_active': True,
                        'verification_status': 'source_bound',
                    }
                ]
            }
        return 200, {
            'identity_status': 'verified',
            'view_count': 12,
            'amazon_url': 'https://example.com/affiliate',
            'rules_content': None,
        }

    def fake_get(url: str, timeout_seconds: float, *, accept: str):
        return 200, 'text/html', '<html>official rule text</html>'

    monkeypatch.setattr(ruleops_readback, '_get_json', fake_get_json)
    monkeypatch.setattr(ruleops_readback, '_get', fake_get)

    result = ruleops_readback.readback_game(
        'https://example.test', 'game-a', expected_text=['official rule text']
    )

    assert result.ok is True
    assert result.active_source_bound_rulesets == 1
    assert result.legacy_rules_content_present is False
    assert result.affiliate_path_present is True
    assert result.view_count == 12
    assert result.expected_text_missing == []


def test_readback_game_fails_when_legacy_authority_or_expected_text_remains_missing(monkeypatch):
    def fake_get_json(url: str, timeout_seconds: float):
        if url.endswith('/rule-sets'):
            return 200, {
                'rulesets': [
                    {
                        'status': 'active',
                        'is_active': True,
                        'verification_status': 'source_bound',
                    }
                ]
            }
        return 200, {'identity_status': 'verified', 'rules_content': 'legacy text'}

    monkeypatch.setattr(ruleops_readback, '_get_json', fake_get_json)
    monkeypatch.setattr(
        ruleops_readback,
        '_get',
        lambda url, timeout_seconds, *, accept: (200, 'text/html', '<html>other</html>'),
    )

    result = ruleops_readback.readback_game(
        'https://example.test', 'game-b', expected_text=['new rule']
    )

    assert result.ok is False
    assert result.legacy_rules_content_present is True
    assert result.expected_text_missing == ['new rule']


def test_batch_readback_keeps_sibling_results_when_one_game_fails(monkeypatch):
    def fake_readback(base_url: str, slug: str, *, expected_text, timeout_seconds):
        if slug == 'broken':
            return ruleops_readback.ReadbackResult(
                slug=slug,
                ok=False,
                game_http=None,
                ruleset_http=None,
                page_http=None,
                identity_status=None,
                active_source_bound_rulesets=None,
                legacy_rules_content_present=None,
                affiliate_path_present=None,
                view_count=None,
                expected_text_missing=expected_text,
                error='TimeoutError: timed out',
            )
        return ruleops_readback.ReadbackResult(
            slug=slug,
            ok=True,
            game_http=200,
            ruleset_http=200,
            page_http=200,
            identity_status='verified',
            active_source_bound_rulesets=1,
            legacy_rules_content_present=False,
            affiliate_path_present=False,
            view_count=3,
            expected_text_missing=[],
        )

    monkeypatch.setattr(ruleops_readback, 'readback_game', fake_readback)

    report = ruleops_readback.generate_report(
        ['good', 'broken'], expected_text={'broken': ['expected']}, workers=2
    )

    assert report['games'] == 2
    assert report['passed'] == 1
    assert report['failed'] == 1
    assert [item['slug'] for item in report['results']] == ['broken', 'good']
    assert report['results'][0]['error'] == 'TimeoutError: timed out'


def test_expected_text_file_requires_string_arrays(tmp_path):
    path = tmp_path / 'expected.json'
    path.write_text('{"game": [1]}', encoding='utf-8')

    try:
        ruleops_readback._load_expected(path)
    except ValueError as exc:
        assert 'string slugs to arrays of strings' in str(exc)
    else:
        raise AssertionError('invalid expected-text payload should fail')
