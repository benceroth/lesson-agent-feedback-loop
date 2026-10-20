import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from loop.providers import make_provider
from loop.providers.base import ProviderError, ProviderRequest, ReplyError, extract_json, parse_builder_reply
from loop.providers.fake import ScriptedProvider
from loop.providers.openai_compat import OpenAICompatibleProvider
from loop.task import discover_tasks, load_scenarios


def request(role="builder", task="001-fix-off-by-one", attempt=1):
    return ProviderRequest(role, task, attempt, "system", "prompt")


def test_scripted_scenario_selection_is_deterministic_and_seeded():
    picks = lambda seed: [ScriptedProvider(seed=seed, run_index=i).scenario_name("001-fix-off-by-one") for i in range(30)]  # noqa: E731
    assert picks(1) == picks(1)
    assert picks(1) != picks(2)
    assert len(set(picks(1))) > 1


def test_builder_and_reviewer_instances_agree_on_the_scenario():
    for i in range(10):
        a = ScriptedProvider(seed=7, run_index=i)
        b = ScriptedProvider(seed=7, run_index=i)
        assert a.scenario_name("002-add-input-validation") == b.scenario_name("002-add-input-validation")


def test_scripted_provider_replays_attempts_and_repeats_the_last():
    provider = ScriptedProvider(scenario="needs-visible-feedback")
    first = parse_builder_reply(provider.complete(request(attempt=1)).text)
    second = parse_builder_reply(provider.complete(request(attempt=2)).text)
    later = parse_builder_reply(provider.complete(request(attempt=5)).text)
    assert first != second and second == later
    assert "src/pagination.py" in first[0]


def test_unknown_scenario_is_a_clear_error():
    with pytest.raises(KeyError, match="no scenario"):
        ScriptedProvider(scenario="nope").complete(request())


def test_every_task_defines_weighted_scenarios_with_expectations():
    for task in discover_tasks():
        for name, scenario in load_scenarios(task).items():
            assert scenario["weight"] > 0 and scenario["attempts"], (task.id, name)
            assert scenario["expect"] == "passed" or scenario["expect"].startswith("stopped:")


def test_extract_json_handles_fences_and_prose():
    assert extract_json('Sure!\n```json\n{"a": 1}\n```') == {"a": 1}
    assert extract_json('text {"a": {"b": 2}} more') == {"a": {"b": 2}}
    for bad in ["no json", "{broken", "[1, 2]"]:
        with pytest.raises(ReplyError):
            extract_json(bad)


def test_builder_reply_requires_string_files():
    with pytest.raises(ReplyError):
        parse_builder_reply('{"files": {"a.py": 3}}')
    assert parse_builder_reply('{"summary": "s", "files": {"a.py": "x"}}') == ({"a.py": "x"}, "s")


def test_make_provider_rejects_unknown_kind():
    with pytest.raises(ProviderError):
        make_provider("nope")


class _Handler(BaseHTTPRequestHandler):
    seen: dict = {}

    def do_POST(self):  # noqa: N802
        length = int(self.headers.get("Content-Length", 0))
        _Handler.seen = {"path": self.path, "auth": self.headers.get("Authorization"), "body": json.loads(self.rfile.read(length))}
        status = 429 if _Handler.seen["body"]["model"] == "rate-limited" else 200
        body = json.dumps({"choices": [{"message": {"content": '{"summary": "ok", "files": {}}'}}], "usage": {"prompt_tokens": 11, "completion_tokens": 5}})
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body.encode() if status == 200 else b'{"error": "secret-key-echo"}')

    def log_message(self, *args):
        pass


@pytest.fixture
def server():
    httpd = HTTPServer(("127.0.0.1", 0), _Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{httpd.server_port}/v1"
    httpd.shutdown()
    httpd.server_close()


def test_openai_compatible_provider_against_a_local_server(server):
    provider = OpenAICompatibleProvider(server, "test-model", api_key="k-123")
    reply = provider.complete(request())
    assert (reply.tokens_in, reply.tokens_out) == (11, 5)
    assert _Handler.seen["path"] == "/v1/chat/completions"
    assert _Handler.seen["auth"] == "Bearer k-123"
    assert _Handler.seen["body"]["model"] == "test-model"
    assert [m["role"] for m in _Handler.seen["body"]["messages"]] == ["system", "user"]


def test_provider_errors_do_not_leak_the_key_or_body(server):
    provider = OpenAICompatibleProvider(server, "rate-limited", api_key="k-123")
    with pytest.raises(ProviderError) as info:
        provider.complete(request())
    assert "429" in str(info.value) and "k-123" not in str(info.value) and "secret-key-echo" not in str(info.value)


def test_unreachable_server_is_a_provider_error():
    with pytest.raises(ProviderError):
        OpenAICompatibleProvider("http://127.0.0.1:9/v1", "m", timeout=1).complete(request())


def test_remote_plain_http_and_missing_model_are_refused():
    with pytest.raises(ProviderError, match="https"):
        OpenAICompatibleProvider("http://example.com/v1", "m")
    with pytest.raises(ProviderError, match="LOOP_MODEL"):
        OpenAICompatibleProvider.from_env(env={})


def test_from_env_reads_configuration_and_reviewer_model():
    env = {"LOOP_API_KEY": "k", "LOOP_BASE_URL": "http://localhost:11434/v1", "LOOP_MODEL": "a", "LOOP_REVIEWER_MODEL": "b"}
    assert OpenAICompatibleProvider.from_env("builder", env).model == "a"
    assert OpenAICompatibleProvider.from_env("reviewer", env).model == "b"
    assert OpenAICompatibleProvider.from_env("reviewer", {"LOOP_MODEL": "a"}).model == "a"
