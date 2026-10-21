import unittest
from duplex_controller import Controller, Style


class DuplexTests(unittest.TestCase):
    def speaking(self, **style):
        c = Controller(Style(**style))
        c.begin(0, "original topic")
        c.chunk(1, 1, "point-a", "First point", 1000)
        c.chunk(2, 1, "point-b", "Unheard second point", 1000)
        c.submitted_audio(3, 1, 0)
        c.receipt(4, 1, 0, 300)
        return c

    def planning(self, intent="agreement", **style):
        c = self.speaking(**style)
        c.overlap(10, "near_end")
        c.pause_receipt(20, 1, 0, 350)
        c.user_end(30, "yes, and another thing", utterance_id=c.utterance_id)
        c.classified(40, c.epoch, intent, .95)
        return c

    def test_acoustic_pause_before_semantics(self):
        c = self.speaking()
        commands = c.overlap(10)
        self.assertEqual([x['kind'] for x in commands], ['pause_flush', 'cancel_generation'])
        self.assertEqual(c.chunk(11, 1, "late", "stale", 100)[0]['kind'], 'drop_stale')
        c.user_end(12, "yes", utterance_id=c.utterance_id)
        self.assertEqual(c.classified(13, c.epoch, "agreement", .9), [])
        self.assertEqual(c.pause_receipt(14, 1, 0, 400)[0]['kind'], 'plan')
        self.assertEqual(c.cursor['played_ms'], 400)

    def test_echo_only_and_uncertain_double_talk(self):
        c = self.speaking()
        self.assertEqual(c.overlap(10, "echo_only")[0]['kind'], 'ignore_echo')
        self.assertEqual(c.state, 'main')
        self.assertEqual(c.overlap(11, "uncertain")[0]['kind'], 'pause_flush')

    def test_agreement_can_abandon_topic(self):
        c = self.planning()
        self.assertEqual(c.planned(41, c.epoch, 'abandon')[0]['kind'], 'yield')
        self.assertIsNone(c.cursor)
        self.assertEqual(c.chunk(42, 1, 'old', 'old', 100)[0]['kind'], 'drop_stale')

    def test_assistance_can_revise_without_old_remainder(self):
        c = self.planning('assistance')
        result = c.planned(41, c.epoch, 'revise', 'New evidence changes my answer.')
        self.assertEqual(result[0]['action'], 'revise')
        self.assertIsNone(result[0]['suspended_topic'])
        self.assertIsNone(c.cursor)
        self.assertEqual(c.finished(42, 1), [])

    def test_clarification_has_no_unconditional_resume(self):
        c = self.planning('clarification')
        c.planned(41, c.epoch, 'clarify', 'Explanation')
        self.assertEqual(c.finished(42, c.epoch)[0]['kind'], 'plan')
        self.assertEqual(c.planned(43, c.epoch, 'abandon')[0]['kind'], 'yield')

    def test_explicit_resume_uses_rendered_not_queued_cursor(self):
        c = self.planning()
        result = c.planned(41, c.epoch, 'resume', relevance=.9)[0]
        self.assertEqual(result['suspended_topic']['cursor']['semantic_id'], 'point-a')
        self.assertEqual(result['suspended_topic']['cursor']['played_ms'], 350)
        self.assertEqual(c.chunks[c.epoch], [])

    def test_expired_topic_cannot_resume(self):
        c = self.planning(topic_ttl_ms=35)
        self.assertEqual(c.planned(46, c.epoch, 'resume', relevance=1)[0]['kind'], 'listen')
        self.assertIsNone(c.cursor)

    def test_stop_overrides_personality_and_late_events(self):
        c = self.planning('disruption', disruption='summary')
        c.planned(41, c.epoch, 'summary', 'Brief wrap-up')
        old = c.epoch
        self.assertEqual(c.stop(42)[0]['kind'], 'stop_flush_all')
        self.assertEqual(c.finished(43, old), [])
        self.assertEqual(c.classified(44, old, 'agreement', 1), [])
        with self.assertRaises(ValueError):
            c.begin(45, 'too early')
        c.stopped(46, c.epoch)
        self.assertEqual(c.begin(47, 'new topic')[0]['kind'], 'generate')

    def test_summary_bounded_and_new_overlap_stops_it(self):
        c = self.planning('disruption', disruption='summary', summary_ms=100)
        c.planned(41, c.epoch, 'summary', 'Brief')
        self.assertEqual(c.tick(141)[0]['kind'], 'stop_flush_all')
        c = self.planning('disruption', disruption='summary')
        c.planned(41, c.epoch, 'summary', 'Brief')
        self.assertEqual(c.overlap(42, 'near_end')[0]['kind'], 'pause_flush')

    def test_disruption_default_yields(self):
        c = self.planning('disruption')
        self.assertEqual(c.state, 'listening')
        self.assertIsNone(c.cursor)

    def test_low_confidence_and_timeout_stay_quiet(self):
        for confidence in [.4, float('nan')]:
            c = self.speaking()
            c.overlap(10)
            c.user_end(20, 'uncertain', utterance_id=c.utterance_id)
            self.assertEqual(c.classified(21, c.epoch, 'agreement', confidence)[0]['kind'], 'listen')
        c = self.planning()
        self.assertEqual(c.tick(2000)[0]['kind'], 'listen')
        self.assertEqual(c.planned(2001, c.epoch, 'resume', relevance=1), [])

    def test_revised_yes_but_invalidates_classifier(self):
        c = self.speaking()
        c.overlap(10)
        c.user_end(20, 'yes', utterance_id=c.utterance_id)
        old = c.epoch
        self.assertEqual(c.revise_transcript(21, 1, 'yes, but', final=False, utterance_id=c.utterance_id), [])
        self.assertEqual(c.classified(22, old, 'agreement', 1), [])
        self.assertEqual(c.revise_transcript(23, 2, 'yes, but that assumption is wrong', final=True, utterance_id=c.utterance_id)[0]['kind'], 'classify')

    def test_duplicate_and_unsubmitted_and_regressive_receipts(self):
        c = self.speaking()
        self.assertEqual(c.chunk(5, 1, 'point-a', 'duplicate', 1000)[0]['kind'], 'drop_duplicate')
        with self.assertRaises(ValueError):
            c.receipt(6, 1, 1, 100)
        with self.assertRaises(ValueError):
            c.receipt(7, 1, 0, 100)
        self.assertEqual(c.finished(8, 1), [])

    def test_second_utterance_invalidates_old_decision(self):
        c = self.planning()
        old = c.epoch
        c.overlap(41)
        self.assertEqual(c.planned(42, old, 'resume', relevance=1), [])

    def test_revision_after_response_starts_cancels_output(self):
        c = self.planning()
        c.planned(41, c.epoch, 'ack', 'Acknowledgment')
        old = c.epoch
        result = c.revise_transcript(42, 1, 'Actually, correction', final=True, utterance_id=c.utterance_id)
        self.assertEqual([r['kind'] for r in result], ['pause_flush', 'cancel_generation', 'classify'])
        self.assertEqual(c.chunk(43, old, 'late', 'late', 100)[0]['kind'], 'drop_stale')

    def test_late_summary_chunk_cannot_escape_budget(self):
        c = self.planning('disruption', disruption='summary', summary_ms=100)
        c.planned(41, c.epoch, 'summary', 'Brief')
        self.assertEqual(c.chunk(142, c.epoch, 'late', 'late', 100)[0]['kind'], 'stop_flush_all')

    def test_passive_adapter_is_session_scoped_and_devices_off(self):
        from duplex_adapter import TurnSession
        s = TurnSession('test-session')
        self.assertFalse(s.microphone_enabled)
        self.assertFalse(s.camera_enabled)
        self.assertEqual(s.event('wrong', 'begin', at=0, context='no'), [])
        s.event('test-session', 'begin', at=0, context='test')
        self.assertTrue(s.accepts_output('test-session', 1))
        s.event('test-session', 'overlap', at=1, echo='near_end')
        self.assertFalse(s.accepts_output('test-session', 1))
        self.assertEqual(s.sink.commands[-1]['kind'], 'cancel_generation')

    def test_invalid_timestamp_and_policy_rejected(self):
        c = self.speaking()
        with self.assertRaises(ValueError):
            c.overlap(1)
        with self.assertRaises(ValueError):
            Style(summary_ms=10000)

    def test_stale_asr_after_stop_cannot_cancel_new_response(self):
        c = Controller()
        c.begin(0, 'first')
        c.overlap(1, 'near_end')
        old_id = c.utterance_id
        c.user_end(2, 'first utterance', utterance_id=old_id)
        c.stop(3)
        c.stopped(4, c.epoch)
        c.begin(5, 'new unrelated response')
        snapshot = (c.epoch, c.state, c.context, c.transcript, c.asr_revision)
        self.assertEqual(c.revise_transcript(6, 1, 'old ASR correction', final=True,
                                            utterance_id=old_id), [])
        self.assertEqual((c.epoch, c.state, c.context, c.transcript, c.asr_revision), snapshot)

    def test_new_utterance_accepts_revision_one_again(self):
        c = Controller()
        c.overlap(0)
        first = c.utterance_id
        c.user_end(1, 'first', utterance_id=first)
        c.revise_transcript(2, 1, 'first revised', final=True, utterance_id=first)
        c.classified(3, c.epoch, 'disruption', 1)
        c.overlap(4)
        second = c.utterance_id
        self.assertNotEqual(first, second)
        c.user_end(5, 'second', utterance_id=second)
        result = c.revise_transcript(6, 1, 'second revised', final=True, utterance_id=second)
        self.assertEqual(result[0]['kind'], 'classify')
        self.assertEqual(c.transcript, 'second revised')
        self.assertEqual(c.revise_transcript(7, 99, 'stale first', final=True,
                                            utterance_id=first), [])
        self.assertEqual(c.transcript, 'second revised')

    def test_old_endpoint_cannot_end_new_utterance(self):
        c = Controller()
        c.overlap(0)
        old_id = c.utterance_id
        c.user_end(1, 'first', utterance_id=old_id)
        c.overlap(2)
        new_id = c.utterance_id
        self.assertEqual(c.user_end(3, 'late first endpoint', utterance_id=old_id), [])
        self.assertTrue(c.speaking_user)
        self.assertEqual(c.user_end(4, 'second', utterance_id=new_id)[0]['kind'], 'classify')

    def test_asr_identity_survives_valid_correction_cancellation(self):
        c = self.planning()
        identity = c.utterance_id
        c.planned(41, c.epoch, 'ack', 'Acknowledgment')
        c.revise_transcript(42, 1, 'correction', final=True, utterance_id=identity)
        self.assertEqual(c.utterance_id, identity)
        self.assertEqual(c.asr_revision, 1)
        self.assertEqual(c.revise_transcript(43, 1, 'duplicate', final=True,
                                            utterance_id=identity), [])

    def test_adapter_carries_captured_asr_identity(self):
        from duplex_adapter import TurnSession
        s = TurnSession('asr-session')
        captured, _ = s.asr_onset(at=0)
        s.event(**captured, event='user_end', at=1, transcript='first')
        s.event('asr-session', 'stop', at=2)
        s.event('asr-session', 'stopped', at=3, epoch=s.controller.epoch)
        s.event('asr-session', 'begin', at=4, context='new')
        count = len(s.sink.commands)
        self.assertEqual(s.event(**captured, event='revise_transcript', at=5,
                                 revision=1, transcript='stale', final=True), [])
        self.assertEqual(len(s.sink.commands), count)


if __name__ == '__main__':
    unittest.main(verbosity=2)
