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
        c.user_end(30, "yes, and another thing")
        c.classified(40, c.epoch, intent, .95)
        return c

    def test_acoustic_pause_before_semantics(self):
        c = self.speaking()
        commands = c.overlap(10)
        self.assertEqual([x['kind'] for x in commands], ['pause_flush', 'cancel_generation'])
        self.assertEqual(c.chunk(11, 1, "late", "stale", 100)[0]['kind'], 'drop_stale')
        c.user_end(12, "yes")
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
            c.user_end(20, 'uncertain')
            self.assertEqual(c.classified(21, c.epoch, 'agreement', confidence)[0]['kind'], 'listen')
        c = self.planning()
        self.assertEqual(c.tick(2000)[0]['kind'], 'listen')
        self.assertEqual(c.planned(2001, c.epoch, 'resume', relevance=1), [])

    def test_revised_yes_but_invalidates_classifier(self):
        c = self.speaking()
        c.overlap(10)
        c.user_end(20, 'yes')
        old = c.epoch
        self.assertEqual(c.revise_transcript(21, 1, 'yes, but', final=False), [])
        self.assertEqual(c.classified(22, old, 'agreement', 1), [])
        self.assertEqual(c.revise_transcript(23, 2, 'yes, but that assumption is wrong', final=True)[0]['kind'], 'classify')

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
        result = c.revise_transcript(42, 1, 'Actually, correction', final=True)
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


if __name__ == '__main__':
    unittest.main(verbosity=2)
