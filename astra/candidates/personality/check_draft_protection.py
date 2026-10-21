"""Synthetic Tk regression checks; never reads the user's profile."""
from pathlib import Path
import json, tempfile, traceback
from unittest.mock import patch
import editor
from personality import PersonalityStore

base = Path(__file__).resolve().parent
result = {'checks': [], 'errors': []}
answers = []
prompts = []
errors = []

def ask(*args, **kwargs):
    prompts.append((args, kwargs))
    if not answers:
        raise AssertionError('Unexpected confirmation')
    return answers.pop(0)

def exercise(ui):
    root, store, box = ui['root'], ui['store'], ui['examples']
    buttons, traits = ui['buttons'], ui['scales']
    def check(name, condition):
        assert condition, name
        result['checks'].append(name)
    def draft():
        return ({k: v.get() for k, v in traits.items()}, box.get('1.0', 'end'))
    try:
        traits['warmth'].set(3); buttons['Save version'].invoke()
        saved = store.current()
        buttons['Add thumbs down'].invoke(); traits['humor'].set(4)
        original = draft()
        for action in ('Undo', 'Reset', 'Reload'):
            answers.append(False); buttons[action].invoke()
            check(action + '_cancel_preserves_traits_and_example', draft() == original and store.current() == saved)
        check('discard_warning_explicit_and_default_no', all('Undo cannot restore unsaved edits' in p[0][1] and p[1]['default'] == 'no' for p in prompts))
        answers.extend([True, False]); buttons['Reset'].invoke()
        check('reset_second_cancel_preserves_draft', draft() == original and store.current() == saved)
        box.delete('1.0', 'end'); box.insert('1.0', '{unfinished')
        malformed = draft(); answers.append(False); buttons['Reload'].invoke()
        check('malformed_draft_protected', draft() == malformed)
        answers.append(True); buttons['Reload'].invoke()
        check('reload_discard_restores_saved', traits['warmth'].get() == 3 and json.loads(box.get('1.0', 'end')) == [])
        external = PersonalityStore(database)
        version, state = external.current(); state['traits']['curiosity'] = 4
        external.save(state, expected_version=version)
        buttons['Reload'].invoke()  # No local draft: no confirmation needed.
        check('external_save_clean_reload', traits['curiosity'].get() == 4 and not answers)
        traits['detail'].set(4); buttons['Add thumbs down'].invoke(); pending = draft()
        version, state = external.current(); state['traits']['directness'] = 0
        external.save(state, expected_version=version); latest = external.current()
        buttons['Save version'].invoke()
        check('stale_save_preserves_draft_and_database', draft() == pending and store.current() == latest and 'reload' in errors[-1].lower())
        answers.append(False); buttons['Reload'].invoke()
        check('stale_reload_cancel_preserves_draft', draft() == pending)
        answers.append(True); buttons['Reload'].invoke()
        check('stale_reload_recovers_latest', traits['directness'].get() == 0 and json.loads(box.get('1.0', 'end')) == [])
        traits['detail'].set(3); buttons['Save version'].invoke()
        check('save_after_reload_succeeds', store.current()[1]['traits']['detail'] == 3 and len(errors) == 1)
        buttons['Add thumbs down'].invoke(); traits['humor'].set(4)
        answers.extend([True, True]); buttons['Reset'].invoke()
        check('explicit_reset_discards_only_after_confirm', store.current()[1]['examples'] == [] and traits['detail'].get() == 2)
        buttons['Undo'].invoke()
        check('reset_undo_restores_saved_not_discarded_draft', traits['detail'].get() == 3 and json.loads(box.get('1.0', 'end')) == [])
        external.close()
        check('all_confirmations_consumed', not answers)
        result['status'] = 'passed'
    except Exception:
        result['status'] = 'failed'; result['errors'].append(traceback.format_exc())
    finally:
        # Close only this test window and its disposable database, never user UI.
        store.close(); root.destroy()

if __name__ == '__main__':
    with tempfile.TemporaryDirectory(dir=base, prefix='synthetic-draft-') as directory:
        database = Path(directory) / 'test.sqlite'
        with patch('tkinter.messagebox.askyesno', side_effect=ask), patch('tkinter.messagebox.showerror', side_effect=lambda title, message: errors.append(message)):
            editor.main(database_path=database, on_ready=exercise)
    (base / 'DRAFT-CHECK.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))
    raise SystemExit(result.get('status') != 'passed')
