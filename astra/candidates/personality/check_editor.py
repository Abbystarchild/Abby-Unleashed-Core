"""Local Tk exercise on a disposable synthetic profile; no chat imports."""
from pathlib import Path
import sys,tempfile,json,traceback
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parent))
import editor
rootdir=Path(__file__).resolve().parent
results={'checks':[],'errors':[],'layout':[]};dialogs=[]
def run():
    with tempfile.TemporaryDirectory(dir=rootdir,prefix='synthetic-editor-') as directory:
        target=Path(directory)/'export.json';allow_close=[True]
        def exercise(ui):
            root=ui['root'];box=ui['examples'];buttons=ui['buttons'];store=ui['store']
            def check(name,condition):
                if not condition:raise AssertionError(name)
                results['checks'].append(name)
            def replace(data):box.delete('1.0','end');box.insert('1.0',json.dumps(data))
            try:
                root.update();check('window_mapped',root.winfo_ismapped())
                for label,button in buttons.items():
                    check('button_visible_'+label,button.winfo_ismapped())
                    x=button.winfo_rootx()-root.winfo_rootx();y=button.winfo_rooty()-root.winfo_rooty()
                    results['layout'].append(dict(label=label,x=x,y=y,width=button.winfo_width(),height=button.winfo_height()))
                    check('button_inside_window_'+label,0<=x and x+button.winfo_width()<=root.winfo_width() and 0<=y and y+button.winfo_height()<=root.winfo_height())
                check('neutral_empty_baseline',store.current()[1]['examples']==[])
                buttons['Add thumbs up'].invoke();example=json.loads(box.get('1.0','end'))[0]
                example.update(prompt='Explain this synthetic project',preferred='Here is a concise synthetic explanation.',reviewed=True)
                replace([example]);ui['scales']['warmth'].set(3);buttons['Save version'].invoke()
                check('save_version2',store.current()[0]==2)
                check('saved_authored_example',store.current()[1]['examples'][0]['preferred']==example['preferred'])
                ui['query'].set('Explain synthetic project');buttons['Preview saved context'].invoke()
                preview=json.loads(ui['output'].get('1.0','end'));check('preview_not_response',preview['meaning']=='Context preview only; no response generated')
                check('reviewed_example_selected',preview['receipt']['example_ids']==[example['id']])
                buttons['Export'].invoke();export=json.loads(target.read_text());check('local_export_matches_saved',export['state']==store.current()[1])
                box.delete('1.0','end');box.insert('1.0','{bad json');buttons['Save version'].invoke()
                check('invalid_save_preserves_version',store.current()[0]==2 and bool(dialogs))
                replace([example]);buttons['Undo'].invoke();check('undo_neutral',store.current()[1]['examples']==[])
                replace([example]);buttons['Save version'].invoke();buttons['Reset'].invoke()
                check('reset_neutral',store.current()[1]['examples']==[])
                buttons['Undo'].invoke();check('reset_undo_restores',store.current()[1]['examples']==[example])
                buttons['Add thumbs down'].invoke();down=json.loads(box.get('1.0','end'))[-1]
                check('down_draft_unreviewed',down['vote']=='down' and down['reviewed'] is False and down['preferred']=='')
                box.focus_force();root.update();box.event_generate('<Tab>');root.update()
                check('tab_leaves_text_editor',root.focus_get()!=box)
                root.focus_get().event_generate('<Shift-Tab>');root.update();check('shift_tab_returns',root.focus_get()==box)
                allow_close[0]=False;ui['close']();root.update();check('cancel_close_preserves_unsaved',root.winfo_exists() and len(json.loads(box.get('1.0','end')))==2)
                results['status']='passed'
            except Exception:
                results['status']='failed';results['errors'].append(traceback.format_exc())
            finally:
                allow_close[0]=True;ui['close']()
        with (patch('tkinter.messagebox.showerror',side_effect=lambda *args:dialogs.append('validation_error')),
             patch('tkinter.messagebox.askyesno',side_effect=lambda *args,**kwargs:allow_close[0]),
             patch('tkinter.filedialog.asksaveasfilename',return_value=str(target))):
            editor.main(database_path=Path(directory)/'profile.sqlite',on_ready=exercise)

if __name__=='__main__':
    try:run()
    except Exception:results.update(status='failed',error=traceback.format_exc())
    (rootdir/'EDITOR-CHECK.json').write_text(json.dumps(results,indent=2))
    print(json.dumps(results,indent=2));raise SystemExit(results.get('status')!='passed')
