"""Generic CLI operations must not silently select a private manuscript profile."""
import pytest
from nutev.cli import build_parser


def test_topics_requires_explicit_project_profile():
    with pytest.raises(SystemExit) as exc:
        build_parser().parse_args(['science-topics'])
    assert exc.value.code == 2


def test_topics_accepts_user_selected_profile_without_rewriting():
    args = build_parser().parse_args(['science-topics', '--topic-profile', 'my-project/profile.json'])
    assert args.topic_profile == 'my-project/profile.json'
    assert args.execute_search is False
