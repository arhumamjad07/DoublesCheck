"""Protocol failures cannot become format retries, approvals or credential output."""
import json
import unittest
from unittest.mock import Mock, patch
import test_ai_coach as existing
from nightshift_client import CoachError, StructuredContentError, MODEL
from evaluate_reasoning import SuiteBudget


class ProtocolTests(unittest.TestCase):
    def setUp(self): self.factory=existing.TransportTests()

    def test_discovery_happens_once_before_any_model_requests(self):
        client,session=self.factory.client()
        client.call("Critic","schema",{});client.call("Critic","schema",{})
        self.assertEqual(session.get.call_count,1)
        self.assertEqual(session.post.call_count,2)
        self.assertEqual(session.method_calls[0][0],"get")

    def test_failed_discovery_never_sends_a_model_request(self):
        for status in (401,403,502):
            client,session=self.factory.client();session.get.return_value.status_code=status
            with self.subTest(status=status),self.assertRaises(CoachError):client.call("Critic","schema",{})
            session.post.assert_not_called();self.assertEqual(client.calls,0)

    def test_alias_only_discovery_is_not_approved_model_availability(self):
        client,session=self.factory.client()
        session.get.return_value.text=json.dumps({"data":[{"id":"meterless/auto"}]})
        with self.assertRaises(CoachError):client.call("Critic","schema",{})
        session.post.assert_not_called()

    def test_corrupt_stream_is_not_retried_as_a_completed_json_command(self):
        response=self.factory.stream_response();response.iter_lines.return_value=[b'data: {broken',b'data: [DONE]']
        client,session=self.factory.client(response)
        with self.assertRaises(CoachError) as caught:client.call("Critic","schema",{})
        self.assertNotIsInstance(caught.exception,StructuredContentError)
        self.assertEqual(session.post.call_count,1)
        self.assertFalse(any(e["action"]=="structured_response_refused" for e in client.trace.events))

    def test_provider_error_diagnostics_are_fixed_categories_not_raw_messages(self):
        response=self.factory.stream_response()
        response.iter_lines.return_value=[b'data: '+json.dumps({'error':{'message':'NVIDIA upstream HTTP 503 timed out private-runtime-token-for-test private prompt'}}).encode()]
        client,session=self.factory.client(response)
        with self.assertRaises(CoachError):client.call("Critic","schema",{})
        events=json.dumps(client.trace.events)
        self.assertNotIn('private prompt',events);self.assertNotIn('private-runtime-token-for-test',events)
        refusal=next(e for e in client.trace.events if e["action"]=="model_withheld")
        self.assertIn('timeout',refusal['diagnostics']['gateway_error_categories'])
        self.assertEqual(refusal['diagnostics']['gateway_error_statuses'],['503'])

    def test_duplicate_command_keys_are_refused(self):
        client,_=self.factory.client(self.factory.response(content='{"verdict":"approve","verdict":"revise"}'))
        with self.assertRaises(StructuredContentError):client.call("Critic","schema",{})

    def test_duplicate_envelope_keys_do_not_trigger_a_model_format_retry(self):
        response=self.factory.response();response.iter_content.return_value=[b'{"model":"x","model":"y"}']
        client,_=self.factory.client(response)
        with self.assertRaises(CoachError) as caught:client.call("Critic","schema",{})
        self.assertNotIsInstance(caught.exception,StructuredContentError)

    def test_response_size_and_active_time_limits_apply_to_normal_json(self):
        response=self.factory.response();response.iter_content.return_value=[b'x'*1_000_001]
        client,_=self.factory.client(response)
        with self.assertRaises(CoachError):client.call("Critic","schema",{})
        now=[0]
        response=self.factory.response()
        def chunks():
            now[0]=481
            yield response.content
        response.iter_content.side_effect=chunks
        client,_=self.factory.client(response,clock=lambda:now[0])
        with self.assertRaises(CoachError):client.call("Critic","schema",{})

    def test_suite_budget_is_shared_across_clients_and_counts_failed_requests(self):
        budget=SuiteBudget(1)
        session=Mock();session.post.side_effect=RuntimeError('provider connection failed')
        discovery=self.factory.response();discovery.text=json.dumps({'data':[{'id':MODEL}]})
        session.get.return_value=discovery
        with patch('nightshift_client.settings',return_value=('http://127.0.0.1:8088/v1','fake-local-runtime-token')):
            one=budget.factory(existing.Trace(),allow_live=True,session=session)
            two=budget.factory(existing.Trace(),allow_live=True,session=session)
        with self.assertRaises(CoachError):one.call('Critic','schema',{})
        self.assertEqual(budget.calls,1)
        with self.assertRaises(CoachError):two.call('Critic','schema',{})
        self.assertEqual(session.post.call_count,1)


if __name__=='__main__':unittest.main()
