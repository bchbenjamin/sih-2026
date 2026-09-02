import json
from pathlib import Path
from unittest.mock import patch

import yaml


def test_overpass_requests_include_json_headers(tmp_path, monkeypatch):
    config = tmp_path / 'case_config.yaml'
    config.write_text(yaml.safe_dump({'case_name': 'rishiganga', 'dem_bbox': [79.55, 30.30, 79.90, 30.50]}))

    with patch('requests.post') as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.raise_for_status.return_value = None
        mock_post.return_value.json.return_value = {'elements': []}

        import scripts.phase1.download_buildings as buildings

        monkeypatch.setattr(buildings, 'ROOT', tmp_path)
        monkeypatch.setattr(buildings, 'Path', Path)
        monkeypatch.setattr('sys.argv', ['download_buildings.py', '--config', str(config)])

        buildings.main()

        called = mock_post.call_args.kwargs
        assert called['headers']['Accept'] == 'application/json'
        assert 'User-Agent' in called['headers']
        assert 'data' in called

        mock_post.reset_mock()

        import scripts.phase1.download_landuse as landuse

        monkeypatch.setattr(landuse, 'ROOT', tmp_path)
        monkeypatch.setattr(landuse, 'Path', Path)
        monkeypatch.setattr('sys.argv', ['download_landuse.py', '--config', str(config)])

        landuse.main()

        called = mock_post.call_args.kwargs
        assert called['headers']['Accept'] == 'application/json'
        assert 'User-Agent' in called['headers']
